"""Pytest configuration and shared fixtures for FiWa CLI tests."""

import sys
from pathlib import Path
import pytest
import tempfile

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests.

    Yields:
        Path: Temporary directory path

    Example:
        >>> def test_something(temp_dir):
        >>>     db_path = temp_dir / "test.db"
        >>>     # Use db_path for testing
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db_path(temp_dir):
    """Create a temporary database path.

    Yields:
        Path: Path to temporary database file

    Example:
        >>> def test_db_operations(temp_db_path):
        >>>     dbh = SQLLiteHandler(db_path=str(temp_db_path))
        >>>     # Use dbh for testing
    """
    db_path = temp_dir / "test_fiwa.db"
    yield db_path


@pytest.fixture
def mock_dbh():
    """Provide a mock database handler for testing without real database.

    Returns:
        Mock: Mock SQLLiteHandler with common methods mocked

    Example:
        >>> def test_without_db(mock_dbh):
        >>>     mock_dbh.op_user_get_all.return_value = [{"user_id": 1}]
        >>>     users = mock_dbh.op_user_get_all()
        >>>     assert len(users) == 1
    """
    from unittest.mock import Mock

    mock = Mock()
    # Mock common methods with default return values
    mock.op_user_get_all.return_value = []
    mock.op_user_get_info.return_value = {}
    mock.op_project_get_info.return_value = []
    mock.op_label_get_all.return_value = []
    mock.op_item_get_by_user.return_value = []
    mock.op_user_login.return_value = None
    mock.op_user_logout.return_value = True
    mock.op_total_number_of_users.return_value = 0

    return mock


@pytest.fixture
def real_dbh(temp_db_path):
    """Provide a real SQLLiteHandler with temporary database.

    Creates an in-memory SQLite database with schema initialized,
    ready for testing actual database operations.

    Yields:
        SQLLiteHandler: Initialized database handler with schema

    Example:
        >>> def test_user_crud(real_dbh):
        >>>     user_id = real_dbh.op_user_create({"username": "test"})
        >>>     assert user_id > 0
        >>>     user = real_dbh.op_user_get_info(user_id)
        >>>     assert user["username"] == "test"

    Note:
        The database is initialized with schema but no data.
        Use sample_user_data, sample_project_data fixtures to populate.
    """
    from fiwa_cli.functions.handler_sqllite import SQLLiteHandler
    import os

    # Use in-memory database for speed
    dbh = SQLLiteHandler(db_path=":memory:")

    # Initialize with schema
    # Get schema path
    schema_path = os.path.join(
        os.path.dirname(__file__),
        "..", "src", "fiwa_cli", "database", "schema.sql"
    )

    if os.path.exists(schema_path):
        dbh.initialize_database(schema_path=schema_path)

    yield dbh

    # Cleanup (close connection if needed)
    # dbh connection auto-closes for in-memory db


@pytest.fixture
def sample_config(mock_dbh):
    """Provide complete sample configuration dictionary matching loader.py structure.

    This fixture provides a complete configuration dictionary that matches
    the structure returned by setup_fiwa() and used throughout the application.

    Returns:
        dict: Complete configuration data with all expected keys

    Structure:
        - configuration: App configuration (host, model, path)
        - development: Dev settings (debug_mode, stage)
        - style: UI styling (form, theme)
        - _data_directory: Data storage path
        - _abs_path: Absolute path to package
        - dbh: Database handler (mocked)

    Example:
        >>> def test_config_loading(sample_config):
        >>>     assert sample_config["style"]["theme"] == "textual-light"
        >>>     assert sample_config["configuration"]["model"] == "local"

    Note:
        The dbh (database handler) is a mock object by default.
        For actual database testing, use real_dbh fixture.
    """
    return {
        "configuration": {
            "host": "terminal",
            "model": "local",
            "path": "/tmp/fiwa-test"
        },
        "development": {
            "debug_mode": True,
            "stage": "test"
        },
        "style": {
            "form": "handsome",
            "theme": "textual-light"
        },
        "_data_directory": "/tmp/fiwa-test",
        "_abs_path": "/tmp/fiwa-cli",
        "dbh": mock_dbh
    }


@pytest.fixture
def mock_app_state():
    """Provide mock app_state dictionary.

    Returns:
        dict: Mock app_state with default values

    Example:
        >>> def test_app_state(mock_app_state):
        >>>     assert mock_app_state["user_name"] == "TestUser"
    """
    return {
        "user_name": "TestUser",
        "user_id": 1,
        "user_scope": "user:write",
        "session_uuid": "test-session-uuid",
        "session_start": "2026-03-29 10:00:00",
        "is_logged_in": True,
        "project_names": ["Test Project"],
        "project_ids": [1],
        "project_id": 1,
        "project_name": "Test Project",
        "project_style": "ExpenseTracker",
        "project_store": {"month_start": 1},
        "current_project_currency_main": "USD",
        "current_project_currency_list": ["EUR", "GBP"],
        "abs_path": "/tmp/fiwa-test",
        "css_form": "handsome",
        "css_theme": "textual-light",
    }


@pytest.fixture
def sample_user_data():
    """Provide sample user data dictionary.

    Returns:
        dict: Sample user data for testing

    Example:
        >>> def test_user_creation(sample_user_data):
        >>>     user_id = dbh.op_user_create(sample_user_data)
        >>>     assert user_id > 0
    """
    return {
        "first_name": "Test",
        "last_name": "User",
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "scope": "user:write",
        "activated": True
    }


@pytest.fixture
def sample_project_data():
    """Provide sample project data dictionary.

    Returns:
        dict: Sample project data for testing with all required fields

    Example:
        >>> def test_project_creation(sample_project_data):
        >>>     project_id = dbh.op_project_create(sample_project_data, user_id=1)
        >>>     assert project_id > 0
    """
    import json
    return {
        "project_name": "Test Project",
        "description": "A test project for pytest",
        "currency_main": "USD",
        "currency_list": json.dumps(["EUR", "GBP"]),
        "project_store": json.dumps({"month_start": 1}),
        "project_style": "ExpenseTracker"
    }


@pytest.fixture
def sample_item_data():
    """Provide sample item/transaction data dictionary.

    Returns:
        dict: Sample item data for testing

    Example:
        >>> def test_item_creation(sample_item_data):
        >>>     item_id = dbh.op_item_create(sample_item_data)
        >>>     assert item_id > 0
    """
    import uuid
    from datetime import datetime

    return {
        "item_uuid": str(uuid.uuid4()),
        "name": "Test Item",
        "note": "Test note",
        "price": 10.50,
        "price_final": 10.50,
        "currency": "USD",
        "currency_final": "USD",
        "bought_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "bought_by_id": 1,
        "bought_for_id": 1,
        "added_by_id": 1,
        "project_id": 1,
        "exchange_rate": 1.0,
        "exchange_rate_date": datetime.now().strftime("%Y-%m-%d"),
        "tags": "1_2_3_4_[]"
    }
