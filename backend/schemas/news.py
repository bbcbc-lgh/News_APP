from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# 新闻分类响应模型
class CategoryResponse(BaseModel):
    id: int
    name: str
    sort_order: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

# 新闻列表项响应模型
class NewsListItem(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    image: Optional[str] = None
    author: Optional[str] = None
    category_id: int
    views: int
    publish_time: datetime
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
