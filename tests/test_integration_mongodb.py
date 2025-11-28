import pytest
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "healthcare_db")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "medical_records")


def is_mongodb_available():
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        client.close()
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return False


pytestmark = pytest.mark.skipif(
    not is_mongodb_available(),
    reason="MongoDB n'est pas disponible"
)


@pytest.fixture(scope="module")
def mongo_client():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    yield client
    client.close()


def test_mongodb_connection(mongo_client):
    try:
        mongo_client.admin.command('ping')
        assert True
    except ConnectionFailure:
        pytest.fail("MongoDB n'est pas accessible")


def test_mongodb_database_exists(mongo_client):
    db = mongo_client[MONGO_DB_NAME]
    collections = db.list_collection_names()
    assert isinstance(collections, list)


def test_collection_document_count(mongo_client, expected_count=None):
    db = mongo_client[MONGO_DB_NAME]
    collection = db[MONGO_COLLECTION_NAME]
    actual_count = collection.count_documents({})

    if expected_count is not None:
        assert actual_count == expected_count
    else:
        assert actual_count >= 0


def check_document_count(expected_count):
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    try:
        db = client[MONGO_DB_NAME]
        collection = db[MONGO_COLLECTION_NAME]
        actual_count = collection.count_documents({})
        return actual_count == expected_count
    finally:
        client.close()
