from pydantic import BaseModel, Field


class BehaviorReport(BaseModel):
    newsId: int
    actionType: str = Field(..., pattern="^(view|favorite|share|complete)$")
    duration: int = Field(0, ge=0, le=86400)
