# settings_project_new.py
from textual.widgets import Static, Button, Input, TextArea
from textual.containers import Vertical, Horizontal, ScrollableContainer, Grid
from textual.app import ComposeResult
from textual.message import Message
from datetime import datetime
import hashlib

class CreateProjectForm(ScrollableContainer):
    """Widget for creating a new project."""

    DEFAULT_CSS = """
    CreateProjectForm {
        width: 100%;
        height: 100%;
    }

    CreateProjectForm .form-title {
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
        background: $accent;
        color: $text;
    }

    CreateProjectForm .form-label {
        padding: 1 0 0 0;
        text-style: bold;
    }

    CreateProjectForm Input {
        margin: 0 0 1 0;
        width: 100%;
    }

    CreateProjectForm TextArea {
        height: 5;
        margin: 0 0 1 0;
    }

    CreateProjectForm Button {
        min-width: 20;
        height: 3;
        margin: 0 1;
    }
       
    CreateProjectForm #action-buttons {
        grid-size: 2 1;
        grid-columns: 1fr 1fr;
        grid-gutter: 1;
        height: 10;
        margin-top: 0;
        width: 100%;
    }
    
    CreateProjectForm #project-create-button {
        background: green;
        color: white;
        width: 20;
        height: 3;
        margin: 0 1;
    }

    CreateProjectForm #project-create-button:hover {
        background: darkgreen;
    }

    CreateProjectForm #project-cancel-button {
        background: red;
        color: white;
        width: 20;
        height: 3;
        margin: 0 1;
    }

    CreateProjectForm #project-cancel-button:hover {
        background: darkred;
    }
    
    CreateProjectForm .warning-box {
        background: $warning;
        color: $text;
        padding: 1;
        margin: 0 0 2 0;
        border: solid $error;
    }
    
    CreateProjectForm .error-box {
        background: $error;
        color: $text;
        padding: 1;
        margin: 0 0 2 0;
        border: solid $error;
    }
    
    CreateProjectForm .info-box {
        background: $panel;
        color: $text;
        padding: 1;
        margin: 0 0 2 0;
        border: solid $accent;
    }
    """




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

        yield Static("Project Name *", classes="form-label")
        yield Input(placeholder="Enter project name", id="project-name", max_length=24)

        yield Static("Description", classes="form-label")
        yield TextArea(id="project-description")

        yield Static("Main Currency (3-letter code) *", classes="form-label")
        yield Input(placeholder="e.g., USD, EUR, GBP", id="currency-main", max_length=3)

        yield Static("Additional Currencies (comma-separated)", classes="form-label")
        yield Input(placeholder="e.g., USD,EUR,JPY", id="currency-list")

        with Grid(id="action-buttons"):
            yield Button("Create", id="project-create-button")
            yield Button("Cancel", id="project-cancel-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "project-cancel-button":
            self.app.notify("Project creation cancelled", severity="info")
        elif event.button.id == "project-create-button":
            self.create_project()

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

        project_data = {
            "name": name,
            "description": description if description else None,
            "created_at": datetime.now(),
            "currency_main": currency_main,
            "currency_list": currency_list,
            "project_hash": project_hash
        }

        self.post_message(self.ProjectCreated(project_data))


# from textual.screen import ModalScreen
# from textual.containers import Vertical, Grid
# from textual.widgets import Static, Button, Input, TextArea
# from textual.app import ComposeResult
# from datetime import datetime
# import hashlib
# import uuid
#
#
# class CreateProjectModal(ModalScreen):
#     """Modal screen for creating a new project."""
#
#     DEFAULT_CSS = """
#     CreateProjectModal {
#         align: center middle;
#     }
#
#     CreateProjectModal > Vertical {
#         width: 60;
#         height: auto;
#         background: $surface;
#         border: solid $accent;
#         padding: 2;
#     }
#
#     CreateProjectModal #modal-title {
#         text-style: bold;
#         padding: 0 0 1 0;
#         text-align: center;
#     }
#
#     CreateProjectModal .form-label {
#         padding: 1 0 0 0;
#         text-style: bold;
#     }
#
#     CreateProjectModal Input {
#         margin: 0 0 1 0;
#     }
#
#     CreateProjectModal TextArea {
#         height: 5;
#         margin: 0 0 1 0;
#     }
#
#     CreateProjectModal Grid {
#         grid-size: 2;
#         grid-gutter: 1;
#         margin-top: 1;
#         background: green;
#         padding: 1;
#     }
#
#     CreateProjectModal Button {
#         width: 50%;
#         background: darkgreen;
#     }
#     """
#
#     def compose(self) -> ComposeResult:
#         with Vertical():
#             yield Static("Create New Project", id="modal-title")
#
#             yield Static("Project Name *", classes="form-label")
#             yield Input(placeholder="Enter project name", id="project-name")
#
#             yield Static("Description", classes="form-label")
#             yield TextArea(id="project-description")
#
#             yield Static("Main Currency (3-letter code) *", classes="form-label")
#             yield Input(placeholder="e.g., USD, EUR, GBP", id="currency-main", max_length=3)
#
#             yield Static("Additional Currencies (comma-separated)", classes="form-label")
#             yield Input(placeholder="e.g., USD,EUR,JPY", id="currency-list")
#
#             with Grid():
#                 yield Button("Create", id="create-button", variant="success")
#                 yield Button("Cancel", id="cancel-button", variant="error")
#
#     def on_button_pressed(self, event: Button.Pressed) -> None:
#         if event.button.id == "cancel-button":
#             self.dismiss(None)
#         elif event.button.id == "create-button":
#             self.create_project()
#
#     def create_project(self) -> None:
#         """Validate and create the project."""
#         name = self.query_one("#project-name", Input).value.strip()
#         description = self.query_one("#project-description", TextArea).text.strip()
#         currency_main = self.query_one("#currency-main", Input).value.strip().upper()
#         currency_list_str = self.query_one("#currency-list", Input).value.strip()
#
#         # Validation
#         if not name:
#             self.notify("Project name is required", severity="error")
#             return
#
#         if not currency_main or len(currency_main) != 3:
#             self.notify("Valid 3-letter currency code required", severity="error")
#             return
#
#         # Parse currency list
#         currency_list = []
#         if currency_list_str:
#             currency_list = [c.strip().upper() for c in currency_list_str.split(",") if c.strip()]
#
#         # Generate project hash
#         project_hash = hashlib.sha256(f"{name}{datetime.now().isoformat()}".encode()).hexdigest()
#
#         # Prepare project data
#         project_data = {
#             "name": name,
#             "description": description if description else None,
#             "created_at": datetime.now(),
#             "currency_main": currency_main,
#             "currency_list": currency_list,
#             "project_hash": project_hash
#         }
#
#         # Dismiss with project data
#         self.dismiss(project_data)
