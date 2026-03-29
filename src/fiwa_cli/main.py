"""Main application entry point for FiWa CLI.

This module contains the main Textual application class and entry point
for the FiWa (Finance Watcher) CLI application. It manages the application
lifecycle, user sessions, project state, and provides the main UI framework.

The application uses Textual for terminal-based UI and supports:
- User authentication and session management
- Multi-project management with project switching
- Reactive state management across all screens
- Custom file logging with rotation
- Keyboard shortcuts for quick navigation
- Dark/light theme toggling

Key Components:
    MyApp: Main Textual application class
    main(): Entry point function handling command-line arguments

Typical Usage:
    Command line::

        $ fiwa run --path /path/to/data --user username
        $ fiwa init --path /path/to/data

    Programmatic::

        >>> from fiwa_cli.main import MyApp, main
        >>> config = setup_fiwa(abs_path="/data", config={})
        >>> app = MyApp(config=config)
        >>> app.run()

See Also:
    fiwa_cli.functions.loader: Configuration loading functions
    fiwa_cli.screens: Application screen modules
    fiwa_cli.components: Reusable UI components
"""

from typing import Any, Dict
from pathlib import Path

from textual.app import App, ComposeResult, Binding
from textual.widgets import Button, Footer, Static
from textual.reactive import reactive

from fiwa_cli.functions.loader import setup_fiwa, get_abs_path, prep_fiwa, handle_args
from fiwa_cli.components.header import FiwaHeader

import datetime


class MyApp(App):
    """Main Textual application for FiWa financial tracking.

    This is the core application class that manages the entire FiWa CLI
    application lifecycle, including user sessions, project state, navigation,
    and screen management.

    The application uses a reactive state pattern where ``app_state`` is a
    reactive dictionary that automatically updates all screens and widgets
    when values change. This ensures UI consistency across the application.

    Attributes:
        CSS_PATH (str): Path to the main CSS stylesheet
        BINDINGS (list): Keyboard shortcuts for quick navigation:
            - Ctrl+C/Q: Quit application (with logout)
            - D: Toggle dark/light theme
            - M: Open menu
            - S: Open settings
            - E: Open expenses/inputs
            - R: Open reports
            - P: Select project
        app_state (reactive dict): Shared application state containing:
            - user_name: Current username
            - user_id: Current user ID
            - session_uuid: Session identifier
            - is_logged_in: Login status
            - project_names: List of project names
            - project_ids: List of project IDs
            - project_id: Current project ID
            - project_name: Current project name
            - project_style: Project type (e.g., "ExpenseTracker")
            - project_store: Project-specific metadata (JSON)
            - current_project_currency_main: Primary currency
            - current_project_currency_list: Available currencies
            - abs_path: Application data directory path
            - css_form: Form style name (e.g., "handsome")
            - css_theme: Theme name (e.g., "textual-light")
        file_log (logging.Logger): Custom file logger for persistent logs
        is_mounted (bool): Flag indicating if app is fully mounted

    Class Variables:
        CSS_PATH: Path to main.tcss stylesheet
        BINDINGS: Keyboard bindings for application-wide shortcuts

    Example:
        Basic usage::

            >>> config = {"dbh": database_handler, "_abs_path": "/data"}
            >>> app = MyApp(config=config)
            >>> app.run()

        Accessing state from a screen::

            >>> class MyScreen(Screen):
            >>>     def on_mount(self):
            >>>         user = self.app.app_state["user_name"]
            >>>         project = self.app.app_state["project_name"]
            >>>         self.app.file_log.info(f"Screen opened by {user}")

    Note:
        The app_state is reactive - any changes trigger automatic UI updates
        across all mounted screens and widgets that watch these values.

    See Also:
        fiwa_cli.screens.base.LoginScreen: User authentication
        fiwa_cli.screens.settings.SettingsScreen: Application settings
        fiwa_cli.components.header.FiwaHeader: Main application header
    """

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

    # Single reactive dictionary that will trigger UI updates when changed
    # This contains all shared state across the application
    app_state = reactive(
        {
            "user_name": "Guest",
            "user_id": "user_id",
            "session_uuid": "No session",
            "session_start": None,
            "is_logged_in": False,
            "project_names": ["No Projects"],
            "project_ids": [0],
            "project_id": 0,  # Primary project ID
            "meta_info": {
                "today": datetime.datetime.today().isoformat(),
                "focus_week": datetime.datetime.today().isocalendar()[1],
                "focus_month": datetime.datetime.today().month,
            },
        }
    )

    def __init__(self, config: Dict[str, Any] | None = None, mode: str = "terminal") -> None:
        """Initialize the FiWa application.

        Sets up the application with configuration, initializes the reactive
        state from the database, and prepares the logging system.

        The initialization process:
        1. Sets up configuration and mode
        2. Creates log file directory and path
        3. Loads user session data from database
        4. Populates app_state with user and project information
        5. Loads currency settings for the primary project

        Args:
            config: Configuration dictionary containing:
                - dbh: Database handler instance (SQLLiteHandler)
                - _abs_path: Absolute path to data directory
                - style: Dictionary with 'form' and 'theme' settings
                Defaults to empty dict if not provided.
            mode: Application mode, either "terminal" or "web".
                Defaults to "terminal".

        Raises:
            KeyError: If required config keys (dbh) are missing

        Side Effects:
            - Creates data directory if it doesn't exist
            - Creates fiwa.log file in data directory
            - Populates self.app_state with database values
            - Sets up self._log_file_path for custom logging

        Example:
            >>> from fiwa_cli.functions.handler_sqllite import SQLLiteHandler
            >>> dbh = SQLLiteHandler(db_path="/data/fiwa.db")
            >>> config = {
            >>>     "dbh": dbh,
            >>>     "_abs_path": "/home/user/fiwa-data",
            >>>     "style": {"form": "handsome", "theme": "textual-light"}
            >>> }
            >>> app = MyApp(config=config, mode="terminal")
            >>> app.run()

        Note:
            The app_state reactive dictionary is updated from the database
            during initialization. Changes to app_state automatically trigger
            UI updates in all mounted screens and widgets.
        """
        super().__init__()
        self._config = config or {}
        self._mode = mode  # "terminal" or "web"
        self.count = 0

        # Setup log file path for textual run command
        data_path = self._config.get("_data_directory", ".")
        log_dir = Path(data_path)
        log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file_path = log_dir / "fiwa.log"

        # Note: app_state is initialized at class level as reactive variable
        # We can update it after initialization if needed from database
        u = self.app._config["dbh"].op_get_user_sessions()

        # ...existing code...
        self.app_state["user_name"] = u.get("user_info", {}).get("username", "Guest")
        self.app_state["user_id"] = u.get("user_info", {}).get("user_id", -1)
        self.app_state["user_scope"] = u.get("user_info", {}).get("scope", "user:write")
        self.app_state["session_uuid"] = u.get("session_info", {}).get("session_uuid", "No session")
        self.app_state["session_start"] = u.get("session_info", {}).get("session_start", None)
        self.app_state["is_logged_in"] = u.get("session_info", {}).get("is_logged_in", False)
        self.app_state["home_path"] = self._config.get("_data_directory", "")
        self.app_state["abs_path"] = self._config.get("_abs_path", "")
        self.app_state["css_form"] = self._config.get("style", {}).get("form", "handsome")
        # todo: theme switching not fully implemented
        self.app_state["css_theme"] = self._config.get("style", {}).get("theme", "textual-light")

        # Process project information
        project_info = u.get("project_info", [])
        if project_info:
            # Extract project IDs and names in the same order
            project_ids = [p["project_id"] for p in project_info]
            project_names = [p["project_name"] for p in project_info]

            # Find the primary project ID
            primary_project = next(
                (p for p in project_info if p.get("project_primary", False)), None
            )
            primary_project_id = (
                primary_project["project_id"]
                if primary_project
                else (project_ids[0] if project_ids else 0)
            )
            primary_project_name = (
                primary_project["project_name"]
                if primary_project
                else (project_names[0] if project_names else "No Projects")
            )
            primary_project_style = (
                primary_project["project_style"] if primary_project else "default"
            )
            primary_project_store = (
                primary_project.get("project_store", {}) if primary_project else {}
            )

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
                except Exception:
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
        """Called when the application is mounted and ready.

        This lifecycle hook runs after the app is composed but before it's
        displayed to the user. It performs final setup tasks including:
        - Initializing custom file logging
        - Logging startup information
        - Setting initial theme
        - Updating session displays

        The method is called automatically by Textual's lifecycle system.

        Side Effects:
            - Creates and configures self.file_log (RotatingFileHandler)
            - Writes startup messages to fiwa.log
            - Sets self.theme to "textual-dark"
            - Calls update_session_display()
            - Sets self.is_mounted = True

        Note:
            This is the appropriate place for setup code that requires
            the app to be fully initialized and have access to all widgets.

        See Also:
            _setup_file_logging(): Custom file logger configuration
            update_session_display(): Updates UI with session info
        """
        # Setup custom file logging
        self._setup_file_logging()

        # Log initial startup using custom logger
        self.file_log.info("-" * 60)
        self.file_log.info("| FiWa Application Started")
        self.file_log.info(f"| User: {self.app_state.get('user_name', 'Guest')}")
        self.file_log.info(f"| Project: {self.app_state.get('project_name', 'No Project')}")
        self.file_log.info(f"| Project Style: {self.app_state.get('project_style', 'default')}")
        self.file_log.info("-" * 60)

        self.theme = "textual-dark"  # Set initial theme
        self.update_session_display()  # Update session info on mount
        self.is_mounted = True  # Flag to indicate the app is fully mounted and ready for updates

    def _setup_file_logging(self) -> None:
        """Setup custom file logging with automatic rotation.

        Creates a custom logger accessible via ``self.file_log`` that writes
        to a rotating log file. This logger can be used from any component
        in the application without interfering with Textual's built-in logging.

        Log Configuration:
            - File location: {data_path}/fiwa.log
            - Max file size: 10 MB
            - Backup count: 5 files (fiwa.log, fiwa.log.1, ..., fiwa.log.5)
            - Encoding: UTF-8
            - Format: "YYYY-MM-DD HH:MM:SS - LEVEL - message"

        Logger Access:
            - From App: ``self.file_log.info("message")``
            - From Screen: ``self.app.file_log.info("message")``
            - From Widget: ``self.app.file_log.info("message")``

        Log Levels:
            - debug(): Detailed debugging information
            - info(): General informational messages
            - warning(): Warning messages
            - error(): Error messages
            - critical(): Critical error messages

        Example:
            From any screen or widget::

                >>> self.app.file_log.info("User logged in")
                >>> self.app.file_log.error("Database connection failed")
                >>> self.app.file_log.debug(f"State: {self.app.app_state}")

        Side Effects:
            - Creates self.file_log (logging.Logger instance)
            - Creates fiwa.log in data directory
            - Writes initial startup marker to log
            - Prints confirmation message to console

        Raises:
            Exception: If logging setup fails, creates a dummy logger
                to prevent application crashes. Error is printed to console.

        Note:
            The RotatingFileHandler ensures the log file never grows
            beyond 50 MB total (10 MB × 5 files). Old logs are automatically
            archived as .log.1, .log.2, etc.

        See Also:
            logging.handlers.RotatingFileHandler: Python's rotating file handler
        """
        try:
            import logging
            from logging.handlers import RotatingFileHandler

            # Ensure log directory exists
            self._log_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Create rotating file handler
            handler = RotatingFileHandler(
                str(self._log_file_path),
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding="utf-8",
            )

            # Set log format
            formatter = logging.Formatter(
                fmt="%(asctime)s - %(levelname)-8s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)

            # Create a custom logger for our app
            file_logger = logging.getLogger("fiwa_app")
            file_logger.handlers.clear()  # Clear any existing handlers
            file_logger.addHandler(handler)
            file_logger.setLevel(logging.DEBUG)
            file_logger.propagate = False  # Don't propagate to root logger

            # Make it accessible as self.file_log
            self.file_log = file_logger

            # Write startup marker
            self.file_log.info("=" * 60)
            self.file_log.info(f"Log file: {self._log_file_path}")
            self.file_log.info(f"Max size: 10 MB, Backups: 5")
            self.file_log.info("=" * 60)

            print(f"✓ Custom file logging configured: {self._log_file_path}")
            print(f"  Usage: self.app.file_log.info('message') from any screen/widget")

        except Exception as e:
            print(f"✗ Warning: Could not setup file logging: {e}")
            import traceback

            traceback.print_exc()
            # Create a dummy logger so code doesn't break
            import logging

            self.file_log = logging.getLogger("fiwa_dummy")

    def compose(self) -> ComposeResult:
        """Create the main application layout and child widgets.

        Constructs the initial UI hierarchy including the header, welcome
        message, and footer. This method is called once during application
        startup by Textual's lifecycle system.

        Layout Structure:
            - FiwaHeader: Top bar with user info, project selector, menu
            - Static: ASCII art logo and welcome message
            - Static: User session information display (updated reactively)
            - Footer: Keyboard shortcuts display

        Yields:
            FiwaHeader: Application header with user and project info
            Static: ASCII art logo
            Static: Session info widget (id="user_session_info")
            Footer: Keyboard shortcut display

        Note:
            The compose method only runs once. For dynamic updates,
            use reactive attributes or watch methods.

        See Also:
            FiwaHeader: Main header component documentation
            update_session_display(): Updates the session info widget
        """
        yield FiwaHeader(
            user=self.app_state["user_name"],
            projects=self.app_state["project_names"],
            project_id=self.app_state["project_id"],
            project_ids=self.app_state["project_ids"],
        )
        c_user = self.app_state.get("user_name", "Guest")
        c_project = self.app_state.get("project_name", "No Project")
        # yield Static(f"Welcome {c_user} to the FiWa CLI Application!\nCurrent Project: {c_project}",
        #             id="main_body")
        m = """
     _____ _
    |  ___(_)_ __   __ _ _ __   ___ ___
    | |_  | | '_ \\ / _` | '_ \\ / __/ _ \\
    |  _| | | | | | (_| | | | | (_|  __/
    |_|   |_|_|_|_|\\__,_|_| |_|\\___\\___|
                     __        __    _       _
                     \\ \\      / /_ _| |_ ___| |__   ___ _ __
                      \\ \\ /\\ / / _` | __/ __| '_ \\ / _ \\ '__|
                       \\ V  V / (_| | || (__| | | |  __/ |
                        \\_/\\_/ \\__,_|\\__\\___|_| |_|\\___|_|
"""
        yield Static(m)
        yield Static(id="user_session_info")  # Will be updated reactively

        yield Footer()

    def watch_app_state(self, new_state: dict) -> None:
        """Called automatically when app_state reactive dictionary changes.

        This is a Textual reactive watch method that's triggered whenever
        any value in the app_state dictionary is modified. It ensures the
        UI stays in sync with the application state.

        Args:
            new_state: The updated app_state dictionary

        Side Effects:
            - Calls update_session_display() to refresh session info
            - Calls update_main_body() to refresh main content

        Note:
            This method only runs if self.is_mounted is True to avoid
            errors during initialization before widgets are available.

        See Also:
            update_session_display(): Updates session-related widgets
            update_main_body(): Updates main content widgets
        """
        if self.is_mounted:
            self.update_session_display()
            self.update_main_body()

    def update_main_body(self) -> None:
        """Update the main body widgets with current app_state.

        Attempts to update various display widgets that show app_state
        information. Uses try/except blocks to handle widgets that may
        not exist or may not be mounted yet.

        Widgets Updated:
            - #app_state_display_1: Raw app_state display (if exists)
            - #app_state_display_2: Alternative app_state display (if exists)

        Side Effects:
            Updates widget content via widget.update() method

        Note:
            All widget queries are wrapped in try/except to gracefully
            handle cases where widgets don't exist. This is common during
            screen transitions or when certain screens are active.
        """

        # Update the welcome message (widget may not exist, so skip)
        # try:
        #     main_body = self.query_one("main_body", Static)
        #     c_user = self.app_state.get("user_name", "Guest")
        #     c_project = self.app_state.get("project_name", "No Project")
        #     main_body.update(
        #         f"Welcome {c_user} to the FiWa CLI Application!\n"
        #         f"Current Project: {c_project}"
        #     )
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
        """Update the session display with current reactive values.

        Refreshes UI widgets that display user session information and
        the application header. This method is called automatically when
        app_state changes and can also be called manually.

        Widgets Updated:
            - FiwaHeader: Updates user, projects, and project_id

        Side Effects:
            - Updates header.user with current username
            - Updates header.projects with project list
            - Updates header.project_id with current project
            - Calls header.refresh() to re-render

        Note:
            Uses try/except to handle cases where widgets aren't ready.
            This is safe to call at any time - it will silently skip
            updates if widgets aren't available.

        See Also:
            FiwaHeader: Header component that displays this information
            watch_app_state(): Calls this method on state changes
        """

        try:
            # session_widget = self.query_one("#user_session_info", Static)
            # session_widget.update(f"{self.app_state['user_name']} - {self.app_state['session_uuid']}")
            c_project = self.app_state.get("project_name", "No Project")
            main_body = self.query_one("#main_body", Static)
            main_body.update(
                f"Welcome {c_user} to the FiWa CLI Application!\nCurrent Project: {c_project}"
            )
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
        """Handle button press events in the main screen.

        Currently a placeholder for future button handlers on the main screen.
        Most navigation is handled through keyboard shortcuts (see BINDINGS).

        Args:
            event: Button.Pressed event containing the pressed button

        Note:
            This method is currently not used as the main screen has no buttons.
            Navigation is handled via keyboard shortcuts and the menu.
        """
        # from screens.base import LoginScreen

        # elif event.button.id == "login_button":
        #     # Check if already logged in
        #     is_logged_in = self.app_state.get("user_id", -1) > 0
        #     username = self.app_state.get("user_name", "")
        #     self.push_screen(LoginScreen(is_logged_in=is_logged_in, username=username), handle_login_result)
        pass

    def action_quit_app(self) -> None:
        """Quit the application with proper logout handling.

        This action is bound to 'q' and Ctrl+C keys. It performs a clean
        shutdown by logging out the user (if logged in) before exiting.

        Process:
            1. Check if user is currently logged in
            2. If logged in, perform logout (clear session, update database)
            3. Exit application with code 0

        Side Effects:
            - Calls perform_logout() if user is logged in
            - Logs logout status to file_log
            - Exits application via self.exit(0)

        Note:
            The logout process clears the user session from the database
            and resets app_state to guest mode. This ensures clean session
            management and prevents orphaned sessions.

        See Also:
            fiwa_cli.functions.logout_util.perform_logout: Shared logout utility
        """
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
        """Toggle between dark and light themes.

        This action is bound to the 'd' key. It switches the application
        theme between "textual-dark" and "textual-light".

        Side Effects:
            - Changes self.theme attribute
            - Triggers automatic re-render with new theme

        Note:
            The theme change affects all screens and widgets immediately.
        """
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"

    def action_open_menu(self) -> None:
        """Open the main application menu.

        This action is bound to the 'm' key. It opens a modal menu screen
        with navigation options for all major application sections.

        Side Effects:
            - Pushes MenuScreen onto the screen stack
            - Displays modal menu overlay

        See Also:
            fiwa_cli.screens.menu.MenuScreen: Menu screen implementation
        """
        from fiwa_cli.screens.menu import MenuScreen

        self.push_screen(MenuScreen())

    def action_open_settings(self) -> None:
        """Open the settings screen.

        This action is bound to the 's' key. Opens the settings screen
        where users can manage projects, users, labels, and preferences.

        Side Effects:
            - Pushes SettingsScreen onto the screen stack

        See Also:
            fiwa_cli.screens.settings.SettingsScreen: Settings screen implementation
        """
        from fiwa_cli.screens.settings import SettingsScreen

        self.push_screen(SettingsScreen())

    def action_open_expenses(self) -> None:
        """Open the expenses/inputs screen.

        This action is bound to the 'e' key. Opens the screen where users
        can add, edit, and view expense transactions.

        Side Effects:
            - Pushes InputsScreen onto the screen stack

        See Also:
            fiwa_cli.screens.inputs.InputsScreen: Inputs screen implementation
        """
        from fiwa_cli.screens.inputs import InputsScreen

        self.push_screen(InputsScreen())

    def action_open_reports(self) -> None:
        """Open the reports screen.

        This action is bound to the 'r' key. Opens the reporting interface
        where users can view expense summaries, charts, and analytics.

        Side Effects:
            - Pushes ReportsScreen onto the screen stack

        See Also:
            fiwa_cli.screens.reports.ReportsScreen: Reports screen implementation
        """
        from fiwa_cli.screens.reports import ReportsScreen

        self.push_screen(ReportsScreen())

    def action_select_project(self) -> None:
        """Open the project selector screen.

        This action is bound to the 'p' key. Opens a modal screen where
        users can switch between their available projects.

        Side Effects:
            - Pushes ProjectSelectorScreen onto the screen stack
            - When user selects a project, app_state is updated

        See Also:
            fiwa_cli.screens.project_selector.ProjectSelectorScreen: Project selector
        """
        from fiwa_cli.screens.project_selector import ProjectSelectorScreen

        self.push_screen(ProjectSelectorScreen())


def main():
    """Main entry point for the FiWa CLI application.

    This function serves as the command-line entry point for the application.
    It handles argument parsing, initialization, user authentication, and
    application startup.

    Command-line modes supported:
        - **init**: Initialize a new FiWa data directory with schema and defaults
        - **run**: Run the FiWa application (requires existing data directory)

    Process Flow:
        1. Parse command-line arguments (mode, path, user, etc.)
        2. Get absolute path to package installation
        3. If mode is "init":
           - Create data directory and database schema
           - Initialize default data
           - Exit
        4. If mode is "run":
           - Prompt for password if --user specified
           - Setup FiWa configuration and database
           - Create and run MyApp instance

    Command-line Arguments:
        Handled by handle_args() which supports:
            - run: Start the application
              ``fiwa run --path /data/dir --user username``
            - init: Initialize new data directory
              ``fiwa init --path /data/dir``

    Example:
        Initialize new FiWa installation::

            $ fiwa init --path /home/user/fiwa-data

        Run with specific user::

            $ fiwa run --path /home/user/fiwa-data --user batman
            Enter password for user batman: ****

        Run without user (login via UI)::

            $ fiwa run --path /home/user/fiwa-data

    Environment:
        The function uses:
            - stdin: For password input via getpass
            - stdout: For status messages
            - exit codes: 0 for success

    Side Effects:
        - May create directories and files in the specified --path
        - Prompts for password if --user is specified
        - Writes to fiwa.log in the data directory
        - May modify database in the data directory

    Raises:
        SystemExit: Always exits with code 0 on success

    Note:
        This function should only be called from the command line entry point.
        For programmatic usage, instantiate MyApp directly.

    See Also:
        handle_args(): Command-line argument parsing
        setup_fiwa(): Application configuration and initialization
        prep_fiwa(): Data directory initialization for 'init' mode
        MyApp: Main application class
    """
    import os
    import getpass

    _mode, _conf = handle_args()

    abs_path = get_abs_path()  # the abs path to your package installation!

    if _mode == "init":
        # prepares the FiWa environment based on the mode (e.g., init or run)
        prep_fiwa(mode=_mode, config=_conf)
        exit(0)

    elif _mode == "run":
        if "user" in _conf and _conf["user"] is not None:
            print(f"Running FiWa as user: {_conf['user']}")
            pw = getpass.getpass(prompt=f"Enter password for user {_conf['user']}: ")
            _conf["password"] = pw
        else:
            print("No user specified. Running FiWa without user authentication.")

        config = setup_fiwa(
            abs_path=abs_path, config=_conf
        )  # Initialize FiWa with the loaded config
        app = MyApp(config=config)

        # Get log file path from app's configuration
        log_file = app._log_file_path
        print(f"Starting app with logging to: {log_file}")

        # Run with textual devtools logging
        # Use textual run command: textual run --dev main.py to see logs in console
        # Or use app.run() and logs go to the file via self.log()
        try:
            # Run the app - Textual's built-in logging will handle file writes
            app.run()
        finally:
            # On exit, log the shutdown
            print(f"App closed. Logs saved to: {log_file}")

        exit(0)

    exit()


if __name__ == "__main__":
    main()
