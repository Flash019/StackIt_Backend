from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from database import collection
from hashing import Hash
from utils.auth import create_access_token  # Not token.create_access_token

router = APIRouter(tags=["Authentication"])

@router.post("/login")
def login(request: OAuth2PasswordRequestForm = Depends()):
    user = collection.find_one({"email": request.username})
    if not user:
        raise HTTPException(status_code=404, detail="Invalid Credentials")
    
    if not Hash.verify(user["password"], request.password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    access_token = create_access_token(data={"user_id": str(user["_id"]), "email": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}
