from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb+srv://ethansinclair527:ethansinclair527@cluster0.5imi7.mongodb.net/")  # replace with your MongoDB URI
db = client['userDatabase']  # replace with your database name
collection = db['users']  # replace with your collection name

username = "KingEthan"
email = "kingethan@gmail.com"
password = "kingethan123"  # Simple password (no hashing)
age = 1000
created_at = datetime.now()  # Current timestamp

new_user = {
    "username": "KingEthan",
    "email": "kingethan@gmail.com",
    "password": "kingethan123", 
    "age": 1000,
    "created_at": datetime.now()
}

result = collection.insert_one(new_user)

