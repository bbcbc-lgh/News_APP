from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.staticfiles import StaticFiles
from routers import news, user, favorite, history
from config.database_conf import async_engine
from config.env import get
from models.news import Base
import models.users
import models.favorite
import models.history
import os
from utils.response import http_exception_handler, validation_exception_handler

# 创建FastAPI应用
app = FastAPI(title="AI掘金头条新闻系统", version="1.0.0")

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

# 注册统一异常处理器（函数定义在 utils/response.py）
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# 包含路由
app.include_router(news.router)
app.include_router(user.router)
app.include_router(favorite.router)
app.include_router(history.router)

# 挂载静态文件目录，用于访问用户上传的头像等资源
# URL 路径：/static/avatars/<filename>
_static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(_static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")
