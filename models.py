from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# ----- User -----
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: Optional[str] = "member"

class UserResponse(UserBase):
    id: str
    role: str

# ----- Book -----
class BookBase(BaseModel):
    title: str
    author: str

class BookCreate(BookBase):
    pass

class BookResponse(BookBase):
    id: str
    available: bool

# ----- Borrow -----
class BorrowResponse(BaseModel):
    id: str
    user_id: str
    book_id: str
    borrowed_at: datetime
    returned_at: Optional[datetime]