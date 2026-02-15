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
        from screens.base import LoginScreen
        from screens.dashboard import DashboardScreen
        from screens.inputs import InputsScreen
        from screens.reports import ReportsScreen
        from screens.settings import SettingsScreen
        from screens.project_selector import ProjectSelectorScreen

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
            self.dismiss()
            # Push LoginScreen with logout mode
            self.app.push_screen(
                LoginScreen(
                    is_logged_in=True,
                    username=self.app.app_state.get("user_name")
                )
            )
        else:
            self.app.notify(f"Selected: {event.option.prompt}")
            self.dismiss()
