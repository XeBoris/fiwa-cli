"""FiWa Header component with branding and menu."""
from typing import List

from textual.widgets import Static, Button
from textual.containers import Horizontal
from textual.app import ComposeResult

from components.time_display import TimeDisplay
from textual.reactive import reactive


class FiwaHeader(Static):
    """Custom header with FiWa branding and dropdown menu."""

    DEFAULT_CSS = """
    FiwaHeader {
        dock: top;
        height: 3;
        background: $accent;
        color: $text;
        layout: horizontal;
        align: center middle;
    }

    FiwaHeader #fiwa-title {
        padding: 0 0 0 2;
        text-style: bold;
        width: auto;
    }

    FiwaHeader #header-menu-button {
        margin-left: 1;
        background: $accent-darken-1;
        border: none;
    }

    FiwaHeader #header-menu-button:hover {
        background: $accent-lighten-1;
    }
    
    FiwaHeader #calendar-button {
        margin-left: 10;
        background: $accent-darken-1;
        border: none;
    }
    FiwaHeader #calendar-button:hover {
        background: $accent-lighten-1;
    }
    
    FiwaHeader #user-info {
        padding: 0 0 0 2;
        margin-left: 0;
        text-align: left;
    }

    FiwaHeader #time-display {
        padding: 0 0 0 0;
        margin-left: 0;
        text-align: right;
    }
    """
    user = reactive("Guest")
    projects = reactive(["No Projects"])
    project_id = reactive(0)
    project_ids = reactive([0])  # Actual project IDs from database

    def watch_user(self, new_user: str) -> None:
        """React to user changes."""
        self.refresh()  # or update specific widgets

    def watch_projects(self, new_projects: list) -> None:
        """React to projects changes."""
        self.refresh()

    def watch_project_id(self, new_id: int) -> None:
        """React to project_id changes."""
        self.refresh()

    def watch_project_ids(self, new_ids: list) -> None:
        """React to project_ids changes."""
        self.refresh()

    def __init__(self,
                 user: str = "Guest",
                 projects: List = [],
                 project_id: int = 0,
                 project_ids: List[int] = [0]) -> None:
        super().__init__(id="fiwa-header")
        self.user = user
        self.projects = projects
        self.project_id = project_id
        self.project_ids = project_ids

    def compose(self) -> ComposeResult:
        yield Static("FiWa", id="fiwa-title")
        with Horizontal():
            yield Button("☰ Menu", id="header-menu-button")
            yield Button("Calendar", id="calendar-button")

        # Find the project name by matching project_id with project_ids
        project_name = "(none)"
        if self.project_id in self.project_ids:
            index = self.project_ids.index(self.project_id)
            if 0 <= index < len(self.projects):
                project_name = self.projects[index]
        elif len(self.projects) > 0:
            project_name = self.projects[0]

        # yield Static(f"User: {self.user} | Project: {project_name}", id="user-info")

        yield TimeDisplay()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "header-menu-button":
            from screens.menu import MenuScreen
            self.app.push_screen(MenuScreen())
        elif event.button.id == "calendar-button":
            from components.calendar_display import CalendarWidget
            self.app.push_screen(CalendarWidget(), callback=self._handle_date_selected)

    def _handle_date_selected(self, selected_date) -> None:
        """Handle the date selected from the calendar."""
        if selected_date:
            self.app.notify(f"Selected date: {selected_date.strftime('%Y-%m-%d')}", severity="information")
            # You can do more with the selected date here
            # For example, store it in app_state or trigger other actions
            # self.app.app_state["selected_date"] = selected_date.strftime('%Y-%m-%d')
