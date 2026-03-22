# settings_project_new.py
from textual.widgets import Static, Button, Input, TextArea
from textual.containers import Vertical, Horizontal, ScrollableContainer, Grid
from textual.app import ComposeResult
from textual.message import Message
from datetime import datetime
import hashlib

from fiwa_cli.functions.loader import load_dynamic_css


class CreateProjectForm(ScrollableContainer):
    """Widget for creating a new project."""

    class ProjectCreated(Message):
        """Message sent when project is created."""
        def __init__(self, project_data: dict) -> None:
            self.project_data = project_data
            super().__init__()

    def compose(self) -> ComposeResult:
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
                classes="error-box"
            )
        elif current_projects >= max_projects - 1:
            yield Static(
                f"⚠ WARNING: You are at your project limit!\n"
                f"Current projects: {current_projects} / {max_projects}\n"
                f"This will be your last project.",
                classes="warning-box"
            )
        else:
            yield Static(
                f"ℹ Project Usage: {current_projects} / {max_projects} projects used",
                classes="info-box"
            )

        with ScrollableContainer(id="form-content"):
            with Vertical(id="form-project-area"):
                yield Static("Project Name *", classes="form-label")
                yield Input(placeholder="Enter project name", id="project-name", max_length=24)

                yield Static("Description", classes="form-label")
                yield TextArea(id="project-description")

                yield Static("Month starts at", classes="form-label")
                yield Input(
                    placeholder=f"pick a day",
                    id="project-start-date",
                    value=f"01"
                )

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
        if event.button.id == "project-reset-button":
            self.reset_form()
        elif event.button.id == "project-create-button":
            self.create_project()

    def on_mount(self) -> None:
        load_dynamic_css(self, "screens_settings_project_new.tcss")
        #update project usage info on mount

    def reset_form(self) -> None:
        """Reset all form fields to their initial empty state."""
        try:
            # Clear all input fields
            self.query_one("#project-name", Input).value = ""
            self.query_one("#project-description", TextArea).text = ""
            self.query_one("#currency-main", Input).value = ""
            self.query_one("#currency-list", Input).value = ""
            self.query_one("#project-start-date", Input).value = datetime.now().replace(day=1).strftime("%Y-%m-%d")

            # Focus on the first field
            self.query_one("#project-name", Input).focus()

            self.app.notify("Form reset successfully", severity="info")
        except Exception as e:
            self.app.notify(f"Error resetting form: {str(e)}", severity="error")

    def create_project(self) -> None:
        """Validate and create the project."""
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
                        severity="error"
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
            #"created_at": datetime.now(),
            "currency_main": currency_main,
            "currency_list": currency_list,
            "project_hash": project_hash,
            "project_style": project_style,  # Add as separate field for database column
            "project_store": {"month_start": int(project_start_date),
                              "style": project_style}  # Also keep in store for backward compatibility

        }

        self.post_message(self.ProjectCreated(project_data))
