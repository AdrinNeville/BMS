from fastapi import APIRouter, Depends
from database import db, obj_to_str
import models
from utils.dependencies import admin_required

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=list[models.UserResponse])
async def list_users(admin=Depends(admin_required)):
    users = []
    async for u in db.users.find():
        u["id"] = obj_to_str(u["_id"])
        users.append(models.UserResponse(**u))
    return users