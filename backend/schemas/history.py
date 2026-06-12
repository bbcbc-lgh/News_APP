from pydantic import BaseModel, Field

# 历史记录添加请求体
class HistoryAdd(BaseModel):
    newsId: int = Field(..., description="新闻ID")
