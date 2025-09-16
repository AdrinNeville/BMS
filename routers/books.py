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
    # Check if book already exists (same title and author)
    existing_book = await db.books.find_one({
        "title": book.title,
        "author": book.author
    })
    
    if existing_book:
        # If book exists, add to the copies count
        new_total = existing_book["total_copies"] + book.total_copies
        new_available = existing_book["available_copies"] + book.total_copies
        
        await db.books.update_one(
            {"id": existing_book["id"]},
            {
                "$set": {
                    "total_copies": new_total,
                    "available_copies": new_available,
                    "available": True  # Set to True since we're adding copies
                }
            }
        )
        
        # Return updated book
        updated_book = await db.books.find_one({"id": existing_book["id"]})
        updated_book["borrowed_copies"] = updated_book["total_copies"] - updated_book["available_copies"]
        return models.BookResponse(**updated_book)
    else:
        # Create new book entry
        next_id = await get_next_sequence("bookid")
        new_book = {
            **book.dict(exclude={"total_copies"}),
            "id": next_id,
            "total_copies": book.total_copies,
            "available_copies": book.total_copies,
            "borrowed_copies": 0,
            "available": True  # Available if we have copies
        }
        
        result = await db.books.insert_one(new_book)
        return models.BookResponse(**new_book)

@router.get("/", response_model=list[models.BookResponse])
async def list_books():
    books = []
    async for b in db.books.find():
        # Calculate borrowed_copies if not present
        if "borrowed_copies" not in b:
            b["borrowed_copies"] = b.get("total_copies", 1) - b.get("available_copies", 0)
        books.append(models.BookResponse(**b))
    return books

@router.get("/{book_id}", response_model=models.BookResponse)
async def get_book(book_id: int):
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Calculate borrowed_copies if not present
    if "borrowed_copies" not in book:
        book["borrowed_copies"] = book.get("total_copies", 1) - book.get("available_copies", 0)
    
    return models.BookResponse(**book)

@router.patch("/{book_id}/add-copies")
async def add_book_copies(book_id: int, copies: int, admin=Depends(admin_required)):
    """Add more copies of an existing book"""
    if copies <= 0:
        raise HTTPException(status_code=400, detail="Number of copies must be positive")
    
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    new_total = book.get("total_copies", 1) + copies
    new_available = book.get("available_copies", 0) + copies
    
    result = await db.books.update_one(
        {"id": book_id},
        {
            "$set": {
                "total_copies": new_total,
                "available_copies": new_available,
                "available": True  # Set to True since we're adding copies
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"message": f"Added {copies} copies. Total: {new_total}, Available: {new_available}"}

@router.patch("/{book_id}/remove-copies")
async def remove_book_copies(book_id: int, copies: int, admin=Depends(admin_required)):
    """Remove copies of a book (only if not borrowed)"""
    if copies <= 0:
        raise HTTPException(status_code=400, detail="Number of copies must be positive")
    
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    available_copies = book.get("available_copies", 0)
    if copies > available_copies:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot remove {copies} copies. Only {available_copies} copies are available (not borrowed)"
        )
    
    new_total = book.get("total_copies", 1) - copies
    new_available = available_copies - copies
    
    # Update availability status based on available copies
    is_available = new_available > 0
    
    result = await db.books.update_one(
        {"id": book_id},
        {
            "$set": {
                "total_copies": new_total,
                "available_copies": new_available,
                "available": is_available
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"message": f"Removed {copies} copies. Total: {new_total}, Available: {new_available}"}

# Legacy endpoint for backward compatibility
@router.put("/{book_id}")
async def update_book_status(book_id: int, available: bool, admin=Depends(admin_required)):
    """Legacy endpoint - now manages available_copies instead"""
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    total_copies = book.get("total_copies", 1)
    borrowed_copies = book.get("borrowed_copies", 0)
    
    if available:
        # Make all copies available (return all borrowed copies)
        new_available = total_copies
        new_borrowed = 0
    else:
        # Make all copies unavailable (mark all as borrowed)
        new_available = 0
        new_borrowed = total_copies
    
    result = await db.books.update_one(
        {"id": book_id},
        {
            "$set": {
                "available": available,
                "available_copies": new_available,
                "borrowed_copies": new_borrowed
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"message": "Book status updated"}

@router.delete("/{book_id}/discontinue-copies")
async def delete_book_copies(book_id: int, admin=Depends(admin_required)):
    """Discontinue all copies of a book (only if no copies are currently borrowed)"""
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    borrowed_copies = book.get("borrowed_copies", 0)
    total_copies = book.get("total_copies", 1)
    
    # Check if any copies are currently borrowed
    if borrowed_copies > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot discontinue book. {borrowed_copies} copies are currently borrowed"
        )
    
    # Remove the book entirely from the collection
    result = await db.books.delete_one({"id": book_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"message": f"Book '{book.get('title', 'Unknown')}' has been discontinued and removed from the library"}

# Alternative version if you want to keep the book record but mark it as discontinued
@router.delete("/{book_id}/discontinue")
async def discontinue_book(book_id: int, admin=Depends(admin_required)):
    """Mark a book as discontinued (only if no copies are currently borrowed)"""
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    borrowed_copies = book.get("borrowed_copies", 0)
    
    # Check if any copies are currently borrowed
    if borrowed_copies > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot discontinue book. {borrowed_copies} copies are currently borrowed"
        )
    
    # Mark book as discontinued but keep the record
    result = await db.books.update_one(
        {"id": book_id},
        {
            "$set": {
                "total_copies": 0,
                "available_copies": 0,
                "borrowed_copies": 0,
                "available": False,
                "discontinued": True
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {"message": f"Book '{book.get('title', 'Unknown')}' has been discontinued"}