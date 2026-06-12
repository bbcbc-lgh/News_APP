"""
Celery 定时采集任务
启动方式：
  celery -A crawler.scheduler worker --loglevel=info
  celery -A crawler.scheduler beat --loglevel=info
"""
import asyncio
from celery import Celery
from celery.schedules import crontab
from config.env import get

REDIS_HOST = get("REDIS_HOST", "localhost")
REDIS_PORT = get("REDIS_PORT", "6379")
REDIS_DB   = get("REDIS_DB", "0")
BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

app = Celery("crawler", broker=BROKER_URL, backend=BROKER_URL)

app.conf.beat_schedule = {
    "fetch-rss-every-2h": {
        "task": "crawler.scheduler.task_fetch_rss",
        "schedule": crontab(minute=0, hour="*/2"),
    },
    "fetch-hn-every-1h": {
        "task": "crawler.scheduler.task_fetch_hn",
        "schedule": crontab(minute=30, hour="*"),
    },
}
app.conf.timezone = "Asia/Shanghai"


def _run(coro):
    """在同步 Celery task 中运行异步函数"""
    return asyncio.get_event_loop().run_until_complete(coro)


@app.task(name="crawler.scheduler.task_fetch_rss")
def task_fetch_rss():
    from config.database_conf import AsyncSessionLocal
    from crawler.rss_fetcher import fetch_all_rss

    async def _inner():
        async with AsyncSessionLocal() as db:
            return await fetch_all_rss(db)

    result = _run(_inner())
    print(f"[RSS] 采集完成: {result}")
    return result


@app.task(name="crawler.scheduler.task_fetch_hn")
def task_fetch_hn():
    from config.database_conf import AsyncSessionLocal
    from crawler.hn_fetcher import fetch_hn

    async def _inner():
        async with AsyncSessionLocal() as db:
            return await fetch_hn(db)

    count = _run(_inner())
    print(f"[HN] 采集完成: 新增 {count} 条")
    return count
