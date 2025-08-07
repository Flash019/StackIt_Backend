from fastapi import APIRouter, HTTPException, Body, Depends, status
from bson import ObjectId
from datetime import datetime
from database import db
from utils.auth import get_current_user  # This should return the user dict with "user_id"
from fastapi.security import OAuth2PasswordBearer
from utils.auth import decode_access_token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter(tags=["Users Can Flag a Question and Answer "])

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload  # contains user_id, email, etc.


@router.post("/questions/{question_id}/flag")
def user_flag_question(
    question_id: str,
    reason: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_user)
):
    try:
        question_obj_id = ObjectId(question_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid question ID")

    questions_collection = db["questions"]
    question = questions_collection.find_one({"_id": question_obj_id})

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Build the flag entry
    flag_entry = {
        "user_id": current_user["user_id"],  
        "reason": reason,
        "timestamp": datetime.utcnow()
    }

    # Add the flag to the question
    update_result = questions_collection.update_one(
        {"_id": question_obj_id},
        {
            "$set": {"flagged": True, "status": "reported"},
            "$push": {"flags": flag_entry}
        }
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to flag question")

    return {
        "message": "Question flagged successfully",
        "question_id": question_id,
        "reason": reason
    }


@router.patch("/answers/{answer_id}/flag")
def user_flag_answer(
    answer_id: str,
    reason: str = Body(..., embed=True),
    current_user: dict = Depends(get_current_user)
):
    try:
        answer_obj_id = ObjectId(answer_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid answer ID")

    answers_collection = db["answers"]
    answer = answers_collection.find_one({"_id": answer_obj_id})

    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    # Check if the user already flagged this answer
    existing_flags = answer.get("flags", [])
    for flag in existing_flags:
        if flag["user_id"] == current_user["user_id"]:
            raise HTTPException(status_code=400, detail="You already flagged this answer")

    # Flag entry
    flag_entry = {
        "user_id": current_user["user_id"],
        "reason": reason,
        "timestamp": datetime.utcnow()
    }

    # Update the answer with the flag
    update_result = answers_collection.update_one(
        {"_id": answer_obj_id},
        {
            "$set": {"flagged": True, "status": "reported"},
            "$push": {"flags": flag_entry}
        }
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to flag answer")

    return {
        "message": "Answer flagged successfully",
        "answer_id": answer_id,
        "reason": reason
    }