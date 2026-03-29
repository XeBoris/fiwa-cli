"""FiWa application header component.

This module provides the main application header bar that appears at the
top of every screen. The header displays branding, navigation controls,
user information, and real-time updates.

The header is a persistent UI element that:
    - Displays the FiWa branding/logo
    - Provides access to the main menu
    - Shows calendar picker for date selection
    - Displays current time (via TimeDisplay component)
    - Updates reactively when user or project changes

Key Features:
    - Docked to top of screen (always visible)
    - Reactive properties (auto-updates on state changes)
    - Menu button with dropdown navigation
    - Calendar button for date selection
    - Current time display
    - Themed styling with accent colors

Components:
    FiwaHeader: Main header widget

Example:
    Creating a header::

        >>> from fiwa_cli.components import FiwaHeader
        >>> header = FiwaHeader(
        >>>     user="batman",
        >>>     projects=["Bat Cave Expenses", "Watchtower Shared"],
        >>>     project_id=1,
        >>>     project_ids=[1, 2]
        >>> )
        >>> yield header

    The header automatically updates when state changes::

        >>> # User logs in
        >>> header.user = "batman"
        >>> # Header refreshes, shows "batman"
        >>>
        >>> # User switches project
        >>> header.project_id = 2
        >>> # Header refreshes, shows "Watchtower Shared"

See Also:
    components.time_display.TimeDisplay: Real-time clock widget
    screens.menu.MenuScreen: Navigation menu opened from header
    components.calendar_picker.CalendarWidget: Date picker modal
"""
from typing import List

from textual.widgets import Static, Button
from textual.containers import Horizontal
from textual.app import ComposeResult

from fiwa_cli.components.time_display import TimeDisplay
from textual.reactive import reactive


class FiwaHeader(Static):
    """Application header bar with branding, navigation, and status display.

    The header is a docked widget that appears at the top of all screens,
    providing consistent branding and quick access to navigation controls.
    It uses reactive properties to automatically update when user or
    project information changes.

    The header provides:
        - FiWa branding/logo (left side)
        - Menu button for navigation (☰ Menu)
        - Calendar button for date selection
        - Time display showing current time (right side, via TimeDisplay)

    Reactive Attributes:
        user (str): Current username, default "Guest"
            - Updates automatically when user logs in/out
            - Triggers header refresh

        projects (list): List of project names, default ["No Projects"]
            - Updates when projects loaded or added
            - Used for project name display

        project_id (int): Currently active project ID, default 0
            - Updates when user switches projects
            - Used to find current project name

        project_ids (list[int]): List of project IDs, default [0]
            - Parallel to projects list
            - Used for project_id to name mapping

    Layout:
        ```
        ┌─────────────────────────────────────────────────────────┐
        │ FiWa  [☰ Menu] [Calendar]              12:34:56 PM      │
        └─────────────────────────────────────────────────────────┘
        ```

    Buttons:
        **☰ Menu Button**:
            - ID: header-menu-button
            - Opens MenuScreen modal
            - Provides navigation to all screens
            - Keyboard shortcut: 'M'

        **Calendar Button**:
            - ID: calendar-button
            - Opens CalendarWidget modal
            - Allows date selection
            - Returns selected date via callback

    Reactive Behavior:
        When reactive properties change:
            1. watch_* method is called automatically
            2. watch_* calls self.refresh()
            3. Header redraws with new values
            4. User sees updated information immediately

    CSS Styling:
        Inline CSS provides:
            - Docked to top (dock: top)
            - Height: 3 lines
            - Background: $accent color
            - Horizontal layout
            - Centered content
            - Hover effects on buttons

    Example:
        Basic usage::

            >>> from fiwa_cli.components import FiwaHeader
            >>> header = FiwaHeader(
            >>>     user="batman",
            >>>     projects=["Bat Cave Expenses"],
            >>>     project_id=1,
            >>>     project_ids=[1]
            >>> )
            >>> yield header

        Updating user after login::

            >>> # User logs in
            >>> header = self.query_one(FiwaHeader)
            >>> header.user = "batman"
            >>> # watch_user() fires
            >>> # Header refreshes automatically
            >>> # Shows: "FiWa  [☰ Menu] [Calendar]  batman  12:34:56 PM"

        Switching projects::

            >>> # User selects different project
            >>> header.projects = ["Bat Cave", "Watchtower", "League HQ"]
            >>> header.project_ids = [1, 2, 3]
            >>> header.project_id = 2
            >>> # watch_* methods fire
            >>> # Header refreshes
            >>> # Shows "Watchtower" as current project

    Integration:
        The header is typically composed in screen layouts:
            - Main screen (MyApp.compose())
            - Settings screen
            - Reports screen
            - Inputs screen

        All major screens include the header to maintain consistent
        navigation access.

    Note:
        The header uses reactive variables which trigger automatic
        UI updates. This eliminates the need for manual refresh calls
        when user or project information changes.

        The project name display logic matches project_id with project_ids
        to find the corresponding name in the projects list. If no match
        is found, it defaults to the first project or "(none)".

        Menu and calendar buttons use delayed imports to avoid circular
        dependencies.

    See Also:
        components.time_display.TimeDisplay: Real-time clock component
        screens.menu.MenuScreen: Navigation menu
        components.calendar_picker.CalendarWidget: Date picker
    """

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
        """React to user changes and refresh header display.

        Called automatically by Textual when the user reactive variable
        changes. Triggers a full header refresh to show the new username.

        Args:
            new_user: The new username to display

        Side Effects:
            - Calls self.refresh() to redraw header
        """
        self.refresh()  # or update specific widgets

    def watch_projects(self, new_projects: list) -> None:
        """React to projects list changes and refresh header.

        Called automatically when the projects reactive variable changes.
        Triggers header refresh to update project name display.

        Args:
            new_projects: New list of project names

        Side Effects:
            - Calls self.refresh() to redraw header
        """
        self.refresh()

    def watch_project_id(self, new_id: int) -> None:
        """React to project_id changes and refresh header.

        Called automatically when the project_id reactive variable changes.
        Triggers header refresh to show the new active project name.

        Args:
            new_id: New active project ID

        Side Effects:
            - Calls self.refresh() to redraw header
        """
        self.refresh()

    def watch_project_ids(self, new_ids: list) -> None:
        """React to project_ids list changes and refresh header.

        Called automatically when the project_ids reactive variable changes.
        Triggers header refresh.

        Args:
            new_ids: New list of project IDs

        Side Effects:
            - Calls self.refresh() to redraw header
        """
        self.refresh()

    def __init__(self,
                 user: str = "Guest",
                 projects: List = [],
                 project_id: int = 0,
                 project_ids: List[int] = [0]) -> None:
        """Initialize the FiWa header component.

        Args:
            user: Username to display, defaults to "Guest"
            projects: List of project names, defaults to []
            project_id: Currently active project ID, defaults to 0
            project_ids: List of all project IDs, defaults to [0]

        Example:
            >>> header = FiwaHeader(
            >>>     user="batman",
            >>>     projects=["Bat Cave Expenses", "Watchtower Shared"],
            >>>     project_id=1,
            >>>     project_ids=[1, 2]
            >>> )

        Note:
            The reactive properties are set in __init__ and will trigger
            watchers after the widget is mounted.
        """
        super().__init__(id="fiwa-header")
        self.user = user
        self.projects = projects
        self.project_id = project_id
        self.project_ids = project_ids

    def compose(self) -> ComposeResult:
        """Compose the header layout with branding, buttons, and time display.

        Creates a horizontal layout with:
            - FiWa branding (static text)
            - Menu button (opens navigation menu)
            - Calendar button (opens date picker)
            - Time display (shows current time)

        Yields:
            Static: "FiWa" branding text
            Horizontal: Container for buttons
                Button: Menu button (☰ Menu)
                Button: Calendar button
            TimeDisplay: Current time widget

        Project Name Display:
            The project name is determined by:
                1. Matching project_id with project_ids list
                2. Getting corresponding name from projects list
                3. Defaulting to first project if no match
                4. Showing "(none)" if no projects available

        Note:
            The user info and project display is commented out in the
            current implementation (lines 109-110). Time display is
            shown instead.
        """
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

        # yield Static(f"User: {self.user} | Project: {project_name}",
        #              id="user-info")

        yield TimeDisplay()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the header.

        Routes button clicks to open appropriate modals (menu or calendar).

        Args:
            event: Button.Pressed event containing the clicked button

        Handles:
            - header-menu-button: Opens MenuScreen navigation modal
            - calendar-button: Opens CalendarWidget date picker modal

        Side Effects:
            - Pushes MenuScreen or CalendarWidget onto screen stack
            - Calendar selection triggers _handle_date_selected callback

        Import Strategy:
            Screens imported within method to avoid circular dependencies.

        Example:
            User clicks menu::

                >>> # User clicks "☰ Menu" button
                >>> # on_button_pressed fires
                >>> # MenuScreen imported
                >>> # MenuScreen pushed onto stack
                >>> # Menu modal appears
        """
        if event.button.id == "header-menu-button":
            from fiwa_cli.screens.menu import MenuScreen
            self.app.push_screen(MenuScreen())
        elif event.button.id == "calendar-button":
            from fiwa_cli.components.calendar_picker import CalendarWidget
            self.app.push_screen(CalendarWidget(
                                        initial_date=None,
                                        margin=(3, 0, 0, 15),
                                        week_starts_monday=True
                                 ),
                                 callback=self._handle_date_selected
            )

    def _handle_date_selected(self, selected_date) -> None:
        """Handle date selection from the calendar picker.

        Called as callback when user selects a date in CalendarWidget.
        Currently shows a notification with the selected date.

        Args:
            selected_date: datetime.date object or None if canceled

        Side Effects:
            - Shows notification with formatted date
            - Optionally stores date in app_state (commented out)

        Example:
            >>> # User clicks "Calendar" button
            >>> # CalendarWidget opens
            >>> # User selects March 29, 2026
            >>> # _handle_date_selected(date(2026, 3, 29)) called
            >>> # Notification: "Selected date: 2026-03-29"

        Note:
            The commented code shows how to store the date in app_state
            for use by other screens. Uncomment to enable:
                self.app.app_state["selected_date"] = selected_date.strftime('%Y-%m-%d')
        """
        if selected_date:
            self.app.notify(f"Selected date: {selected_date.strftime('%Y-%m-%d')}", severity="information")
            # You can do more with the selected date here
            # For example, store it in app_state or trigger other actions
            # self.app.app_state["selected_date"] = selected_date.strftime('%Y-%m-%d')
