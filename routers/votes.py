from fastapi import APIRouter,HTTPException,Depends
from fastapi.security import OAuth2PasswordBearer
from bson import ObjectId
from database import db
from utils.auth import decode_access_token,get_current_user
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
router = APIRouter()

@router.post("/answers/{answer_id}/vote",tags=["Answers"])
def vote_answer(answer_id: str, vote: int, current_user=Depends(get_current_user)):
    user_id = current_user["user_id"]
    # Validate vote value
    if vote not in [1, -1]:
        raise HTTPException(status_code=400, detail="Invalid vote value. Must be 1 (upvote) or -1 (downvote)")

    try:
        answer_obj_id = ObjectId(answer_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid answer ID")

    answer = db.answers.find_one({"_id": answer_obj_id})
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    # Calculate total votes
    upvotes = answer.get("upvotes", 0)
    downvotes = answer.get("downvotes", 0)
    total_votes = upvotes + downvotes

    if total_votes >= 10:
        raise HTTPException(status_code=403, detail="Vote limit reached (10 votes max)")

    # Apply vote
    update = {"$inc": {"upvotes": 1}} if vote == 1 else {"$inc": {"downvotes": 1}}
    db.answers.update_one({"_id": answer_obj_id}, update)

    return {"message": "Vote recorded"}
@router.post("/answers/{answer_id}/accept",tags=["Answers"]
)
def accept_answer(answer_id: str,current_user=Depends(get_current_user)):
    user_id = current_user["user_id"]
    db.answers.update_one({"_id": ObjectId(answer_id)}, {"$set": {"is_accepted": True}})
    return {"message": "Answer accepted"}
