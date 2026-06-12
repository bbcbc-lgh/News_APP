import json
import redis.asyncio as aioredis
from typing import Optional, Any
from config.env import get

# Redis 配置，从环境变量读取，未配置时回退到本地默认值
REDIS_HOST = get("REDIS_HOST", "localhost")
REDIS_PORT = int(get("REDIS_PORT", "6379"))
REDIS_DB   = int(get("REDIS_DB", "0"))

# Cache键前缀
TTL_NEWS_DETAIL = 3600      # 1 hour
TTL_NEWS_LIST = 1800        # 30 minutes
TTL_CATEGORIES = 7200       # 2 hours
TTL_HISTORY = 3600          # 1 hour

# Redis实例
_redis_client: Optional[aioredis.Redis] = None

# 获取Redis连接
async def get_redis() -> Optional[aioredis.Redis]:
    global _redis_client
    if _redis_client is None:
        try:
            client = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
            await client.ping()
            _redis_client = client
        except Exception:
            return None
    return _redis_client

# Cache操作
async def cache_get(key: str) -> Optional[Any]:
    client = await get_redis()
    if not client:
        return None
    try:
        val = await client.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None

# Cache设置，默认TTL为300秒（5分钟）
async def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    client = await get_redis()
    if not client:
        return False
    try:
        await client.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception:
        return False

# Cache删除
async def cache_delete(key: str) -> bool:
    client = await get_redis()
    if not client:
        return False
    try:
        await client.delete(key)
        return True
    except Exception:
        return False

# Cache删除模式匹配的键
async def cache_delete_pattern(pattern: str) -> int:
    client = await get_redis()
    if not client:
        return 0
    try:
        keys = await client.keys(pattern)
        if keys:
            return await client.delete(*keys)
        return 0
    except Exception:
        return 0
