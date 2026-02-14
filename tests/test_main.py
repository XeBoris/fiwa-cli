"""Tests for the main FiWa application."""
import pytest
from unittest.mock import Mock

from main import MyApp


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    # Create a mock database handler
    mock_dbh = Mock()

    # Mock the op_get_user_sessions method
    mock_dbh.op_get_user_sessions.return_value = {
        "user_info": {
            "username": "TestUser",
            "user_id": 123
        },
        "session_info": {
            "session_uuid": "test-session-uuid-123",
            "session_start": "2025-01-01 10:00:00",
            "is_logged_in": True
        },
        "project_info": [
            {
                "project_id": 1,
                "project_name": "Test Project Alpha",
                "project_primary": True
            },
            {
                "project_id": 2,
                "project_name": "Test Project Beta",
                "project_primary": False
            }
        ]
    }

    # Mock the op_get_current_user method
    mock_dbh.op_get_current_user.return_value = "TestUser"

    return {
        "dbh": mock_dbh,
        "other_key": "other_value"
    }


@pytest.mark.asyncio
async def test_app_initialization(mock_config):
    """Test that the MyApp initializes correctly with mock configuration."""
    # Initialize the app with mock config
    app = MyApp(config=mock_config)

    # Test that app_state was properly initialized from database
    assert app.app_state["user_name"] == "TestUser"
    assert app.app_state["user_id"] == 123
    assert app.app_state["session_uuid"] == "test-session-uuid-123"
    assert app.app_state["session_start"] == "2025-01-01 10:00:00"
    assert app.app_state["is_logged_in"] is True

    # Test project information
    assert app.app_state["project_ids"] == [1, 2]
    assert app.app_state["project_names"] == ["Test Project Alpha", "Test Project Beta"]
    assert app.app_state["project_id"] == 1  # Primary project

    # Test config is stored
    assert app._config == mock_config
    assert app._mode == "terminal"

    # Run the app in test mode to verify it composes correctly
    async with app.run_test() as pilot:
        # Wait for the app to fully initialize
        await pilot.pause()

        # Verify the app composed successfully and key widgets exist
        main_body = app.query_one("#main_body")
        assert main_body is not None

        user_session_info = app.query_one("#user_session_info")
        assert user_session_info is not None

        calendar_button = app.query_one("#calendar_button")
        assert calendar_button is not None

        # Wait a bit more for reactive updates to propagate
        await pilot.pause()

        # Verify the app state is correctly set (this is the main validation)
        # The UI update might be async, but app_state should be immediate
        assert app.app_state["user_name"] == "TestUser"
        assert app.app_state["session_uuid"] == "test-session-uuid-123"
