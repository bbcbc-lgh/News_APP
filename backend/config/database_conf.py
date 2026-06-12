from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config.env import get

# 数据库连接 URL，从环境变量读取，避免密码硬编码到代码里
ASYNC_DATABASE_URL = get("DATABASE_URL", "mysql+aiomysql://root:password@localhost:3306/news_app?charset=utf8mb4")

# 创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,
    pool_size=10,
    max_overflow=10,
)

# 创建异步会话工厂方法
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 依赖项：获取数据库会话
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()