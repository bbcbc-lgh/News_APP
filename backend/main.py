from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from contextlib import asynccontextmanager
import asyncio
import os
from routers import news, user, favorite, history, search_history, reading_queue, favorite_folder, reading_behavior, topic_tag, reading_progress, vote, comment, user_follow
from config.database_conf import async_engine, AsyncSessionLocal
from config.env import get
from models.news import Base
import models.users
import models.favorite
import models.history
import models.search_history
import models.reading_queue
import models.favorite_folder
import models.reading_behavior
import models.topic_tag
import models.reading_progress
import models.vote
import models.comment
import models.user_follow
from utils.response import http_exception_handler, validation_exception_handler

FETCH_INTERVAL = 2 * 60 * 60  # 2小时
TOKEN_CLEANUP_INTERVAL = 24 * 60 * 60  # 24小时
FETCH_LOCK = asyncio.Lock()


async def _run_fetch():
    if FETCH_LOCK.locked():
        print("[scheduler] 已有采集任务在运行，跳过本次触发")
        return False
    from crawler.rss_fetcher import fetch_all_rss
    from crawler.hn_fetcher import fetch_hn
    from crawler.arxiv_fetcher import fetch_arxiv
    async with FETCH_LOCK:
        async with AsyncSessionLocal() as db:
            await fetch_all_rss(db)
            await fetch_hn(db)
            await fetch_arxiv(db)
    return True


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
    allow_methods=["*"],
    allow_credentials=True,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'"
        )
        return response


app.add_middleware(SecurityHeadersMiddleware)

# 注册统一异常处理器（函数定义在 utils/response.py）
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# 包含路由
app.include_router(news.router)
app.include_router(user.router)
app.include_router(favorite.router)
app.include_router(favorite_folder.router)
app.include_router(history.router)
app.include_router(search_history.router)
app.include_router(reading_queue.router)
app.include_router(reading_behavior.router)
app.include_router(topic_tag.router)
app.include_router(reading_progress.router)
app.include_router(vote.router)
app.include_router(comment.router)
app.include_router(user_follow.router)

# 挂载静态文件目录，用于访问用户上传的头像等资源
# URL 路径：/static/avatars/<filename>
_static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(_static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")
