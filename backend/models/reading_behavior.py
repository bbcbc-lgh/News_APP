from datetime import datetime
from sqlalchemy import Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime, Integer, String
from models.news import Base


class ReadingBehavior(Base):
    __tablename__ = "reading_behavior"
    __table_args__ = (
        Index('idx_user_time', 'user_id', 'created_at'),
        Index('idx_news', 'news_id'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="view/favorite/share/complete")
    duration: Mapped[int] = mapped_column(Integer, default=0, comment="阅读时长(秒)")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
