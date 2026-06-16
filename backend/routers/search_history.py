from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from config.database_conf import get_db
from utils.security import get_current_user
from models.users import User
from schemas.search_history import SearchHistoryAdd
from utils.response import success_response
from crud.search_history import (
    add_search,
    get_search_history,
    delete_search_history_one,
    clear_search_history,
)

router = APIRouter(prefix="/api/search/history", tags=["search-history"])


@router.post("")
async def add_search_endpoint(
    body: SearchHistoryAdd,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = body.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="查询不能为空")
    record = await add_search(db, user_id=current_user.id, query=query)
    return success_response({
        "id": record.id,
        "query": record.query,
        "createdAt": record.created_at,
    }, "已记录")


@router.get("")
async def list_search_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items = await get_search_history(db, user_id=current_user.id, limit=limit)
    return success_response({
        "list": [
            {"id": h.id, "query": h.query, "createdAt": h.created_at}
            for h in items
        ]
    })


@router.delete("/{history_id}")
async def delete_one(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_search_history_one(db, user_id=current_user.id, history_id=history_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="记录不存在")
    return success_response(message="已删除")


@router.delete("")
async def clear_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count = await clear_search_history(db, user_id=current_user.id)
    return success_response(message=f"已清空 {count} 条记录")
