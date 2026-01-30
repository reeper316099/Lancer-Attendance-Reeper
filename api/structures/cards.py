import random
import time
from datetime import datetime

from pymongo.synchronous.collection import Collection


class Cards:

    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, user_id: str, academic_year: str, expires: str):
        while True:
            card_id = str(random.randint(0, 999999)).zfill(6)

            if not self.collection.find_one({"id": card_id}):
                break

        expires_date = datetime.strptime(expires, "%m/%d/%y")

        self.collection.insert_one({
            "id": card_id,
            "user_id": user_id,
            "academic_year": academic_year,
            "expires": expires_date,
            "issued": int(time.time()),
            "expired": False,
            "enabled": True
        })
        return True

    def update(self, card_id: str, enabled: bool):
        filter = {"id": card_id}
        document = self.collection.find_one(filter)

        if not document:
            return

        document["enabled"] = enabled
        self.collection.replace_one(filter, document)

    def delete(self, card_id: str):
        filter = {"id": card_id}
        document = self.collection.find_one(filter)

        if not document:
            return False

        self.collection.delete_one(filter)
        return True

    def get(self, filter: dict):
        return list(self.collection.find(filter, {"_id": 0}))

    def get_all(self):
        return self.collection.find({}, {"_id": 0}).to_list()
