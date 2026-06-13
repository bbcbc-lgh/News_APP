# Nexus AI 新闻系统

全栈 AI 资讯聚合 App，自动采集多平台 AI 技术新闻，使用 Claude Haiku 翻译为中文，支持新闻浏览、搜索、收藏、历史记录及用户管理。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11+、FastAPI、SQLAlchemy（异步）、MySQL |
| 前端 | Vue 3、TypeScript、Pinia、Vue Router、Vite |
| 采集 | httpx、feedparser（asyncio 定时，无需 Celery） |
| 翻译 | Claude Haiku（入库时自动翻译为中文） |

## 数据来源

| 平台 | 类型 | 采集频率 |
|------|------|----------|
| Hacker News | JSON API | 每 2 小时 |
| OpenAI Blog | RSS | 每 2 小时 |
| Google AI Blog | RSS | 每 2 小时 |
| MIT Technology Review | RSS | 每 2 小时 |

采集由 FastAPI `lifespan` 后台协程驱动，无需单独启动 Celery。前端头部刷新按钮可手动触发。

## 项目结构

```
News_APP/
├── backend/
│   ├── config/            # 数据库、Redis、环境变量配置
│   ├── crawler/           # 采集器
│   │   ├── base.py        # 入库基类（去重 + 翻译）
│   │   ├── rss_fetcher.py # RSS 采集
│   │   ├── hn_fetcher.py  # Hacker News 采集
│   │   └── scheduler.py   # （已弃用）原 Celery 任务
│   ├── crud/              # 数据库操作层
│   ├── migrations/        # 迁移脚本（无 alembic）
│   ├── models/            # SQLAlchemy ORM 模型
│   ├── routers/           # 路由层
│   ├── utils/
│   │   ├── response.py    # 统一响应格式
│   │   ├── security.py    # Token 认证 + 限流
│   │   └── translator.py  # Claude Haiku 翻译
│   ├── docs/              # 设计文档
│   ├── main.py            # 应用入口（含 lifespan 定时采集）
│   └── requirements.txt
└── frontend/
    └── src/
        ├── api/           # API 请求封装
        ├── stores/        # Pinia 状态管理
        ├── views/         # 页面组件
        └── router/        # 路由配置
```

## 本地运行

### 前置条件

- Python 3.11+
- Node.js 20+（pnpm）
- MySQL 8.0+

### 1. 克隆项目

```bash
git clone https://github.com/bbcbc-lgh/News_APP.git
cd News_APP
```

### 2. 配置后端环境变量

```bash
cd backend
cp .env.example .env
# 编辑 .env，填入数据库密码和翻译 API 配置
```

`.env` 关键配置项：

```env
DATABASE_URL=mysql+aiomysql://root:your_password@localhost:3306/news_app?charset=utf8mb4
ALLOWED_ORIGINS=http://localhost:5173
ANTHROPIC_API_KEY=your_key
ANTHROPIC_BASE_URL=https://your-proxy.com/v1
```

> `ANTHROPIC_BASE_URL` 若已含 `/v1`，系统会自动处理，不会重复拼接。

### 3. 安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 4. 初始化数据库

```bash
mysql -u root -p -e "CREATE DATABASE news_app CHARACTER SET utf8mb4;"
python migrations/migrate.py
```

### 5. 启动后端

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后自动开始首次采集，并每 2 小时采集一次。接口文档：http://localhost:8000/docs

### 6. 配置并启动前端

```bash
cd ../frontend
pnpm install
pnpm dev
```

前端地址：http://localhost:5173

## 主要接口

| 模块 | 方法 | 路径 | 说明 |
|---|---|---|---|
| 用户 | POST | /api/user/register | 注册 |
| 用户 | POST | /api/user/login | 登录 |
| 用户 | GET | /api/user/info | 获取当前用户信息 |
| 用户 | PUT | /api/user/update | 修改用户信息 |
| 新闻 | GET | /api/news/categories | 数据源列表 |
| 新闻 | GET | /api/news/list | 新闻列表（分页 + source 过滤） |
| 新闻 | GET | /api/news/detail | 新闻详情（含中文字段） |
| 新闻 | GET | /api/news/search | 关键词搜索 |
| 新闻 | POST | /api/news/refresh | 手动触发采集 |
| 收藏 | GET/POST/DELETE | /api/favorite/* | 收藏管理 |
| 历史 | GET/POST/DELETE | /api/history/* | 浏览历史管理 |

## 安全说明

- 登录/注册接口限流（每 IP 每分钟 10 次）
- 密码 bcrypt 哈希存储
- Token 登出后立即失效
- 敏感配置通过 `.env` 管理，不进入版本控制
