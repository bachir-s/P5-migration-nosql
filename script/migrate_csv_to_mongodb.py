import pandas as pd
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "medical_db"
COLLECTION_NAME = "patients"

def migrate_data(csv_path):
    
    df = pd.read_csv(csv_path)

    
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    data = df.to_dict(orient="records")

    result = collection.insert_many(data)
    print(f"{len(result.inserted_ids)} documents insérés.")

if __name__ == "__main__":
    migrate_data("data/medical.csv")
