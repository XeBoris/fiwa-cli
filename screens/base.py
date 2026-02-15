"""Base screen components - Login/Logout functionality."""
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, Button
from textual.app import ComposeResult

from textual.screen import Screen

class ReactiveScreen(Screen):
    """Base screen that automatically watches app_state changes."""

    def on_mount(self) -> None:
        """Set up watchers when screen is mounted."""
        self.app.watch(self.app, "app_state", self._on_app_state_change)

    def _on_app_state_change(self, new_state: dict) -> None:
        """Called when app.app_state changes. Override in subclasses."""
        self.update_displays()

    def update_displays(self) -> None:
        """Override this method in subclasses to update specific widgets."""
        pass

class LoginScreen(ModalScreen):
    """Login/Logout screen - handles user authentication."""

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
        """Initialize the LoginScreen.

        Args:
            is_logged_in: Whether a user is currently logged in
            username: The username of the logged-in user (if applicable)
        """
        super().__init__()
        self._is_logged_in = is_logged_in
        self._username = username

    def compose(self) -> ComposeResult:
        """Create child widgets based on login status."""
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
        """Handle button presses."""
        if event.button.id == "login-button":
            self.perform_login()
        elif event.button.id == "logout-button":
            self.perform_logout()
        elif event.button.id == "cancel-button":
            self.dismiss()

    def perform_login(self) -> None:
        """Perform login operation with backend API.

        This function will:
        1. Validate input fields
        2. Send credentials to backend API
        3. Receive and store bearer token
        4. Update application state
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

            if project_info and len(project_info) > 0:
                for project in project_info:
                    project_ids.append(project["project_id"])
                    project_names.append(project["project_name"])
                    if project.get("project_primary", False):
                        primary_project_id = project["project_id"]

                # If no primary project is set, use the first one
                if primary_project_id == 0 and len(project_ids) > 0:
                    primary_project_id = project_ids[0]
            else:
                # No projects found
                project_names = ["No Projects"]
                project_ids = [0]
                primary_project_id = 0

            # Update app_state reactive dictionary with ALL information
            self.app.app_state = {
                "user_name": user_info.get("username", username),
                "user_id": user_id,
                "session_uuid": user_session.get("session_uuid", "No session"),
                "session_start": user_session.get("session_start"),
                "is_logged_in": True,
                "project_names": project_names,
                "project_ids": project_ids,
                "project_id": primary_project_id,
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
        """Perform logout operation with backend API.

        This function will:
        1. Send logout request to backend with bearer token
        2. Invalidate bearer and refresh tokens
        3. Clear stored credentials
        4. Update application state
        5. Return to main screen (fallback)
        """
        k = self.app._config["dbh"]
        verify = k.op_user_logout(session_uuid=self.app.app_state["session_uuid"])
        if verify:
            # Reset ALL app_state fields to initial values (same as main.py initialization)
            self.app.app_state = {
                "user_name": "Guest",
                "user_id": -1,
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
        """Pop all screens to return to the main screen."""
        try:
            # Pop all screens except the main screen
            while len(self.app.screen_stack) > 1:
                self.app.pop_screen()
        except Exception as e:
            self.app.log(f"Error returning to main screen: {e}")

