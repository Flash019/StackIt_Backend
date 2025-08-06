from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "InvoX")  # fallback to InvoX

if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is not set")

# Sync client
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db["DB"]  # this is the actual collection name
collection = users_collection
# Async client
async_client = AsyncIOMotorClient(MONGO_URI)
async_db = async_client[DB_NAME]
async_users_collection = async_db["DB"]

# Test connection
def test_connection():
    try:
        client.admin.command("ping")
        print(" Connected to MongoDB Atlas (sync)")
        return True
    except Exception as e:
        print(f" Sync MongoDB connection failed: {e}")
        return False

# Async test
async def test_async_connection():
    try:
        await async_client.admin.command("ping")
        print(" Connected to MongoDB Atlas (async)")
        return True
    except Exception as e:
        print(f" Async MongoDB connection failed: {e}")
        return False