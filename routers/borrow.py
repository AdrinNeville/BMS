from fastapi import APIRouter, Depends, HTTPException
from database import db, obj_to_str
import models
from utils.dependencies import get_current_user
from datetime import datetime

router = APIRouter(prefix="/borrow", tags=["Borrow"])

@router.post("/{book_id}", response_model=models.BorrowResponse)
async def borrow_book(book_id: str, current_user=Depends(get_current_user)):
    book = await db.books.find_one({"_id": {"$eq": db.client.get_database().codec_options.uuid_representation.objectid_class(book_id)}})
    if not book or not book["available"]:
        raise HTTPException(status_code=400, detail="Book not available")

    # mark book unavailable
    await db.books.update_one({"_id": book["_id"]}, {"$set": {"available": False}})

    borrow = {
        "user_id": current_user["id"],
        "book_id": str(book["_id"]),
        "borrowed_at": datetime.utcnow(),
        "returned_at": None
    }
    result = await db.borrow_records.insert_one(borrow)
    borrow["id"] = str(result.inserted_id)
    return models.BorrowResponse(**borrow)

@router.patch("/{borrow_id}/return", response_model=models.BorrowResponse)
async def return_book(borrow_id: str):
    record = await db.borrow_records.find_one({"_id": {"$eq": db.client.get_database().codec_options.uuid_representation.objectid_class(borrow_id)}})
    if not record or record["returned_at"]:
        raise HTTPException(status_code=400, detail="Invalid borrow record")

    await db.borrow_records.update_one({"_id": record["_id"]}, {"$set": {"returned_at": datetime.utcnow()}})
    await db.books.update_one({"_id": record["book_id"]}, {"$set": {"available": True}})

    record["id"] = obj_to_str(record["_id"])
    record["returned_at"] = datetime.utcnow()
    return models.BorrowResponse(**record)
