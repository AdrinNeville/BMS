from fastapi import FastAPI
from routers import users, books, borrow, auth

app = FastAPI(title="Library Management with Auth")

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(books.router)
app.include_router(borrow.router)