"""Project selection modal for FiWa CLI.

This module provides a modal dialog for switching between available projects.
Users can quickly select a different project from a list, and the entire
application state updates to reflect the new project context.

The project selector:
    - Displays all projects accessible to the current user
    - Highlights the currently active project
    - Updates app_state with selected project details
    - Refreshes label cache for the new project
    - Updates UI header with new project information

Key Features:
    - Modal overlay with project list
    - Visual indicator for current project (► arrow)
    - Keyboard navigation (arrow keys, enter, escape)
    - Automatic currency and style loading
    - Label cache refresh
    - Header synchronization
    - Dismissible with Escape key

Classes:
    ProjectSelectorScreen: Modal screen for project selection

State Updates on Selection:
    When a user selects a project, app_state is updated with:
        - project_id: Selected project identifier
        - project_name: Selected project name
        - project_style: Project type (e.g., "ExpenseTracker")
        - project_store: Project metadata (e.g., month_start)
        - current_project_currency_main: Main currency code
        - current_project_currency_list: Additional currencies

Example:
    Opening the selector::

        >>> from fiwa_cli.screens.project_selector import ProjectSelectorScreen
        >>> self.app.push_screen(ProjectSelectorScreen())

    Or using keyboard shortcut 'P' from main screen.

    User workflow::

        >>> # User presses 'P' key
        >>> # ProjectSelectorScreen opens as modal
        >>> # List shows:
        >>> #   ► Bat Cave Expenses     (current)
        >>> #     Watchtower Shared
        >>> #     Justice League Budget
        >>> # User clicks "Watchtower Shared"
        >>> # app_state updated with new project_id
        >>> # Currency and style loaded
        >>> # Label cache refreshed
        >>> # Header updated
        >>> # Modal closes
        >>> # Notification: "Switched to project: Watchtower Shared"

See Also:
    main.MyApp: Main application with app_state
    components.header.FiwaHeader: Header showing current project
    functions.handler_sqllite.op_project_get_info: Project data retrieval
"""
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Static, OptionList
from textual.widgets.option_list import Option
from textual.app import ComposeResult

from fiwa_cli.functions.loader import load_dynamic_css

class ProjectSelectorScreen(ModalScreen):
    """Modal screen for selecting and switching between user projects.

    This modal provides a simple, focused interface for changing the active
    project. It displays all projects the user has access to and allows
    quick selection via keyboard or mouse.

    The selector handles the complete project switching workflow:
        1. Display all available projects
        2. Highlight current project
        3. Accept user selection
        4. Load project details (currency, style, store)
        5. Refresh label cache
        6. Update header display
        7. Update app_state
        8. Dismiss modal

    Attributes:
        None (uses app_state for all data)

    BINDINGS:
        - Escape: Cancel selection and close modal

    Display Format:
        The OptionList shows each project with:
            - "► Project Name" for current project (with arrow)
            - "  Project Name" for other projects (indented)

    Keyboard Navigation:
        - ↑/↓: Navigate through project list
        - Enter: Select highlighted project
        - Escape: Cancel and close without selecting

    State Management:
        On project selection, updates app_state with:
            - project_id: New active project
            - project_name: Project display name
            - project_style: Project type for ProjectComposer
            - project_store: JSON metadata (month_start, etc.)
            - current_project_currency_main: Primary currency
            - current_project_currency_list: Additional currencies

    Side Effects of Selection:
        1. **Label cache refresh**: Calls op_label_get_all(force_refresh=True)
           to clear cached labels for old project and load new project's labels

        2. **Header update**: Refreshes FiwaHeader to show new project name
           in the application header bar

        3. **State propagation**: All screens/widgets watching app_state
           automatically see the new project_id and related fields

    Example:
        Basic usage::

            >>> selector = ProjectSelectorScreen()
            >>> self.app.push_screen(selector)

        Complete workflow::

            >>> # User working in "Bat Cave Expenses" project
            >>> # app_state["project_id"] = 1
            >>> # User presses 'P' key
            >>> # ProjectSelectorScreen opens
            >>> # OptionList displays:
            >>> #   ► Bat Cave Expenses
            >>> #     Watchtower Shared
            >>> #     Justice League Budget
            >>> # User selects "Watchtower Shared"
            >>> # on_option_list_option_selected() fires
            >>> # Extracts project_id = 2
            >>> # Updates app_state["project_id"] = 2
            >>> # Loads currency: USD (main), [EUR, GBP] (additional)
            >>> # Loads style: "ExpenseTracker"
            >>> # Loads store: {"month_start": 15}
            >>> # Refreshes label cache
            >>> # Updates header display
            >>> # Shows notification: "Switched to project: Watchtower Shared"
            >>> # Modal dismisses
            >>> # All screens now show Watchtower data

        Canceling selection::

            >>> # User opens selector
            >>> # User presses Escape
            >>> # action_cancel() fires
            >>> # Modal dismisses without changes
            >>> # app_state unchanged

    Performance:
        - Lightweight: Only displays project list, no database queries
        - Fast switching: Pre-loads all project IDs and names
        - Efficient cache refresh: Only reloads labels for new project

    Note:
        The selector reads project_ids and project_names from app_state,
        which are loaded during user login. No additional database queries
        are needed to display the list.

        When a project is selected, the label cache is explicitly refreshed
        with force_refresh=True to ensure stale labels from the previous
        project don't appear in the new project context.

        The modal uses ModalScreen, so it appears as an overlay and can
        be dismissed by clicking outside the container or pressing Escape.

    See Also:
        main.MyApp.action_select_project: Keyboard shortcut ('P') handler
        components.header.FiwaHeader: Header with project dropdown
        functions.handler_sqllite.op_project_get_info: Project info loading
        functions.handler_sqllite.op_label_get_all: Label cache management
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    # DEFAULT_CSS = """
    #
    # """
    def on_mount(self) -> None:
        """Load CSS stylesheet when the modal is mounted.

        Side Effects:
            - Loads screens_project_selection.tcss stylesheet
            - Logs mount event or any loading errors

        Note:
            Called automatically by Textual after compose() but before
            widgets are displayed.
        """
        try:
            load_dynamic_css(self, "screens_project_selection.tcss")
        except Exception as e:
            self.app.log(f"Could not load CSS for ProjectSelectorScreen: {e}")

    def compose(self) -> ComposeResult:
        """Compose the project selector modal interface.

        Creates a vertical container with a title and an OptionList
        displaying all available projects. The current project is
        visually marked with an arrow (►).

        Yields:
            Static: Title "Select a Project"
            OptionList: List of projects with current one marked

        Option Format:
            - Current project: "► {project_name}"
            - Other projects: "  {project_name}" (two spaces)

        Data Source:
            Reads from app_state:
                - project_names: List of project names
                - project_ids: Corresponding list of IDs
                - project_id: Current active project ID

        Example:
            If app_state contains:
                - project_ids: [1, 2, 3]
                - project_names: ["Bat Cave", "Watchtower", "League HQ"]
                - project_id: 1

            OptionList displays:
                ► Bat Cave
                  Watchtower
                  League HQ
        """
        with Vertical():
            yield Static("Select a Project", id="project-title")
            # Get projects from app store
            project_names = self.app.app_state.get("project_names", ["No Projects"])
            project_ids = self.app.app_state.get("project_ids", [0])
            current_project_id = self.app.app_state.get("project_id", 0)

            # Create options for each project
            options = []
            for idx, (proj_id, proj_name) in enumerate(zip(project_ids, project_names)):
                # Mark current project with arrow
                prompt = f"► {proj_name}" if proj_id == current_project_id else f"  {proj_name}"
                options.append(Option(prompt, id=f"project-{proj_id}"))

            yield OptionList(*options)

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        """Handle project selection from the OptionList.

        When a user selects a project, this method:
            1. Extracts the project_id from the option ID
            2. Updates app_state with new project_id
            3. Loads project details (currency, style, store)
            4. Refreshes label cache for new project
            5. Updates application header
            6. Shows success notification
            7. Dismisses the modal

        Args:
            event: OptionSelected event containing the selected option

        Side Effects:
            - Updates app_state["project_id"]
            - Loads currency information via _load_project_currency()
            - Clears and refreshes label cache
            - Updates FiwaHeader with new project
            - Shows notification message
            - Dismisses modal screen

        Option ID Format:
            Options have IDs like "project-1", "project-2", etc.
            The number after the hyphen is the project_id.

        Example:
            User selects "Watchtower Shared"::

                >>> # Option ID: "project-2"
                >>> # on_option_list_option_selected() fires
                >>> # Extracts: selected_project_id = 2
                >>> # Updates: app_state["project_id"] = 2
                >>> # Loads: currency=USD, style=ExpenseTracker, store={...}
                >>> # Refreshes: Label cache for project 2
                >>> # Updates: Header shows "Watchtower Shared"
                >>> # Notifies: "Switched to project: Watchtower Shared"
                >>> # Dismisses modal

        Note:
            If the option ID is invalid or doesn't start with "project-",
            the modal simply dismisses without making changes.
        """
        # Extract project ID from option id (format: "project-1", "project-2", etc.)
        option_id = event.option.id
        if option_id and option_id.startswith("project-"):
            selected_project_id = int(option_id.split("-")[1])

            # Update the app's store with the new primary project ID
            self.app.app_state["project_id"] = selected_project_id

            # Find the project name for notification
            project_ids = self.app.app_state.get("project_ids", [])
            project_names = self.app.app_state.get("project_names", [])

            project_name = "Unknown Project"
            if selected_project_id in project_ids:
                idx = project_ids.index(selected_project_id)
                project_name = project_names[idx]

            # Load currency information for the selected project
            self._load_project_currency(selected_project_id)

            # we need to refresh the cached labels:
            dbh = self.app._config.get("dbh")
            dbh.op_label_get_all(project_id=selected_project_id,
                                 use_cache=False,
                                 force_refresh=True)

            # Explicitly update the header to reflect the new project BEFORE dismissing
            self._refresh_header()

            # Notify and dismiss
            self.app.notify(f"Switched to project: {project_name}")
            self.dismiss()
        else:
            # If no valid selection, just dismiss
            self.dismiss()

    def _load_project_currency(self, project_id: int) -> None:
        """Load currency information and project details into app_state.

        Queries the database for complete project information and updates
        app_state with currency settings, project style, name, and store
        metadata.

        This method is called automatically when a user selects a project
        to ensure all project-specific settings are loaded and available
        throughout the application.

        Args:
            project_id: ID of the project to load details for

        Side Effects:
            Updates app_state with:
                - current_project_currency_main: Primary currency (e.g., "USD")
                - current_project_currency_list: Additional currencies list
                - project_style: Project type (e.g., "ExpenseTracker")
                - project_name: Full project name
                - project_store: JSON metadata dictionary

            Logs the loaded project information

        Database Query:
            Calls op_project_get_info(user_id) to retrieve all projects
            for the current user, then filters to find the selected one.

        Error Handling:
            - If database unavailable: Returns silently
            - If project not found: No updates made
            - If JSON parse fails: Uses empty list for currencies
            - Logs all errors for debugging

        Example:
            Loading project details::

                >>> self._load_project_currency(project_id=2)
                >>> # Queries database for project 2
                >>> # Found: {
                >>> #   "currency_main": "EUR",
                >>> #   "currency_list": '["USD", "GBP"]',
                >>> #   "project_style": "ExpenseTracker",
                >>> #   "project_name": "European Travel",
                >>> #   "project_store": '{"month_start": 15}'
                >>> # }
                >>> # Updates app_state:
                >>> #   current_project_currency_main = "EUR"
                >>> #   current_project_currency_list = ["USD", "GBP"]
                >>> #   project_style = "ExpenseTracker"
                >>> #   project_name = "European Travel"
                >>> #   project_store = {"month_start": 15}

        Note:
            The currency_list is stored as a JSON string in the database
            and parsed into a Python list here.

            The project_store field contains metadata like month_start
            that affects period calculations throughout the application.

        See Also:
            functions.handler_sqllite.op_project_get_info: Database query
        """
        try:
            dbh = self.app._config.get("dbh")
            if not dbh:
                return

            # Get project info
            user_id = self.app.app_state.get("user_id", -1)
            project_info_list = dbh.op_project_get_info(user_id)

            # Find the selected project
            project = next((p for p in project_info_list if p["project_id"] == project_id), None)

            if project:
                import json
                currency_main = project.get("currency_main", "USD")
                currency_list_str = project.get("currency_list", "[]")
                project_style = project.get("project_style", "default")
                project_name = project.get("project_name", "Unknown Project")
                project_store = project.get("project_store", {})

                try:
                    currency_list = json.loads(currency_list_str) if currency_list_str else []
                except:
                    currency_list = []

                self.app.app_state["current_project_currency_main"] = currency_main
                self.app.app_state["current_project_currency_list"] = currency_list
                self.app.app_state["project_style"] = project_style
                self.app.app_state["project_name"] = project_name
                self.app.app_state["project_store"] = project_store
                self.app.log(f"Loaded project info for {project_id}: style={project_style}, currency={currency_main}, store={project_store}")
        except Exception as e:
            self.app.log(f"Error loading project info: {e}")

    def _refresh_header(self) -> None:
        """Refresh the FiwaHeader to display the newly selected project.

        Updates the application header with the new project information
        so users immediately see which project is now active.

        This method is called after project selection to ensure the header
        displays the correct project name before the modal dismisses.

        Side Effects:
            - Queries for FiwaHeader widget
            - Updates header.project_id
            - Updates header.project_ids
            - Updates header.projects
            - Calls header.refresh() to redraw
            - Logs any errors

        Error Handling:
            Wrapped in try/except to handle cases where:
                - Header widget not yet mounted
                - Header already removed from screen
                - Other widget query issues

            Errors are logged but don't prevent modal dismissal.

        Example:
            After project selection::

                >>> # User selected "Watchtower Shared"
                >>> # app_state["project_id"] = 2
                >>> # app_state["project_name"] = "Watchtower Shared"
                >>> # _refresh_header() called
                >>> # Header widget found
                >>> # header.project_id = 2
                >>> # header.projects = ["Bat Cave", "Watchtower", "League HQ"]
                >>> # header.refresh()
                >>> # Header now displays "Watchtower Shared" in dropdown

        Note:
            The header refresh is synchronous and completes before the
            modal dismisses, ensuring users see the updated project
            immediately.
        """
        try:
            from components.header import FiwaHeader
            header = self.app.query_one(FiwaHeader)
            header.project_id = self.app.app_state["project_id"]
            header.project_ids = self.app.app_state["project_ids"]
            header.projects = self.app.app_state["project_names"]
            header.refresh()
        except Exception as e:
            # Header might not be available yet or other error
            self.app.log(f"Could not refresh header: {e}")

    def action_cancel(self) -> None:
        """Handle escape key press to dismiss modal without selecting.

        Allows users to close the project selector without changing
        the active project. No app_state modifications are made.

        Bound to:
            - Escape key

        Side Effects:
            - Dismisses modal screen
            - No app_state changes
            - No notifications shown

        Example:
            User cancels selection::

                >>> # User opens project selector
                >>> # User presses Escape
                >>> # action_cancel() fires
                >>> # Modal closes
                >>> # app_state["project_id"] unchanged
        """
        self.dismiss()
