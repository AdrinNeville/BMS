from fastapi import FastAPI
from database import db
from routers import users, books, borrow
import auth
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Library Management System with Auth")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[""
    "https://bookmanagementsystem1109.netlify.app/",
    "http://localhost:3000/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(books.router)
app.include_router(borrow.router)