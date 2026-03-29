"""Main application entry point for FiWa CLI."""
from typing import Any, Dict
import os
from pathlib import Path

from textual.app import App, ComposeResult, Binding
from textual.containers import Horizontal
from textual.widgets import Button, Footer, Static
from textual.reactive import reactive

from fiwa_cli.functions.loader import load_yaml_config
from fiwa_cli.functions.loader import setup_fiwa, get_abs_path, prep_fiwa, handle_args
from fiwa_cli.components.header import FiwaHeader

import datetime
import argparse

class MyApp(App):
    """A Textual app for FiWa financial tracking."""

    # Use Path(__file__) to get the directory where main.py is installed
    print(str(Path(__file__).parent))
    CSS_PATH = str(Path(__file__).parent / "main.tcss")
    BINDINGS = [
        Binding("ctrl+c", "quit_app", "Quit", show=False),
        ("q", "quit_app", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
        ("m", "open_menu", "Menu"),
        ("s", "open_settings", "Settings"),
        ("e", "open_expenses", "Expenses"),
        ("r", "open_reports", "Reports"),
        ("p", "select_project", "Projects"),
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
        self.app_state["user_scope"] = u.get("user_info", {}).get("scope", "user:write")
        self.app_state["session_uuid"] = u.get("session_info", {}).get("session_uuid", "No session")
        self.app_state["session_start"] = u.get("session_info", {}).get("session_start", None)
        self.app_state["is_logged_in"] = u.get("session_info", {}).get("is_logged_in", False)
        self.app_state["abs_path"] = self._config.get("_abs_path", "")
        self.app_state["css_form"] = self._config.get("style", {}).get("form", "handsome")
        self.app_state["css_theme"] = self._config.get("style", {}).get("theme", "textual-light") #todo: not implemented


        # Process project information
        project_info = u.get("project_info", [])
        if project_info:
            # Extract project IDs and names in the same order
            project_ids = [p["project_id"] for p in project_info]
            project_names = [p["project_name"] for p in project_info]

            # Find the primary project ID
            primary_project = next((p for p in project_info if p.get("project_primary", False)), None)
            primary_project_id = primary_project["project_id"] if primary_project else (project_ids[0] if project_ids else 0)
            primary_project_name = primary_project["project_name"] if primary_project else (project_names[0] if project_names else "No Projects")
            primary_project_style = primary_project["project_style"] if primary_project else "default"
            primary_project_store = primary_project.get("project_store", {}) if primary_project else {}

            self.app_state["project_ids"] = project_ids
            self.app_state["project_names"] = project_names
            self.app_state["project_id"] = primary_project_id
            self.app_state["project_name"] = primary_project_name
            self.app_state["project_style"] = primary_project_style
            self.app_state["project_store"] = primary_project_store

            # Load currency information for the primary project
            if primary_project:
                import json
                currency_main = primary_project.get("currency_main", "USD")
                currency_list_str = primary_project.get("currency_list", "[]")
                try:
                    currency_list = json.loads(currency_list_str) if currency_list_str else []
                except:
                    currency_list = []

                self.app_state["current_project_currency_main"] = currency_main
                self.app_state["current_project_currency_list"] = currency_list
            else:
                self.app_state["current_project_currency_main"] = "USD"
                self.app_state["current_project_currency_list"] = []
        else:
            self.app_state["project_ids"] = [0]
            self.app_state["project_names"] = ["No Projects"]
            self.app_state["project_id"] = 0
            self.app_state["project_name"] = "No Project"
            self.app_state["project_style"] = "default"
            self.app_state["current_project_currency_main"] = "USD"
            self.app_state["current_project_currency_list"] = []

    def on_mount(self) -> None:
        self.theme = "textual-dark"  # Set initial theme
        self.update_session_display()  # Update session info on mount
        self.is_mounted = True  # Flag to indicate the app is fully mounted and ready for updates

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield FiwaHeader(
            user=self.app_state["user_name"],
            projects=self.app_state["project_names"],
            project_id=self.app_state["project_id"],
            project_ids=self.app_state["project_ids"]
        )
        c_user = self.app_state.get("user_name", "Guest")
        c_project = self.app_state.get("project_name", "No Project")
        #yield Static(f"Welcome {c_user} to the FiWa CLI Application!\nCurrent Project: {c_project}",
        #             id="main_body")
        m = """
     _____ _                                
    |  ___(_)_ __   __ _ _ __   ___ ___    
    | |_  | | '_ \ / _` | '_ \ / __/ _ \\
    |  _| | | | | | (_| | | | | (_|  __/
    |_|   |_|_|_|_|\__,_|_| |_|\___\___|
                     __        __    _       _               
                     \ \      / /_ _| |_ ___| |__   ___ _ __ 
                      \ \ /\ / / _` | __/ __| '_ \ / _ \ '__|
                       \ V  V / (_| | || (__| | | |  __/ |   
                        \_/\_/ \__,_|\__\___|_| |_|\___|_|           
"""
        yield Static(m)
        yield Static(id="user_session_info")  # Will be updated reactively

        yield Footer()

    def watch_app_state(self, new_state: dict) -> None:
        """Called automatically when app_state changes."""
        if self.is_mounted:
            self.update_session_display()
            self.update_main_body()

    def update_main_body(self) -> None:
        """Update the main body widgets with current app_state."""
        
        # Update the welcome message
        # main_body = self.query_one("main_body", Static)
        # c_user = self.app_state.get("user_name", "Guest")
        # c_project = self.app_state.get("project_name", "No Project")
        # main_body.update(f"Welcome {c_user} to the FiWa CLI Application!\nCurrent Project: {c_project}")
        # except Exception:
        #     pass

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
            # session_widget = self.query_one("#user_session_info", Static)
            # session_widget.update(f"{self.app_state['user_name']} - {self.app_state['session_uuid']}")
            c_project = self.app_state.get("project_name", "No Project")
            main_body = self.query_one("#main_body", Static)
            main_body.update(f"Welcome {c_user} to the FiWa CLI Application!\nCurrent Project: {c_project}")
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
        """An action to quit the app - performs logout before exiting."""
        # Check if user is logged in
        is_logged_in = self.app_state.get("is_logged_in", False)

        if is_logged_in:
            # Perform logout using shared utility
            from fiwa_cli.functions.logout_util import perform_logout
            logout_success = perform_logout(self)

            if logout_success:
                self.log("User logged out before exit")
            else:
                self.log("Logout failed during exit, but continuing to close app")

        # Exit the application
        self.exit(0)

    def action_toggle_dark(self) -> None:
        """An action to toggle between dark and light themes."""
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"

    def action_open_menu(self) -> None:
        """An action to open the menu."""
        from fiwa_cli.screens.menu import MenuScreen
        self.push_screen(MenuScreen())

    def action_open_settings(self) -> None:
        """An action to open the settings screen."""
        from fiwa_cli.screens.settings import SettingsScreen
        self.push_screen(SettingsScreen())

    def action_open_expenses(self) -> None:
        """An action to open the expenses/inputs screen."""
        from fiwa_cli.screens.inputs import InputsScreen
        self.push_screen(InputsScreen())

    def action_open_reports(self) -> None:
        """An action to open the reports screen."""
        from fiwa_cli.screens.reports import ReportsScreen
        self.push_screen(ReportsScreen())

    def action_select_project(self) -> None:
        """An action to open the project selector screen."""
        from fiwa_cli.screens.project_selector import ProjectSelectorScreen
        self.push_screen(ProjectSelectorScreen())






def main():
    import os
    import getpass

    _mode, _conf = handle_args()


    abs_path = get_abs_path() #the abs path to your package installation!

    if _mode == "init":
        prep_fiwa(mode=_mode, config=_conf) #prepares the FiWa environment based on the mode (e.g., init or run)
        exit(0)

    elif _mode == "run":
        if 'user' in _conf and _conf['user'] is not None:
            print(f"Running FiWa as user: {_conf['user']}")
            pw = getpass.getpass(prompt=f"Enter password for user {_conf['user']}: ")
            _conf['password'] = pw
        else:
            print("No user specified. Running FiWa without user authentication.")

        config = setup_fiwa(abs_path=abs_path, config=_conf)  # Initialize FiWa with the loaded config
        app = MyApp(config=config)
        app.run()
        exit(0)

    exit()
    # app = MyApp(config=config)
    # app.run()


if __name__ == "__main__":
    main()