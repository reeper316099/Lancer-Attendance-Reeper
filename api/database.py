import os
import random
import uuid

from pymongo import MongoClient
from dotenv import load_dotenv


class Database:

    load_dotenv()

    URI = os.getenv("DB_URI")
    NAME = os.getenv("DB_NAME")

    @staticmethod
    def establish_connection(uri, database_name):
        client = MongoClient(uri)
        return client[database_name]
