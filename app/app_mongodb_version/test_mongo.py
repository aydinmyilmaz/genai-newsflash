from pymongo import MongoClient

# Connect to MongoDB on port 27018
client = MongoClient("mongodb://localhost:27017/")

# Test the connection
db_list = client.list_database_names()
print("Databases:", db_list)
