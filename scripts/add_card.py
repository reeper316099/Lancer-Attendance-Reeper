from pymongo import MongoClient
from dotenv import load_dotenv
import os
import time
from datetime import datetime

load_dotenv()

client = MongoClient(os.getenv("DB_URI"))
db = client[os.getenv("DB_NAME")]

print("\n=== ADD RFID CARD ===\n")

card_id = input("Card ID(6 digits): ").strip()
user_id = input("User ID to link: ").strip()
academic_year = input("Academic year (2025): ").strip() or "2025"
expires = input("Expiration (MM/DD/YY) [06/01/26]: ").strip() or "06/01/26"

if not db.users.find_one({"id": user_id}):
    print("User does not exist")
    exit()

if db.cards.find_one({"id": card_id}):
    print("Card ID already in use")
    exit()

expires_date = datetime.strptime(expires, "%m/%d/%y")

db. cards.insert_one({
    "id": card_id,
    "user_id": user_id,
    "academic_year": academic_year,
    "expires": expires_date,
    "issued": int(time.time()),
    "expired": False,
    "enabled": True
})

print("Card linked successfully")