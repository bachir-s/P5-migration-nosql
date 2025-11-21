from unittest.mock import MagicMock, patch
import pandas as pd
from script.migrate import migrate_csv_to_mongodb

def test_migrate_csv_to_mongodb(tmp_path):
  
    csv = tmp_path / "data.csv"
    pd.DataFrame([
        {"name": "Ali", "age": 30},
        {"name": "Sara", "age": 25},
    ]).to_csv(csv, index=False)

    
    mock_collection = MagicMock()

    with patch("script.migrate.MongoClient") as MockClient:
        mock_client = MagicMock()
        MockClient.return_value = mock_client

        mock_client.__getitem__.return_value = {
            "patients": mock_collection
        }
    
        migrate_csv_to_mongodb(
            csv_path=str(csv),
            mongo_uri="mongodb://fake",
            db_name="fake_db",
            collection_name="patients"
        )

        mock_collection.insert_many.assert_called_once_with([
            {"name": "Ali", "age": 30},
            {"name": "Sara", "age": 25}
        ])
