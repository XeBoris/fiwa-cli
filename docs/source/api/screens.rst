Screens Module
==============

Screen and modal components for FiWa CLI.

Overview
--------

The screens module contains all full-screen views and modal dialogs used
throughout the FiWa application. Screens are organized by functionality
and follow consistent patterns for navigation and state management.

Module Organization
-------------------

.. automodule:: fiwa_cli.screens
   :members:
   :undoc-members:
   :show-inheritance:

Screens are categorized by function:

* **Main screens**: Primary application views (Settings, Reports, Inputs)
* **Modal dialogs**: Overlay screens for focused tasks
* **Form screens**: Data entry and editing interfaces
* **Utility screens**: Login, project selection, etc.

Modal Screens
-------------

Password Update Modal
~~~~~~~~~~~~~~~~~~~~~

.. automodule:: fiwa_cli.screens.password_update_modal
   :members:
   :undoc-members:
   :show-inheritance:

Secure password update dialog:

* **Three-field validation**: Current, new, confirm
* **bcrypt verification**: Current password checked against hash
* **Strength requirement**: Minimum 6 characters
* **Masked inputs**: All fields use password=True
* **Security**: No plain text storage or logging
* **User experience**: Clear error messages, retry on failure

Workflow:
    1. User clicks "Update Password" in settings
    2. Modal opens with three password fields
    3. User enters current password
    4. User enters new password twice
    5. User clicks Update
    6. System validates all inputs
    7. System verifies current password
    8. System hashes and saves new password
    9. Success notification shown
    10. Modal closes

Return Value:
    * ``True``: Password updated successfully
    * ``False``: Canceled or verification failed

Project Selection Modal
~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: fiwa_cli.screens.project_selector
   :members:
   :undoc-members:
   :show-inheritance:

Quick project switching:

* **OptionList display**: All available projects
* **Visual indicator**: Current project marked with ►
* **State updates**: project_id, currency, style, store
* **Cache refresh**: Label cache cleared and reloaded
* **Header sync**: Application header updated immediately

Keyboard Shortcut:
    Press **P** to open project selector

Main Navigation Menu
~~~~~~~~~~~~~~~~~~~~

.. automodule:: fiwa_cli.screens.menu
   :members:
   :undoc-members:
   :show-inheritance:

Dropdown navigation menu:

* **Context-aware items**: Login/Logout toggle based on state
* **Mode-specific options**: Exit (terminal) vs. Disconnect (web)
* **Quick navigation**: Access all major screens
* **Keyboard access**: 'M' key opens menu
* **Visual positioning**: Top-left dropdown from header

Menu Items:
    - Dashboard: Main overview
    - Select Project: Project switcher
    - Inputs: Expense management
    - Reports: Financial analytics
    - Settings: Configuration
    - Login/Logout: Session management (adaptive)
    - Exit/Disconnect: Application termination (mode-dependent)

Keyboard Shortcut:
    Press **M** to open navigation menu

Base Screens
------------

Base Module
~~~~~~~~~~~

.. automodule:: fiwa_cli.screens.base
   :members:
   :undoc-members:
   :show-inheritance:

The base module provides foundational classes for all screens:

ReactiveScreen
^^^^^^^^^^^^^^

Base class with automatic app_state change detection:

* **Automatic reactivity**: Watches app_state for changes
* **Update hooks**: Calls update_displays() on state changes
* **Subclass pattern**: Override update_displays() to respond
* **Efficient**: Only updates when state actually changes
* **Safe**: Exceptions don't crash app

Usage pattern::

    class MyScreen(ReactiveScreen):
        def update_displays(self):
            # Called automatically when app_state changes
            try:
                header = self.query_one(FiwaHeader)
                header.user = self.app.app_state["user_name"]
            except:
                pass  # Handle missing widgets gracefully

Screens using ReactiveScreen:
    - SettingsScreen
    - ReportsScreen
    - InputsScreen
    - DashboardScreen

LoginScreen
^^^^^^^^^^^

Dual-purpose authentication modal:

* **Login mode**: Username/password form with validation
* **Logout mode**: Current user display with logout button
* **State switching**: Different UI based on is_logged_in
* **Complete workflow**: Handles full login/logout cycle
* **Security**: bcrypt password verification, session management
* **Data loading**: Loads user info and projects on login

Login Features:
    - Username/email input
    - Masked password field
    - Credential validation
    - Session creation
    - Project loading
    - app_state population
    - Success/error notifications

Logout Features:
    - Session invalidation
    - app_state reset
    - Screen stack cleanup
    - Return to main screen

State Updates:
    Login populates 15+ app_state fields:
        - User data (name, id, scope)
        - Session data (uuid, start time)
        - Project data (ids, names, primary)
        - Currency settings
        - Config preservation

Main Application Screens
-------------------------

Settings Screen
~~~~~~~~~~~~~~~

See :doc:`settings` for complete documentation.

Features:
    * Sidebar navigation
    * Project management
    * User management
    * Label management

Reports Screen
~~~~~~~~~~~~~~

See :doc:`reports` for complete documentation.

Features:
    * Period selection
    * Cost overview
    * Repayment calculations
    * Multi-user views

Inputs Screen
~~~~~~~~~~~~~

See :doc:`inputs` for complete documentation.

Features:
    * New expense creation
    * Expense editing
    * Recurring expense replication
    * Period filtering

Keyboard Shortcuts
------------------

Global Application Shortcuts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These shortcuts work from any screen:

* **M**: Open navigation menu
* **P**: Open project selector
* **E**: Open inputs/expenses screen
* **R**: Open reports screen
* **S**: Open settings screen
* **Q**: Quit application (with logout if logged in)
* **Ctrl+C**: Quit application (with logout if logged in)

Menu Navigation Shortcuts
~~~~~~~~~~~~~~~~~~~~~~~~~~

When the menu is open:

* **↑/↓**: Navigate menu items
* **Enter**: Select highlighted item
* **Escape**: Close menu without action

Modal Dialog Shortcuts
~~~~~~~~~~~~~~~~~~~~~~~

Most modals support:

* **Escape**: Close modal (cancel action)
* **Enter**: Often triggers OK/Confirm button
* **Tab**: Navigate between input fields

Screen-Specific Shortcuts
~~~~~~~~~~~~~~~~~~~~~~~~~~

Individual screens may have additional shortcuts documented
in their respective modules. Check the BINDINGS attribute
of each screen class.

Screen Patterns
---------------

Modal Dialog Pattern
~~~~~~~~~~~~~~~~~~~~

Modal screens in FiWa follow a consistent pattern:

**Structure**::

    class MyModal(ModalScreen):
        BINDINGS = [("escape", "cancel", "Cancel")]

        def compose(self) -> ComposeResult:
            with Vertical():
                yield Static("Title")
                # ... form fields ...
                with Horizontal():
                    yield Button("OK", id="ok-button")
                    yield Button("Cancel", id="cancel-button")

        def on_button_pressed(self, event):
            if event.button.id == "ok-button":
                # Validate and process
                self.dismiss(result)
            elif event.button.id == "cancel-button":
                self.dismiss(None)

        def action_cancel(self):
            self.dismiss(None)

**Usage**::

    # Push and wait for result
    result = await self.app.push_screen_wait(MyModal())
    if result:
        # User clicked OK
        process_result(result)
    else:
        # User canceled
        pass

**Best Practices**:
    * Always include Escape key binding
    * Provide both OK and Cancel buttons
    * Validate before dismissing with result
    * Show clear error messages for validation failures
    * Keep modal focused on single task
    * Use dismiss(result) to return data

Form Screen Pattern
~~~~~~~~~~~~~~~~~~~

Form screens follow this pattern:

**Structure**::

    class MyForm(Vertical):
        class DataSubmitted(Message):
            def __init__(self, data: dict):
                self.data = data
                super().__init__()

        def compose(self) -> ComposeResult:
            yield Static("Form Title")
            # ... input fields ...
            yield Button("Save", id="save-button")

        def on_button_pressed(self, event):
            if event.button.id == "save-button":
                data = self._validate_and_collect()
                if data:
                    self.post_message(self.DataSubmitted(data))

**Benefits**:
    * Reusable within different screens
    * Message-based communication
    * Separation of concerns
    * Easy testing

Navigation Screen Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~

Screens with sidebar navigation:

**Structure**::

    class MyScreen(ReactiveScreen):
        def compose(self) -> ComposeResult:
            yield FiwaHeader(...)
            with Horizontal():
                with ScrollableContainer(id="sidebar"):
                    # Navigation buttons
                    yield Button("Option 1", id="opt1")
                    yield Button("Option 2", id="opt2")
                with ScrollableContainer(id="content-area"):
                    # Dynamic content
                    pass

        def on_button_pressed(self, event):
            if event.button.id == "opt1":
                self.show_content("Option 1")

**Examples**: SettingsScreen, ReportsScreen, InputsScreen

Common Workflows
----------------

Logging In
~~~~~~~~~~

Via menu::

    # Press 'M' to open menu
    # Select "Login"
    # Enter username and password
    # Click "Login"
    # Session created
    # Projects loaded
    # Returns to main screen as logged-in user

Programmatically::

    from fiwa_cli.screens.base import LoginScreen

    async def do_login(self):
        login = LoginScreen(is_logged_in=False)
        result = await self.app.push_screen_wait(login)
        if result and result.get("success"):
            username = result["username"]
            self.notify(f"Welcome, {username}!")

Logging Out
~~~~~~~~~~~

Via menu::

    # Press 'M' to open menu
    # Select "Logout"
    # Session cleared
    # Returns to main screen as Guest

From LoginScreen::

    login = LoginScreen(is_logged_in=True, username="batman")
    self.app.push_screen(login)
    # User clicks Logout button
    # Session cleared
    # Returns to main screen

Opening a Modal Dialog
~~~~~~~~~~~~~~~~~~~~~~

Async method (recommended)::

    async def open_password_modal(self):
        from fiwa_cli.screens.password_update_modal import PasswordUpdateModal
        modal = PasswordUpdateModal(user_id=1, username="batman")
        result = await self.app.push_screen_wait(modal)
        if result:
            self.notify("Password updated!")

Callback method::

    def open_password_modal(self):
        from fiwa_cli.screens.password_update_modal import PasswordUpdateModal
        modal = PasswordUpdateModal(user_id=1, username="batman")
        self.app.push_screen(modal, callback=self._handle_password_result)

    def _handle_password_result(self, result):
        if result:
            self.notify("Password updated!")

Switching Projects
~~~~~~~~~~~~~~~~~~

From any screen::

    # Press 'P' key
    # Project selector opens
    # Select project from list
    # app_state updates automatically
    # All screens reflect new project

Programmatically::

    from fiwa_cli.screens.project_selector import ProjectSelectorScreen
    self.app.push_screen(ProjectSelectorScreen())

Using the Menu
~~~~~~~~~~~~~~

Open menu with keyboard::

    # Press 'M' key from any screen
    # Menu opens in top-left corner
    # Use ↑/↓ to navigate
    # Press Enter to select
    # Press Escape to cancel

Navigate to Reports via menu::

    # Press 'M' to open menu
    # Navigate to "Reports"
    # Press Enter
    # Menu closes
    # Reports screen opens

Logout via menu::

    # Press 'M' to open menu
    # Menu shows "Logout" (if logged in)
    # Select "Logout"
    # Session cleared
    # Returns to main screen
    # Next menu shows "Login"

Programmatically::

    from fiwa_cli.screens.menu import MenuScreen
    self.app.push_screen(MenuScreen())

Navigating Screens
~~~~~~~~~~~~~~~~~~

Push screen onto stack::

    from fiwa_cli.screens.settings import SettingsScreen
    self.app.push_screen(SettingsScreen())

Pop current screen::

    self.app.pop_screen()

Return to main screen::

    while len(self.app.screen_stack) > 1:
        self.app.pop_screen()

Best Practices
--------------

Modal Dialogs
~~~~~~~~~~~~~

* Keep modals focused on single task
* Always provide Cancel/Escape option
* Validate before dismissing with data
* Show clear error messages inline
* Return meaningful results (not just True/False)
* Don't nest modals too deeply

Form Screens
~~~~~~~~~~~~

* Use Messages for parent communication
* Validate inputs before posting messages
* Provide clear field labels and placeholders
* Show validation errors near relevant fields
* Implement Reset button for complex forms
* Save state on successful submission

Navigation Screens
~~~~~~~~~~~~~~~~~~

* Maintain consistent sidebar width
* Use ScrollableContainer for content
* Update content area dynamically
* Preserve user's position when refreshing
* Show active menu item visually
* Provide clear back/exit option

State Management
~~~~~~~~~~~~~~~~

* Use app_state for global application state
* Use reactive variables for screen-local state
* Watch app_state changes for automatic updates
* Update app_state atomically (all related fields together)
* Don't store sensitive data in app_state
* Clear transient state on screen exit

Troubleshooting
---------------

Modal Not Opening
~~~~~~~~~~~~~~~~~

* Check if another modal is already open
* Verify modal class imported correctly
* Check for errors in compose() method
* Review logs for exceptions

Modal Won't Close
~~~~~~~~~~~~~~~~~

* Ensure dismiss() is called
* Check if dismiss() is in except block (may be skipped)
* Verify no infinite loops in validation
* Use action_cancel() for Escape key

Screen Stack Errors
~~~~~~~~~~~~~~~~~~~

* "Can't pop screen" - At base screen already
* Use screen_stack check before popping
* Don't pop in on_mount() or compose()
* Return to main with while loop

Password Update Issues
~~~~~~~~~~~~~~~~~~~~~~

* **"Current password is incorrect"**
  - Verify you're entering the right password
  - Check caps lock is off
  - Try resetting password via admin

* **"New passwords do not match!"**
  - Retype both new password fields
  - Copy/paste may not work with masked fields
  - Type carefully, passwords are hidden

* **"Must be at least 6 characters long"**
  - Choose a longer password
  - Consider using passphrase
  - Add numbers or special characters

See Also
--------

* :doc:`settings`: Settings screens and workflows
* :doc:`reports`: Reports screens and analytics
* :doc:`inputs`: Input and expense screens
* :doc:`main`: Main application

