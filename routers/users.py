from fastapi import APIRouter, Depends, HTTPException
from database import db, obj_to_str
import models
from utils.dependencies import librarian_required

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=models.UserResponse)
async def create_user(user: models.UserCreate):
    new_user = user.dict()
    result = await db.users.insert_one(new_user)
    return models.UserResponse(id=str(result.inserted_id), **user.dict())

@router.get("/", response_model=list[models.UserResponse])
async def list_users(librarian=Depends(librarian_required)):
    users = []
    async for u in db.users.find():
        u["id"] = obj_to_str(u["_id"])
        users.append(models.UserResponse(**u))
    return users