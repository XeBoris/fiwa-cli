"""Main navigation menu for FiWa CLI.

This module provides the dropdown menu interface accessible from the
application header. The menu offers quick navigation to all major screens
and system functions like login/logout and exit.

The menu adapts based on:
    - Login state (shows "Login" or "Logout")
    - Application mode (terminal shows "Exit", web shows "Disconnect")
    - Current context (highlights available actions)

Key Features:
    - Modal dropdown menu from header
    - Context-aware menu items (Login/Logout toggle)
    - Mode-specific options (Exit vs. Disconnect)
    - Quick navigation to all major screens
    - Keyboard shortcuts for all items
    - Dismissible with Escape key

Menu Items:
    - **Dashboard**: Main overview screen
    - **Select Project**: Project switching modal
    - **Inputs**: Expense management screens
    - **Reports**: Financial reports and analytics
    - **Settings**: Configuration and management
    - **Login/Logout**: Session management (context-aware)
    - **---**: Visual separator (disabled)
    - **Exit/Disconnect**: Application termination (mode-dependent)

Classes:
    MenuScreen: Main dropdown menu modal

Example:
    Opening the menu::

        >>> from fiwa_cli.screens.menu import MenuScreen
        >>> self.app.push_screen(MenuScreen())

    Or using keyboard shortcut 'M' from any screen.

    User workflow::

        >>> # User presses 'M' key (or clicks menu in header)
        >>> # MenuScreen opens as modal dropdown
        >>> # Menu displays:
        >>> #   Dashboard
        >>> #   Select Project
        >>> #   Inputs
        >>> #   Reports
        >>> #   Settings
        >>> #   Logout              (if logged in)
        >>> #   ---
        >>> #   Exit                (terminal mode)
        >>> # User clicks "Reports"
        >>> # Menu dismisses
        >>> # ReportsScreen opens

    Login state awareness::

        >>> # User not logged in
        >>> # Menu shows: "Login"
        >>> # User clicks "Login"
        >>> # Menu dismisses
        >>> # LoginScreen opens
        >>> # --- After login ---
        >>> # User opens menu again
        >>> # Menu now shows: "Logout"
        >>> # User clicks "Logout"
        >>> # perform_logout() executes
        >>> # Session cleared
        >>> # Returns to main screen

See Also:
    components.header.FiwaHeader: Header with menu button
    main.MyApp: Keyboard binding 'M' for menu
    functions.logout_util.perform_logout: Shared logout logic
"""
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Static, OptionList
from textual.widgets.option_list import Option
from textual.app import ComposeResult

from fiwa_cli.functions.logout_util import perform_logout


class MenuScreen(ModalScreen):
    """Modal dropdown menu for application navigation.

    This modal screen provides a comprehensive navigation menu accessible
    from the application header. It offers quick access to all major
    screens and system functions.

    The menu is context-aware and adapts based on:
        - Login state: Shows "Login" or "Logout" accordingly
        - Application mode: Terminal shows "Exit", web shows "Disconnect"
        - User permissions: Future - may hide restricted items

    Attributes:
        None (reads from app_state and app._mode)

    BINDINGS:
        - Escape: Dismiss menu without action

    Menu Structure:
        Navigation Items (top):
            - Dashboard: Return to main overview
            - Select Project: Open project switcher
            - Inputs: Expense management
            - Reports: Financial analytics
            - Settings: Configuration

        Session Management (middle):
            - Login/Logout: Context-aware session control

        Separator:
            - --- (disabled, visual only)

        System Actions (bottom):
            - Exit (terminal mode): Close application
            - Disconnect (web mode): End web session

    Menu Item IDs:
        - menu-dashboard: Dashboard screen
        - menu-select-project: Project selector modal
        - menu-inputs: Inputs screen
        - menu-report: Reports screen
        - menu-settings: Settings screen
        - menu-login: Login/Logout (context-dependent)
        - menu-exit: Exit application (terminal)
        - menu-disconnect: Disconnect session (web)

    Navigation Flow:
        1. User opens menu (M key or header button)
        2. Modal appears in top-left corner
        3. User selects option (keyboard or mouse)
        4. Menu dismisses
        5. Selected screen opens or action executes

    Login/Logout Logic:
        The menu dynamically shows either "Login" or "Logout":
            - If is_logged_in == False: Shows "Login"
              → Clicking opens LoginScreen
            - If is_logged_in == True: Shows "Logout"
              → Clicking calls perform_logout()

    Exit/Disconnect Logic:
        The last menu item adapts to application mode:
            - Terminal mode (app._mode == "terminal"):
              → Shows "Exit"
              → Clicking calls app.exit(0)
            - Web mode (app._mode == "web"):
              → Shows "Disconnect"
              → Clicking ends web session (future implementation)

    Example:
        Basic usage::

            >>> from fiwa_cli.screens.menu import MenuScreen
            >>> self.app.push_screen(MenuScreen())

        User navigates to Reports::

            >>> # User presses 'M' key
            >>> # MenuScreen opens
            >>> # User presses ↓ to "Reports"
            >>> # User presses Enter
            >>> # on_option_list_option_selected() fires
            >>> # option_id = "menu-report"
            >>> # Menu dismisses
            >>> # ReportsScreen pushed onto stack
            >>> # User now sees reports interface

        User logs out::

            >>> # User logged in as "batman"
            >>> # User opens menu
            >>> # Menu shows "Logout" (not "Login")
            >>> # User clicks "Logout"
            >>> # _perform_logout() called
            >>> # perform_logout(app) executes:
            >>> #   - Clears session in database
            >>> #   - Updates app_state (is_logged_in = False)
            >>> #   - Clears sensitive state data
            >>> #   - Reloads css_form, css_theme, abs_path from config
            >>> # Menu dismisses
            >>> # Returns to main screen
            >>> # Next time menu opens, shows "Login"

        Terminal mode exit::

            >>> # User in terminal application
            >>> # User opens menu
            >>> # Last item: "Exit"
            >>> # User clicks "Exit"
            >>> # app.exit(0) called
            >>> # Application terminates cleanly

    CSS Styling:
        The menu uses inline CSS for:
            - Top-left alignment (align: left top)
            - 30 character width
            - Auto height based on items
            - Top-left margin (3, 0, 0, 2)
            - Themed surface background
            - Accent border
            - Max height 20 for scrolling

    Performance:
        - Lightweight: No database queries
        - Fast rendering: Simple OptionList
        - Instant dismiss: No async operations
        - Minimal state: Reads from existing app_state

    Note:
        The menu is designed to appear in the top-left corner, just
        below the header where the menu button is located. This provides
        a natural dropdown appearance.

        Screen navigation is implemented via delayed imports to avoid
        circular dependencies. Each screen is imported only when needed
        in on_option_list_option_selected().

        The logout functionality uses the shared perform_logout() utility
        to ensure consistent behavior across the application (both menu
        logout and settings logout use the same logic).

    See Also:
        components.header.FiwaHeader: Header with menu button
        main.MyApp: Keyboard binding 'M' opens menu
        functions.logout_util.perform_logout: Shared logout function
        base.LoginScreen: Login screen for authentication
    """

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
        """Compose the menu dropdown interface.

        Creates a vertical container with an OptionList containing all
        navigation items. The menu adapts based on login state and
        application mode.

        Yields:
            OptionList: Menu with 8 items:
                - Dashboard (always shown)
                - Select Project (always shown)
                - Inputs (always shown)
                - Reports (always shown)
                - Settings (always shown)
                - Login/Logout (context-dependent text)
                - --- (separator, disabled)
                - Exit/Disconnect (mode-dependent text)

        Menu Adaptation:
            **Login State**:
                - Not logged in: "Login"
                - Logged in: "Logout"

            **Application Mode**:
                - Terminal mode: "Exit"
                - Web mode: "Disconnect"

        Example:
            Terminal mode, logged in::

                Menu displays:
                    Dashboard
                    Select Project
                    Inputs
                    Reports
                    Settings
                    Logout         ← Shows "Logout" (logged in)
                    ---
                    Exit           ← Shows "Exit" (terminal mode)

            Web mode, not logged in::

                Menu displays:
                    Dashboard
                    Select Project
                    Inputs
                    Reports
                    Settings
                    Login          ← Shows "Login" (not logged in)
                    ---
                    Disconnect     ← Shows "Disconnect" (web mode)
        """
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

    def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        """Handle menu item selection and navigate to chosen screen.

        Routes the selected menu option to the appropriate action:
        opening a screen, performing logout, or exiting the application.

        Args:
            event: OptionSelected event containing the selected option

        Handles:
            - menu-dashboard: Opens DashboardScreen
            - menu-select-project: Opens ProjectSelectorScreen
            - menu-inputs: Opens InputsScreen
            - menu-report: Opens ReportsScreen
            - menu-settings: Opens SettingsScreen
            - menu-login (not logged in): Opens LoginScreen
            - menu-login (logged in): Performs logout
            - menu-exit: Exits application (terminal mode)
            - menu-disconnect: Disconnects session (web mode, future)

        Side Effects:
            - Dismisses menu modal
            - Pushes selected screen onto stack (navigation)
            - Calls app.exit(0) for terminal exit
            - Calls perform_logout() for logout
            - Shows notifications for actions

        Import Strategy:
            Screens are imported within this method (not at module level)
            to avoid circular dependencies. This allows menu.py to import
            into other screens without causing import loops.

        Example:
            User selects Dashboard::

                >>> # User clicks "Dashboard"
                >>> # option_id = "menu-dashboard"
                >>> # Menu dismisses
                >>> # DashboardScreen imported
                >>> # DashboardScreen pushed onto stack
                >>> # User sees dashboard

            User logs out::

                >>> # User logged in as "batman"
                >>> # User clicks "Logout"
                >>> # option_id = "menu-login" (same ID for both)
                >>> # is_logged_in = True (checked)
                >>> # _perform_logout() called
                >>> # perform_logout(app) executes
                >>> # Session cleared from database
                >>> # app_state updated (is_logged_in = False)
                >>> # Menu dismisses
                >>> # Returns to main screen

            User exits in terminal::

                >>> # Terminal mode
                >>> # User clicks "Exit"
                >>> # option_id = "menu-exit"
                >>> # Menu dismisses
                >>> # app.exit(0) called
                >>> # Application terminates cleanly

        Note:
            The "Login" and "Logout" options share the same ID
            (menu-login) but have different behaviors based on the
            is_logged_in state. This allows dynamic text while
            maintaining a consistent menu structure.
        """
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
            # Unhandled menu option - just dismiss
            self.app.log(f"Unhandled menu option: {option_id} with prompt: {event.option.prompt}")
            self.dismiss()

    def _perform_logout(self) -> None:
        """Perform logout operation using shared logout utility.

        Delegates to the centralized perform_logout() function to ensure
        consistent logout behavior across the application (menu logout
        and settings logout use the same implementation).

        The logout process:
            1. Clears session in database
            2. Updates app_state (is_logged_in = False)
            3. Clears sensitive user data
            4. Reloads CSS paths from config
            5. Returns to main screen

        Side Effects:
            - Calls perform_logout(app) from logout_util
            - Session cleared in database
            - app_state updated with logged-out state
            - User-specific state cleared
            - CSS configuration reloaded
            - Screen stack may be cleared

        Example:
            >>> # User clicks "Logout" in menu
            >>> # _perform_logout() called
            >>> # perform_logout(self.app) executes
            >>> # Database: UPDATE sessions SET is_logged_in = 0
            >>> # app_state["is_logged_in"] = False
            >>> # app_state["user_id"] = -1
            >>> # app_state["user_name"] = "Guest"
            >>> # CSS paths restored from config file
            >>> # Returns to main screen
            >>> # Next menu open shows "Login"

        Note:
            This method is a thin wrapper around perform_logout() to
            avoid code duplication. The shared utility ensures that
            logout works the same whether initiated from the menu or
            from the settings screen.

        See Also:
            functions.logout_util.perform_logout: Shared logout implementation
            base.LoginScreen.perform_logout: Alternative logout pathway
        """
        # Use shared logout utility to avoid code duplication
        perform_logout(self.app)

