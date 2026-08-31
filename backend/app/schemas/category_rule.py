from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CategoryRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keyword: str
    match_type: str
    category_id: int
    priority: int
    enabled: bool
    source: str
    created_at: datetime


class CategoryRuleCreate(BaseModel):
    keyword: str
    category_id: int
    match_type: str = "CONTAINS"
    priority: int = 0
    enabled: bool = True


class CategoryRuleUpdate(BaseModel):
    keyword: str | None = None
    category_id: int | None = None
    match_type: str | None = None
    priority: int | None = None
    enabled: bool | None = None
