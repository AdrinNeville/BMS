from fastapi import FastAPI
from database import db
from routers import users, books, borrow
import auth
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()  # Make sure .env variables are loaded

app = FastAPI(title="Library Management System with Auth")

# Get origins from .env (comma-separated string)
origins = os.getenv("origins")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(books.router)
app.include_router(borrow.router)

@app.get("/config")
def get_config():
    return {"API_BASE_URL": os.getenv("API_BASE_URL")}