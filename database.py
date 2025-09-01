from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

MONGO_URL = "mongodb://localhost:27017"
client = AsyncIOMotorClient(MONGO_URL)
db = client.library_db

# helper to convert ObjectId → str
def obj_to_str(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj