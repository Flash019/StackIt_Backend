from fastapi import APIRouter, Depends,HTTPException,Form,Body

from services import admin_service
from database import db
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from services.admin_service import get_all_flagged_answers
from bson import ObjectId

router = APIRouter(prefix="/admin", tags=["Admin"])

security = HTTPBasic()

#  Very simple admin auth — use real auth in production
def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "Apexars")
    correct_password = secrets.compare_digest(credentials.password, "Sov@King")
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/questions")
def admin_get_questions(credentials: HTTPBasicCredentials = Depends(verify_admin)):
    return {"data": admin_service.get_all_questions()}

@router.get("/users")
def admin_get_all_users(credentials: HTTPBasicCredentials = Depends(verify_admin)):
    return {
        
        "data": admin_service.get_all_users()
    }



@router.get("/admin/users/{user_id}")
def get_user_details_by_id(user_id: str, credentials=Depends(verify_admin)):
    try:
        object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    user = db["DB"].find_one({"_id": object_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prepare and return filtered details
    return {
        "_id": str(user["_id"]),
        "name": user.get("name"),
        "email": user.get("email"),
        "hashed_password": user.get("password"),  # hashed password
        "status": user.get("status", "active")    # default to active if not set
    }



@router.get("/admin/questions/flagged")
def get_all_flagged_questions(
    credentials: HTTPBasicCredentials = Depends(verify_admin)
):
    return admin_service.get_all_flagged_questions_with_user_details()






@router.get("/admin/answers/flagged")
def admin_get_all_flagged_answers(credentials: HTTPBasicCredentials = Depends(verify_admin)):
    return get_all_flagged_answers()


@router.patch("/admin/users/{user_id}/status")
def update_user_status(
    user_id: str,
    status: str = Form(...),  # Use Form if you're submitting via form-data
    credentials=Depends(verify_admin)
):
    valid_statuses = ["active", "banned", "suspended"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid_statuses}")

    try:
        object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user_id format")

    result = db["DB"].update_one(
        {"_id": object_id},
        {"$set": {"status": status}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "success": True,
        "message": f"User status updated to '{status}'",
        "user_id": user_id
    }
@router.patch("/admin/flag-question/{question_id}")
def admin_flag_question(
    question_id: str,
    reason: str = Body(..., embed=True),
    credentials=Depends(verify_admin)
):
    try:
        question_obj_id = ObjectId(question_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid question ID")

    questions_collection = db["questions"]
    question = questions_collection.find_one({"_id": question_obj_id})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    update_result = questions_collection.update_one(
        {"_id": question_obj_id},
        {
            "$set": {
                "flagged": True,
                "flag_reason": reason,
                "status": "reported"
            }
        }
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Question could not be flagged")

    # Return the flagged question details
    return {
        "message": "Question flagged successfully",
        "question_id": question_id,
        "status": "reported",
        "reason": reason,
        "title": question.get("title", "N/A"),
        "description": question.get("description", "N/A")
    }

{
  "message": "Question flagged successfully",
  "question_id": "64cda12f45d9b63df23bfe1a",
  "status": "reported",
  "reason": "Spam content",
  "title": "How do I fix this bug in FastAPI?",
  "description": "I'm getting a 422 error when posting a form. Here's the code..."
}
@router.patch("/admin/flag-answer/{answer_id}")
def flag_answer_as_admin(
    answer_id: str,
    reason: str = Body(..., embed=True),
    credentials: HTTPBasicCredentials = Depends(verify_admin)
):
    return admin_service.admin_flag_answer(answer_id, reason)

@router.delete("/admin/questions/{question_id}/remove-flag/{user_id}")
def remove_flag(
    question_id: str,
    user_id: str,
    credentials: HTTPBasicCredentials = Depends(verify_admin)
):
    return admin_service.remove_user_flag_from_question(question_id, user_id)

@router.delete("/users/{user_id}")
def admin_delete_user(user_id: str, credentials: HTTPBasicCredentials = Depends(verify_admin)):
    return admin_service.delete_user_by_id(user_id)

@router.delete("/questions/{question_id}")
def admin_delete_question(question_id: str, credentials: HTTPBasicCredentials = Depends(verify_admin)):
    return admin_service.delete_question_by_id(question_id)

# Delete all questions
@router.delete("/admin/delete-all-questions")
def delete_all_questions(credentials=Depends(verify_admin)):
    result = db["questions"].delete_many({})
    return {
        "message": f"Deleted {result.deleted_count} questions"
    }

#  Delete all answers
@router.delete("/admin/delete-all-answers")
def delete_all_answers(credentials=Depends(verify_admin)):
    result = db["answers"].delete_many({})
    return {
        "message": f"Deleted {result.deleted_count} answers"
    }