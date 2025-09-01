from fastapi import APIRouter, Depends
from database import db, obj_to_str
import models
from utils.dependencies import librarian_required

router = APIRouter(prefix="/books", tags=["Books"])

@router.post("/", response_model=models.BookResponse)
async def add_book(book: models.BookCreate, librarian=Depends(librarian_required)):
    new_book = {**book.dict(), "available": True}
    result = await db.books.insert_one(new_book)
    return models.BookResponse(id=str(result.inserted_id), **new_book)

@router.get("/", response_model=list[models.BookResponse])
async def list_books():
    books = []
    async for b in db.books.find():
        b["id"] = obj_to_str(b["_id"])
        books.append(models.BookResponse(**b))
    return books