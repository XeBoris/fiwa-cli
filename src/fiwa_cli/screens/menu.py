"""Menu-related screens for FiWa application."""
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Static, OptionList
from textual.widgets.option_list import Option
from textual.app import ComposeResult


class MenuScreen(ModalScreen):
    """Dropdown menu screen."""

    BINDINGS = [
        ("escape", "dismiss", "Close menu"),
    ]

    DEFAULT_CSS = """
    MenuScreen {
        align: left top;
    }

    MenuScreen > Vertical {
        width: 30;
        height: auto;
        margin: 3 0 0 2;
        background: $surface;
        border: solid $accent;
    }

    MenuScreen OptionList {
        height: auto;
        max-height: 20;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            # Determine the last option based on mode
            mode = self.app._mode
            if mode == "terminal":
                last_option = Option("Exit", id="menu-exit")
            else:  # web mode
                last_option = Option("Disconnect", id="menu-disconnect")

            # use an interactive menu option for login/logout based on current state:
            if self.app.app_state.get("is_logged_in", False):
                op_log = "Logout"
            else:
                op_log = "Login"

            yield OptionList(
                Option("Dashboard", id="menu-dashboard"),
                Option("Select Project", id="menu-select-project"),
                Option("Inputs", id="menu-inputs"),
                Option("Reports", id="menu-report"),
                Option("Settings", id="menu-settings"),
                Option(op_log, id="menu-login"),
                Option("---", disabled=True),
                last_option,
            )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        option_id = event.option.id

        # Import here to avoid circular dependencies
        from fiwa_cli.screens.base import LoginScreen
        from fiwa_cli.screens.dashboard import DashboardScreen
        from fiwa_cli.screens.inputs import InputsScreen
        from fiwa_cli.screens.reports import ReportsScreen
        from fiwa_cli.screens.settings import SettingsScreen
        from fiwa_cli.screens.project_selector import ProjectSelectorScreen

        if option_id == "menu-dashboard":
            self.dismiss()
            self.app.push_screen(DashboardScreen())
        elif option_id == "menu-inputs":
            self.dismiss()
            self.app.push_screen(InputsScreen())
        elif option_id == "menu-report":
            self.dismiss()
            self.app.push_screen(ReportsScreen())
        elif option_id == "menu-settings":
            self.dismiss()
            self.app.push_screen(SettingsScreen())
        elif option_id == "menu-select-project":
            self.dismiss()
            self.app.push_screen(ProjectSelectorScreen())
        elif option_id == "menu-exit":
            # Terminal mode - exit the application
            self.dismiss()
            self.app.exit(0)
        elif option_id == "menu-disconnect":
            # Web mode - placeholder for future web disconnect logic
            self.app.notify("Disconnect functionality - to be implemented")
            self.dismiss()
            # TODO: Implement web session disconnect logic here
            # For example: close websocket, clear session, redirect to login, etc.
        elif option_id == "menu-login" and self.app.app_state.get("is_logged_in", False) is False:
            self.dismiss()
            self.app.push_screen(LoginScreen(is_logged_in=self.app.app_state.get("is_logged_in", False)),
                                 # self.handle_login_result
                                 )
        elif option_id == "menu-login" and self.app.app_state.get("is_logged_in", False) is True:
            # Perform logout directly here
            self._perform_logout()
            self.dismiss()
        else:
            self.app.notify(f"Selected: {event.option.prompt}")
            self.dismiss()

    def _perform_logout(self) -> None:
        """Perform logout operation directly from menu."""
        try:
            # Get database handler
            k = self.app._config.get("dbh")

            # Get session UUID from app state
            session_uuid = self.app.app_state.get("session_uuid")

            # IMPORTANT: Preserve application-level configuration that should persist across login/logout
            # These are not user-specific, they're application configuration
            abs_path = self.app.app_state.get("abs_path", "")
            css_form = self.app.app_state.get("css_form", "handsome")
            css_theme = self.app.app_state.get("css_theme", "textual-light")

            # Verify logout - call the correct database method with session_uuid
            verify = k.op_user_logout(session_uuid=session_uuid)

            if verify:
                # Update app state to logged-out state
                self.app.app_state = {
                    "user_name": "Guest",
                    "user_id": -1,
                    "user_scope": "user:write",
                    "session_uuid": "No session",
                    "session_start": None,
                    "is_logged_in": False,
                    "project_names": ["No Projects"],
                    "project_ids": [0],
                    "project_id": 0,
                    # Restore application-level configuration
                    "abs_path": abs_path,
                    "css_form": css_form,
                    "css_theme": css_theme,
                }

                self.app.notify("Logout successful!", severity="success")

                # Pop all screens to return to main screen
                self.app.call_after_refresh(self._return_to_main_screen)
            else:
                self.app.notify("Logout failed. Please try again.", severity="error")

        except Exception as e:
            self.app.notify(f"Error during logout: {str(e)}", severity="error")
            self.app.log(f"Logout error: {e}")

    def _return_to_main_screen(self) -> None:
        """Pop all screens to return to the main screen."""
        try:
            # Pop all screens except the main screen
            while len(self.app.screen_stack) > 1:
                self.app.pop_screen()
        except Exception as e:
            self.app.log(f"Error returning to main screen: {e}")

