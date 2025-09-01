from fastapi import FastAPI
from database import db
from routers import users, books, borrow
import auth

app = FastAPI(title="Library Management System with Auth")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(books.router)
app.include_router(borrow.router)