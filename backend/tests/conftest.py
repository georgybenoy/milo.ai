"""
Shared test fixtures.
"""

import pytest
import pandas as pd
from pathlib import Path

from backend.app.data_loader import load_orders, _df
from backend.app.config import CSV_PATH


@pytest.fixture(autouse=True, scope="session")
def loaded_orders():
    """Load orders once for all tests."""
    import backend.app.data_loader as dl
    dl._df = None  # Reset
    df = load_orders(CSV_PATH)
    return df


@pytest.fixture
def orders_df(loaded_orders):
    """Return the loaded DataFrame."""
    return loaded_orders
