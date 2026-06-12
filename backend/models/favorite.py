from datetime import datetime
from sqlalchemy import Index, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime, Integer
from models.news import Base


class Favorite(Base):
    # 收藏表，记录用户收藏的新闻
    __tablename__ = "favorite"
    # 通过联合唯一约束确保同一用户对同一新闻只能有一条收藏记录，同时为 user_id 创建索引以优化查询性能
    __table_args__ = (
        UniqueConstraint('user_id', 'news_id', name='uq_user_news_favorite'),
        Index('idx_favorite_user', 'user_id'),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
