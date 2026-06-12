import secrets
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import User, UserToken

# 根据用户名获取用户
async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

# 创建新用户
async def create_user(db: AsyncSession, username: str, password_hash: str) -> User:
    user = User(username=username, password_hash=password_hash)
    db.add(user)
    # 需要先flush以获取user.id，才能创建关联的token
    await db.flush()
    return user

# 创建访问令牌
async def create_token(db: AsyncSession, user_id: int) -> str:
    # 生成一个随机的令牌，设置过期时间为7天
    token = secrets.token_hex(32)
    expire_time = datetime.now() + timedelta(days=7)
    # 创建UserToken对象并添加到数据库
    user_token = UserToken(user_id=user_id, token=token, expire_time=expire_time)
    db.add(user_token)
    # 需要flush以确保token被写入数据库，才能在后续验证时查询到
    await db.flush()
    return token

# 根据令牌获取用户
async def get_user_by_token(db: AsyncSession, token: str) -> User | None:
    result = await db.execute(
        select(User)
        .join(UserToken, UserToken.user_id == User.id)
        .where(UserToken.token == token)
        .where(UserToken.expire_time > datetime.now())
    )
    return result.scalar_one_or_none()

# 删除指定 token，用于登出
async def delete_token(db: AsyncSession, token: str) -> bool:
    result = await db.execute(
        select(UserToken).where(UserToken.token == token)
    )
    user_token = result.scalar_one_or_none()
    if not user_token:
        return False
    await db.delete(user_token)
    await db.flush()
    return True


# 更新用户信息
async def update_user(db: AsyncSession, user_id: int, **kwargs) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    for key, value in kwargs.items():
        if value is not None:
            setattr(user, key, value)
    # 需要flush以将更新写入数据库，才能在后续查询时获取到最新数据
    await db.flush()
    # 刷新用户对象以获取最新数据，特别是当数据库触发器或默认值可能修改了数据时
    await db.refresh(user)
    return user

# 更新用户密码
async def update_password(db: AsyncSession, user_id: int, new_password_hash: str) -> bool:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.password_hash = new_password_hash
    # 需要flush以将更新写入数据库，才能在后续验证时获取到最新密码哈希
    await db.flush()
    return True
