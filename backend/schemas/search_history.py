from pydantic import BaseModel, Field


class SearchHistoryAdd(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
