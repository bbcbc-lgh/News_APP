from pydantic import BaseModel

# 收藏相关的请求体模型
class FavoriteAdd(BaseModel):
    newsId: int
