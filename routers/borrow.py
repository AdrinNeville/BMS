from fastapi import APIRouter, Depends, HTTPException
from database import db, obj_to_str
import models
from utils.dependencies import get_current_user
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/borrow", tags=["Borrow"])

@router.post("/{book_id}", response_model=models.BorrowResponse)
async def borrow_book(book_id: int, current_user=Depends(get_current_user)):
    # Find book by auto-increment ID instead of ObjectId
    book = await db.books.find_one({"id": book_id})
    if not book or not book["available"]:
        raise HTTPException(status_code=400, detail="Book not available")

    await db.books.update_one({"id": book_id}, {"$set": {"available": False}})
    borrow = {
        "user_id": current_user["id"],
        "book_id": book_id,  # Use the auto-increment ID
        "borrowed_at": datetime.utcnow(),
        "returned_at": None
    }
    result = await db.borrow_records.insert_one(borrow)
    borrow["id"] = str(result.inserted_id)
    return models.BorrowResponse(**borrow)

@router.patch("/{borrow_id}/return", response_model=models.BorrowResponse)
async def return_book(borrow_id: str, current_user=Depends(get_current_user)):
    record = await db.borrow_records.find_one({"_id": ObjectId(borrow_id)})
    if not record or record["returned_at"]:
        raise HTTPException(status_code=400, detail="Invalid borrow record")

    # Check if current user is the one who borrowed the book or is admin
    if record["user_id"] != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Cannot return someone else's book")

    await db.borrow_records.update_one(
        {"_id": record["_id"]}, 
        {"$set": {"returned_at": datetime.utcnow()}}
    )
    await db.books.update_one(
        {"id": record["book_id"]}, 
        {"$set": {"available": True}}
    )

    record["id"] = obj_to_str(record["_id"])
    record["returned_at"] = datetime.utcnow()
    return models.BorrowResponse(**record)

@router.get("/my-borrows", response_model=list[models.BorrowResponse])
async def get_my_borrows(current_user=Depends(get_current_user)):
    records = []
    async for record in db.borrow_records.find({"user_id": current_user["id"]}):
        record["id"] = obj_to_str(record["_id"])
        records.append(models.BorrowResponse(**record))
    return records