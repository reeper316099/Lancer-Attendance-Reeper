import time
from datetime import datetime

from pymongo.synchronous.collection import Collection


class Users:

    def __init__(self, collection: Collection):
        self.collection = collection

    def create(self, name: str, id: str, position: str, admin: bool):
        filter = {"id": id}
        document = self.collection.find_one(filter)

        if document:
            return False

        self.collection.insert_one({
            "id": id,
            "name": name,
            "position": position,
            "admin": admin,
            "score": 0,
            "attendance": []
        })
        return True

    def update(self, id: str, position: str = None, score: int = None, admin: bool = False):
        filter = {"id": id}
        document = self.collection.find_one(filter)

        if not document:
            return False

        document["position"] = position if position else document["position"]
        document["score"] = score if score else document["score"]
        document["admin"] = admin if admin else False

        self.collection.replace_one(filter, document)
        return True

    def delete(self, id):
        filter = {"id": id}
        document = self.collection.find_one(filter)

        if not document:
            return False

        self.collection.delete_one(filter)
        return True

    def get(self, filter: dict):
        return self.collection.find_one(filter, {"_id": 0})

    def get_all(self):
        return self.collection.find({}, {"_id": 0}).to_list()

    def set_score(self, id: str, score: int):
        filter = {"id": id}
        document = self.collection.find_one(filter)

        if not document:
            return

        document["score"] = score
        self.collection.replace_one(filter, document)

    def check_in(self, id: str):
        filter = {"id": id}
        document = self.collection.find_one(filter)

        if not document:
            return

        for obj in document["attendance"]:
            if not obj["out"] and obj["date"] == datetime.now().strftime("%x"):
                obj["out"] = int(time.time())
                document["score"] += int((obj["out"] - obj["in"]) / 60)

                self.collection.replace_one(filter, document)
                return False

        document["attendance"].append({
            "date": datetime.now().strftime("%x"),
            "in": int(time.time()),
            "out": None
        })

        self.collection.replace_one(filter, document)
        return True
