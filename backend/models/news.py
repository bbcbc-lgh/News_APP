from typing import Optional
from datetime import datetime
from sqlalchemy import Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.sql.sqltypes import DateTime, Integer, String, Text

# 基类
class Base(DeclarativeBase):
    pass

# 新闻分类类
class Category(Base):
    __tablename__ = "news_category"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="分类ID")
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable= False, comment="分类名称")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable= False, comment="排序")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 定义__repr__方法,方便调试时查看对象信息
    def __repr__(self):
        return f"<Category(name={self.name}, sort_order={self.sort_order})>"

# 新闻类
class News(Base):
    __tablename__ = "news"

    # 索引, 用于加速查询
    __table_args__ = (
        Index('fk_news_category_idx', 'category_id'),   # 高频访问字段
        Index('idx_publish_time', 'publish_time')       # 按发布时间升序
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="新闻ID")
    title: Mapped[str] = mapped_column(String(255), nullable=False, comment="新闻标题")
    description: Mapped[Optional[str]] = mapped_column(String(500), comment="新闻简介")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="新闻内容")
    image: Mapped[Optional[str]] = mapped_column(String(255), comment="封面图URL")
    author: Mapped[Optional[str]] = mapped_column(String(50), comment="作者")
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("news_category.id"), nullable=False, comment="分类ID")
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False,comment="浏览量")
    publish_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="发布时间")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<News(title={self.title})>"