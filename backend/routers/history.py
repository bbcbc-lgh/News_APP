from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from config.database_conf import get_db
from crud.history import add_history, get_history, get_history_count, delete_history, clear_history
from schemas.history import HistoryAdd
from utils.security import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/api/history", tags=["history"])

# 添加历史记录接口
@router.post("/add")
async def add_history_endpoint(
    body: HistoryAdd,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    hist = await add_history(db, current_user.id, body.newsId)
    await db.commit()
    return success_response({
            "id": hist.id,
            "userId": current_user.id,
            "newsId": body.newsId,
            "viewTime": hist.view_time,
        }, "添加成功")

# 获取历史记录列表接口
@router.get("/list")
async def get_history_list(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    skip = (page - 1) * pageSize
    rows = await get_history(db, current_user.id, skip=skip, limit=pageSize)
    total = await get_history_count(db, current_user.id)

    items = [
        {
            "historyId": history_id,
            "id": news.id,
            "title": news.title,
            "description": news.description or "",
            "image": news.image or "",
            "author": news.author or "",
            "publishTime": news.publish_time,
            "categoryId": news.category_id,
            "views": news.views,
            "viewTime": view_time,
        }
        for news, view_time, history_id in rows
    ]

    return success_response({
            "list": items,
            "total": total,
            "hasMore": (skip + len(items)) < total,
        })

# 删除单条历史记录接口
@router.delete("/delete/{history_id}")
async def delete_history_endpoint(
    history_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    deleted = await delete_history(db, current_user.id, history_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="记录不存在")
    await db.commit()
    return success_response(message="删除成功")

# 清空历史记录接口
@router.delete("/clear")
async def clear_history_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await clear_history(db, current_user.id)
    await db.commit()
    return success_response(message="清空成功")
