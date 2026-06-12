from sqlalchemy import Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime, Integer
from datetime import datetime
from models.news import Base


class History(Base):
    __tablename__ = "history"
    __table_args__ = (Index('idx_history_user', 'user_id'),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey("news.id", ondelete="CASCADE"), nullable=False)
    view_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="浏览时间")
