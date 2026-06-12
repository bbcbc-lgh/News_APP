# AI 掘金头条新闻系统

全栈 AI 资讯 App，聚合多平台实时 AI 技术新闻，支持新闻浏览、搜索、收藏、历史记录及用户管理。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11+、FastAPI、SQLAlchemy（异步）、MySQL、Redis |
| 前端 | Vue 3、TypeScript、Pinia、Vue Router、Vite |
| 采集 | Celery、feedparser、httpx |

## 数据来源

| 平台 | 类型 | 采集频率 |
|------|------|----------|
| Hacker News | JSON API | 每1小时 |
| OpenAI Blog | RSS | 每2小时 |
| Google AI Blog | RSS | 每2小时 |
| MIT Technology Review | RSS | 每2小时 |

## 项目结构

```
News_APP/
├── backend-FastAPI/
│   ├── config/            # 数据库、Redis、环境变量配置
│   ├── crawler/           # 采集器模块
│   │   ├── base.py        # 入库基类
│   │   ├── filters.py     # AI关键词过滤
│   │   ├── rss_fetcher.py # RSS采集（OpenAI/Google/MIT）
│   │   ├── hn_fetcher.py  # Hacker News采集
│   │   └── scheduler.py   # Celery定时任务
│   ├── crud/              # 数据库操作层
│   ├── migrations/        # 数据库迁移脚本
│   ├── models/            # SQLAlchemy ORM 模型
│   ├── routers/           # 路由层（接口定义）
│   ├── schemas/           # Pydantic 请求/响应模型
│   ├── static/            # 静态文件（用户头像等）
│   ├── utils/             # 工具函数（鉴权、限流、统一响应）
│   ├── main.py            # 应用入口
│   ├── requirements.txt   # 依赖列表
│   └── .env.example       # 环境变量模板
└── frontend-Vue/
    ├── src/
    │   ├── api/           # API 请求封装
    │   ├── stores/        # Pinia 状态管理
    │   ├── views/         # 页面组件
    │   └── router/        # 路由配置
    └── .env.example       # 前端环境变量模板
```

## 本地运行

### 前置条件

- Python 3.11+
- Node.js 18+（pnpm）
- MySQL 8.0+
- Redis 6+

### 1. 克隆项目

```bash
git clone https://github.com/bbcbc-lgh/News_APP.git
cd News_APP
```

### 2. 配置后端环境变量

```bash
cd backend-FastAPI
cp .env.example .env
# 编辑 .env，填入你的数据库密码和相关配置
```

`.env` 关键配置项：

```env
DATABASE_URL=mysql+aiomysql://root:your_password@localhost:3306/my_first_app?charset=utf8mb4
REDIS_HOST=localhost
REDIS_PORT=6379
ALLOWED_ORIGINS=http://localhost:5173
BASE_URL=http://localhost:8000
```

### 3. 安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 4. 初始化数据库

```bash
# 在 MySQL 中创建数据库
mysql -u root -p -e "CREATE DATABASE my_first_app CHARACTER SET utf8mb4;"

# 执行迁移（建表）
python migrations/migrate.py

# 查看迁移状态
python migrations/migrate.py --status
```

### 5. 启动后端

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

接口文档：http://localhost:8000/docs

### 6. 启动采集器

需要开两个终端分别启动 Celery worker 和定时调度：

```bash
# 终端1：启动 worker
celery -A crawler.scheduler worker --loglevel=info

# 终端2：启动定时调度
celery -A crawler.scheduler beat --loglevel=info
```

手动触发一次采集（测试用）：

```bash
python -c "
import asyncio
from config.database_conf import AsyncSessionLocal
from crawler.rss_fetcher import fetch_all_rss
from crawler.hn_fetcher import fetch_hn

async def main():
    async with AsyncSessionLocal() as db:
        await fetch_all_rss(db)
        await fetch_hn(db)

asyncio.run(main())
"
```

### 7. 配置并启动前端

```bash
cd ../frontend-Vue
pnpm install
pnpm dev
```

前端地址：http://localhost:5173

## 主要接口

| 模块 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 用户 | POST | /api/user/register | 注册 |
| 用户 | POST | /api/user/login | 登录 |
| 用户 | POST | /api/user/logout | 登出 |
| 用户 | GET | /api/user/info | 获取当前用户信息 |
| 用户 | PUT | /api/user/update | 修改用户信息 |
| 用户 | PUT | /api/user/password | 修改密码 |
| 用户 | POST | /api/user/avatar | 上传头像 |
| 新闻 | GET | /api/news/categories | 新闻分类列表 |
| 新闻 | GET | /api/news/list | 新闻列表（分页，支持 source 过滤） |
| 新闻 | GET | /api/news/detail | 新闻详情 |
| 新闻 | GET | /api/news/search | 关键词搜索 |
| 收藏 | GET/POST/DELETE | /api/favorite/* | 收藏管理 |
| 历史 | GET/POST/DELETE | /api/history/* | 浏览历史管理 |

## 安全说明

- 登录/注册接口有限流保护（每 IP 每分钟最多 10 次）
- 密码使用 bcrypt 哈希存储
- Token 登出后立即失效
- 敏感配置全部通过 `.env` 管理，不进入版本控制
