from fastapi import APIRouter, Query
from database import db

router = APIRouter()

@router.get("/search")
def search_questions(q: str = Query(...)):
    results = list(db.questions.find({"$text": {"$search": q}}))
    for r in results:
        r["_id"] = str(r["_id"])
    return results


# --- routers/questions.py update (pagination) ---
@router.get("/questions")
def get_questions(skip: int = 0, limit: int = 10):
    questions = list(db.questions.find().skip(skip).limit(limit))
    for q in questions:
        q["_id"] = str(q["_id"])
    return questions
