from models import schemas
from database import collection
from hashing import Hash
from fastapi import HTTPException, status
from bson import ObjectId

def create(user: schemas.User):
    existing = collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = Hash.bcrypt(user.password)
    new_user = {"name": user.name, "email": user.email, "password": hashed}
    res = collection.insert_one(new_user)
    new_user["_id"] = res.inserted_id
    return schemas.ShowUser(**new_user)

def show(user_id: str):
    user = collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas.ShowUser(**user)
