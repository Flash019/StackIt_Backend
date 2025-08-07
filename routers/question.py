import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from typing import Optional
from datetime import datetime
import cloudinary
from cloudinary.uploader import unsigned_upload
from fastapi.responses import JSONResponse
from bson import ObjectId
from dotenv import load_dotenv
from database import db
from utils.auth import get_current_user  # Import from utils
from fastapi.security import OAuth2PasswordBearer

# Load environment variables
load_dotenv()

# Initialize router
router = APIRouter(tags=["Questions"])

# Cloudinary config
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

@router.post("/questions")
async def post_question(
    title: str = Form(...),
    description: str = Form(...),
    tags_str: str = Form(...),
    author_id: str = Form(...),  # Keep this to match client request
    file: UploadFile = File(None),
    current_user=Depends(get_current_user)  # Authentication dependency
):
    user_id = current_user["user_id"]
    try:
        # Note: author_id from form is ignored, using authenticated user instead
        # Validate inputs
        if not title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        if not description.strip():
            raise HTTPException(status_code=400, detail="Description cannot be empty")

        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        
        # Initialize attachment_url
        attachment_url = None

        # Upload file if provided
        if file and file.filename:
            try:
                result = unsigned_upload(file.file, upload_preset="questions")
                attachment_url = result.get("secure_url")  # Get the URL from result
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

        # Construct question object
        question = {
            "title": title.strip(),
            "description": description.strip(),
            "tags": tags,
            "author_id": ObjectId(current_user["user_id"]),  # Use authenticated user ID
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
                "author_id": current_user["user_id"],  # Return the authenticated user ID
                "attachment_url": attachment_url,
                "created_at": datetime.utcnow().isoformat()
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        print("Unexpected error:", e)
        raise HTTPException(status_code=500, detail="Internal Server Error")