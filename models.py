from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class Memory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    type: str  # 'user', 'internet', 'action'
    content: str
    source: Optional[str] = None
    added_at: datetime = Field(default_factory=datetime.utcnow)