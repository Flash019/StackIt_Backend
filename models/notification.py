from pydantic import BaseModel, Field
from datetime import datetime

class Notification(BaseModel):
    user_id: str
    message: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
