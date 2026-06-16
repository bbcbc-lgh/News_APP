from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from config.database_conf import get_db
from utils.security import get_current_user
from models.users import User
from schemas.reading_behavior import BehaviorReport
from utils.response import success_response
from crud.reading_behavior import report_behavior, get_user_stats

router = APIRouter(prefix="/api/reading", tags=["reading-behavior"])

PERIOD_DAYS = {"today": 1, "week": 7, "month": 30, "all": None}


@router.post("/behavior")
async def report_behavior_endpoint(
    body: BehaviorReport,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await report_behavior(
        db, user_id=current_user.id, news_id=body.newsId,
        action_type=body.actionType, duration=body.duration,
    )
    return success_response(message="已记录")


@router.get("/stats")
async def get_stats(
    period: str = Query("week", pattern="^(today|week|month|all)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    days = PERIOD_DAYS.get(period)
    stats = await get_user_stats(db, user_id=current_user.id, days=days)
    return success_response(stats)
