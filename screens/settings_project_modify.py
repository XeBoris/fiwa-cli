# settings_project_modify.py
from textual.widgets import Static, Button, Input, TextArea
from textual.containers import Vertical, Grid, Horizontal
from textual.app import ComposeResult
from textual.message import Message
from datetime import datetime
import hashlib
import json

class ModifyProjectForm(Vertical):
    """Widget for modifying the currently loaded project."""

    DEFAULT_CSS = """
    ModifyProjectForm {
        width: 100%;
        height: 100%;
        overflow-y: auto;
    }

    ModifyProjectForm .form-title {
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
        background: $accent;
        color: $text;
    }

    ModifyProjectForm .current-project-header {
        text-style: bold;
        text-align: center;
        padding: 1 0;
        background: $primary;
        color: $text;
        margin: 0 0 2 0;
    }

    ModifyProjectForm .form-label {
        padding: 1 0 0 0;
        text-style: bold;
    }

    ModifyProjectForm Input {
        margin: 0 0 1 0;
    }

    ModifyProjectForm TextArea {
        height: 5;
        margin: 0 0 1 0;
    }

    ModifyProjectForm Button {
        min-width: 20;
        height: 3;
        margin: 0 1;
    }
    
    ModifyProjectForm #project-buttons {
        height: 5;
        margin-top: 2;
        width: 100%;
        align: center middle;
        layout: horizontal;
    }
    
    ModifyProjectForm #project-update-button {
        background: blue;
        color: white;
        width: 20;
        height: 3;
    }

    ModifyProjectForm #project-update-button:hover {
        background: darkblue;
    }
    
    ModifyProjectForm #project-cancel-button {
        background: red;
        color: white;
        width: 20;
        height: 3;
    }

    ModifyProjectForm #project-cancel-button:hover {
        background: darkred;
    }
    """

    class ProjectModified(Message):
        """Message sent when project is modified."""
        def __init__(self, project_data: dict) -> None:
            self.project_data = project_data
            super().__init__()

    def compose(self) -> ComposeResult:
        # Get current project information from app_state
        project_id = self.app.app_state.get("project_id", 0)
        user_id = self.app.app_state.get("user_id", -1)

        # Get project details from database
        project_info = None
        if project_id and user_id > 0:
            dbh = self.app._config["dbh"]
            all_projects = dbh.op_project_get_info(user_id)
            project_info = next((p for p in all_projects if p["project_id"] == project_id), None)

        yield Static("Modify Project", classes="form-title")

        # Show current project name as header
        if project_info:
            current_name = project_info.get("project_name", "Unknown Project")
            yield Static(f"Currently Editing: {current_name}", classes="current-project-header")
        else:
            yield Static("No Project Loaded", classes="current-project-header")

        # Pre-fill form fields with current values
        current_description = ""
        current_currency_main = ""
        current_currency_list = ""

        if project_info:
            current_description = project_info.get("description", "")
            current_currency_main = project_info.get("currency_main", "")

            # Parse currency_list (stored as JSON string)
            currency_list_raw = project_info.get("currency_list", "[]")
            try:
                if isinstance(currency_list_raw, str):
                    currency_list_parsed = json.loads(currency_list_raw)
                else:
                    currency_list_parsed = currency_list_raw
                current_currency_list = ", ".join(currency_list_parsed) if currency_list_parsed else ""
            except:
                current_currency_list = ""

        yield Static("Project Name *", classes="form-label")
        yield Input(
            placeholder="Enter project name",
            id="project-name",
            value=project_info.get("project_name", "") if project_info else ""
        )

        yield Static("Description", classes="form-label")
        yield TextArea(
            id="project-description",
            text=current_description
        )

        yield Static("Main Currency (3-letter code) *", classes="form-label")
        yield Input(
            placeholder="e.g., USD, EUR, GBP",
            id="currency-main",
            max_length=3,
            value=current_currency_main
        )

        yield Static("Additional Currencies (comma-separated)", classes="form-label")
        yield Input(
            placeholder="e.g., USD,EUR,JPY",
            id="currency-list",
            value=current_currency_list
        )

        with Horizontal(id="project-buttons"):
            yield Button("Update", id="project-update-button")
            yield Button("Cancel", id="project-cancel-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "project-cancel-button":
            self.app.notify("Project modification cancelled", severity="info")
        elif event.button.id == "project-update-button":
            self.update_project()

    def update_project(self) -> None:
        """Validate and update the project."""
        project_id = self.app.app_state.get("project_id", 0)
        user_id = self.app.app_state.get("user_id", -1)

        if not project_id or user_id <= 0:
            self.app.notify("No project loaded or user not logged in", severity="error")
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

        project_data = {
            "project_id": project_id,
            "name": name,
            "description": description if description else None,
            "currency_main": currency_main,
            "currency_list": currency_list,
        }

        # Update in database
        try:
            dbh = self.app._config["dbh"]
            dbh.op_project_update(project_data)
            self.app.notify("Project updated successfully!", severity="information")
            self.post_message(self.ProjectModified(project_data))
        except ValueError as e:
            self.app.notify(f"Update failed: {str(e)}", severity="error")
        except Exception as e:
            self.app.notify(f"Error updating project: {str(e)}", severity="error")
