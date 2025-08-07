import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from datetime import datetime
import cloudinary
from cloudinary.uploader import unsigned_upload
from fastapi.responses import JSONResponse
from bson import ObjectId
from dotenv import load_dotenv
from database import db
from utils.auth import get_current_user

# Load environment variables
load_dotenv()

# Initialize router
router = APIRouter(tags=["Questions"])

# Configure Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)
@router.get("/questions")
async def get_all_questions():
    try:
        questions = list(db.questions.find().sort("created_at", -1))
        for q in questions:
            q["_id"] = str(q["_id"])
            q["author_id"] = str(q["author_id"])
            q["created_at"] = q["created_at"].isoformat()
        return {"success": True, "count": len(questions), "data": questions}
    except Exception as e:
        print("Error fetching questions:", e)
        raise HTTPException(status_code=500, detail="Failed to fetch questions")

@router.get("/questions/{question_id}")
async def get_question_by_id(question_id: str):
    try:
        if not ObjectId.is_valid(question_id):
            raise HTTPException(status_code=400, detail="Invalid question ID")

        question = db.questions.find_one({"_id": ObjectId(question_id)})
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        question["_id"] = str(question["_id"])
        question["author_id"] = str(question["author_id"])
        question["created_at"] = question["created_at"].isoformat()

        return {"success": True, "data": question}
    except HTTPException:
        raise
    except Exception as e:
        print("Error fetching question by ID:", e)
        raise HTTPException(status_code=500, detail="Failed to fetch question")

@router.post("/questions")
async def post_question(
    title: str = Form(...),
    description: str = Form(...),
    tags_str: str = Form(...),
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Validate inputs
        if not title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        if not description.strip():
            raise HTTPException(status_code=400, detail="Description cannot be empty")

        # Parse comma-separated tags
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]

        # Initialize attachment URL
        attachment_url = None

        # Upload file to Cloudinary (unsigned)
        if file and file.filename:
            try:
                result = unsigned_upload(file.file, upload_preset="questions")
                attachment_url = result.get("secure_url")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

        # Construct DB entry
        question = {
            "title": title.strip(),
            "description": description.strip(),
            "tags": tags,
            "author_id": ObjectId(current_user["user_id"]),
            "created_at": datetime.utcnow(),
            "attachment_url": attachment_url
        }

        # Insert into MongoDB
        result = db.questions.insert_one(question)

        # Response
        return JSONResponse({
            "success": True,
            "filename": file.filename if file else None,
            "message": "Question posted successfully!",
            "data": {
                "question_id": str(result.inserted_id),
                "title": title.strip(),
                "description": description.strip(),
                "tags": tags,
                "author_id": current_user["user_id"],
                "attachment_url": attachment_url,
                "created_at": datetime.utcnow().isoformat()
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        print("Unexpected error:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
