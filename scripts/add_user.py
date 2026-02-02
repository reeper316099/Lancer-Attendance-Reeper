from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("DB_URI"))
db = client[os.getenv("DB_NAME")]

print("\n===ADD NEW USER ===\n")

user_id = input("User ID Email (Ex. wchung27): ").strip()
name = input("Full name: ").strip()
position = input("Position (Member/Chairman): ").strip() or "Member"

existing = db.users.find_one({"id": user_id})
if existing:
    print("User already exists")
    exit()

db.users.insert_one({
    "id": user_id,
    "name": name,
    "position": position,
    "admin": False,
    "score": 0,
    "attendance": []
})

print(f"User {name} added successfully")
