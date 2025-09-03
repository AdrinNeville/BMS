from fastapi import APIRouter, Depends, HTTPException, status
from database import db, obj_to_str
import models
from utils.dependencies import admin_required, get_current_user
from bson import ObjectId
from typing import Optional

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=list[models.UserResponse])
async def list_users(admin=Depends(admin_required)):
    """Get all users (Admin only)"""
    users = []
    async for u in db.users.find():
        u["id"] = obj_to_str(u["_id"])
        users.append(models.UserResponse(**u))
    return users

@router.get("/{user_id}", response_model=models.UserResponse)
async def get_user(user_id: str, admin=Depends(admin_required)):
    """Get a specific user by ID (Admin only)"""
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user["id"] = obj_to_str(user["_id"])
    return models.UserResponse(**user)

@router.delete("/{user_id}")
async def delete_user(user_id: str, current_admin=Depends(admin_required)):
    """Delete a user (Admin only)"""
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    # Check if user exists
    user_to_delete = await db.users.find_one({"_id": user_obj_id})
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves
    if str(user_obj_id) == current_admin["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")
    
    # Check if user has active borrows
    active_borrows = await db.borrow_records.find_one({
        "user_id": user_id,
        "returned_at": None
    })
    
    if active_borrows:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete user with active borrows. Please ensure all books are returned first."
        )
    
    # Delete the user
    result = await db.users.delete_one({"_id": user_obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "message": f"User '{user_to_delete['name']}' ({user_to_delete['email']}) has been deleted successfully",
        "deleted_user_id": user_id
    }

@router.patch("/{user_id}/role")
async def change_user_role(user_id: str, new_role: str, current_admin=Depends(admin_required)):
    """Change a user's role (Admin only)"""
    # Validate role
    valid_roles = ["member", "admin"]
    if new_role not in valid_roles:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid role. Must be one of: {valid_roles}"
        )
    
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    # Check if user exists
    user_to_update = await db.users.find_one({"_id": user_obj_id})
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from changing their own role (to avoid locking out)
    if str(user_obj_id) == current_admin["id"]:
        raise HTTPException(status_code=400, detail="You cannot change your own role")
    
    # Check if role is already the same
    current_role = user_to_update.get("role", "member")
    if current_role == new_role:
        raise HTTPException(status_code=400, detail=f"User already has role: {new_role}")
    
    # Update the user's role
    result = await db.users.update_one(
        {"_id": user_obj_id},
        {"$set": {"role": new_role}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "message": f"User '{user_to_update['name']}' role changed from '{current_role}' to '{new_role}'",
        "user_id": user_id,
        "old_role": current_role,
        "new_role": new_role
    }

@router.get("/{user_id}/borrows", response_model=list[models.BorrowResponse])
async def get_user_borrows(user_id: str, admin=Depends(admin_required)):
    """Get all borrow records for a specific user (Admin only)"""
    try:
        ObjectId(user_id)  # Validate user ID format
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    # Check if user exists
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's borrow records
    records = []
    async for record in db.borrow_records.find({"user_id": user_id}):
        record["id"] = str(record["_id"])
        records.append(models.BorrowResponse(**record))
    
    return records

@router.get("/{user_id}/active-borrows", response_model=list[models.BorrowResponse])
async def get_user_active_borrows(user_id: str, admin=Depends(admin_required)):
    """Get only active (unreturned) borrow records for a specific user (Admin only)"""
    try:
        ObjectId(user_id)  # Validate user ID format
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    # Check if user exists
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's active borrow records
    records = []
    async for record in db.borrow_records.find({
        "user_id": user_id,
        "returned_at": None
    }):
        record["id"] = str(record["_id"])
        records.append(models.BorrowResponse(**record))
    
    return records

@router.get("/stats/summary")
async def get_user_stats(admin=Depends(admin_required)):
    """Get user statistics summary (Admin only)"""
    # Count total users
    total_users = await db.users.count_documents({})
    
    # Count users by role
    admin_count = await db.users.count_documents({"role": "admin"})
    member_count = await db.users.count_documents({"role": {"$ne": "admin"}})
    
    # Count users with active borrows
    active_borrowers = len(await db.borrow_records.distinct("user_id", {"returned_at": None}))
    
    return {
        "total_users": total_users,
        "admin_count": admin_count,
        "member_count": member_count,
        "active_borrowers": active_borrowers,
        "inactive_users": total_users - active_borrowers
    }