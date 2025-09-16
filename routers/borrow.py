from fastapi import APIRouter, Depends, HTTPException, status
from database import db
from datetime import datetime
from bson import ObjectId
import models
from utils.dependencies import get_current_user, admin_required

router = APIRouter(prefix="/borrow", tags=["Borrow"])

@router.post("/{book_id}", response_model=models.BorrowResponse)
async def borrow_book(book_id: int, current_user=Depends(get_current_user)):
    # Debug: Print current_user to see what we're getting
    print(f"Current user: {current_user}")
    
    # Ensure we have user ID
    if "id" not in current_user:
        current_user["id"] = str(current_user["_id"])
    
    # Find book by auto-increment ID
    book = await db.books.find_one({"id": book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Check available copies instead of just available status
    available_copies = book.get("available_copies", 0)
    if available_copies <= 0:
        raise HTTPException(status_code=400, detail="No copies of this book are currently available")

    # Check if user already has this book borrowed
    existing_borrow = await db.borrow_records.find_one({
        "user_id": current_user["id"],
        "book_id": book_id,
        "returned_at": None
    })
    
    if existing_borrow:
        raise HTTPException(status_code=400, detail="You already have this book borrowed")

    # Decrement available copies and increment borrowed copies
    new_available = available_copies - 1
    new_borrowed = book.get("borrowed_copies", 0) + 1
    
    # Update availability status only if no copies are left
    is_available = new_available > 0
    
    await db.books.update_one(
        {"id": book_id}, 
        {
            "$set": {
                "available_copies": new_available,
                "borrowed_copies": new_borrowed,
                "available": is_available  # Only False when no copies left
            }
        }
    )
    
    # Create borrow record
    borrow = {
        "user_id": current_user["id"],
        "book_id": book_id,
        "borrowed_at": datetime.utcnow(),
        "returned_at": None
    }
    
    result = await db.borrow_records.insert_one(borrow)
    borrow["id"] = str(result.inserted_id)
    
    return models.BorrowResponse(**borrow)

@router.patch("/{borrow_id}/return", response_model=models.BorrowResponse)
async def return_book(borrow_id: str, current_user=Depends(get_current_user)):
    # Ensure we have user ID
    if "id" not in current_user:
        current_user["id"] = str(current_user["_id"])
    
    try:
        record = await db.borrow_records.find_one({"_id": ObjectId(borrow_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid borrow ID format")
    
    if not record:
        raise HTTPException(status_code=404, detail="Borrow record not found")
    
    if record.get("returned_at") is not None:
        raise HTTPException(status_code=400, detail="Book already returned")

    # Check if current user is the one who borrowed the book or is admin
    if record["user_id"] != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Cannot return someone else's book")

    # Get book details
    book = await db.books.find_one({"id": record["book_id"]})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Increment available copies and decrement borrowed copies
    new_available = book.get("available_copies", 0) + 1
    new_borrowed = max(0, book.get("borrowed_copies", 1) - 1)
    
    # Book becomes available again since we have at least one copy
    is_available = True
    
    return_time = datetime.utcnow()
    
    # Update borrow record
    await db.borrow_records.update_one(
        {"_id": record["_id"]}, 
        {"$set": {"returned_at": return_time}}
    )
    
    # Update book availability and counts
    await db.books.update_one(
        {"id": record["book_id"]}, 
        {
            "$set": {
                "available_copies": new_available,
                "borrowed_copies": new_borrowed,
                "available": is_available
            }
        }
    )

    # Prepare response
    record["id"] = str(record["_id"])
    record["returned_at"] = return_time
    
    return models.BorrowResponse(**record)

@router.get("/my-borrows", response_model=list[models.BorrowResponse])
async def get_my_borrows(current_user=Depends(get_current_user)):
    # Ensure we have user ID
    if "id" not in current_user:
        current_user["id"] = str(current_user["_id"])
    
    records = []
    async for record in db.borrow_records.find({"user_id": current_user["id"]}):
        record["id"] = str(record["_id"])
        records.append(models.BorrowResponse(**record))
    
    return records

@router.get("/all", response_model=list[models.BorrowResponse])
async def get_all_borrows(admin_user=Depends(get_current_user)):
    # Admin only endpoint to see all borrows
    if admin_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    records = []
    async for record in db.borrow_records.find():
        record["id"] = str(record["_id"])
        records.append(models.BorrowResponse(**record))
    
    return records

@router.get("/overdue", response_model=list[dict])
async def get_overdue_books(admin=Depends(admin_required)):
    """Get all overdue books (Admin only) - books borrowed more than 14 days ago and not returned"""
    from datetime import timedelta
    
    # Calculate cutoff date (14 days ago)
    cutoff_date = datetime.utcnow() - timedelta(days=14)
    
    overdue_records = []
    async for record in db.borrow_records.find({
        "returned_at": None,  # Not returned
        "borrowed_at": {"$lt": cutoff_date}  # Borrowed more than 14 days ago
    }):
        # Get book details
        book = await db.books.find_one({"id": record["book_id"]})
        # Get user details
        user = await db.users.find_one({"_id": ObjectId(record["user_id"])})
        
        overdue_record = {
            "borrow_id": str(record["_id"]),
            "user_id": record["user_id"],
            "user_name": user.get("name", "Unknown") if user else "Unknown",
            "user_email": user.get("email", "Unknown") if user else "Unknown",
            "book_id": record["book_id"],
            "book_title": book.get("title", "Unknown") if book else "Unknown",
            "book_author": book.get("author", "Unknown") if book else "Unknown",
            "borrowed_at": record["borrowed_at"],
            "days_overdue": (datetime.utcnow() - record["borrowed_at"]).days
        }
        overdue_records.append(overdue_record)
    
    return overdue_records