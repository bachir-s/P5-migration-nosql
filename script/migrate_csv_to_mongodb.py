import pandas as pd
import uuid
from pymongo import MongoClient , InsertOne
from bson.decimal128 import Decimal128
import os
from dotenv import load_dotenv
from script.roles import create_roles

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

ENUM_MAP = {
    "Gender": {"Male": 1, "Female": 2},
    "Blood Type": {
        "A+": 1, "A-": 2, "B+": 3, "B-": 4,
        "O+": 5, "O-": 6, "AB+": 7, "AB-": 8
    },
    "Medical Condition": {
        "Cancer": 1, "Diabetes": 2, "Obesity": 3,
        "Asthma": 4, "Hypertension": 5, "Healthy": 6
    },
    "Insurance Provider": {
        "Blue Cross": 1, "Aetna": 2, "Medicare": 3,
        "Medicaid": 4, "Cigna": 5
    },
    "Admission Type": {"Urgent": 1, "Emergency": 2, "Elective": 3},
    "Medication": {"Paracetamol": 1, "Ibuprofen": 2, "Aspirin": 3, "Penicillin": 4, "Insulin": 5},
    "Test Results": {"Normal": 1, "Abnormal": 2, "Inconclusive": 3}
}

DOCTOR_CACHE = {}
HOSPITAL_CACHE = {}

BATCH_SIZE = 100


def get_or_create_id(name: str, cache: dict) -> str:
    if name not in cache:
        cache[name] = str(uuid.uuid4())
    return cache[name]

def create_indexes(db):
    collection = db[COLLECTION_NAME]
    collection.create_index("patient.name.last")
    collection.create_index("encounter.admissionDate")
    collection.create_index("encounter.hospital.id")
    collection.create_index("encounter.doctor.id")  

def clean_and_transform(df):
    df["Name"] = df["Name"].str.title()
    df["Date of Admission"] = pd.to_datetime(df["Date of Admission"])
    df["Discharge Date"] = pd.to_datetime(df["Discharge Date"])
    df["Billing Amount"] = df["Billing Amount"].apply(lambda x: Decimal128(str(x)))
    for col, mapping in ENUM_MAP.items():
        if col in df.columns:
            df[col] = df[col].map(mapping)
    return df

def df_to_mongo_documents(df):
    docs = []
    for _, row in df.iterrows():
        doctor_name = row["Doctor"]
        hospital_name = row["Hospital"]

        doc = {
            "patient": {
                "name": row["Name"],
                "age": int(row["Age"]),
                "gender": row["Gender"],
                "bloodType": row["Blood Type"],
                "condition": row["Medical Condition"],
                "insurance": {
                    "provider": row["Insurance Provider"]
                }
            },
            
            "encounter": {
                "admissionDate": row["Date of Admission"].to_pydatetime(),
                "dischargeDate": row["Discharge Date"].to_pydatetime(),
                "admissionType": row["Admission Type"],
                "room": int(row["Room Number"]),
                "medication": row["Medication"],
                "testResults": row["Test Results"],
                "doctor": {
                    "id": get_or_create_id(doctor_name, DOCTOR_CACHE),
                    "name": doctor_name
                },
                "hospital": {
                    "id": get_or_create_id(hospital_name, HOSPITAL_CACHE),
                    "name": hospital_name
                },
                "billingAmount": Decimal128(str(row["Billing Amount"]))
            }
        }
        docs.append(doc)
    return docs


def migrate_csv_to_mongodb(csv_path, mongo_uri, db_name, collection_name):
    df = pd.read_csv(csv_path)
    df_cleaned = clean_and_transform(df)
    documents = df_to_mongo_documents(df_cleaned)

    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    create_roles(db)
    create_indexes(db)

    operations = []
    inserted_total = 0

    for doc in documents:
        operations.append(InsertOne(doc))

        if len(operations) == BATCH_SIZE:
            result = collection.bulk_write(operations, ordered=False)
            inserted_total += result.inserted_count
            operations = []

    # dernier batch
    if operations:
        result = collection.bulk_write(operations, ordered=False)
        inserted_total += result.inserted_count

    print(f"{inserted_total} documents insérés avec succès !")
if __name__ == "__main__":
    migrate_csv_to_mongodb(
        "data/healthcare_dataset.csv",
        MONGO_URI,
        DB_NAME,
        COLLECTION_NAME
    )
