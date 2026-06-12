"""
安全相关工具
- auth_rate_limit: 登录/注册接口限流依赖项（滑动窗口，纯内存）
- get_current_user: 从 Authorization 请求头解析并验证当前用户
"""
import time
from collections import defaultdict
from fastapi import Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from config.database_conf import get_db
from crud.users import get_user_by_token


# ── 限流 ────────────────────────────────────────────────────────────────────

class RateLimiter:
    """
    滑动窗口限流器
    window_seconds: 时间窗口大小（秒）
    max_requests:   窗口内最大请求次数
    """

    def __init__(self, window_seconds: int = 60, max_requests: int = 10):
        self.window = window_seconds
        self.max_requests = max_requests
        # 格式：{ip: [timestamp1, timestamp2, ...]}
        self._records: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, ip: str) -> bool:
        """判断该 IP 是否在限额内，同时清理过期记录"""
        now = time.time()
        cutoff = now - self.window
        self._records[ip] = [t for t in self._records[ip] if t > cutoff]
        if len(self._records[ip]) >= self.max_requests:
            return False
        self._records[ip].append(now)
        return True


# 登录/注册专用限流实例：每 IP 每分钟最多 10 次
_auth_limiter = RateLimiter(window_seconds=60, max_requests=10)


def auth_rate_limit(request: Request):
    """FastAPI 依赖项，用于登录/注册接口的限流检查"""
    ip = request.client.host if request.client else "unknown"
    if not _auth_limiter.is_allowed(ip):
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁，请稍后再试",
        )


# ── 认证 ────────────────────────────────────────────────────────────────────

async def get_current_user(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """FastAPI 依赖项，验证 Authorization 请求头中的 token 并返回当前用户"""
    user = await get_user_by_token(db, authorization)
    if not user:
        raise HTTPException(status_code=401, detail="未登录或登录已过期")
    return user
