import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from datetime import datetime
import cloudinary
from cloudinary.uploader import unsigned_upload
from fastapi.responses import JSONResponse
from bson import ObjectId
from dotenv import load_dotenv
from database import db

# Load environment variables
load_dotenv()

# Initialize router
router = APIRouter(tags=["Questions"])

# Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")  # Note: Don't expose secrets in production
)


@router.post("/questions")
async def post_question(
    title: str = Form(...),
    description: str = Form(...),
    tags_str: str = Form(...),
    author_id: str = Form(...),
    file: UploadFile = File(None)
):
    try:
        if not title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        if not description.strip():
            raise HTTPException(status_code=400, detail="Description cannot be empty")

        # Validate author_id
        try:
            author_obj_id = ObjectId(author_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid author_id format")

        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        #attachment_url = None

        # Upload file if provided
        if file:
            try:
                result = unsigned_upload(file.file, upload_preset="questions")
                attachment_url = result
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

        # Construct question object
        question = {
            "title": title.strip(),
            "description": description.strip(),
            "tags": tags,
            "author_id": author_obj_id,
            "created_at": datetime.utcnow(),
            "attachment_url": attachment_url
        }

        # Insert into DB
        result = db.questions.insert_one(question)

        # Return success response
        return JSONResponse({
            "success": True,
            "filename": file.filename if file else None,
            "message": "Question posted successfully!",
            "data": {
                "question_id": str(result.inserted_id),
                "title": title.strip(),
                "description": description.strip(),
                "tags": tags,
                "author_id": author_id,
                "attachment_url": attachment_url,
                "created_at": datetime.utcnow().isoformat()
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        print("Unexpected error:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")
