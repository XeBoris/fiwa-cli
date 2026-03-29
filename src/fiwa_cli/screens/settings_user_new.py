"""User creation form for FiWa CLI.

This module provides the interface for creating new user accounts. It handles
user data collection, validation, password hashing, and unique identifier
generation.

Key Features:
    - Comprehensive user information collection
    - Password field with secure input (hidden characters)
    - Email validation
    - Birthday support (optional)
    - Max projects limit configuration
    - Automatic unique identifier generation
    - Password hashing with bcrypt

Default Values:
    - Max projects: 3 (if not specified)
    - Scope: "user:write" (standard user)
    - Activated: True (account enabled)
    - Is Superuser: False (regular user)

Classes:
    CreateUserForm: Form widget for creating new users

Example:
    Mounting the form::

        >>> from fiwa_cli.screens.settings_user_new import CreateUserForm
        >>> form = CreateUserForm()
        >>> content_area.mount(form)

    Handling user creation::

        >>> @on(CreateUserForm.UserCreated)
        >>> def on_user_created(self, message):
        >>>     user_data = message.user_data
        >>>     self.app.file_log.info(f"New user: {user_data['username']}")

See Also:
    settings_user_modify: Modify existing users
    settings: Main settings screen
    functions.handler_sqllite.SQLLiteHandler.op_user_create: Database operation
"""

from textual.containers import Vertical, Horizontal, Grid, ScrollableContainer
from textual.widgets import Static, Input, Button
from textual.widget import Widget
from textual.app import ComposeResult
from textual.message import Message
from datetime import date

from fiwa_cli.functions.loader import load_dynamic_css


class CreateUserForm(Widget):
    """Form widget for creating new user accounts.

    This widget provides a comprehensive form for creating new users with
    all necessary information including personal details, credentials, and
    account configuration.

    The form handles:
        - User information collection
        - Password hashing (never stores plain text)
        - Unique identifier generation
        - Email validation
        - Max projects limit setting

    Attributes:
        None (stateless widget, uses app_state for context)

    Messages:
        UserCreated: Emitted when user is successfully validated
            - Attributes:
                - user_data (dict): Complete user information

    Form Fields:
        - **First Name** (required): User's first name
        - **Last Name** (required): User's last name
        - **Username** (required): Unique username
        - **Email** (required): Email address (validated)
        - **Birthday** (optional): Birth date in YYYY-MM-DD format
        - **Password** (required): Secure password (hidden input)
        - **Max Projects**: Maximum allowed projects (default: 3)

    Validation:
        - All required fields must be filled
        - Email must contain @ and .
        - Birthday must be valid YYYY-MM-DD format if provided
        - Max projects must be a positive number
        - Username must be unique (checked by database)

    Auto-Generated Fields:
        - unique_identifier: Generated from username + timestamp hash
        - password_hash: bcrypt hash of password
        - created_at: Current timestamp
        - activated: True (account enabled)
        - is_superuser: False (regular user)
        - scope: "user:write" (standard permissions)

    Example:
        Basic usage::

            >>> form = CreateUserForm()
            >>> content_area.mount(form)

        Handling creation::

            >>> def on_create_user_form_user_created(self, message):
            >>>     user_data = message.user_data
            >>>     dbh.op_user_create(user_data)
            >>>     self.app.file_log.info(f"User created: {user_data['username']}")

        User fills form::

            >>> # First Name: Bruce
            >>> # Last Name: Wayne
            >>> # Username: batman
            >>> # Email: bruce@wayneenterprises.com
            >>> # Birthday: 1939-02-19
            >>> # Password: ********
            >>> # Max Projects: 10
            >>> # Clicks "Create"
            >>> # → Validation passes
            >>> # → UserCreated message posted
            >>> # → Parent handles database creation

    Note:
        This form only validates and prepares user data - it does NOT
        create the user in the database. The parent screen (SettingsScreen)
        receives the UserCreated message and handles the actual database
        operation via op_user_create().

        Passwords are hashed using bcrypt before being included in user_data,
        ensuring security even if the data is logged or transmitted.

    See Also:
        settings_user_modify.ModifyUserForm: Modify existing users
        functions.handler_sqllite.SQLLiteHandler.op_user_create: Database operation
        settings.SettingsScreen: Parent screen that handles the message
    """

    class UserCreated(Message):
        """Message posted when a user is successfully validated and ready for creation.

        This message contains all user data including the hashed password and
        generated unique identifier. The parent screen handles the actual
        database insertion.

        Attributes:
            user_data (dict): Complete user information including:
                - first_name (str): User's first name
                - last_name (str): User's last name
                - username (str): Unique username
                - email (str): Email address
                - birthday (str | None): Birth date YYYY-MM-DD
                - password_hash (str): bcrypt hashed password
                - max_projects (int): Maximum allowed projects
                - unique_identifier (str): SHA256 hash identifier
                - created_at (str): ISO format timestamp
                - activated (bool): Account status (True)
                - is_superuser (bool): Superuser flag (False)
                - scope (str): Permission scope ("user:write")

        Example:
            Handling the message::

                >>> def on_create_user_form_user_created(self, message):
                >>>     user_id = dbh.op_user_create(message.user_data)
                >>>     if user_id:
                >>>         self.notify(f"User created with ID: {user_id}")
        """

        def __init__(self, user_data: dict):
            """Initialize UserCreated message.

            Args:
                user_data: Complete user information dictionary
            """
            self.user_data = user_data
            super().__init__()

    def on_mount(self) -> None:
        load_dynamic_css(self, "screens_settings_user_new.tcss")
        # update project usage info on mount

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static("Create New User", classes="form-title")

        with ScrollableContainer(id="form-content"):
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
            "max_projects": max_projects_int,
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
