"""
集成测试配置：直连真实 MySQL，测试数据用唯一前缀，每个测试后清理。
使用 NullPool 避免连接复用导致的 aiomysql EOF 问题（Windows pytest-asyncio 已知限制）。
"""
import asyncio
import sys
import pytest
import pytest_asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from httpx import AsyncClient, ASGITransport
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.database_conf import get_db, ASYNC_DATABASE_URL
from utils.security import auth_rate_limit
from main import app

TEST_PREFIX = "test_ci_"

# 测试专用引擎：NullPool 禁止连接复用，每次请求用完即关闭
_test_engine = create_async_engine(ASYNC_DATABASE_URL, poolclass=NullPool)
_TestSession = async_sessionmaker(bind=_test_engine, class_=AsyncSession, expire_on_commit=False)


async def _override_get_db():
    async with _TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def cleanup_test_users(username: str = None):
    async with _TestSession() as db:
        from sqlalchemy import text
        if username:
            await db.execute(text("DELETE FROM user WHERE username = :u"), {"u": username})
        else:
            await db.execute(text("DELETE FROM user WHERE username LIKE :p"), {"p": f"{TEST_PREFIX}%"})
        await db.commit()


@pytest_asyncio.fixture(autouse=True)
async def override_db():
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[auth_rate_limit] = lambda: None  # 测试时跳过限流
    yield
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(auth_rate_limit, None)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


@pytest_asyncio.fixture
async def auth_client():
    import uuid
    username = f"{TEST_PREFIX}{uuid.uuid4().hex[:8]}"
    password = "Test1234!"

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        await c.post("/api/user/register", json={"username": username, "password": password})
        resp = await c.post("/api/user/login", json={"username": username, "password": password})
        token = resp.json().get("data", {}).get("token", "")
        c.headers.update({"Authorization": token})
        c._test_username = username
        yield c

    await cleanup_test_users(username)

