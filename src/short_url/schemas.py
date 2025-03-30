from datetime import datetime

from pydantic import BaseModel
from typing import Optional

class LinkCreate(BaseModel):
    original_url: str
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

class LinkUpdate(BaseModel):
    original_url: str

class LinkStats(BaseModel):
    original_url: str
    created_at: datetime
    click_count: int
    last_accessed: datetime
