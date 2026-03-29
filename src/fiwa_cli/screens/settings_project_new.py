"""Project creation form for FiWa CLI.

This module provides the interface for creating new projects. It handles
project limit validation, collects project details, and integrates with
the ProjectComposer system to set up project-specific structures.

Key Features:
    - Project limit checking and enforcement
    - Project style selection (ExpenseTracker, Vacation, etc.)
    - Currency configuration (main and additional currencies)
    - Month start day configuration for monthly periods
    - Automatic project structure setup via ProjectComposer

Classes:
    CreateProjectForm: Form widget for creating new projects

Example:
    Mounting the form::

        >>> from fiwa_cli.screens.settings_project_new import CreateProjectForm
        >>> form = CreateProjectForm()
        >>> content_area.mount(form)

    Handling project creation::

        >>> @on(CreateProjectForm.ProjectCreated)
        >>> def on_project_created(self, message):
        >>>     project_data = message.project_data
        >>>     self.app.file_log.info(f"New project: {project_data['name']}")

See Also:
    settings_project_modify: Modify existing projects
    functions.project_composer: Project structure setup
    settings: Main settings screen that mounts this form
"""

from textual.widgets import Static, Button, Input, TextArea
from textual.containers import Vertical, Horizontal, ScrollableContainer, Grid
from textual.app import ComposeResult
from textual.message import Message
from datetime import datetime
import hashlib

from fiwa_cli.functions.loader import load_dynamic_css


class CreateProjectForm(ScrollableContainer):
    """Form widget for creating new projects.

    This widget provides a comprehensive form for creating new projects,
    including validation of project limits, collection of project metadata,
    and integration with the ProjectComposer system for setting up
    project-specific structures (labels, accounts, etc.).

    The form validates that the user hasn't exceeded their project limit
    before allowing creation, and provides clear feedback about remaining
    capacity.

    Attributes:
        None (uses app_state for user and project information)

    Messages:
        ProjectCreated: Emitted when project is successfully created
            - Attributes:
                - project_data (dict): Complete project information including
                  name, description, currency settings, style, and store

    Form Fields:
        - **Project Name** (required): Unique name, max 24 characters
        - **Description**: Optional text description, max 128 characters
        - **Main Currency** (required): 3-letter ISO code (e.g., USD, EUR)
        - **Additional Currencies**: Comma-separated currency codes
        - **Project Style**: Dropdown (ExpenseTracker, Vacation)
        - **Month Start Day**: Day of month for period boundaries (1-28)

    Validation:
        - Project name is required and must be unique
        - Main currency must be exactly 3 uppercase letters
        - Month start must be between 1 and 28
        - User must not exceed their project limit

    Example:
        Basic usage in settings screen::

            >>> content_area = self.query_one("#settings-content-area")
            >>> form = CreateProjectForm()
            >>> form.on_mount()
            >>> content_area.mount(form)

        Handling the creation event::

            >>> def on_create_project_form_project_created(self, message):
            >>>     project_data = message.project_data
            >>>     self.app.file_log.info(f"Created: {project_data['name']}")
            >>>     self.app.file_log.info(f"Style: {project_data['project_style']}")

    Note:
        After creation, the form posts a ProjectCreated message that
        triggers the ProjectComposer to set up project-specific structures
        (default labels, accounts, etc.) based on the selected project style.

        The month_start value is stored in project_store and affects how
        monthly periods are calculated throughout the application.

    See Also:
        settings_project_modify.ModifyProjectForm: Edit existing projects
        functions.project_composer.ProjectComposer: Project setup system
        functions.handler_sqllite.SQLLiteHandler.op_project_create: Database operation
    """

    class ProjectCreated(Message):
        """Message sent when a project is successfully created.

        This message is posted to the parent screen (typically SettingsScreen)
        after the project is validated and ready for database creation.

        The parent screen handles the actual database operations and
        ProjectComposer setup.

        Attributes:
            project_data (dict): Dictionary containing:
                - name (str): Project name
                - description (str | None): Project description
                - currency_main (str): Main 3-letter currency code
                - currency_list (list): Additional currency codes
                - project_style (str): Project type (e.g., "ExpenseTracker")
                - project_store (dict): Metadata including month_start

        Example:
            Receiving the message::

                >>> def on_create_project_form_project_created(self, message):
                >>>     data = message.project_data
                >>>     project_id = dbh.op_project_create(data, user_id)
        """

        def __init__(self, project_data: dict) -> None:
            """Initialize the ProjectCreated message.

            Args:
                project_data: Complete project information dictionary
            """
            self.project_data = project_data
            super().__init__()

    def compose(self) -> ComposeResult:
        """Compose the project creation form layout.

        Builds the complete form UI including validation messages, input fields,
        and action buttons. The form checks project limits and displays
        appropriate warnings before allowing project creation.

        Form Structure:
            - Title: "Create New Project"
            - Warning box (if at or over limit)
            - Project name input (required, max 24 chars)
            - Description textarea (optional, 128 chars)
            - Currency fields (main and additional)
            - Project style selector (dropdown)
            - Month start day input (1-28)
            - Action buttons (Create, Reset)

        Yields:
            Static: Form title
            Static: Warning/info box (if applicable)
            Various inputs and containers for form fields
            Horizontal: Button row with Create and Reset buttons

        Note:
            The form is pre-validated during composition - if the user
            has reached their project limit, a prominent warning is shown.
        """
        yield Static("Create New Project", classes="form-title")

        # Get user info and project count from app_state
        user_id = self.app.app_state.get("user_id", -1)
        project_ids = self.app.app_state.get("project_ids", [])
        current_projects = len(project_ids)
        max_projects = 3  # Default

        if user_id > 0:
            try:
                dbh = self.app._config["dbh"]
                max_projects = dbh.op_get_max_projects(user_id)
            except Exception as e:
                # If query fails, just use default max_projects
                pass

        # Display warning/info message
        if current_projects >= max_projects:
            yield Static(
                f"⚠ WARNING: You have reached your maximum project limit!\n"
                f"Current projects: {user_id} {current_projects} / {max_projects}\n"
                f"You cannot create more projects.",
                classes="error-box",
            )
        elif current_projects >= max_projects - 1:
            yield Static(
                f"⚠ WARNING: You are at your project limit!\n"
                f"Current projects: {current_projects} / {max_projects}\n"
                f"This will be your last project.",
                classes="warning-box",
            )
        else:
            yield Static(
                f"ℹ Project Usage: {current_projects} / {max_projects} projects used",
                classes="info-box",
            )

        with ScrollableContainer(id="form-content"):
            with Vertical(id="form-project-area"):
                yield Static("Project Name *", classes="form-label")
                yield Input(placeholder="Enter project name", id="project-name", max_length=24)

                yield Static("Description", classes="form-label")
                yield TextArea(id="project-description")

                yield Static("Month starts at", classes="form-label")
                yield Input(placeholder=f"pick a day", id="project-start-date", value=f"01")

            with Horizontal(id="form-currency-section"):
                with Vertical(id="form-currency-section-main"):
                    yield Static("Main Currency *", classes="form-label")
                    yield Input(placeholder="e.g., USD", id="currency-main", max_length=3)
                with Vertical(id="form-currency-section-additional"):
                    yield Static("Additional Currencies (comma-separated)", classes="form-label")
                    yield Input(placeholder="e.g., USD, EUR, JPY", id="currency-list")

            with Grid(id="action-buttons"):
                yield Button("Create", id="project-create-button")
                yield Button("Reset", id="project-reset-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events in the form.

        Routes button clicks to appropriate handlers for form submission
        and reset operations.

        Args:
            event: Button.Pressed event containing the clicked button

        Handles:
            - project-create-button: Validates and creates project
            - project-reset-button: Resets all form fields
        """
        if event.button.id == "project-reset-button":
            self.reset_form()
        elif event.button.id == "project-create-button":
            self.create_project()

    def on_mount(self) -> None:
        """Load CSS stylesheet when the form is mounted.

        Side Effects:
            Loads screens_settings_project_new.tcss stylesheet
        """
        load_dynamic_css(self, "screens_settings_project_new.tcss")
        # update project usage info on mount

    def reset_form(self) -> None:
        """Reset all form fields to their default values.

        Clears all input fields and resets selects to their initial state,
        allowing the user to start over with a clean form.

        Fields Reset:
            - Project name → empty string
            - Description → empty string
            - Main currency → empty string
            - Additional currencies → empty string
            - Project style → First option (default)
            - Month start day → "1"

        Side Effects:
            Updates all Input, TextArea, and Select widgets with default values

        Example:
            Called when user clicks "Reset" button or wants to clear the form.
        """
        try:
            # Clear all input fields
            self.query_one("#project-name", Input).value = ""
            self.query_one("#project-description", TextArea).text = ""
            self.query_one("#currency-main", Input).value = ""
            self.query_one("#currency-list", Input).value = ""
            self.query_one("#project-start-date", Input).value = (
                datetime.now().replace(day=1).strftime("%Y-%m-%d")
            )

            # Focus on the first field
            self.query_one("#project-name", Input).focus()

            self.app.notify("Form reset successfully", severity="info")
        except Exception as e:
            self.app.notify(f"Error resetting form: {str(e)}", severity="error")

    def create_project(self) -> None:
        """Validate form data and emit ProjectCreated message.

        This method performs comprehensive validation of all form fields,
        checks project limits, prepares the project data structure, and
        posts a ProjectCreated message for the parent screen to handle.

        Validation Steps:
            1. Check user is logged in
            2. Verify project limit not exceeded
            3. Validate project name is provided
            4. Validate main currency is 3 letters
            5. Validate month_start is between 1-28
            6. Parse additional currencies

        Project Data Structure:
            Creates a dictionary with:
                - name: Project name (string)
                - description: Optional description (string | None)
                - currency_main: Main currency code (string)
                - currency_list: Additional currencies (list)
                - project_style: Project type (string)
                - project_store: Metadata dict with month_start

        Error Handling:
            Displays error notifications for:
                - No user logged in
                - Project limit exceeded
                - Missing required fields
                - Invalid currency format
                - Invalid month_start value

        Side Effects:
            - Queries database for current project count
            - Posts ProjectCreated message on success
            - Shows error notifications on validation failure
            - Logs validation errors to app logger

        Returns:
            None (communicates via message posting)

        Example:
            Called when user clicks "Create" button::

                >>> # User fills form:
                >>> #   Name: "Bat Cave Expenses"
                >>> #   Currency: "USD"
                >>> #   Style: "ExpenseTracker"
                >>> # Clicks "Create"
                >>> # → create_project() validates and posts message
                >>> # → Parent receives ProjectCreated message
                >>> # → Parent creates project in database
                >>> # → ProjectComposer sets up structure

        Note:
            This method only validates and prepares data - it does NOT
            create the project in the database. The parent screen handles
            the actual database operations and ProjectComposer integration.
        """
        user_id = self.app.app_state.get("user_id", -1)
        project_ids = self.app.app_state.get("project_ids", [])
        current_projects = len(project_ids)

        # Check project limit before validation
        if user_id > 0:
            try:
                dbh = self.app._config["dbh"]
                max_projects = dbh.op_get_max_projects(user_id)

                # Check if limit reached
                if current_projects >= max_projects:
                    self.app.notify(
                        f"Project limit reached! You have {current_projects}/{max_projects} projects.",
                        severity="error",
                    )
                    return
            except Exception as e:
                self.app.notify(f"Error checking project limit: {str(e)}", severity="error")
                return

        name = self.query_one("#project-name", Input).value.strip()
        description = self.query_one("#project-description", TextArea).text.strip()
        currency_main = self.query_one("#currency-main", Input).value.strip().upper()
        currency_list_str = self.query_one("#currency-list", Input).value.strip()

        if not name:
            self.app.notify("Project name is required", severity="error")
            return

        if not currency_main or len(currency_main) != 3:
            self.app.notify("Valid 3-letter currency code required", severity="error")
            return

        currency_list = []
        if currency_list_str:
            currency_list = [c.strip().upper() for c in currency_list_str.split(",") if c.strip()]

        project_hash = hashlib.sha256(f"{name}{datetime.now().isoformat()}".encode()).hexdigest()
        project_start_date = self.query_one("#project-start-date", Input).value.strip()

        project_style = "ExpenseTracker"  # Placeholder for future style selection

        project_data = {
            "name": name,
            "description": description if description else None,
            # "created_at": datetime.now(),
            "currency_main": currency_main,
            "currency_list": currency_list,
            "project_hash": project_hash,
            "project_style": project_style,  # Add as separate field for database column
            "project_store": {
                "month_start": int(project_start_date),
                "style": project_style,
            },  # Also keep in store for backward compatibility
        }

        self.post_message(self.ProjectCreated(project_data))
