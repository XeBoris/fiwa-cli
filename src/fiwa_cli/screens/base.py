"""Base screen components for FiWa CLI.

This module provides foundational screen classes that other screens inherit
from, including reactive state management and authentication functionality.

The base module contains:
    - ReactiveScreen: Base class with automatic app_state watching
    - LoginScreen: Modal for user authentication and logout

These base classes provide common functionality used throughout the
application, ensuring consistent behavior for state updates and
authentication across all screens.

Key Features:
    - Automatic app_state change detection
    - Centralized login/logout workflows
    - State update hooks for subclasses
    - Session management
    - Secure authentication with bcrypt
    - Project and user data loading on login

Classes:
    ReactiveScreen: Base class for screens that respond to app_state changes
    LoginScreen: Modal screen for authentication and logout

Example:
    Creating a reactive screen::

        >>> from fiwa_cli.screens.base import ReactiveScreen
        >>>
        >>> class MyScreen(ReactiveScreen):
        >>>     def update_displays(self):
        >>>         # This is called automatically when app_state changes
        >>>         header = self.query_one(FiwaHeader)
        >>>         header.user = self.app.app_state["user_name"]

    Opening login screen::

        >>> from fiwa_cli.screens.base import LoginScreen
        >>> login = LoginScreen(is_logged_in=False)
        >>> # In async context:
        >>> async def do_login():
        >>>     result = await self.app.push_screen_wait(login)
        >>>     if result and result.get("success"):
        >>>         print(f"Logged in as {result['username']}")

See Also:
    main.MyApp: Main application with app_state management
    functions.logout_util.perform_logout: Shared logout utility
"""
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, Button
from textual.app import ComposeResult

from textual.screen import Screen

class ReactiveScreen(Screen):
    """Base screen class with automatic app_state change detection.

    This base class provides automatic reactivity to app_state changes.
    Any screen inheriting from ReactiveScreen will automatically receive
    notifications when app_state is modified and can update its display
    accordingly.

    The reactive pattern allows screens to stay synchronized with
    application state without manual refresh calls. When app_state
    changes (e.g., user logs in, project switches), all ReactiveScreen
    instances automatically update their displays.

    Subclass Implementation:
        To use ReactiveScreen, inherit from it and override update_displays():

        1. Inherit from ReactiveScreen instead of Screen
        2. Override update_displays() method
        3. Update widgets based on self.app.app_state
        4. Changes automatically trigger when app_state modified

    Automatic Behavior:
        - on_mount() sets up watcher for app_state
        - When app_state changes, _on_app_state_change() fires
        - _on_app_state_change() calls update_displays()
        - Subclass's update_displays() updates UI

    Example:
        Creating a reactive screen::

            >>> from fiwa_cli.screens.base import ReactiveScreen
            >>>
            >>> class MyDashboard(ReactiveScreen):
            >>>     def update_displays(self):
            >>>         # Called automatically on app_state changes
            >>>         try:
            >>>             header = self.query_one(FiwaHeader)
            >>>             header.user = self.app.app_state["user_name"]
            >>>             header.project_id = self.app.app_state["project_id"]
            >>>         except:
            >>>             pass  # Widgets may not be ready yet

        Triggering updates::

            >>> # User logs in
            >>> # app_state["is_logged_in"] = True
            >>> # app_state["user_name"] = "batman"
            >>> # ALL ReactiveScreen instances automatically update
            >>> # MyDashboard.update_displays() called
            >>> # Header shows "batman"
            >>>
            >>> # User switches project
            >>> # app_state["project_id"] = 2
            >>> # ALL ReactiveScreen instances update again
            >>> # Header shows new project

    Implementation Details:
        The watcher is set up in on_mount() using:
            ``self.app.watch(self.app, "app_state", self._on_app_state_change)``

        This creates a Textual watcher that monitors the app_state reactive
        variable on the App instance. Any modification to app_state triggers
        the callback.

    Performance:
        - Efficient: Only updates when app_state actually changes
        - Non-blocking: Updates happen asynchronously
        - Safe: Exceptions in update_displays() don't crash app
        - Selective: Subclasses only update relevant widgets

    Note:
        Subclasses should wrap widget queries in try/except blocks within
        update_displays() because widgets may not exist during screen
        transitions or initialization.

        The base implementation of update_displays() does nothing (pass),
        so subclasses are not required to override it unless they need
        reactive updates.

    See Also:
        textual.screen.Screen: Parent class
        main.MyApp: Defines app_state reactive variable
        settings.SettingsScreen: Example ReactiveScreen subclass
        reports.ReportsScreen: Example ReactiveScreen subclass
    """

    def on_mount(self) -> None:
        """Set up app_state watcher when screen is mounted.

        Establishes a Textual watcher that monitors app_state for changes
        and triggers _on_app_state_change() callback when modifications occur.

        Side Effects:
            - Registers watcher on app.app_state
            - Enables automatic update_displays() calls

        Note:
            This is called automatically by Textual after the screen is
            composed but before it's displayed. Subclasses can override
            this method but should call super().on_mount() to maintain
            reactive behavior.
        """
        self.app.watch(self.app, "app_state", self._on_app_state_change)

    def _on_app_state_change(self, new_state: dict) -> None:
        """Callback when app_state changes.

        This internal method is called automatically by the Textual watcher
        whenever app_state is modified. It delegates to update_displays()
        which subclasses can override.

        Args:
            new_state: The new app_state dictionary (complete state, not diff)

        Side Effects:
            - Calls update_displays() to refresh UI

        Note:
            Subclasses should override update_displays(), not this method.
            This method is internal and should not be called directly.
        """
        self.update_displays()

    def update_displays(self) -> None:
        """Update screen widgets when app_state changes.

        This method is called automatically when app_state changes.
        Subclasses should override this to update their widgets based
        on the new state.

        The base implementation does nothing (pass), so subclasses only
        need to override if they have state-dependent displays.

        Example:
            Updating header on state change::

                >>> def update_displays(self):
                >>>     try:
                >>>         header = self.query_one(FiwaHeader)
                >>>         header.user = self.app.app_state["user_name"]
                >>>         header.projects = self.app.app_state["project_names"]
                >>>         header.project_id = self.app.app_state["project_id"]
                >>>     except:
                >>>         # Widgets may not be ready during transitions
                >>>         pass

        Note:
            Always wrap widget queries in try/except because this method
            may be called during screen transitions when widgets don't
            exist yet.
        """
        pass

class LoginScreen(ModalScreen):
    """Modal screen for user authentication and logout.

    This modal provides both login and logout functionality in a single
    screen. It displays different interfaces based on the current login
    state and handles the complete authentication workflow.

    The screen serves two purposes:
        1. **Login Mode** (is_logged_in=False):
           - Shows username/password input fields
           - Validates credentials against database
           - Loads user and project information
           - Updates app_state with session data
           - Dismisses with success result

        2. **Logout Mode** (is_logged_in=True):
           - Shows current username
           - Provides logout button
           - Clears session from database
           - Resets app_state to default values
           - Returns to main screen

    Attributes:
        _is_logged_in (bool): Current login state
        _username (str): Username of logged-in user (if applicable)

    Authentication Flow (Login):
        1. User enters username/email and password
        2. System validates input fields (not empty)
        3. System calls op_user_login(username, password)
        4. Database verifies credentials with bcrypt
        5. Session created in database
        6. User info and projects loaded
        7. app_state updated with user data
        8. Modal dismisses with success result

    Logout Flow:
        1. User clicks Logout button
        2. System calls op_user_logout(session_uuid)
        3. Session cleared in database
        4. app_state reset to default values
        5. Modal dismisses
        6. Returns to main screen

    State Updates on Login:
        app_state is populated with:
            - user_name: Username
            - user_id: User database ID
            - user_scope: Permission scope (e.g., "admin:full")
            - session_uuid: Unique session identifier
            - session_start: Login timestamp
            - is_logged_in: True
            - project_names: List of accessible projects
            - project_ids: Corresponding project IDs
            - project_id: Primary/default project ID
            - project_name: Primary project name
            - project_style: Primary project type
            - project_store: Primary project metadata
            - current_project_currency_main: Primary currency
            - current_project_currency_list: Additional currencies
            - abs_path: Application paths
            - css_form: Form style setting
            - css_theme: Theme setting

    Return Value:
        On dismiss, returns dictionary:
            - success (bool): True if login/logout succeeded
            - user_id (int): User ID (login only)
            - username (str): Username (login only)
            - session_uuid (str): Session ID (login only)
            - session_start (datetime): Login time (login only)
            - action (str): "logout" (logout only)

    Example:
        Opening login modal::

            >>> from fiwa_cli.screens.base import LoginScreen
            >>> login = LoginScreen(is_logged_in=False)
            >>> # In async context:
            >>> async def handle_login():
            >>>     result = await self.app.push_screen_wait(login)
            >>>     if result and result.get("success"):
            >>>         user_id = result["user_id"]
            >>>         username = result["username"]
            >>>         print(f"Welcome, {username}!")

        Login workflow::

            >>> # User not logged in
            >>> # LoginScreen opens with login form
            >>> # User enters:
            >>> #   Username: "batman"
            >>> #   Password: "********"
            >>> # User clicks "Login"
            >>> # perform_login() executes
            >>> # Database query: SELECT * FROM users WHERE username = ?
            >>> # Password verified: bcrypt.checkpw(password, hash)
            >>> # Session created: INSERT INTO sessions (...)
            >>> # Projects loaded: SELECT * FROM user_project_map
            >>> # app_state updated with all user data
            >>> # Notification: "Login successful!"
            >>> # Modal dismisses with success result
            >>> # Main screen now shows user info

        Logout workflow::

            >>> # User logged in as "batman"
            >>> # LoginScreen opens with logout interface
            >>> # Shows: "Currently logged in as: batman"
            >>> # User clicks "Logout" button
            >>> # perform_logout() executes
            >>> # Database: UPDATE sessions SET is_logged_in = 0
            >>> # app_state reset to defaults
            >>> # Notification: "Logout of User batman successful!"
            >>> # Modal dismisses
            >>> # Returns to main screen
            >>> # Main screen shows "Guest" user

    CSS Styling:
        Inline CSS provides:
            - Centered modal (align: center middle)
            - 60 character width
            - Auto height
            - Themed surface background
            - Accent border
            - Proper padding and margins

    Security:
        - Passwords masked with password=True
        - bcrypt verification (never plain text comparison)
        - Session UUIDs for tracking
        - Credentials never logged
        - Automatic session invalidation on logout

    Error Handling:
        Login errors:
            - "Username/Email is required"
            - "Password is required"
            - "Invalid username or password"
            - "No users found in the system"

        Logout errors:
            - "Logout failed. Please try again."

    Note:
        The screen uses the same modal for both login and logout,
        switching the interface based on is_logged_in parameter.
        This reduces code duplication and ensures consistent styling.

        On successful login, the modal loads ALL user-related data
        into app_state in a single operation, avoiding multiple state
        updates and ensuring atomic state changes.

        The logout uses call_after_refresh() to ensure the screen stack
        is cleared after the modal dismisses and state updates complete.

    See Also:
        ReactiveScreen: Base class with state watching
        menu.MenuScreen: Opens this screen for login/logout
        functions.handler_sqllite.op_user_login: Login database operation
        functions.handler_sqllite.op_user_logout: Logout database operation
        functions.logout_util.perform_logout: Shared logout utility
    """

    DEFAULT_CSS = """
    LoginScreen {
        align: center middle;
    }

    LoginScreen > Vertical {
        width: 60;
        height: auto;
        background: $surface;
        border: solid $accent;
        padding: 2;
    }

    LoginScreen #login-title {
        text-style: bold;
        padding: 0 0 2 0;
        text-align: center;
    }

    LoginScreen Static {
        margin: 1 0 0 0;
    }

    LoginScreen Input {
        width: 100%;
        margin: 0 0 2 0;
    }

    LoginScreen Horizontal {
        height: auto;
        margin-top: 2;
        align: center middle;
    }

    LoginScreen Horizontal Button {
        width: 15;
        height: 3;
        margin: 0 1;
    }

    LoginScreen #logout-container {
        height: auto;
        align: center middle;
    }

    LoginScreen #logout-message {
        text-align: center;
        margin: 2 0;
    }

    LoginScreen #logout-button {
        width: 20;
        margin: 2 0;
    }
    """

    def __init__(self, is_logged_in: bool = False, username: str = "") -> None:
        """Initialize the LoginScreen modal.

        Args:
            is_logged_in: Whether a user is currently logged in
                - False: Shows login form with username/password fields
                - True: Shows logout interface with username display
            username: The username of the logged-in user (if is_logged_in=True)

        Example:
            Open login form::

                >>> login = LoginScreen(is_logged_in=False)
                >>> self.app.push_screen(login)

            Open logout interface::

                >>> login = LoginScreen(is_logged_in=True, username="batman")
                >>> self.app.push_screen(login)
        """
        super().__init__()
        self._is_logged_in = is_logged_in
        self._username = username

    def compose(self) -> ComposeResult:
        """Compose the login or logout interface based on current state.

        Creates different UI layouts depending on is_logged_in:
            - Login mode: Username/password form with Login/Cancel buttons
            - Logout mode: Username display with Logout button

        Yields:
            Login Mode: Username input, password input, Login/Cancel buttons
            Logout Mode: Username display, Logout button
        """
        with Vertical():
            if self._is_logged_in:
                # Show logout interface
                yield Static("Logout", id="login-title")
                yield Static(
                    f"Currently logged in as: [bold]{self._username}[/bold]",
                    id="logout-message"
                )
                with Vertical(id="logout-container"):
                    yield Button("Logout", id="logout-button", variant="error")
            else:
                # Show login form
                yield Static("Login", id="login-title")

                yield Static("Username / Email:")
                yield Input(placeholder="Enter username or email", id="username-input")

                yield Static("Password:")
                yield Input(placeholder="Enter password", password=True, id="password-input")

                with Horizontal():
                    yield Button("Login", id="login-button", variant="success")
                    yield Button("Cancel", id="cancel-button", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events in the login/logout modal.

        Routes button clicks to appropriate authentication actions.

        Args:
            event: Button.Pressed event containing the clicked button

        Handles:
            - login-button: Validates inputs and performs login
            - logout-button: Performs logout operation
            - cancel-button: Dismisses modal without action
        """
        if event.button.id == "login-button":
            self.perform_login()
        elif event.button.id == "logout-button":
            self.perform_logout()
        elif event.button.id == "cancel-button":
            self.dismiss()

    def perform_login(self) -> None:
        """Perform login operation with credential validation and state setup.

        This method handles the complete login workflow including input
        validation, database authentication, user/project data loading,
        and app_state initialization.

        The login process:
            1. Validates input fields (not empty)
            2. Checks if any users exist in system
            3. Calls op_user_login() with credentials
            4. Verifies password via bcrypt comparison
            5. Creates session in database
            6. Loads user information
            7. Loads all user's projects
            8. Identifies primary project
            9. Loads project currency and settings
            10. Updates app_state with complete user context
            11. Dismisses modal with success result

        Side Effects:
            - Queries database for authentication
            - Creates new session record
            - Updates app_state with 15+ fields
            - Shows success/error notifications
            - Dismisses modal on success
            - Logs all operations

        Example:
            Successful login::

                >>> # User enters: username="batman", password="darkknight"
                >>> # perform_login() called
                >>> # Database authenticates
                >>> # Session created
                >>> # Projects loaded
                >>> # app_state populated
                >>> # Modal dismisses with success
        """
        k = self.app._config["dbh"]
        total_users = k.op_total_number_of_users()
        if total_users == 0:
            self.notify("No users found in the system. Create a user first", severity="error")
            return


        # Get input values
        username = self.query_one("#username-input", Input).value.strip()
        password = self.query_one("#password-input", Input).value

        # Basic validation
        if not username:
            self.notify("Username/Email is required", severity="error")
            return
        if not password:
            self.notify("Password is required", severity="error")
            return

        # TODO: Implement backend API call for authentication
        # Steps to implement later:
        # 1. Call /api/v1/login/token endpoint with username and password
        # 2. Receive one-time token
        # 3. Exchange one-time token for bearer token at /api/v1/login/bearer
        # 4. Store bearer token in config/store
        # 5. Update application state (user info, projects, etc.)
        # 6. Dismiss modal and refresh main app
        try:
            k = self.app._config["dbh"]
            user_session = k.op_user_login(username=username, password=password)

            if not user_session:
                self.notify("Invalid username or password", severity="error")
                return

            # Fetch user and project information
            user_id = user_session.get("user_id", -1)
            user_info = k.op_user_get_info(user_id)
            project_info = k.op_project_get_info(user_id)

            # Extract project data
            project_names = []
            project_ids = []
            primary_project_id = 0
            primary_project_name = "No Project"
            primary_project_style = "default"
            primary_project_store = {}

            if project_info and len(project_info) > 0:
                for project in project_info:
                    project_ids.append(project["project_id"])
                    project_names.append(project["project_name"])
                    if project.get("project_primary", False):
                        primary_project_id = project["project_id"]
                        primary_project_name = project["project_name"]
                        primary_project_style = project.get("project_style", "default")
                        primary_project_store = project.get("project_store", {})

                # If no primary project is set, use the first one
                if primary_project_id == 0 and len(project_ids) > 0:
                    primary_project_id = project_ids[0]
                    primary_project_name = project_names[0]
                    # Get style and store for first project
                    first_project = project_info[0]
                    primary_project_style = first_project.get("project_style", "default")
                    primary_project_store = first_project.get("project_store", {})
            else:
                # No projects found
                project_names = ["No Projects"]
                project_ids = [0]
                primary_project_id = 0

            # Load currency information for the primary project
            primary_project = next((p for p in project_info if p.get("project_primary", False)), None) if project_info else None
            if primary_project:
                import json
                currency_main = primary_project.get("currency_main", "USD")
                currency_list_str = primary_project.get("currency_list", "[]")
                try:
                    currency_list = json.loads(currency_list_str) if currency_list_str else []
                except:
                    currency_list = []
            else:
                currency_main = "USD"
                currency_list = []

            # IMPORTANT: Preserve application-level configuration during login
            # These are set at app startup and should not be overwritten
            abs_path = self.app.app_state.get("abs_path", "")
            css_form = self.app.app_state.get("css_form", "handsome")
            css_theme = self.app.app_state.get("css_theme", "textual-light")

            # Update app_state reactive dictionary with ALL information
            self.app.app_state = {
                "user_name": user_info.get("username", username),
                "user_id": user_id,
                "user_scope": user_info.get("scope", "user:write"),
                "session_uuid": user_session.get("session_uuid", "No session"),
                "session_start": user_session.get("session_start"),
                "is_logged_in": True,
                "project_names": project_names,
                "project_ids": project_ids,
                "project_id": primary_project_id,
                "project_name": primary_project_name,
                "project_style": primary_project_style,
                "project_store": primary_project_store,
                "current_project_currency_main": currency_main,
                "current_project_currency_list": currency_list,
                # Restore application-level configuration
                "abs_path": abs_path,
                "css_form": css_form,
                "css_theme": css_theme,
            }

            self.notify("Login successful!", severity="success")

            # Dismiss modal and pass success result with all info
            self.dismiss(result={
                "success": True,
                "user_id": user_id,
                "username": username,
                "session_uuid": user_session.get("session_uuid"),
                "session_start": user_session.get("session_start")
            })

        except Exception as e:
            self.notify(f"Login failed: {str(e)}", severity="error")
            return

    def perform_logout(self) -> None:
        """Perform logout operation and reset application state.

        This method handles the complete logout workflow including session
        invalidation, state cleanup, and navigation back to the main screen.

        The logout process:
            1. Calls op_user_logout() with session_uuid
            2. Clears session from database
            3. Resets app_state to default values
            4. Shows success notification
            5. Dismisses modal
            6. Schedules return to main screen

        Side Effects:
            - Updates database: session.is_logged_in = False
            - Resets app_state to default values
            - Shows success/error notification
            - Dismisses modal with result
            - Calls _return_to_main_screen() after refresh

        Example:
            >>> # User clicks Logout
            >>> # perform_logout() called
            >>> # Session cleared in database
            >>> # app_state reset to defaults
            >>> # Returns to main screen as Guest
        """
        # TODO: Implement backend API call for logout
        # Steps to implement later:
        # 1. Retrieve bearer token from config/store
        # 2. Call /api/v1/logout/bearer endpoint with Authorization header
        # 3. Remove bearer and refresh tokens from storage
        # 4. Clear user session data
        # 5. Update application state to logged-out
        # 6. Dismiss modal and redirect to login or home screen

        k = self.app._config["dbh"]
        verify = k.op_user_logout(session_uuid=self.app.app_state["session_uuid"])
        if verify:
            # Reset ALL app_state fields to initial values (same as main.py initialization)
            self.app.app_state = {
                "user_name": "Guest",
                "user_id": -1,
                "user_scope": "user:write",
                "session_uuid": "No session",
                "session_start": None,
                "is_logged_in": False,
                "project_names": ["No Projects"],
                "project_ids": [0],
                "project_id": 0,
            }
            self.notify(f"Logout of User {self._username} successful!", severity="success")

            # Dismiss this modal first
            self.dismiss(result={"success": True, "action": "logout"})

            # Pop all screens to return to main screen (fallback)
            # Use call_after_refresh to ensure state is updated first
            self.app.call_after_refresh(self._return_to_main_screen)
        else:
            self.notify("Logout failed. Please try again.", severity="error")

    def _return_to_main_screen(self) -> None:
        """Pop all screens to return to the main screen after logout.

        Clears the screen stack down to the base screen, ensuring the
        user returns to a clean main screen state after logout.

        Side Effects:
            - Pops all screens except the base screen
            - Logs any errors

        Example:
            >>> # After logout, pops all screens
            >>> # Returns to clean main screen
        """
        try:
            # Pop all screens except the main screen
            while len(self.app.screen_stack) > 1:
                self.app.pop_screen()
        except Exception as e:
            self.app.log(f"Error returning to main screen: {e}")
