from datetime import datetime
from sqlalchemy import Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime, Integer, String
from models.news import Base

# 用户表
class User(Base):
    __tablename__ = "user"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, comment="用户名")
    password_hash: Mapped[str] = mapped_column("password", String(255), nullable=False, comment="密码哈希")
    nickname: Mapped[str | None] = mapped_column(String(50), comment="昵称")
    avatar: Mapped[str | None] = mapped_column(String(255), default="https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg", comment="头像URL")
    gender: Mapped[str] = mapped_column(String(10), default="unknown", comment="性别: male/female/unknown")
    bio: Mapped[str | None] = mapped_column(String(200), default="这个人很懒，什么都没留下", comment="个人简介")
    phone: Mapped[str | None] = mapped_column(String(20), comment="手机号")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

# 用户令牌表
class UserToken(Base):
    __tablename__ = "user_token"
    __table_args__ = (Index('idx_token', 'token'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, comment="访问令牌")
    expire_time: Mapped[datetime] = mapped_column("expires_at", DateTime, nullable=False, comment="过期时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
