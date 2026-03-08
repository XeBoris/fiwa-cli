"""Inputs screen - add transactions and items."""
from textual.containers import Vertical, Horizontal, ScrollableContainer, Grid, VerticalScroll, Container
from textual.widgets import Static, Button, Select
from textual.app import ComposeResult

import datetime

from fiwa.components import FiwaHeader
from fiwa.functions.loader import load_dynamic_css
from fiwa.components.week_month_picker import WeekMonthWidget

from .base import ReactiveScreen
from .inputs_insert_expense import CreateExpenseForm
from .inputs_edit_expense import EditExpenseView


class InputsScreen(ReactiveScreen):
    """Inputs screen - add transactions and items."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mounted = False

        # Initialize period tracking
        self._current_period_type = "week"  # "week" or "month"
        self._current_year = datetime.date.today().year
        self._current_week = datetime.date.today().isocalendar()[1]
        self._current_month = datetime.date.today().month

    # DEFAULT_CSS = ""

    def compose(self) -> ComposeResult:
        yield FiwaHeader(
            user=self.app.app_state["user_name"],
            projects=self.app.app_state["project_names"],
            project_id=self.app.app_state["project_id"],
            project_ids=self.app.app_state["project_ids"]
        )

        with Container(id="container-body"):
            with ScrollableContainer(id="container-sidebar"):
                yield Static("Quick Actions", classes="menu-section")
                yield Button("New",
                             id="new-item-button",
                             classes="sidebar-menu-button",
                             compact=True, flat=True)
                yield Button("Edit",
                             id="edit-item-button",
                             classes="sidebar-menu-button",
                             compact=True, flat=True)

                yield Static("Period", classes="menu-section")

                # Week/Month picker widget (includes dropdown and navigation)
                yield WeekMonthWidget()




                # yield Button("View Recent", id="view-recent-button", variant="default")
                # yield Button("Import CSV", id="import-csv-button", variant="default")
                #
                # yield Static("Statistics", classes="menu-section")
                # yield Static("[bold]Today:[/bold] 0 items", classes="info-row")
                # yield Static("[bold]This Month:[/bold] 0 items", classes="info-row")

                # Always show Back button
                yield Button("Back", id="back-button", variant="primary")

            # Right content area with input form
            with ScrollableContainer(id="inputs-content-area"):
                # Load the EditExpenseView by default
                yield EditExpenseView()


    def on_mount(self) -> None:
        """Called when screen is mounted."""
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
        """Handle button presses."""
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

    def on_week_month_widget_period_changed(self, message: WeekMonthWidget.PeriodChanged) -> None:
        """Handle PeriodChanged messages from WeekMonthWidget.

        Synchronizes the screen's internal state with the widget.
        """
        # Update internal state from widget
        self._current_period_type = message.period_type
        self._current_year = message.year
        if message.week is not None:
            self._current_week = message.week
        if message.month is not None:
            self._current_month = message.month

        self.app.log(f"WeekMonthWidget period changed: {message.period_type} " +
                    f"Year {message.year}, Week {message.week}, Month {message.month}")

        # Update app_state and refresh data tables
        self._update_app_state_period()

    def show_create_input_form(self) -> None:
        """Show the create expense form in the content area."""
        content_area = self.query_one("#inputs-content-area", ScrollableContainer)
        content_area.remove_children()
        content_area.mount(CreateExpenseForm())

    def show_edit_expense_view(self) -> None:
        """Show the edit expense view in the content area."""
        content_area = self.query_one("#inputs-content-area", ScrollableContainer)
        content_area.remove_children()
        content_area.mount(EditExpenseView())

    def on_item_input_form_item_created(self, message) -> None:
        """Handle ItemCreated message - refresh the EditExpenseView tables."""
        try:
            self.app.log(f"Item created with ID {message.item_id}, refreshing tables...")

            # Try to find EditExpenseView and refresh its tables
            try:
                edit_view = self.query_one(EditExpenseView)
                edit_view.refresh_tables()
                self.app.log("EditExpenseView tables refreshed successfully")
            except:
                self.app.log("EditExpenseView not currently displayed, skipping refresh")

        except Exception as e:
            self.app.log(f"Error handling ItemCreated message: {e}")


    def _return_to_main_screen(self) -> None:
        """Pop all screens to return to the main screen."""
        try:
            while len(self.app.screen_stack) > 1:
                self.app.pop_screen()
        except Exception as e:
            self.app.log(f"Error returning to main screen: {e}")


    def _update_app_state_period(self) -> None:
        """Update app_state with current period selection."""
        try:
            # Calculate date range based on period type
            if self._current_period_type == "week":
                # Calculate week boundaries
                from functions.compute_time import TimeClass
                tc = TimeClass()
                week_info = tc.cmp_week_by_number(self._current_year, self._current_week)

                period_start = week_info['week_beg']
                period_end = week_info['week_end']
                period_label = f"{self._current_year} Week {self._current_week}"
            else:  # month
                # Calculate month boundaries
                from functions.compute_time import TimeClass
                tc = TimeClass()
                month_info = tc.cmp_month_by_number(self._current_year, self._current_month)

                period_start = month_info['month_beg']
                period_end = month_info['month_end']
                period_label = f"{self._current_year} {month_info['month_name']}"

            # Update app_state with period information
            self.app.app_state["current_period_type"] = self._current_period_type
            self.app.app_state["current_period_year"] = self._current_year
            self.app.app_state["current_period_week"] = self._current_week
            self.app.app_state["current_period_month"] = self._current_month
            self.app.app_state["current_period_start"] = period_start
            self.app.app_state["current_period_end"] = period_end
            self.app.app_state["current_period_label"] = period_label

            self.app.log(f"Updated app_state period: {period_label} ({period_start} to {period_end})")

            # Refresh the data tables with new period data
            self._refresh_data_tables()

        except Exception as e:
            self.app.log(f"Error updating app_state period: {e}")

    def _refresh_data_tables(self) -> None:
        """Refresh DataTables in EditExpenseView if it's currently displayed."""
        try:
            # Try to find EditExpenseView in the content area
            edit_view = self.query_one(EditExpenseView)
            edit_view.refresh_tables()
            self.app.log("Refreshed EditExpenseView tables")
        except Exception as e:
            self.app.log(f"Could not refresh tables (EditExpenseView may not be loaded): {e}")

    def update_displays(self) -> None:
        """Update displays when app_state changes."""
        try:
            # Update header
            header = self.query_one(FiwaHeader)
            header.user = self.app.app_state["user_name"]
            header.projects = self.app.app_state["project_names"]
            header.project_id = self.app.app_state["project_id"]
            header.project_ids = self.app.app_state["project_ids"]
        except Exception as e:
            self.app.log(f"Error updating header: {e}")
