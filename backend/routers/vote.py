from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from config.database_conf import get_db
from utils.response import success_response
from utils.security import get_current_user

router = APIRouter(prefix="/api/news", tags=["vote"])


class VoteIn(BaseModel):
    value: int  # 1 或 -1，0 表示撤销


@router.post("/{news_id}/vote")
async def cast_vote(
    news_id: int = Path(...),
    body: VoteIn = ...,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uid = current_user.id

    # 查询已有投票
    row = await db.execute(text(
        "SELECT value FROM vote WHERE user_id = :uid AND news_id = :nid"
    ), {"uid": uid, "nid": news_id})
    old = row.scalar()

    if body.value == 0:
        # 撤销
        if old is not None:
            await db.execute(text(
                "DELETE FROM vote WHERE user_id = :uid AND news_id = :nid"
            ), {"uid": uid, "nid": news_id})
            col = "upvotes" if old == 1 else "downvotes"
            await db.execute(text(
                f"UPDATE news SET {col} = GREATEST(0, {col} - 1) WHERE id = :nid"
            ), {"nid": news_id})
    elif body.value in (1, -1):
        if old is None:
            await db.execute(text(
                "INSERT INTO vote (user_id, news_id, value) VALUES (:uid, :nid, :v)"
            ), {"uid": uid, "nid": news_id, "v": body.value})
        elif old != body.value:
            await db.execute(text(
                "UPDATE vote SET value = :v WHERE user_id = :uid AND news_id = :nid"
            ), {"v": body.value, "uid": uid, "nid": news_id})
            # 旧方向 -1，新方向 +1
            old_col = "upvotes" if old == 1 else "downvotes"
            new_col = "upvotes" if body.value == 1 else "downvotes"
            await db.execute(text(
                f"UPDATE news SET {old_col} = GREATEST(0, {old_col} - 1), {new_col} = {new_col} + 1 WHERE id = :nid"
            ), {"nid": news_id})
        else:
            # 相同投票，幂等，无需操作
            return success_response(None, "已投票")
        if old is None:
            new_col = "upvotes" if body.value == 1 else "downvotes"
            await db.execute(text(
                f"UPDATE news SET {new_col} = {new_col} + 1 WHERE id = :nid"
            ), {"nid": news_id})

    await db.commit()

    # 返回最新计数
    counts = await db.execute(text(
        "SELECT upvotes, downvotes FROM news WHERE id = :nid"
    ), {"nid": news_id})
    r = counts.fetchone()
    user_vote = body.value if body.value != 0 else None
    if body.value == 0:
        user_vote_row = await db.execute(text(
            "SELECT value FROM vote WHERE user_id = :uid AND news_id = :nid"
        ), {"uid": uid, "nid": news_id})
        user_vote = user_vote_row.scalar()
    return success_response({
        "upvotes": r[0] if r else 0,
        "downvotes": r[1] if r else 0,
        "userVote": user_vote,
    }, "投票成功")


@router.get("/{news_id}/vote")
async def get_vote(
    news_id: int = Path(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await db.execute(text(
        "SELECT value FROM vote WHERE user_id = :uid AND news_id = :nid"
    ), {"uid": current_user.id, "nid": news_id})
    user_vote = row.scalar()
    counts = await db.execute(text(
        "SELECT upvotes, downvotes FROM news WHERE id = :nid"
    ), {"nid": news_id})
    r = counts.fetchone()
    return success_response({
        "upvotes": r[0] if r else 0,
        "downvotes": r[1] if r else 0,
        "userVote": user_vote,
    })
