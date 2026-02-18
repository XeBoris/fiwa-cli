"""Main application entry point for FiWa CLI."""
from typing import Any, Dict

from textual.app import App, ComposeResult, Binding
from textual.containers import Horizontal
from textual.widgets import Button, Footer, Static
from textual.reactive import reactive

from functions.loader import load_yaml_config
from functions.loader import setup_fiwa, get_abs_path
from components.header import FiwaHeader

import datetime

class MyApp(App):
    """A Textual app for FiWa financial tracking."""

    CSS_PATH = "main.css"
    BINDINGS = [
        Binding("ctrl+c", "quit_app", "Quit", show=False),
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    # r = self.app._config["dbh"].op_get_user_sessions()
    # ruser = r["user_info"]
    # rsession = r["session_info"]

    # Single reactive dictionary that will trigger UI updates when changed
    # This contains all shared state across the application
    app_state = reactive({
        "user_name": "Guest",
        "user_id": "user_id",
        "session_uuid": "No session",
        "session_start": None,
        "is_logged_in": False,
        "project_names": ["No Projects"],
        "project_ids": [0],
        "project_id": 0,  # Primary project ID
        "meta_info": {"today": datetime.datetime.today().isoformat(),
                      "focus_week": datetime.datetime.today().isocalendar()[1],
                      "focus_month": datetime.datetime.today().month,
                      },
    })

    def __init__(self, config: Dict[str, Any] | None = None, mode: str = "terminal") -> None:
        super().__init__()
        self._config = config or {}
        self._mode = mode  # "terminal" or "web"
        self.count = 0

        # Note: app_state is initialized at class level as reactive variable
        # We can update it after initialization if needed from database
        u = self.app._config["dbh"].op_get_user_sessions()

        # let's update the app_state with actual session info from the database on startup
        self.app_state["user_name"] = u.get("user_info", {}).get("username", "Guest")
        self.app_state["user_id"] = u.get("user_info", {}).get("user_id", -1)
        self.app_state["session_uuid"] = u.get("session_info", {}).get("session_uuid", "No session")
        self.app_state["session_start"] = u.get("session_info", {}).get("session_start", None)
        self.app_state["is_logged_in"] = u.get("session_info", {}).get("is_logged_in", False)




        # Process project information
        project_info = u.get("project_info", [])
        if project_info:
            # Extract project IDs and names in the same order
            project_ids = [p["project_id"] for p in project_info]
            project_names = [p["project_name"] for p in project_info]

            # Find the primary project ID
            primary_project = next((p for p in project_info if p.get("project_primary", False)), None)
            primary_project_id = primary_project["project_id"] if primary_project else (project_ids[0] if project_ids else 0)

            self.app_state["project_ids"] = project_ids
            self.app_state["project_names"] = project_names
            self.app_state["project_id"] = primary_project_id
        else:
            self.app_state["project_ids"] = [0]
            self.app_state["project_names"] = ["No Projects"]
            self.app_state["project_id"] = 0

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield FiwaHeader(
            user=self.app_state["user_name"],
            projects=self.app_state["project_names"],
            project_id=self.app_state["project_id"],
            project_ids=self.app_state["project_ids"]
        )
        c_user = self.app_state.get("user_name", "Guest")
        yield Static(f"Welcome {c_user} to the FiWa CLI Application!", id="main_body")
        yield Static()
        yield Static(str(self.app_state), id="app_state_display_1")
        yield Static(str(self.app.app_state), id="app_state_display_2")

        yield Static(id="user_session_info")  # Will be updated reactively
        yield Footer()

    def watch_app_state(self, new_state: dict) -> None:
        """Called automatically when app_state changes."""
        if self.is_mounted:
            self.update_session_display()
            self.update_main_body()

    def update_main_body(self) -> None:
        """Update the main body widgets with current app_state."""
        try:
            # Update the welcome message
            main_body = self.query_one("#main_body", Static)
            c_user = self.app_state.get("user_name", "Guest")
            main_body.update(f"Welcome {c_user} to the FiWa CLI Application!")
        except Exception:
            pass

        try:
            # Update app_state display widgets
            app_state_display_1 = self.query_one("#app_state_display_1", Static)
            app_state_display_1.update(str(self.app_state))
        except Exception:
            pass

        try:
            app_state_display_2 = self.query_one("#app_state_display_2", Static)
            app_state_display_2.update(str(self.app.app_state))
        except Exception:
            pass

    def update_session_display(self) -> None:
        """Update the session display with current reactive values."""
        try:
            session_widget = self.query_one("#user_session_info", Static)
            session_widget.update(f"{self.app_state['user_name']} - {self.app_state['session_uuid']}")
        except Exception:
            # Widget might not be ready yet
            pass

            # Update header if needed
        try:
            header = self.query_one(FiwaHeader)
            header.user = self.app_state["user_name"]
            header.projects = self.app_state["project_names"]
            header.project_id = self.app_state["project_id"]
            header.project_ids = self.app_state["project_ids"]
        except Exception as e:
            self.log(f"Header widget not ready for update {e}")
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Event handler called when a button is pressed."""
        # from screens.base import LoginScreen


        # elif event.button.id == "login_button":
        #     # Check if already logged in
        #     is_logged_in = self.app_state.get("user_id", -1) > 0
        #     username = self.app_state.get("user_name", "")
        #     self.push_screen(LoginScreen(is_logged_in=is_logged_in, username=username), handle_login_result)
        pass

    def action_quit_app(self) -> None:
        """An action to quit the app."""
        self.exit(0)

    def action_toggle_dark(self) -> None:
        """An action to toggle between dark and light themes."""
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"






if __name__ == "__main__":

    abs_path = get_abs_path()
    print(abs_path)
    config_path = "./config.yml"  # for testing purposes
    config = load_yaml_config(config_path)

    config = setup_fiwa(abs_path=abs_path,
                        config=config)  # Initialize FiWa with the loaded config


    app = MyApp(config=config)
    app.run()
