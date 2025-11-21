import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_URI")
COLLECTION_NAME = os.getenv("MONGO_URI")

def migrate_csv_to_mongodb(csv_path, mogo_uri, db_name, collection_name):
    
    df = pd.read_csv(csv_path)

    client = MongoClient(mogo_uri)
    db = client[db_name]
    collection = db[collection_name]

    data = df.to_dict(orient="records")

    result = collection.insert_many(data)
    print(f"{len(result.inserted_ids)} documents insérés.")

if __name__ == "__main__":
    migrate_csv_to_mongodb("data/migrate_csv_to_mongodb.csv",MONGO_URI,DB_NAME,COLLECTION_NAME)
