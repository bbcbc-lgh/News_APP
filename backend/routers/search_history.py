from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from config.database_conf import get_db
from utils.security import get_current_user, get_optional_user
from models.users import User
from models.search_history import SearchHistory
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


@router.get("/suggestions")
async def get_suggestions(
    q: str = Query("", max_length=50),
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """按前缀返回搜索建议：用户历史 + 全局热词，合并去重，最多 8 条"""
    suggestions: list[str] = []

    # 用户历史匹配
    if current_user and q.strip():
        rows = await db.execute(
            select(SearchHistory.query)
            .where(SearchHistory.user_id == current_user.id, SearchHistory.query.like(f"{q}%"))
            .order_by(SearchHistory.created_at.desc())
            .limit(5)
        )
        suggestions = [r for r, in rows.all()]

    # 全局热词（搜索次数最多，去重用户历史已有的）
    seen = set(suggestions)
    popular_rows = await db.execute(
        select(SearchHistory.query, func.count(SearchHistory.id).label("cnt"))
        .group_by(SearchHistory.query)
        .order_by(text("cnt DESC"))
        .limit(20)
    )
    for (word, _) in popular_rows.all():
        if q and not word.startswith(q):
            continue
        if word not in seen:
            suggestions.append(word)
            seen.add(word)
        if len(suggestions) >= 8:
            break

    return success_response(suggestions)
