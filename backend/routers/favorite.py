from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from config.database_conf import get_db
from utils.security import get_current_user
from models.users import User
from schemas.favorite import FavoriteAdd
from utils.response import success_response
from crud.favorite import (
    check_favorite,
    add_favorite,
    remove_favorite,
    get_favorites,
    get_favorites_count,
    clear_favorites,
)

router = APIRouter(prefix="/api/favorite", tags=["favorite"])

# 检查用户是否已收藏某条新闻，返回布尔值
@router.get("/check")
async def check_favorite_status(
    newsId: int = Query(..., alias="newsId"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_fav = await check_favorite(db, user_id=current_user.id, news_id=newsId)
    return success_response({"isFavorite": is_fav})

# 添加收藏记录，并返回新创建的 Favorite 对象
@router.post("/add")
async def add_favorite_endpoint(
    body: FavoriteAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 首先检查是否已经收藏过，如果已经收藏则返回错误提示
    already = await check_favorite(db, user_id=current_user.id, news_id=body.newsId)
    if already:
        raise HTTPException(status_code=400, detail="已收藏")
    # 添加收藏记录，并返回新创建的 Favorite 对象
    fav = await add_favorite(db, user_id=current_user.id, news_id=body.newsId)
    return success_response({
            "id": fav.id,
            "userId": fav.user_id,
            "newsId": fav.news_id,
            "createTime": fav.created_at,
        }, "收藏成功")

# 移除收藏记录，返回是否成功删除
@router.delete("/remove")
async def remove_favorite_endpoint(
    newsId: int = Query(..., alias="newsId"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 首先检查是否已经收藏过，如果没有收藏则返回错误提示
    removed = await remove_favorite(db, user_id=current_user.id, news_id=newsId)
    if not removed:
        raise HTTPException(status_code=404, detail="收藏记录不存在")
    # 成功删除收藏记录
    return success_response(message="取消收藏成功")

# 获取用户的收藏列表
@router.get("/list")
async def list_favorites(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, alias="pageSize", ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 计算分页参数
    skip = (page - 1) * pageSize
    rows = await get_favorites(db, user_id=current_user.id, skip=skip, limit=pageSize)
    total = await get_favorites_count(db, user_id=current_user.id)
    items = [
        {
            "id": news.id,
            "title": news.title,
            "description": news.description,
            "image": news.image,
            "author": news.author,
            "publishTime": news.publish_time,
            "categoryId": news.category_id,
            "views": news.views,
            "favoriteTime": fav_time,
        }
        for news, fav_time in rows
    ]

    return success_response({
            "list": items,
            "total": total,
            "hasMore": (skip + len(items)) < total,
        })

# 清空用户的所有收藏记录，返回删除的记录数
@router.delete("/clear")
async def clear_favorites_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await clear_favorites(db, user_id=current_user.id)
    return success_response(message=f"成功删除{count}条收藏记录")
