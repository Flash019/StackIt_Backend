from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Answer(BaseModel):
    question_id: str
    author_id: str
    content: str  # rich text as HTML
    created_at: datetime = Field(default_factory=datetime.utcnow)
    upvotes: int = 0
    downvotes: int = 0
    is_accepted: bool = False
