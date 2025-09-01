from fastapi import Depends, HTTPException
from database import db, obj_to_str

# Fake auth: always pretend user = first one in DB
async def get_current_user():
    user = await db.users.find_one()
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user["id"] = obj_to_str(user["_id"])
    return user

async def librarian_required(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "librarian":
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user