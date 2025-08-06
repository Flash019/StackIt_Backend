from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Question(BaseModel):
    title: str
    description: str  # rich text as HTML
    tags: List[str]
    author_id: str
    attachment_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
