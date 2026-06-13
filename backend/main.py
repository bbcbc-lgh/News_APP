from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio
import os
from routers import news, user, favorite, history
from config.database_conf import async_engine, AsyncSessionLocal
from config.env import get
from models.news import Base
import models.users
import models.favorite
import models.history
from utils.response import http_exception_handler, validation_exception_handler

FETCH_INTERVAL = 2 * 60 * 60  # 2小时
TOKEN_CLEANUP_INTERVAL = 24 * 60 * 60  # 24小时


async def _run_fetch():
    from crawler.rss_fetcher import fetch_all_rss
    from crawler.hn_fetcher import fetch_hn
    async with AsyncSessionLocal() as db:
        await fetch_all_rss(db)
        await fetch_hn(db)


async def _scheduler_loop():
    while True:
        try:
            await _run_fetch()
        except Exception as e:
            print(f"[scheduler] 采集出错: {e}")
        await asyncio.sleep(FETCH_INTERVAL)


async def _cleanup_tokens():
    """定期清理过期的 user_token 记录"""
    from sqlalchemy import text
    while True:
        await asyncio.sleep(TOKEN_CLEANUP_INTERVAL)
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(text("DELETE FROM user_token WHERE expire_time < NOW()"))
                await db.commit()
                print(f"[token_cleanup] 清理过期 token {result.rowcount} 条")
        except Exception as e:
            print(f"[token_cleanup] 清理出错: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    fetch_task = asyncio.create_task(_scheduler_loop())
    cleanup_task = asyncio.create_task(_cleanup_tokens())
    yield
    fetch_task.cancel()
    cleanup_task.cancel()


app = FastAPI(title="AI掘金头条新闻系统", version="1.0.0", lifespan=lifespan)

# 从环境变量读取允许的前端域名列表，多个域名用逗号分隔
# 生产环境应配置为具体域名，不能使用通配符 * 同时开启 allow_credentials
_origins_str = get("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8100")
ALLOWED_ORIGINS = [o.strip() for o in _origins_str.split(",") if o.strip()]

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_headers=["*"],
    allow_methods=