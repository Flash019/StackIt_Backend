from fastapi import APIRouter, HTTPException
from models import schemas
from repository import user

router = APIRouter( )

@router.post("/auth/register", response_model=schemas.ShowUser)
def create_user(request: schemas.User):
    return user.create(request)

@router.get("/{id}", response_model=schemas.ShowUser)
def get_user(id: str):
    return user.show(id)
