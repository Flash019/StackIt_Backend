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
from fastapi.encoders import jsonable_encoder
# Load environment variables
load_dotenv()

# Initialize router
router = APIRouter(tags=["Questions"])

# Cloudinary config
cloudinary.config(
    cloud_name="dpab6rwk6",
    api_key="643176234975145",
    api_secret="Z_a-vSfNAEE4ShTSBlvvK6Lk2tg"  # Note: Don't expose secrets in production
)

@router.get("/questions")
async def get_all_questions():
    try:
        # Use synchronous iteration for PyMongo
        questions_cursor = db.questions.find().sort("created_at", -1)
        questions = []
        for question in questions_cursor:
            question["_id"] = str(question["_id"])
            question["author_id"] = str(question["author_id"])
            questions.append(question)

        return {"success": True, "count": len(questions), "data": questions}
    except Exception as e:
        print(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch questions")


@router.post("/questions")
async def post_question(
    title: str = Form(...),
    description: str = Form(...),
    tags_str: str = Form(...),
    author_id: str = Form(...),
    file: Optional[UploadFile] = File(None)  # Make it explicitly Optional
):
    try:
        # Validate required fields
        if not title.strip():
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        if not description.strip():
            raise HTTPException(status_code=400, detail="Description cannot be empty")
        if not tags_str.strip():
            raise HTTPException(status_code=400, detail="Tags cannot be empty")

        # Validate author_id
        try:
            author_obj_id = ObjectId(author_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid author_id format")

        # Parse tags
        tags = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
        if not tags:
            raise HTTPException(status_code=400, detail="At least one valid tag is required")

        # Initialize attachment_url
        attachment_url = None

        # Upload file if provided
        if file and file.filename:  # Check if file exists and has a filename
            try:
                # Validate file type if needed
                allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
                if file.content_type not in allowed_types:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"File type {file.content_type} not allowed"
                    )
                
                # Upload to Cloudinary
                result = unsigned_upload(file.file, upload_preset="questions")
                attachment_url = result.get('secure_url')  # Get the secure URL from result
                
            except HTTPException:
                raise
            except Exception as e:
                print(f"File upload error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

        # Construct question object
        current_time = datetime.utcnow()
        question = {
            "title": title.strip(),
            "description": description.strip(),
            "tags": tags,
            "author_id": author_obj_id,
            "created_at": current_time,
            "attachment_url": attachment_url
        }

        # Insert into DB
        try:
            result = db.questions.insert_one(question)
        except Exception as e:
            print(f"Database error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save question to database")

        # Return success response
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "filename": file.filename if file and file.filename else None,
                "message": "Question posted successfully!",
                "data": {
                    "question_id": str(result.inserted_id),
                    "title": title.strip(),
                    "description": description.strip(),
                    "tags": tags,
                    "author_id": author_id,
                    "attachment_url": attachment_url,
                    "created_at": current_time.isoformat()
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.get("/questions/{question_id}")
async def get_question_by_id(question_id: str):
    try:
        # Validate and convert question_id to ObjectId
        try:
            obj_id = ObjectId(question_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid question_id format")

      
        question = db.questions.find_one({"_id": obj_id})

        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        # Convert ObjectId fields to strings
        question["_id"] = str(question["_id"])
        question["author_id"] = str(question["author_id"])

        return {"success": True, "data": question}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch question")
