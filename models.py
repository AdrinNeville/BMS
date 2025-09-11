from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ---------- Auth ----------
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: Optional[str] = "member"   # "member" or "admin"

class UserResponse(UserBase):
    id: str
    role: str

class UserRoleUpdate(BaseModel):
    role: str  # New role to assign

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ---------- Books ----------
class BookBase(BaseModel):
    title: str
    author: str

class BookCreate(BookBase):
    total_copies: int = 1  # Number of copies to add

class BookResponse(BookBase):
    id: int  # Changed to int for auto-increment
    available: bool
    total_copies: int  # Total number of copies
    available_copies: int  # Currently available copies
    borrowed_copies: int  # Currently borrowed copies

# ---------- Borrow ----------
class BorrowResponse(BaseModel):
    id: str
    user_id: str
    book_id: int  # Changed to int to match auto-increment book ID
    borrowed_at: datetime
    returned_at: Optional[datetime]