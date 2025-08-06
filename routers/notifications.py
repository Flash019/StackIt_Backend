from fastapi import APIRouter, HTTPException, Depends, status
from bson import ObjectId
from database import db
from utils.auth import decode_access_token
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime

router = APIRouter(tags=["Notification"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

#  Get all notifications (secure)
@router.get("/notifications")
def get_notifications(current_user=Depends(get_current_user)):
    user_id = current_user["user_id"]

    # Try both ObjectId and string for user_id compatibility
    try:
        object_id = ObjectId(user_id)
        query = {"user_id": {"$in": [object_id, user_id]}}
    except Exception:
        query = {"user_id": user_id}

    notifications = list(db.notifications.find(query).sort("timestamp", -1))

    for n in notifications:
        n["_id"] = str(n["_id"])
        n["user_id"] = str(n["user_id"])
        n["question_id"] = str(n.get("question_id")) if n.get("question_id") else None
        n["answer_id"] = str(n.get("answer_id")) if n.get("answer_id") else None
        n["timestamp"] = n.get("timestamp").isoformat() if n.get("timestamp") else None
        n["type"] = n.get("type", "generic")
        n["message"] = n.get("message", "You have a new notification")

    return notifications

#  Mark all as read (secure)
@router.post("/notifications/mark_read")
def mark_notifications_read(current_user=Depends(get_current_user)):
    user_id = current_user["user_id"]

    try:
        object_id = ObjectId(user_id)
        query = {"user_id": {"$in": [object_id, user_id]}}
    except Exception:
        query = {"user_id": user_id}

    result = db.notifications.update_many(
        query,
        {"$set": {"is_read": True}}
    )

    return {
        "message": "All notifications marked as read",
        "matched": result.matched_count,
        "modified": result.modified_count
    }
