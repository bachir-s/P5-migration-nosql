from unittest.mock import MagicMock, patch, Mock
import pandas as pd
from script.migrate_csv_to_mongodb import migrate_csv_to_mongodb


def test_migrate_csv_to_mongodb(tmp_path):
    csv = tmp_path / "data.csv"

    # Create a CSV with the expected structure
    test_data = pd.DataFrame([
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
    test_data.to_csv(csv, index=False)

    mock_collection = MagicMock()
    mock_db = MagicMock()
    mock_client = MagicMock()

    # Setup mock to return db when accessed
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection

    # Mock bulk_write result
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

        # Verify MongoClient was called with correct URI
        MockClient.assert_called_once_with("mongodb://fake")

        # Verify create_roles was called
        mock_create_roles.assert_called_once_with(mock_db)

        # Verify create_index was called
        assert mock_collection.create_index.call_count == 4

        # Verify bulk_write was called
        mock_collection.bulk_write.assert_called()

        # Verify that documents were inserted
        call_args = mock_collection.bulk_write.call_args[0][0]
        assert len(call_args) == 2


#test de connexion
