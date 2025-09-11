"""
Migration script to update existing books with copy counts
Run this script once to migrate existing data

Usage:
    python migrate_book_copies.py
"""

from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from database import MONGO_URL  # Import from your existing database.py

async def migrate_books():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.library_db
    
    print("Starting migration of existing books...")
    
    # Get all books that don't have the new fields
    books_to_update = []
    async for book in db.books.find():
        if "total_copies" not in book or "available_copies" not in book:
            books_to_update.append(book)
    
    if not books_to_update:
        print("No books need migration. All books already have copy count fields.")
        await client.close()
        return
    
    print(f"Found {len(books_to_update)} books to migrate")
    
    for book in books_to_update:
        # Count how many active borrows this book has
        active_borrows = await db.borrow_records.count_documents({
            "book_id": book["id"],
            "returned_at": None
        })
        
        # For existing books, assume they had 1 copy initially
        total_copies = 1
        borrowed_copies = active_borrows
        available_copies = max(0, total_copies - borrowed_copies)
        is_available = available_copies > 0
        
        # Update the book with new fields
        await db.books.update_one(
            {"_id": book["_id"]},
            {
                "$set": {
                    "total_copies": total_copies,
                    "available_copies": available_copies,
                    "borrowed_copies": borrowed_copies,
                    "available": is_available
                }
            }
        )
        
        print(f"Updated book '{book['title']}' - Total: {total_copies}, Available: {available_copies}, Borrowed: {borrowed_copies}")
    
    print("Migration completed successfully!")
    await client.close()

if __name__ == "__main__":
    print("Library Management System - Book Copies Migration")
    print("=" * 50)
    asyncio.run(migrate_books())