from bson import ObjectId
from database import db
from fastapi import HTTPException, Depends, Body
from utils.auth import get_current_user
from datetime import datetime

def get_all_questions():
    questions = db.questions.find().sort("created_at", -1)
    result = []
    for q in questions:
        q["_id"] = str(q["_id"])
        q["author_id"] = str(q["author_id"])
        result.append(q)
    return result


def delete_question_by_id(question_id: str):
    try:
        obj_id = ObjectId(question_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    result = db.questions.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Question not found")

    return {"success": True, "message": "Question deleted"}

def get_all_users():
    users_cursor = db.DB.find().sort("created_at", -1)  # Use the actual collection name
    result = []
    for user in users_cursor:
        user["_id"] = str(user["_id"])
        result.append(user)
    return result



def delete_user_by_id(user_id : str):
    try:
        object_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    result = db.DB.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"success": True, "message": "User deleted"}


def get_all_flagged_questions_with_user_details():
    questions_collection = db["questions"]
    users_collection = db["DB"]

    flagged_questions = questions_collection.find({"flagged": True})
    result = []

    for question in flagged_questions:
        question_id = str(question["_id"])
        flags = question.get("flags", [])

        enriched_flags = []
        for flag in flags:
            user_info = users_collection.find_one({"_id": ObjectId(flag["user_id"])})
            if user_info:
                enriched_flags.append({
                    "user_id": flag["user_id"],
                    "email": user_info.get("email", "unknown"),
                    "reason": flag.get("reason", "N/A"),
                    "timestamp": flag.get("timestamp", "N/A")
                })

        result.append({
            "question_id": question_id,
            "title": question.get("title", "N/A"),
            "description": question.get("description", "N/A"),
            "status": question.get("status", "N/A"),
            "flagged_by_users": enriched_flags
        })

    if not result:
        raise HTTPException(status_code=404, detail="No flagged questions found")

    return result

def remove_user_flag_from_question(question_id: str, user_id: str):
    try:
        question_obj_id = ObjectId(question_id)
        user_obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid question_id or user_id")

    questions_collection = db["questions"]

    question = questions_collection.find_one({"_id": question_obj_id})
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Remove the flag from the "flags" array
    update_result = questions_collection.update_one(
        {"_id": question_obj_id},
        {"$pull": {"flags": {"user_id": str(user_obj_id)}}}
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Flag not found or already removed")

    # Check if there are any flags left after removal
    updated_question = questions_collection.find_one({"_id": question_obj_id})
    if not updated_question.get("flags"):
        # If no more flags, remove flag status
        questions_collection.update_one(
            {"_id": question_obj_id},
            {"$unset": {"flagged": "", "status": "", "flags": ""}}
        )

    return {
        "message": f"Flag by user {user_id} removed from question {question_id}"
    }


def admin_flag_answer(answer_id: str, reason: str):
    try:
        answer_obj_id = ObjectId(answer_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid answer ID")

    answers_collection = db["answers"]

    answer = answers_collection.find_one({"_id": answer_obj_id})
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found")

    flag_data = {
        "by_admin": True,
        "reason": reason,
        "timestamp": datetime.utcnow()
    }

    update_result = answers_collection.update_one(
        {"_id": answer_obj_id},
        {
            "$set": {"flagged": True, "status": "reported"},
            "$push": {"flags": flag_data}
        }
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to flag answer")

    return {
        "message": "Answer flagged successfully by admin",
        "answer_id": answer_id,
        "reason": reason
    }


def get_all_flagged_answers():
    answers_collection = db["answers"]
    users_collection = db["DB"]  # Change if your user collection has a different name

    flagged_answers = answers_collection.find({"flagged": True})

    results = []
    for answer in flagged_answers:
        answer_id = str(answer["_id"])
        content = answer.get("content", "")
        flags = answer.get("flags", [])

        enriched_flags = []
        for flag in flags:
            flagged_by = flag.get("flagged_by", "user")
            reason = flag.get("reason", "No reason provided")
            timestamp = flag.get("timestamp")

            if flagged_by == "admin":
                enriched_flags.append({
                    "user_id": None,
                    "email": "admin",
                    "reason": reason,
                    "flagged_by": "admin",
                    "timestamp": timestamp
                })
            else:
                user_id = flag.get("user_id")
                if user_id:
                    user = users_collection.find_one({"_id": ObjectId(user_id)})
                    email = user.get("email", "unknown") if user else "unknown"
                else:
                    email = "unknown"

                enriched_flags.append({
                    "user_id": user_id,
                    "email": email,
                    "reason": reason,
                    "flagged_by": flagged_by,
                    "timestamp": timestamp
                })

        results.append({
            "answer_id": answer_id,
            "content": content,
            "status": answer.get("status", "unknown"),
            "flags": enriched_flags
        })

    return results