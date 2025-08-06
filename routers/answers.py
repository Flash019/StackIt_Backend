from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from database import db
from models.answer import Answer
from routers.notifications_ws import send_notification
from utils.auth import decode_access_token
from datetime import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
router = APIRouter(tags=["Answers"])

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload  # contains user_id, email, etc.

@router.post("/answers")
async def post_answer(answer: Answer, current_user=Depends(get_current_user)):
    user_id = current_user["user_id"]

    #  Validate and convert question_id
    try:
        question_obj_id = ObjectId(answer.question_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid question_id format")

    #  Check if question exists
    question = db.questions.find_one({"_id": question_obj_id})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    #  Prepare answer data
    answer_data = {
        "question_id": question_obj_id,
        "user_id": ObjectId(user_id),
        "content": answer.content,
        "timestamp": datetime.utcnow()
    }

    # Save answer
    result = db.answers.insert_one(answer_data)
    answer_id = result.inserted_id

    #  Skip notification if user answers their own question
    question_owner_id = str(question["author_id"])
    if question_owner_id != user_id:
        #  Save notification in DB
        db.notifications.insert_one({
            "user_id": question["author_id"],
            "question_id": question_obj_id,
            "answer_id": answer_id,
            "message": answer.content[:200],
            "is_read": False,
            "timestamp": datetime.utcnow()
        })

        #  Send WebSocket notification
        await send_notification(question_owner_id, {
            "type": "new_answer",
            "question_id": str(question_obj_id),
            "answer_id": str(answer_id),
            "message": answer.content[:100],
            "timestamp": datetime.utcnow().isoformat()
        })

    return {
        "message": "Answer posted successfully",
        "answer_id": str(answer_id)
    }
