from unittest.mock import MagicMock, patch, Mock
import pandas as pd
import pytest
from script.migrate_csv_to_mongodb import migrate_csv_to_mongodb


@pytest.fixture
def sample_healthcare_data():
    """Fixture that provides sample healthcare data for testing"""
    return pd.DataFrame([
        {
            "Name": "ali hassan",
            "Age": 30,
            "Gender": "Male",
            "Blood Type": "A+",
            "Medical Condition": "Diabetes",
            "Date of Admission": "2023-01-15",
            "Doctor": "Dr. Smith",
            "Hospital": "City Hospital",
            "Insurance Provider": "Blue Cross",
            "Billing Amount": 1500.50,
            "Room Number": 101,
            "Admission Type": "Urgent",
            "Discharge Date": "2023-01-20",
            "Medication": "Insulin",
            "Test Results": "Normal"
        },
        {
            "Name": "sara ahmed",
            "Age": 25,
            "Gender": "Female",
            "Blood Type": "B+",
            "Medical Condition": "Asthma",
            "Date of Admission": "2023-02-10",
            "Doctor": "Dr. Jones",
            "Hospital": "Metro Hospital",
            "Insurance Provider": "Aetna",
            "Billing Amount": 2000.75,
            "Room Number": 202,
            "Admission Type": "Emergency",
            "Discharge Date": "2023-02-15",
            "Medication": "Ibuprofen",
            "Test Results": "Abnormal"
        }
    ])


def test_migrate_csv_to_mongodb(tmp_path, sample_healthcare_data):
    """Test the complete migration process with mocked MongoDB"""
    csv = tmp_path / "data.csv"
    sample_healthcare_data.to_csv(csv, index=False)

    mock_collection = MagicMock()
    mock_db = MagicMock()
    mock_client = MagicMock()

    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection

    mock_result = Mock()
    mock_result.inserted_count = 2
    mock_collection.bulk_write.return_value = mock_result

    with patch("script.migrate_csv_to_mongodb.MongoClient") as MockClient, \
         patch("script.migrate_csv_to_mongodb.create_roles") as mock_create_roles:

        MockClient.return_value = mock_client

        migrate_csv_to_mongodb(
            csv_path=str(csv),
            mongo_uri="mongodb://fake",
            db_name="fake_db",
            collection_name="patients"
        )

        MockClient.assert_called_once_with("mongodb://fake")

        mock_create_roles.assert_called_once_with(mock_db)
        assert mock_collection.create_index.call_count == 4
        mock_collection.bulk_write.assert_called()
        call_args = mock_collection.bulk_write.call_args[0][0]
        assert len(call_args) == 2


def test_data_formatting(tmp_path, sample_healthcare_data):
    """Test that data is properly formatted: dates, names (title case), and billing amounts (Decimal128)"""
    from script.migrate_csv_to_mongodb import clean_and_transform, df_to_mongo_documents
    from bson.decimal128 import Decimal128
    from datetime import datetime

    csv = tmp_path / "data.csv"
    sample_healthcare_data.to_csv(csv, index=False)

    df = pd.read_csv(csv)
    df_cleaned = clean_and_transform(df)
    documents = df_to_mongo_documents(df_cleaned)

    assert len(documents) == 2

    doc1 = documents[0]

    assert doc1["patient"]["name"] == "Ali Hassan", f"Expected 'Ali Hassan', got '{doc1['patient']['name']}'"

    assert isinstance(doc1["encounter"]["admissionDate"], datetime), \
        f"admissionDate should be datetime, got {type(doc1['encounter']['admissionDate'])}"
    assert isinstance(doc1["encounter"]["dischargeDate"], datetime), \
        f"dischargeDate should be datetime, got {type(doc1['encounter']['dischargeDate'])}"

    assert isinstance(doc1["encounter"]["billingAmount"], Decimal128), \
        f"billingAmount should be Decimal128, got {type(doc1['encounter']['billingAmount'])}"

    billing_value = float(doc1["encounter"]["billingAmount"].to_decimal())
    assert billing_value == 1500.50, f"Expected 1500.50, got {billing_value}"

    assert doc1["encounter"]["admissionDate"].year == 2023
    assert doc1["encounter"]["admissionDate"].month == 1
    assert doc1["encounter"]["admissionDate"].day == 15
    assert doc1["encounter"]["dischargeDate"].year == 2023
    assert doc1["encounter"]["dischargeDate"].month == 1
    assert doc1["encounter"]["dischargeDate"].day == 20

    doc2 = documents[1]

    assert doc2["patient"]["name"] == "Sara Ahmed", f"Expected 'Sara Ahmed', got '{doc2['patient']['name']}'"

    billing_value2 = float(doc2["encounter"]["billingAmount"].to_decimal())
    assert billing_value2 == 2000.75, f"Expected 2000.75, got {billing_value2}"


