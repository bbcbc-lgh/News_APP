from datetime import datetime
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import DateTime, Integer
from models.news import Base


class ReadingProgress(Base):
    __tablename__ = "reading_progress"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey("news.id", ondelete="CASCADE"), primary_key=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    last_position: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
