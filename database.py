# database.py
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

MONGO_URL = "mongodb://localhost:27017/library_db"
client = AsyncIOMotorClient(MONGO_URL)
db = client.library_db

def obj_to_str(obj):
    return str(obj) if isinstance(obj, ObjectId) else obj