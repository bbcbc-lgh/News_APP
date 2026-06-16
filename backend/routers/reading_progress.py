from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from config.database_conf import get_db
from utils.response import success_response
from utils.security import get_current_user

router = APIRouter(prefix="/api/reading-progress", tags=["reading-progress"])


class ProgressIn(BaseModel):
    news_id: int
    progress: int   # 0-100
    last_position: int = 0


@router.post("")
async def save_progress(
    body: ProgressIn,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(text("""
        INSERT INTO reading_progress (user_id, news_id, progress, last_position, updated_at)
        VALUES (:uid, :nid, :prog, :pos, NOW())
        ON DUPLICATE KEY UPDATE progress = :prog, last_position = :pos, updated_at = NOW()
    """), {"uid": current_user.id, "nid": body.news_id, "prog": body.progress, "pos": body.last_position})
    await db.commit()
    return success_response(None, "进度已保存")


@router.get("/{news_id}")
async def get_progress(
    news_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await db.execute(text("""
        SELECT progress, last_position FROM reading_progress
        WHERE user_id = :uid AND news_id = :nid
    """), {"uid": current_user.id, "nid": news_id})
    r = row.fetchone()
    if r:
        return success_response({"progress": r[0], "lastPosition": r[1]})
    return success_response({"progress": 0, "lastPosition": 0})
