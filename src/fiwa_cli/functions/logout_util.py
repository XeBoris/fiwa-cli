"""Logout utility - Centralized logout logic for FiWa CLI."""


def perform_logout(app) -> bool:
    """Perform logout operation - can be called from anywhere in the app.

    This is the centralized logout logic used by menu.py and other components.

    Args:
        app: The main application instance

    Returns:
        True if logout was successful, False otherwise
    """
    try:
        # Get database handler
        k = app._config.get("dbh")

        # Get session UUID from app state
        session_uuid = app.app_state.get("session_uuid")

        # IMPORTANT: Preserve application-level configuration that should persist across login/logout
        # These are not user-specific, they're application configuration
        abs_path = app.app_state.get("abs_path", "")
        css_form = app.app_state.get("css_form", "handsome")
        css_theme = app.app_state.get("css_theme", "textual-light")

        # Verify logout - call the correct database method with session_uuid
        verify = k.op_user_logout(session_uuid=session_uuid)

        if verify:
            # Update app state to logged-out state
            app.app_state = {
                "user_name": "Guest",
                "user_id": -1,
                "user_scope": "user:write",
                "session_uuid": "No session",
                "session_start": None,
                "is_logged_in": False,
                "project_names": ["No Projects"],
                "project_ids": [0],
                "project_id": 0,
                "project_name": "No Project",
                "project_style": "default",
                # Restore application-level configuration
                "abs_path": abs_path,
                "css_form": css_form,
                "css_theme": css_theme,
            }

            app.notify("Logout successful!", severity="success")

            # Pop all screens to return to main screen
            app.call_after_refresh(lambda: return_to_main_screen(app))

            return True
        else:
            app.notify("Logout failed. Please try again.", severity="error")
            return False

    except Exception as e:
        app.notify(f"Error during logout: {str(e)}", severity="error")
        app.log(f"Logout error: {e}")
        return False


def return_to_main_screen(app) -> None:
    """Pop all screens to return to the main screen.

    Args:
        app: The main application instance
    """
    try:
        # Pop all screens except the main screen
        while len(app.screen_stack) > 1:
            app.pop_screen()
    except Exception as e:
        app.log(f"Error returning to main screen: {e}")
