from fastapi import APIRouter, HTTPException
from models import schemas
from repository import user

router = APIRouter(prefix="/user", tags=["User"])

@router.post("/", response_model=schemas.ShowUser)
def create_user(request: schemas.User):
    return user.create(request)

@router.get("/{id}", response_model=schemas.ShowUser)
def get_user(id: str):
    return user.show(id)
