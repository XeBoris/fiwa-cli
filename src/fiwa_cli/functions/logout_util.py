"""Centralized logout functionality for FiWa CLI.

This module provides shared logout logic used across the application to
ensure consistent session cleanup and state reset behavior regardless of
where logout is initiated (menu, settings, keyboard shortcut).

The logout utility:
    - Clears user session in database
    - Resets app_state to default values
    - Preserves application-level configuration
    - Returns to main screen
    - Shows success/error notifications

Key Functions:
    - **perform_logout()**: Complete logout workflow
    - **return_to_main_screen()**: Screen stack cleanup

Design Rationale:
    Centralized logout prevents code duplication and ensures that logout
    behaves consistently whether initiated from:
        - Menu (press M → Logout)
        - Settings (user management)
        - Keyboard (press Q with logout)
        - LoginScreen modal

Example:
    Using perform_logout::

        >>> from fiwa_cli.functions.logout_util import perform_logout
        >>>
        >>> # From menu or any screen
        >>> success = perform_logout(self.app)
        >>> if success:
        >>>     # User logged out, returned to main screen
        >>>     pass

    Complete logout flow::

        >>> # User clicks "Logout" in menu
        >>> perform_logout(self.app)
        >>> # 1. Clears session in database
        >>> # 2. Resets app_state to defaults
        >>> # 3. Shows "Logout successful!" notification
        >>> # 4. Returns to main screen
        >>> # 5. Returns True

See Also:
    screens.menu.MenuScreen: Uses perform_logout for menu logout
    screens.base.LoginScreen: Has own perform_logout (includes modal dismissal)
    main.MyApp: Keyboard bindings for quit with logout
"""


def perform_logout(app) -> bool:
    """Perform complete logout operation with session cleanup and state reset.

    This is the centralized logout logic used throughout the application.
    It handles database session invalidation, app_state reset, and
    navigation back to the main screen.

    The logout process:
        1. Retrieves session_uuid from app_state
        2. Preserves application-level config (abs_path, css_form, css_theme)
        3. Calls op_user_logout() to clear session in database
        4. Resets app_state to default "logged out" values
        5. Restores preserved application config
        6. Shows success notification
        7. Schedules return to main screen
        8. Returns True

    Args:
        app: The main application instance (MyApp)
            Must have:
                - _config: Config dict with "dbh" (database handler)
                - app_state: Reactive state dict
                - notify(): Notification method
                - log(): Logging method
                - call_after_refresh(): Deferred execution

    Returns:
        bool: True if logout successful, False if failed

    Side Effects:
        - Updates database: session.is_logged_in = False
        - Resets app_state to default values (user_name="Guest", etc.)
        - Preserves abs_path, css_form, css_theme
        - Shows success/error notification
        - Schedules return_to_main_screen()
        - Logs all operations

    Example:
        Successful logout::

            >>> success = perform_logout(app)
            >>> # Database session cleared
            >>> # app_state reset to defaults
            >>> # Returns to main screen
            >>> # success = True
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
    """Pop all screens from stack to return to main application screen.

    Cleans up the screen stack by removing all screens except the base
    main screen. This is typically called after logout to provide a
    clean starting state.

    Args:
        app: The main application instance (MyApp)
            Must have:
                - screen_stack: List of active screens
                - pop_screen(): Method to remove top screen
                - log(): Logging method

    Side Effects:
        - Pops all screens except the base screen (len=1)
        - Logs navigation or any errors

    Example:
        After logout::

            >>> # Screen stack: [MainScreen, SettingsScreen, MenuScreen]
            >>> return_to_main_screen(app)
            >>> # Pops all except MainScreen
            >>> # User sees clean main screen
    """
    try:
        # Pop all screens except the main screen
        while len(app.screen_stack) > 1:
            app.pop_screen()
    except Exception as e:
        app.log(f"Error returning to main screen: {e}")
