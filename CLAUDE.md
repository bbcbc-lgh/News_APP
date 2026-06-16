## 编码行为规范

### 一、先思考，再动手

**不要假设，不要隐藏困惑，主动暴露权衡。**

动手之前：
- 明确说出你的假设。不确定时，先问。
- 如果存在多种理解方式，把它们列出来，不要自己悄悄挑一个。
- 如果有更简单的方案，说出来，必要时推回去。
- 如果有不清楚的地方，停下来，说明哪里困惑，再问。

### 二、简单优先

**最少的代码解决问题，不写投机性代码。**

- 只实现被要求的功能，不多加。
- 单次使用的代码不做抽象。
- 没被要求的"灵活性"或"可配置性"不要加。
- 不可能发生的场景不做错误处理。
- 如果写了 200 行但 50 行够用，重写。

自检：「一个有经验的工程师会觉得这过于复杂吗？」如果是，简化。

### 三、外科手术式修改

**只动必须动的地方，只清理自己制造的乱。**

改已有代码时：
- 不"顺手优化"旁边的代码、注释或格式。
- 不重构没问题的东西。
- 匹配已有风格，即使你会做不同的选择。
- 发现无关的死代码，提一句，不要删。

自己的改动产生孤儿时：
- 删除因你的改动而变成无用的 import / 变量 / 函数。
- 不要删除改动前就已存在的死代码，除非被明确要求。

检验标准：每一行改动都能直接追溯到用户的需求。

### 四、目标驱动执行

**定义成功标准，循环直到验证通过。**

把任务转化为可验证的目标：
- "加校验" → "针对非法输入写测试，再让测试通过"
- "修 bug" → "写能复现 bug 的测试，再让测试通过"
- "重构 X" → "重构前后测试都通过"

多步任务先写简短计划：
```
1. [步骤] → 验证：[检查方式]
2. [步骤] → 验证：[检查方式]
3. [步骤] → 验证：[检查方式]
```
清晰的成功标准让你可以独立循环推进。模糊标准（"让它能跑"）需要不断追问确认。

# Nexus AI 新闻系统 — 项目指令

## 项目概览

全栈 AI 资讯聚合 App，后端 FastAPI + MySQL，前端 Vue 3 + TypeScript + Pinia + Vite。
数据源：Hacker News、OpenAI Blog、Google AI Blog、MIT Technology Review。

## 启动命令

```bash
# 后端
cd D:\News_APP\backend
.venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 前端
cd D:\News_APP\frontend
pnpm run dev

# 数据库迁移
cd D:\News_APP\backend
python migrations/migrate.py

# 手动触发采集
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

## 用户编码习惯

### 工作流偏好
- 回答要简洁，不用重复解释已完成的事
- 每次改动后自动执行 `pnpm run build` 验证，不报错再推送
- 改动完成后直接 `git add / commit / push`，不需要询问是否推送
- commit message 用中文，格式：`type: 说明`
- 任务多时主动用 subagent 并行处理提升效率

### 代码风格
- Vue 3 Composition API（`<script setup lang="ts">`）
- 不写多余注释，只在逻辑非显而易见时才写
- CSS 用 scoped，变量统一定义在 `App.vue` 的 `:root`
- 不引入新依赖，用项目已有的技术栈解决问题

### 前端设计偏好
- Light 主题：米白底色 `#F7F4EF`，琥珀色 accent `#C8860A`
- 字体：`Libre Baskerville`（标题）+ `JetBrains Mono`（等宽/标签）+ `Noto Serif SC` / `Noto Sans SC`（中文）
- 四个数据源各有专属颜色：HN `#E05D00`、OpenAI `#0D8A6A`、Google AI `#1A73E8`、MIT `#C0364D`
- 设计风格：editorial / 纸质感，避免通用 AI slop 设计
- 桌面端响应式（≥768px 侧边栏导航，内容区 960px），移动端 max-width 480px

### Git 习惯
- 直接推送到 `master`（个人项目，不需要 PR 流程）
- 不需要询问确认，改完直接提交推送

## 数据库注意事项

- MySQL 不支持 `ADD COLUMN IF NOT EXISTS`，迁移脚本需用 `information_schema` 检查列是否存在
- `source_platform` 字段值：`hackernews` / `openai` / `google_ai` / `mit`
- 迁移脚本放在 `backend/migrations/versions/`，命名格式 `000N_描述.py`
- **外键类型坑**：`user.id` 是 `INT UNSIGNED`（无符号），新建带外键的表时 `user_id` 必须用 `INT UNSIGNED`，否则报 `Referencing column and referenced column incompatible`。`news.id` 同理（建表前用 `SHOW CREATE TABLE` 确认）。

## 翻译服务

- 使用 Claude Haiku（`claude-haiku-4-5-20251001`）在爬虫入库时自动翻译
- 代理 base_url 已含 `/v1`，必须用 `httpx` 直接发请求，不能用 anthropic SDK（SDK 会重复拼接 `/v1`）
- 翻译逻辑在 `backend/utils/translator.py`，翻译字段：`title_zh` / `description_zh` / `content_zh`

## 不要做的事

- 不要修改 `.env` 文件
- 不要在 commit 中包含 `.env` 文件
- 不要用 `git add .`，要指定具体文件
- 不要在代码里硬编码数据库密码或 token

---

## UpGrade.md 升级文档执行策略

> 当任务涉及「逐步执行 `D:\News_APP\UpGrade.md` 中的优化点」时，遵循以下策略，确保可中断、可续接。

### 总体原则
- 文档结构：32 个功能点（Phase 1-6）+ 19 个技术债务点（高危/中危/低危）。
- 单次会话无法全部完成，必须保证「中断 → 续接」零成本。

### 执行顺序
1. 按 Phase 1 → Phase 6 顺序推进。
2. 每个 Phase 内，按工作量从小到大排序（先做轻量的）。
3. 技术债务点穿插在对应功能之后处理（例如「XSS 防护」在评论系统之前）。

### 单点执行流程（每个优化点都要走完）
1. **写代码** → 改动范围严格遵循 UpGrade.md 中标注的「改动范围」，不多做。
2. **构建验证** → `cd D:\News_APP\frontend && pnpm run build`（纯后端改动则跳过）。
3. **标记完成** → 在 `UpGrade.md` 对应小节标题**正下方**插入一行：
   ```
   > ✅ 已完成 2026-06-16（commit: <hash 短>）
   ```
   - 技术债务点同理，加在 `#### N. 标题` 标题下。
4. **提交** → 指定文件 `git add`（不用 `git add .`）+ 中文 commit message `feat: 说明` 或 `chore: 技术债务-说明`。
5. **更新任务** → TaskUpdate 标记该点为 completed。

### 跳过/延后规则
- 工作量标注 ≥1 周且依赖外部基础设施（如 Elasticsearch、Sentry、CDN）的点：在 UpGrade.md 标记 `> ⏸ 暂缓，需外部依赖`，跳过执行。
- 同一会话内连续完成 3-5 个点后主动停一下，让用户决定是否继续（避免单次消耗过多额度）。

### 续接检查清单（新会话开始时）
1. `grep -n "✅ 已完成" D:\News_APP\UpGrade.md` 确认进度。
2. `git log --oneline -20` 看最近提交，对照已完成点。
3. 找到第一个**未标记**的优化点继续。

### 完成标记格式（严格统一，便于 grep）
- 完成：`> ✅ 已完成 YYYY-MM-DD（commit: <hash>）`
- 暂缓：`> ⏸ 暂缓 YYYY-MM-DD（原因：<...>）`
- 部分完成：`> 🔶 部分完成 YYYY-MM-DD（剩余：<...>）`

---