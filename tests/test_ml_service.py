import pytest
from unittest.mock import MagicMock
import pandas as pd
from backend.app.domains.ml.service import MLDatasetService

def test_ml_dataset_service_empty():
    mock_engine = MagicMock()
    service = MLDatasetService(mock_engine)

    # When query returns empty dataframe
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(pd, "read_sql_query", lambda sql, con: pd.DataFrame())
        dataset = service.build_flattened_dataset()
        assert dataset == []
