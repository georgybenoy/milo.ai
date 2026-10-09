"""
Shared test fixtures for Milo test suite.
"""

import sys
from pathlib import Path
import pytest
import pandas as pd

# Ensure backend directory is in sys.path so both 'import app...' and 'import backend.app...' work
backend_dir = Path(__file__).resolve().parent.parent
root_dir = backend_dir.parent
for p in [str(backend_dir), str(root_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.data_loader import load_orders, reset_orders
from app.config import CSV_PATH


@pytest.fixture(autouse=True, scope="session")
def loaded_orders():
    """Load orders once for test session."""
    reset_orders()
    df = load_orders(CSV_PATH, force_reload=True)
    return df


@pytest.fixture
def orders_df(loaded_orders):
    """Return the loaded DataFrame."""
    return loaded_orders
