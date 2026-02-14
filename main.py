"""Main application entry point for FiWa CLI."""
from typing import Any, Dict

from textual.app import App, ComposeResult, Binding
from textual.containers import Horizontal
from textual.widgets import Button, Footer, Static
from textual.reactive import reactive

from functions.loader import load_yaml_config
from functions.loader import setup_fiwa, get_abs_path
from components.header import FiwaHeader

import logging

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
        yield Static("Welcome to the FiWa CLI Application!", id="main_body")
        with Horizontal():
            yield Button("Open Calendar", id="calendar_button")
            #yield Button("Login", id="login_button", variant="success")
        yield Static(str(self.app._config.keys()))
        yield Static(str(self.app._config["dbh"].op_get_current_user()))
        yield Static(str(self.count))
        yield Static(id="user_session_info")  # Will be updated reactively
        yield Footer()

    def watch_app_state(self, new_state: dict) -> None:
        """Called automatically when app_state changes."""
        if self.is_mounted:
            self.update_session_display()

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
        from screens.calendar_screen import CalendarScreen
        from screens.base import LoginScreen

        def check_date(selected_date):
            if selected_date:
                self.notify(f"You selected {selected_date.strftime('%Y-%m-%d')}")

        # def handle_login_result(result):
        #     """Handle the result from LoginScreen and update app_state."""
        #     if result and result.get("success"):
        #         if result.get("action") == "logout":
        #             # Handle logout - update app_state dictionary
        #             self.app_state = {
        #                 **self.app_state,
        #                 "user_name": "Guest",
        #                 "user_id": -1,
        #                 "session_uuid": "No session",
        #                 "session_start": None
        #             }
        #             self.notify("You have been logged out", severity="information")
        #         else:
        #             # Handle login - update app_state dictionary
        #             self.app_state = {
        #                 **self.app_state,
        #                 "user_name": result.get("username", "Guest"),
        #                 "user_id": result.get("user_id", -1),
        #                 "session_uuid": result.get("session_uuid", "No session"),
        #                 "session_start": result.get("session_start")
        #             }
        #             self.notify(f"Welcome back, {result.get('username')}!", severity="success")

        if event.button.id == "calendar_button":
            self.push_screen(CalendarScreen(), check_date)

        # elif event.button.id == "login_button":
        #     # Check if already logged in
        #     is_logged_in = self.app_state.get("user_id", -1) > 0
        #     username = self.app_state.get("user_name", "")
        #     self.push_screen(LoginScreen(is_logged_in=is_logged_in, username=username), handle_login_result)

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
