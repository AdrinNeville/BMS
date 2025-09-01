from fastapi import FastAPI
from routers import users, books, borrow

app = FastAPI(title="Library Management with MongoDB")

app.include_router(users.router)
app.include_router(books.router)
app.include_router(borrow.router)