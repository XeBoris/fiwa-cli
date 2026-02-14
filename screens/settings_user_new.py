"""User creation form widget."""
from textual.containers import Vertical, Horizontal, Grid
from textual.widgets import Static, Input, Button
from textual.widget import Widget
from textual.app import ComposeResult
from textual.message import Message
from datetime import date


class CreateUserForm(Widget):
    """Form for creating a new user."""

    class UserCreated(Message):
        """Message posted when a user is successfully created."""

        def __init__(self, user_data: dict):
            self.user_data = user_data
            super().__init__()

    DEFAULT_CSS = """
    CreateUserForm {
        width: 100%;
        height: auto;
    }

    CreateUserForm Static {
        margin: 1 0;
    }

    CreateUserForm Input {
        width: 100%;
        margin: 0 0 1 0;
    }

    CreateUserForm Horizontal {
        height: auto;
        margin-top: 1;
    }

    CreateUserForm Horizontal Button {
        width: 1fr;
        height: 3;
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("[bold]Create New User[/bold]", id="form-title")

        yield Static("First Name:")
        yield Input(placeholder="Enter first name", id="first-name-input")

        yield Static("Last Name:")
        yield Input(placeholder="Enter last name", id="last-name-input")

        yield Static("Username:")
        yield Input(placeholder="Enter username", id="username-input")

        yield Static("Email:")
        yield Input(placeholder="Enter email address", id="email-input")

        yield Static("Birthday (YYYY-MM-DD, optional):")
        yield Input(placeholder="YYYY-MM-DD", id="birthday-input")

        yield Static("Password:")
        yield Input(placeholder="Enter password", password=True, id="password-input")

        yield Static("Max Projects (default: 3):")
        yield Input(placeholder="3", id="max-projects-input")

        with Horizontal():
            yield Button("Create", id="user-create-button", variant="success")
            yield Button("Cancel", id="user-cancel-button", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "user-create-button":
            self.create_user()
        elif event.button.id == "user-cancel-button":
            self.cancel()

    def create_user(self) -> None:
        """Validate and create user."""
        # Get input values
        first_name = self.query_one("#first-name-input", Input).value.strip()
        last_name = self.query_one("#last-name-input", Input).value.strip()
        username = self.query_one("#username-input", Input).value.strip()
        email = self.query_one("#email-input", Input).value.strip()
        birthday = self.query_one("#birthday-input", Input).value.strip()
        password = self.query_one("#password-input", Input).value
        max_projects = self.query_one("#max-projects-input", Input).value.strip()

        # Validate required fields
        if not first_name:
            self.notify("First name is required", severity="error")
            return
        if not last_name:
            self.notify("Last name is required", severity="error")
            return
        if not username:
            self.notify("Username is required", severity="error")
            return
        if not email:
            self.notify("Email is required", severity="error")
            return
        if not password:
            self.notify("Password is required", severity="error")
            return

        # Validate max_projects
        try:
            max_projects_int = int(max_projects) if max_projects else 3
        except ValueError:
            self.notify("Max projects must be a number", severity="error")
            return

        # Create user data dictionary
        user_data = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "email": email,
            "birthday": birthday if birthday else None,
            "password": password,  # TODO: Hash this before saving
            "max_projects": max_projects_int
        }

        # use the backend API to create the user:
        k = self.app._config["dbh"]
        try:
            user_id = k.op_user_create(user_data)
            if user_id is None:
                self.notify("Failed to create user. Please try again.", severity="error")
                return
            user_data["user_id"] = user_id
        except Exception as e:
            self.notify(f"Error creating user: {str(e)}", severity="error")
            return

        # Post message to parent
        self.post_message(self.UserCreated(user_data))

    def cancel(self) -> None:
        """Cancel user creation."""
        self.notify("User creation cancelled", severity="information")
        # Clear all inputs
        for input_widget in self.query(Input):
            input_widget.value = ""
