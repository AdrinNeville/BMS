from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from auth import create_access_token, hash_password, verify_password
from database import db, obj_to_str
from bson import ObjectId
import models
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=models.UserResponse)
async def register(user: models.UserCreate):
    # check if email exists
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)
    new_user = {**user.dict(), "password": hashed}
    result = await db.users.insert_one(new_user)
    return models.UserResponse(id=str(result.inserted_id), name=user.name, email=user.email, role=user.role)

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await db.users.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_access_token(data={"sub": str(user["_id"])}, expires_delta=timedelta(minutes=60))
    return {"access_token": token, "token_type": "bearer"}