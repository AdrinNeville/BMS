from fastapi import APIRouter, Depends, HTTPException
from pymongo import ReturnDocument
from database import db, obj_to_str
import models
from utils.dependencies import get_current_user, admin_required

router = APIRouter(prefix="/books", tags=["Books"])

# --- Auto Increment Function ---
async def get_next_sequence(name: str):
    counter = await db.counters.find_one_and_update(
        {"_id": name},
        {"$inc": {"sequence_value": 1}},
        return_document=ReturnDocument.AFTER,
        upsert=True
    )
    return counter["sequence_value"]

@router.post("/", response_model=models.BookResponse)
async def add_book(book: models.BookCreate, admin=Depends(admin_required)):
    next_id = await get_next_sequence("bookid")
    new_book = {**book.dict(), "id": next_id, "available": True}
    result = await db.books.insert_one(new_book)
    return models.BookResponse(**new_book)

@router.get("/", response_model=list[models.BookResponse])
async def list_books():
    books = []
    async for b in db.books.find():
        books.append(models.BookResponse(**b))
    return books

@router.get("/{book_id}", response_model=models.BookResponse)
async def get_book(book_id: int):
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return models.BookResponse(**book)

@router.put("/{book_id}")
async def update_book_status(book_id: int, available: bool, admin=Depends(admin_required)):
    result = await db.books.update_one(
        {"id": book_id}, {"$set": {"available": available}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book updated"}