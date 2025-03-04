
import os
import sys

from pymongo.errors import PyMongoError
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname('app'), '..')))

from motor.motor_asyncio import AsyncIOMotorClient as MongoClient, AsyncIOMotorDatabase
from beanie import init_beanie



class MongoDB:

    def __init__(self, mongo_uri: str, database_name: str, document_models = None):
        self.mongo_uri = mongo_uri
        self.document_models = document_models if document_models is not None else []
        self.database_name = database_name
        self.client: MongoClient | None = None
        self.db: AsyncIOMotorDatabase | None = None


    async def init_db(self) -> None:

        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.database_name]

            self.ping()

            # ADD TO THIS LIST THE PYDANTIC DOCUMENT CLASS

            await init_beanie(database=self.db, document_models=self.document_models)
            print("MongoDB connection established and Beanie initialized.")
        except Exception as e:
            print(f"Error initializing MongoDB: {e}")
            raise

    async def close_connection(self) -> None:

        if self.client:
            self.client.close()
            print("MongoDB connection closed.")

    def ping(self) -> None:

        try:
            self.client.admin.command('ping')
            print("Pinged MongoDB deployment successfully.")
        except PyMongoError as e:
            print(f"Failed to ping MongoDB: {e}")
            raise

    def get_db(self) -> AsyncIOMotorDatabase:

        if self.db == None:
            raise ValueError("Database not initialized. Call init_db() first.")
        return self.db

    def get_client(self) -> MongoClient:

        if not self.client:
            raise ValueError("Client not initialized. Call init_db() first.")
        return self.client

