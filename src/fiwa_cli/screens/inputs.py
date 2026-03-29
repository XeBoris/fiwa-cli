"""Inputs screen - main interface for expense/transaction management.

This module provides the central hub for all expense-related operations,
featuring a sidebar with quick actions and a content area for different
input modes (add new, edit existing, replicate recurring).

The inputs screen follows the same sidebar/content pattern as Settings and
Reports screens for consistent UX. It integrates the WeekMonthWidget for
period selection that affects the edit view.

Key Features:
    - Quick action buttons for common tasks (New, Edit, Replicate)
    - Period selection widget (week/month picker)
    - Dynamic content area loading different forms
    - Integration with ItemInputForm for expense creation
    - Integration with EditExpenseView for expense editing
    - Integration with ReplicateExpensesView for recurring expenses

Screen Modes:
    - **New**: Create new expense/transaction (CreateExpenseForm)
    - **Edit**: View and edit existing expenses (EditExpenseView)
    - **Replicate**: Project recurring expenses to next month (ReplicateExpensesView)

Classes:
    InputsScreen: Main inputs screen with sidebar navigation

Example:
    Opening the inputs screen::

        >>> from fiwa_cli.screens.inputs import InputsScreen
        >>> self.app.push_screen(InputsScreen())

    Or using keyboard shortcut 'E' from main screen.

    Adding a new expense::

        >>> # User presses 'E' key
        >>> # InputsScreen opens
        >>> # User clicks "New" button
        >>> # CreateExpenseForm loaded in content area
        >>> # User fills form and saves
        >>> # Expense written to database

See Also:
    inputs_insert_expense: New expense creation form
    inputs_edit_expense: Expense editing interface
    inputs_repl_expenses: Recurring expense replication
    components.item_input_form: Core expense input widget
"""

from textual.containers import (
    Vertical,
    Horizontal,
    ScrollableContainer,
    Grid,
    VerticalScroll,
    Container,
)
from textual.widgets import Static, Button, Select
from textual.app import ComposeResult

import datetime
import json
from fiwa_cli.components import FiwaHeader
from fiwa_cli.functions.loader import load_dynamic_css
from fiwa_cli.components.week_month_picker import WeekMonthWidget

from .base import ReactiveScreen
from .inputs_insert_expense import CreateExpenseForm
from .inputs_edit_expense import EditExpenseView
from .inputs_repl_expenses import ReplicateExpensesView


class InputsScreen(ReactiveScreen):
    """Main inputs screen for expense and transaction management.

    This screen provides a centralized interface for all expense-related
    operations with a sidebar for quick actions and navigation, and a
    dynamic content area that displays different forms based on the
    selected action.

    The screen manages three primary operations:
        1. **New**: Add new expenses/transactions
        2. **Edit**: View and modify existing expenses
        3. **Replicate**: Project recurring expenses to future months

    Attributes:
        _mounted (bool): Flag indicating if screen is fully mounted
        _current_period_type (str): "week" or "month"
        _current_year (int): Currently selected year
        _current_week (int): Currently selected week number (1-53)
        _current_month (int): Currently selected month (1-12)
        _month_start (int): Day of month for period boundaries (from project_store)

    Layout Structure:
        Container (container-body)
        ├── ScrollableContainer (container-sidebar)
        │   ├── Static ("Quick Actions")
        │   ├── Button ("New")
        │   ├── Button ("Edit")
        │   ├── Static ("Period")
        │   ├── WeekMonthWidget (date picker)
        │   ├── Button ("Replicate")
        │   └── Button ("Back")
        └── ScrollableContainer (inputs-content-area)
            └── Dynamic content (forms)

    Sidebar Components:
        **Quick Actions (top)**:
            - New: Opens CreateExpenseForm for adding expenses
            - Edit: Opens EditExpenseView with expense list and editing

        **Period Selection (middle)**:
            - WeekMonthWidget for choosing week/month
            - Affects EditExpenseView data filtering

        **Advanced Actions (below period)**:
            - Replicate: Opens ReplicateExpensesView for recurring expenses

        **Navigation (bottom)**:
            - Back: Returns to main screen

    Content Area Forms:
        - **CreateExpenseForm**: New expense entry with:
          - Item details (name, price, date)
          - Label selection
          - Cost sharing between users
          - Exchange rate handling

        - **EditExpenseView**: Tabbed expense editor with:
          - DataTable of all expenses in period
          - Per-user tabs
          - Inline editing capabilities
          - Delete functionality

        - **ReplicateExpensesView**: Recurring expense tool with:
          - Fixed expense selection
          - Date projection to next month
          - Batch creation workflow

    Period Integration:
        The WeekMonthWidget updates app_state with:
            - current_period_type: "week" or "month"
            - current_period_start: ISO date string (inclusive)
            - current_period_end: ISO date string (exclusive)

        These values are used by EditExpenseView to filter displayed
        expenses to the selected period.

    Example:
        Basic usage::

            >>> from fiwa_cli.screens.inputs import InputsScreen
            >>> self.app.push_screen(InputsScreen())

        Adding new expense workflow::

            >>> # User presses 'E' key (or clicks Expenses in menu)
            >>> # InputsScreen opens
            >>> # User clicks "New" button
            >>> # CreateExpenseForm appears in content area
            >>> # User fills: Name="Groceries", Price=50, Currency=USD
            >>> # User selects labels, sets date
            >>> # User clicks Save
            >>> # ItemInputForm validates and shows confirmation modal
            >>> # User confirms, expense written to database

        Editing expense workflow::

            >>> # User clicks "Edit" button
            >>> # EditExpenseView appears with tabbed interface
            >>> # User selects their tab
            >>> # DataTable shows all expenses in current period
            >>> # User clicks expense row
            >>> # Inline editor opens
            >>> # User modifies price/date/labels
            >>> # User saves, database updated

        Replicating expenses workflow::

            >>> # User clicks "Replicate" button
            >>> # ReplicateExpensesView appears
            >>> # Shows all "fixed" expenses in current month
            >>> # User selects which to project forward
            >>> # User clicks "Update to Next Month"
            >>> # Dates adjusted, preview shown
            >>> # User clicks "Write to Database"
            >>> # New expenses created for next month

    Note:
        The period selection (WeekMonthWidget) only affects the Edit view.
        The New and Replicate views are not period-dependent.

        All forms are mounted dynamically in the content area, allowing
        clean separation of concerns and efficient resource usage.

    See Also:
        inputs_insert_expense.CreateExpenseForm: New expense form
        inputs_edit_expense.EditExpenseView: Expense editing interface
        inputs_repl_expenses.ReplicateExpensesView: Recurring expense tool
        components.item_input_form.ItemInputForm: Core input widget
        components.week_month_picker.WeekMonthWidget: Period selector
    """

    def __init__(self, *args, **kwargs):
        """Initialize the inputs screen.

        Sets up period tracking with current date as default and loads
        month_start configuration from project_store.

        Args:
            *args: Positional arguments passed to parent ReactiveScreen
            **kwargs: Keyword arguments passed to parent ReactiveScreen

        Side Effects:
            - Sets _mounted to False
            - Initializes period tracking variables
            - Loads _month_start from project_store (defaults to 1)

        Note:
            The month_start value affects monthly period calculations
            in the EditExpenseView.
        """
        super().__init__(*args, **kwargs)
        self._mounted = False

        # Initialize period tracking
        self._current_period_type = "week"  # "week" or "month"
        self._current_year = datetime.date.today().year
        self._current_week = datetime.date.today().isocalendar()[1]
        self._current_month = datetime.date.today().month
        try:
            self._month_start = json.loads(self.app.app_state["project_store"])
        except Exception:
            self._month_start = {}
        self._month_start = int(self._month_start.get("month_start", "1"))

    # DEFAULT_CSS = ""

    def compose(self) -> ComposeResult:
        """Compose the inputs screen layout with sidebar and content area.

        Creates a two-column layout with sidebar navigation and dynamic
        content area for different expense management forms.

        Yields:
            FiwaHeader: Application header with user and project info
            Container: Main body container with:
                - ScrollableContainer: Sidebar with action buttons and period picker
                - ScrollableContainer: Content area for forms

        Layout:
            - If logged in: Shows all action buttons and period picker
            - If not logged in: Shows login prompt

        Note:
            The WeekMonthWidget in sidebar bubbles up PeriodChanged events
            that update the EditExpenseView data filtering.
        """
        yield FiwaHeader(
            user=self.app.app_state["user_name"],
            projects=self.app.app_state["project_names"],
            project_id=self.app.app_state["project_id"],
            project_ids=self.app.app_state["project_ids"],
        )

        with Container(id="container-body"):
            with ScrollableContainer(id="container-sidebar"):
                if self.app.app_state["is_logged_in"] is True:
                    yield Static("Quick Actions", classes="menu-section")
                    yield Button(
                        "New",
                        id="new-item-button",
                        classes="sidebar-menu-button",
                        compact=True,
                        flat=True,
                    )
                    yield Button(
                        "Edit",
                        id="edit-item-button",
                        classes="sidebar-menu-button",
                        compact=True,
                        flat=True,
                    )

                    yield Static("Period", classes="menu-section")

                    # Week/Month picker widget (includes dropdown and navigation)
                    yield WeekMonthWidget(id="reports-date-picker")
                    yield Button(
                        "Replicate",
                        id="replicate-button",
                        classes="sidebar-menu-button",
                        compact=True,
                        flat=True,
                    )
                # Always show Back button
                yield Button("Back", id="back-button", variant="primary")

            # Right content area with input form
            with ScrollableContainer(id="inputs-content-area"):
                # Load the EditExpenseView by default
                yield EditExpenseView()

    def on_mount(self) -> None:
        """Called when the inputs screen is mounted.

        Loads CSS, initializes period state, and displays the default view
        (edit expenses).

        Side Effects:
            - Loads screens_inputs.tcss stylesheet
            - Calls _update_app_state_period() to sync period data
            - Calls show_edit_expense_view() to display default content
            - Sets _mounted flag to True
            - Logs mount event

        Note:
            The default view (Edit) is shown automatically when the
            screen opens, using the current period from WeekMonthWidget.
        """
        super().on_mount()

        load_dynamic_css(self, "screens_inputs.tcss")

        self._mounted = True
        self.app.log("InputsScreen mounted")

        # Initialize app_state with current period
        self._update_app_state_period()

        # Initialize WeekMonthWidget with current values
        try:
            week_month_widget = self.query_one(WeekMonthWidget)
            week_month_widget.period_type = self._current_period_type
            week_month_widget.current_year = self._current_year
            week_month_widget.current_week = self._current_week
            week_month_widget.current_month = self._current_month
            week_month_widget.update_display()
            self.app.log("WeekMonthWidget initialized")
        except Exception as e:
            self.app.log(f"Could not initialize WeekMonthWidget: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle sidebar button clicks for navigation and form selection.

        Routes button clicks to show different forms or navigate back.

        Args:
            event: Button.Pressed event containing the clicked button

        Handles:
            - new-item-button: Shows CreateExpenseForm
            - edit-item-button: Shows EditExpenseView
            - replicate-button: Shows ReplicateExpensesView
            - menu-back-button: Returns to main screen

        Side Effects:
            - Calls show_* methods to load forms
            - Pops screen if back button clicked

        Example:
            >>> # User clicks "New" button
            >>> # on_button_pressed fires
            >>> # show_create_input_form() called
            >>> # CreateExpenseForm mounted
        """
        if event.button.id == "back-button":
            self._return_to_main_screen()
        elif event.button.id == "new-item-button":
            self.show_create_input_form()
        elif event.button.id == "edit-item-button":
            self.show_edit_expense_view()
        elif event.button.id == "view-recent-button":
            self.app.notify("View Recent - Coming soon!", severity="info")
        elif event.button.id == "import-csv-button":
            self.app.notify("Import CSV - Coming soon!", severity="info")
        elif event.button.id == "replicate-button":
            self.show_replicate_view()

    def on_week_month_widget_period_changed(self, message: WeekMonthWidget.PeriodChanged) -> None:
        """Handle period changes from WeekMonthWidget.

        Updates internal period state and refreshes the EditExpenseView
        to show expenses for the new period.

        Args:
            message: PeriodChanged message containing:
                - period_type: "week" or "month"
                - year: Selected year
                - week: Selected week (if type=week)
                - month: Selected month (if type=month)

        Side Effects:
            - Updates _current_period_type, _current_year, etc.
            - Calls _update_app_state_period() to update app_state
            - Calls _refresh_data_tables() to reload EditExpenseView
            - Logs period change

        Note:
            Period changes only affect EditExpenseView (not New or Replicate).
        """
        # Update internal state from widget
        self._current_period_type = message.period_type
        self._current_year = message.year
        if message.week is not None:
            self._current_week = message.week
        if message.month is not None:
            self._current_month = message.month

        self.app.log(
            f"WeekMonthWidget period changed: {message.period_type} "
            + f"Year {message.year}, Week {message.week}, Month {message.month}"
        )

        # Update app_state and refresh data tables
        self._update_app_state_period()

    def show_create_input_form(self) -> None:
        """Show the CreateExpenseForm in the content area.

        Clears current content and mounts the expense creation form.

        Side Effects:
            - Removes all children from inputs-content-area
            - Mounts CreateExpenseForm widget
            - Logs form loading
        """
        content_area = self.query_one("#inputs-content-area", ScrollableContainer)
        content_area.remove_children()
        content_area.mount(CreateExpenseForm())

    def show_edit_expense_view(self) -> None:
        """Show the EditExpenseView in the content area.

        Clears current content and mounts the expense editing interface.

        Side Effects:
            - Removes all children from inputs-content-area
            - Mounts EditExpenseView widget
            - Logs view loading
        """
        content_area = self.query_one("#inputs-content-area", ScrollableContainer)
        content_area.remove_children()
        content_area.mount(EditExpenseView())

    def show_replicate_view(self) -> None:
        """Show the ReplicateExpensesView in the content area.

        Clears current content and mounts the recurring expense replication tool.

        Side Effects:
            - Removes all children from inputs-content-area
            - Mounts ReplicateExpensesView widget
            - Logs view loading
        """
        content_area = self.query_one("#inputs-content-area", ScrollableContainer)
        content_area.remove_children()
        content_area.mount(ReplicateExpensesView())

    def on_item_input_form_item_created(self, message) -> None:
        """Handle ItemCreated message from CreateExpenseForm.

        Called when a new expense is successfully created and saved to
        the database. Refreshes the EditExpenseView to show the new item.

        Args:
            message: ItemCreated message containing item_data

        Side Effects:
            - Calls _refresh_data_tables() to reload EditExpenseView
            - Shows success notification
            - Logs item creation

        Note:
            This ensures the newly created expense appears immediately
            in the Edit view without requiring manual refresh.
        """
        try:
            self.app.log(f"Item created with ID {message.item_id}, refreshing tables...")

            # Try to find EditExpenseView and refresh its tables
            try:
                edit_view = self.query_one(EditExpenseView)
                edit_view.refresh_tables()
                self.app.log("EditExpenseView tables refreshed successfully")
            except Exception:
                self.app.log("EditExpenseView not currently displayed, skipping refresh")

        except Exception as e:
            self.app.log(f"Error handling ItemCreated message: {e}")

    def _return_to_main_screen(self) -> None:
        """Return to the main application screen.

        Pops all screens from the stack except the base screen.

        Side Effects:
            - Pops screens until only main screen remains
            - Logs navigation

        Note:
            Uses a loop to handle deeply nested screen stacks.
        """
        try:
            while len(self.app.screen_stack) > 1:
                self.app.pop_screen()
        except Exception as e:
            self.app.log(f"Error returning to main screen: {e}")

    def _update_app_state_period(self) -> None:
        """Update app_state with current period selection.

        Calculates period_start and period_end dates based on the current
        period type (week/month) and selection, then updates app_state.

        For weekly periods:
            - Uses ISO week numbers (1-53)
            - Calculates Monday-Sunday range

        For monthly periods:
            - Respects month_start from project_store
            - Example: month_start=15 means period is 15th to 14th

        Side Effects:
            - Updates app_state with period information
            - Calls _refresh_data_tables() to reload expense data
            - Logs period update

        Note:
            This method is called when WeekMonthWidget period changes.
        """
        try:
            # Calculate date range based on period type
            if self._current_period_type == "week":
                # Calculate week boundaries
                from fiwa_cli.functions.compute_time import TimeClass

                tc = TimeClass(country_code="DE")
                week_info = tc.cmp_week_by_number(self._current_year, self._current_week)

                period_start = week_info["week_beg"]
                period_end = week_info["week_end"]
                period_end += datetime.timedelta(days=1)  # Include the end date in the range
                period_label = f"{self._current_year} Week {self._current_week}"
            else:  # month
                # Calculate month boundaries
                from fiwa_cli.functions.compute_time import TimeClass

                tc = TimeClass(country_code="DE")

                month_info = tc.cmp_month_by_number(
                    self._current_year, self._current_month, self._month_start
                )

                period_start = month_info["month_beg"]
                period_end = month_info["month_end"]
                period_label = f"{self._current_year} {month_info['month_name']}"

            # Update app_state with period information
            self.app.app_state["current_period_type"] = self._current_period_type
            self.app.app_state["current_period_year"] = self._current_year
            self.app.app_state["current_period_week"] = self._current_week
            self.app.app_state["current_period_month"] = self._current_month
            self.app.app_state["current_period_start"] = period_start
            self.app.app_state["current_period_end"] = period_end
            self.app.app_state["current_period_label"] = period_label

            self.app.log(
                f"Updated app_state period: {period_label} ({period_start} to {period_end})"
            )

            # Refresh the data tables with new period data
            self._refresh_data_tables()

        except Exception as e:
            self.app.log(f"Error updating app_state period: {e}")

    def _refresh_data_tables(self) -> None:
        """Refresh data tables in the EditExpenseView.

        Finds the EditExpenseView widget (if mounted) and calls its
        refresh_data() method to reload expenses for the new period.

        Side Effects:
            - Calls EditExpenseView.refresh_data() if found
            - Logs refresh operation

        Note:
            Only affects EditExpenseView - New and Replicate views
            are not period-dependent.
        """
        try:
            # Try to find EditExpenseView in the content area
            edit_view = self.query_one(EditExpenseView)
            edit_view.refresh_tables()
            self.app.log("Refreshed EditExpenseView tables")
        except Exception:
            # EditExpenseView not loaded, try ReplicateExpensesView
            try:
                replicate_view = self.query_one(ReplicateExpensesView)
                replicate_view.refresh_data()
                self.app.log("Refreshed ReplicateExpensesView")
            except Exception as e:
                self.app.log(f"Could not refresh tables (no active view found): {e}")

    def update_displays(self) -> None:
        """Update any display widgets with current app_state.

        Placeholder for future reactive display updates.

        Note:
            Currently not used, reserved for future enhancements.
        """
        try:
            # Update header
            header = self.query_one(FiwaHeader)
            header.user = self.app.app_state["user_name"]
            header.projects = self.app.app_state["project_names"]
            header.project_id = self.app.app_state["project_id"]
            header.project_ids = self.app.app_state["project_ids"]
        except Exception as e:
            self.app.log(f"Error updating header: {e}")
