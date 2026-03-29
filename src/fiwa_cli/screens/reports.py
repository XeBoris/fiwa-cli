"""Reports screen - financial reports and analytics with sidebar navigation.

This module provides the main reporting interface for FiWa CLI, featuring
a sidebar with period selection and report type navigation, and a main
content area that displays different report types.

The reports screen is structured similarly to the settings screen with:
    - Left sidebar: Week/Month picker and report type buttons
    - Right content area: Active report display (dynamically loaded)

Key Features:
    - Period selection (weekly or monthly) via WeekMonthWidget
    - Multiple report types (Cost Overview, Monthly Summary, etc.)
    - Sidebar navigation matching settings screen pattern
    - Real-time period updates affecting all reports
    - Integration with project_store for month_start boundaries

Report Types:
    - **Cost Overview**: Detailed expense breakdown by user (BasicReportForm)
    - **Monthly**: Monthly summary report (future)
    - **Quarterly**: Quarterly analysis (future)
    - **Yearly**: Annual overview (future)

Period Selection:
    The WeekMonthWidget in the sidebar allows users to:
        - Switch between week and month views
        - Navigate to previous/next periods
        - Jump to current period
        - Select specific weeks/months from dropdown

    Period changes automatically refresh the active report with new data.

Classes:
    ReportsScreen: Main reports screen with sidebar and content management

Example:
    Opening the reports screen::

        >>> from fiwa_cli.screens.reports import ReportsScreen
        >>> self.app.push_screen(ReportsScreen())

    Or using keyboard shortcut 'R' from main screen.

    Changing period::

        >>> # User clicks WeekMonthWidget
        >>> # Selects "March 2026"
        >>> # on_week_month_picker_period_changed fires
        >>> # Updates app_state with new period_start/period_end
        >>> # Active report refreshes with new data

See Also:
    reports_basic: Basic cost overview report implementation
    components.week_month_picker: Period selection widget
    settings: Settings screen with similar sidebar pattern
"""
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Button
from textual.app import ComposeResult
from fiwa_cli.components import FiwaHeader
from fiwa_cli.components.week_month_picker import WeekMonthWidget

from .reports_basic import BasicReportForm

from fiwa_cli.functions.loader import load_dynamic_css

from .base import ReactiveScreen
import datetime
import json
#from datetime import datetime, timedelta



class ReportsScreen(ReactiveScreen):
    """Main reports screen with sidebar navigation and dynamic content area.

    This screen provides a comprehensive reporting interface with period
    selection and multiple report types. It follows the same two-column
    layout pattern as SettingsScreen for consistent UX.

    The screen manages:
        - Period selection via WeekMonthWidget
        - Report type navigation via sidebar buttons
        - Dynamic report loading in content area
        - Period state synchronization with app_state
        - Automatic report refresh on period changes

    Attributes:
        _last_login_state (bool): Cached login state to detect changes
        _mounted (bool): Flag indicating if screen is fully mounted
        _current_period_type (str): "week" or "month"
        _current_year (int): Currently selected year
        _current_week (int): Currently selected week number (1-53)
        _current_month (int): Currently selected month (1-12)
        _month_start (int): Day of month for period boundaries (from project_store)

    Layout Structure:
        Horizontal (reports-body)
        ├── ScrollableContainer (reports-sidebar)
        │   ├── Static ("Select Period:")
        │   ├── WeekMonthWidget (date picker)
        │   ├── Static ("Reports")
        │   ├── Button ("Cost Overview")
        │   ├── Button ("Monthly")
        │   ├── Button ("Quarterly")
        │   ├── Button ("Yearly")
        │   └── Button ("Back")
        └── ScrollableContainer (reports-content-area)
            └── Dynamic report content

    Sidebar Components:
        **Period Selection (top)**:
            - WeekMonthWidget for choosing week/month
            - Automatically updates period_start and period_end in app_state

        **Report Navigation (middle)**:
            - Cost Overview: BasicReportForm with detailed expense breakdown
            - Monthly: Monthly summary (future)
            - Quarterly: Quarterly analysis (future)
            - Yearly: Annual overview (future)

        **Actions (bottom)**:
            - Back: Return to main screen

    Period Boundaries:
        Monthly periods respect project_store.month_start:
            - If month_start = 15:
              - Period: 15th of current month to 14th of next month
            - If month_start = 1:
              - Period: 1st to last day of month (standard calendar)

        Weekly periods follow ISO 8601:
            - Week starts Monday (configurable in WeekMonthWidget)
            - Weeks numbered 1-52 (or 53 in some years)

    State Management:
        Period selection updates app_state with:
            - current_period_type: "week" or "month"
            - current_period_year: Selected year
            - current_period_week: Selected week (if type=week)
            - current_period_month: Selected month (if type=month)
            - period_start: ISO date string for period start
            - period_end: ISO date string for period end (exclusive)

    Example:
        Basic usage::

            >>> from fiwa_cli.screens.reports import ReportsScreen
            >>> self.app.push_screen(ReportsScreen())

        Period selection flow::

            >>> # User opens reports (defaults to current week)
            >>> # User clicks WeekMonthWidget
            >>> # Selects "Month" from dropdown
            >>> # Selects "March 2026"
            >>> # on_week_month_picker_period_changed() fires
            >>> # Calculates period_start = "2026-03-15" (if month_start=15)
            >>> # Calculates period_end = "2026-04-15"
            >>> # Updates app_state
            >>> # Active report refreshes with new data

        Report type switching::

            >>> # User viewing "Cost Overview"
            >>> # User clicks "Monthly" button
            >>> # on_button_pressed() handles click
            >>> # show_content() clears content area
            >>> # Future: MonthlyReportForm mounted

    Note:
        The period_end date is EXCLUSIVE - data is selected with
        ``bought_date >= period_start AND bought_date < period_end``.

        When switching between week and month modes, the year is preserved
        but the period is recalculated based on the current selection.

        All reports automatically use the period from app_state, ensuring
        consistency across different report types.

    See Also:
        reports_basic.BasicReportForm: Cost overview report implementation
        components.week_month_picker.WeekMonthWidget: Period selector
        settings.SettingsScreen: Similar sidebar/content layout pattern
        base.ReactiveScreen: Base class with state watching
    """
    def __init__(self, *args, **kwargs):
        """Initialize the reports screen.

        Sets up period tracking with current date as default and loads
        month_start configuration from project_store.

        Args:
            *args: Positional arguments passed to parent ReactiveScreen
            **kwargs: Keyword arguments passed to parent ReactiveScreen

        Side Effects:
            - Sets _last_login_state from app_state
            - Initializes _mounted to False
            - Sets _current_period_type to "week"
            - Sets _current_year, _current_week, _current_month to today's values
            - Loads _month_start from project_store (defaults to 1)

        Note:
            The month_start value affects monthly period calculations.
            It's loaded from project_store which is set during project
            creation and can be modified in project settings.
        """
        super().__init__(*args, **kwargs)
        self._last_login_state = self.app.app_state.get("is_logged_in", False)
        self._mounted = False

        # Initialize period tracking
        self._current_period_type = "week"  # "week" or "month"
        self._current_year = datetime.date.today().year
        self._current_week = datetime.date.today().isocalendar()[1]
        self._current_month = datetime.date.today().month
        try:
            self._month_start = json.loads(self.app.app_state["project_store"])
        except:
            self._month_start = {}
        self._month_start = int(self._month_start.get("month_start", "1"))
        # # Initialize date range (default: current month)
        # today = datetime.now()
        # self.period_start = today.replace(day=1)
        # # Last day of current month
        # if today.month == 12:
        #     self.period_end = today.replace(day=31)
        # else:
        #     self.period_end = (today.replace(month=today.month + 1, day=1) - timedelta(days=1))

    def compose(self) -> ComposeResult:
        """Compose the reports screen layout with sidebar and content area.

        Creates a two-column layout similar to SettingsScreen:
            - Left: Sidebar with WeekMonthWidget and report type buttons
            - Right: Content area for displaying active report

        The sidebar adapts based on login state:
            - Logged in: Shows period picker and all report options
            - Not logged in: Shows login prompt and back button

        Yields:
            FiwaHeader: Application header with user and project info
            Horizontal: Main body container with:
                - ScrollableContainer: Sidebar with navigation
                - ScrollableContainer: Content area for reports

        Note:
            The WeekMonthWidget is mounted in the sidebar and bubbles
            up PeriodChanged events that are handled by
            on_week_month_picker_period_changed().
        """
        yield FiwaHeader(
            user=self.app.app_state["user_name"],
            projects=self.app.app_state["project_names"],
            project_id=self.app.app_state["project_id"],
            project_ids=self.app.app_state["project_ids"]
        )

        with Horizontal(id="reports-body"):
            # Left sidebar with navigation
            with ScrollableContainer(id="reports-sidebar"):
                if self.app.app_state["is_logged_in"] is True:
                    # Date range picker at the top of sidebar
                    yield Static("Select Period:", classes="menu-section")
                    yield WeekMonthWidget(id="reports-date-picker")
                    yield Button("↻ Reset to Today", id="reset-period-button", variant="default")
                    # Report type selection buttons
                    yield Static("Report:", classes="menu-section")
                    yield Button("📊 Cost Overview", id="cost-overview-button")
                    yield Button("📈 Monthly Summary", id="monthly-summary-button")
                    # yield Button("🏷️ Category Breakdown", id="category-breakdown-button")
                    # yield Button("📉 Spending Trends", id="spending-trends-button")
                    # yield Button("👥 User Comparison", id="user-comparison-button")
                    # yield Button("📄 Export Report", id="export-report-button")
                    # Back button at bottom
                    yield Static("", classes="menu-section")  # Spacer
                yield Button("← Back to Main", id="menu-back-button", variant="default")
            # Main content area
            with ScrollableContainer(id="reports-content-area"):
                yield Static("Select a report type from the sidebar",
                             #classes="reports-placeholder"
                             )
                m = """
 ____                       _       
|  _ \ ___ _ __   ___  _ __| |_ ___ 
| |_) / _ \ '_ \ / _ \| '__| __/ __|
|  _ <  __/ |_) | (_) | |  | |_\__ \\
|_| \_\___| .__/ \___/|_|   \__|___/
          |_|  """
                yield Static(m)

    def on_mount(self) -> None:
        """Called when the reports screen is mounted.

        Loads CSS, initializes period state, and displays the default report.

        Side Effects:
            - Loads screens_reports.tcss stylesheet
            - Calls _update_period_state() to sync app_state
            - Calls show_content("Cost Overview") to display default report
            - Sets _mounted flag to True
            - Logs mount event

        Note:
            The default report (Cost Overview) is shown automatically
            when the screen opens, using the current period from
            WeekMonthWidget initialization.
        """
        super().on_mount()

        load_dynamic_css(self, css_filename="screens_reports.tcss")

        self._mounted = True
        self.app.log("ReportsScreen mounted")

        # Initialize app_state with current period
        self._update_app_state_period()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle sidebar button clicks for navigation and report selection.

        Routes button clicks to show different reports or navigate back
        to the main screen.

        Args:
            event: Button.Pressed event containing the clicked button

        Handles:
            - report-cost-overview: Shows BasicReportForm (cost breakdown)
            - report-monthly: Shows monthly summary (placeholder)
            - report-quarterly: Shows quarterly analysis (placeholder)
            - report-yearly: Shows annual overview (placeholder)
            - report-back-button: Returns to main screen

        Side Effects:
            - Calls show_content() to load selected report
            - Pops screen if back button clicked

        Example:
            User clicks "Cost Overview"::

                >>> # Button ID: "report-cost-overview"
                >>> # on_button_pressed fires
                >>> # show_content("Cost Overview") called
                >>> # BasicReportForm mounted in content area
        """
        if event.button.id == "menu-back-button":
            self._return_to_main_screen()
        elif event.button.id == "reset-period-button":
            self._reset_to_current_period()
        elif event.button.id == "cost-overview-button":
            self.show_cost_overview()
        elif event.button.id == "monthly-summary-button":
            self.show_content("Monthly Summary", "Coming soon...")
        elif event.button.id == "category-breakdown-button":
            self.show_content("Category Breakdown", "Coming soon...")
        elif event.button.id == "spending-trends-button":
            self.show_content("Spending Trends", "Coming soon...")
        elif event.button.id == "user-comparison-button":
            self.show_content("User Comparison", "Coming soon...")
        elif event.button.id == "export-report-button":
            self.show_content("Export Report", "Coming soon...")

    def on_week_month_widget_period_changed(self, message: WeekMonthWidget.PeriodChanged) -> None:
        """Handle period changes from WeekMonthWidget.

        This event handler is called when the user changes the period
        selection in the WeekMonthWidget (changes week/month, navigates
        to prev/next, or resets to current).

        Args:
            message: PeriodChanged message containing:
                - period_type: "week" or "month"
                - year: Selected year
                - week: Selected week (if period_type="week")
                - month: Selected month (if period_type="month")

        Side Effects:
            - Updates _current_period_type, _current_year, etc.
            - Calls _update_period_state() to sync app_state
            - Calls _refresh_current_report() to reload data
            - Logs period change

        Example:
            User selects March 2026::

                >>> # User clicks month dropdown
                >>> # Selects "March"
                >>> # WeekMonthWidget posts PeriodChanged message
                >>> # on_week_month_picker_period_changed fires
                >>> # Updates _current_month = 3
                >>> # Calls _update_period_state()
                >>> # Calculates period_start/end
                >>> # Calls _refresh_current_report()
                >>> # Active report reloads with March data

        Note:
            The period change automatically triggers a refresh of the
            currently visible report, ensuring data stays in sync with
            the selected period.
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

        # Refresh current report if one is loaded
        self._refresh_current_report()

    def _refresh_current_report(self) -> None:
        """Refresh the currently displayed report with updated period data.

        Re-mounts the current report to force it to reload data from the
        database using the updated period from app_state.

        This method determines which report is currently active and
        calls show_content() to remount it.

        Side Effects:
            - Queries content area for active report
            - Calls show_content() with current report name
            - Active report reloads from database

        Example:
            After period change::

                >>> # User changes from Week 10 to Week 11
                >>> # on_week_month_picker_period_changed fires
                >>> # _refresh_current_report() called
                >>> # Determines "Cost Overview" is active
                >>> # Calls show_content("Cost Overview")
                >>> # BasicReportForm remounted with Week 11 data

        Note:
            Currently only "Cost Overview" is implemented as BasicReportForm.
            Future report types will be detected and refreshed similarly.
        """
        try:
            # Check if BasicReportForm is currently loaded
            content_area = self.query_one("#reports-content-area", ScrollableContainer)
            # Try to find BasicReportForm in content area

            forms = list(content_area.query(BasicReportForm))
            if forms:
                # Refresh the existing form
                forms[0].refresh_data()
                self.app.log("Refreshed Cost Overview report")
        except Exception as e:
            self.app.log(f"Could not refresh report: {e}")

    def show_cost_overview(self) -> None:
        """Show the Cost Overview report in the content area."""

        content_area = self.query_one("#reports-content-area", ScrollableContainer)
        content_area.remove_children()


        form = BasicReportForm()
        form.on_mount()
        content_area.mount(form)
        self.app.log("Cost Overview loaded")
    def show_content(self, title: str, message: str) -> None:
        """Update the content area with new information."""
        content_area = self.query_one("#reports-content-area", ScrollableContainer)
        content_area.remove_children()
        content_area.mount(Static(f"[bold]{title}[/bold]\n\n{message}",
                                 classes="reports-placeholder"))
    def _return_to_main_screen(self) -> None:
        """Return to the main application screen."""
        try:
            while len(self.app.screen_stack) > 1:
                self.app.pop_screen()
        except Exception as e:
            self.app.log(f"Error returning to main screen: {e}")

    def _reset_to_current_period(self) -> None:
        """Reset the WeekMonthWidget to current week or month based on period type."""
        try:
            import datetime
            today = datetime.date.today()

            # Reset internal state to current date
            self._current_year = today.year
            self._current_week = today.isocalendar()[1]
            self._current_month = today.month

            # Update WeekMonthWidget
            week_month_widget = self.query_one("#reports-date-picker", WeekMonthWidget)
            week_month_widget.current_year = self._current_year
            week_month_widget.current_week = self._current_week
            week_month_widget.current_month = self._current_month
            # Keep the current period_type (week or month)
            week_month_widget.update_display()

            # Update app_state with current period
            self._update_app_state_period()

            # Refresh the current report with new date range
            self._refresh_current_report()

            period_type_name = "week" if self._current_period_type == "week" else "month"
            #self.app.notify(f"Reset to current {period_type_name}", severity="information")
            self.app.log(f"Reset period to current {period_type_name}: Year {self._current_year}, Week {self._current_week}, Month {self._current_month}")

        except Exception as e:
            self.app.log(f"Error resetting period: {e}")
            self.app.notify(f"Error resetting period: {str(e)}", severity="error")

    def _update_app_state_period(self) -> None:
        """Update app_state with current period selection."""
        try:
            # Calculate date range based on period type
            if self._current_period_type == "week":
                # Calculate week boundaries
                from fiwa_cli.functions.compute_time import TimeClass
                tc = TimeClass(country_code="DE")
                week_info = tc.cmp_week_by_number(self._current_year, self._current_week)

                period_start = week_info['week_beg']
                period_end = week_info['week_end']
                period_end += datetime.timedelta(days=1)  # Include the end date in the range
                period_label = f"{self._current_year} Week {self._current_week}"
            else:  # month
                # Calculate month boundaries
                from fiwa_cli.functions.compute_time import TimeClass
                tc = TimeClass(country_code="DE")
                month_info = tc.cmp_month_by_number(self._current_year,
                                                    self._current_month,
                                                    self._month_start #from class init
                                                    )

                period_start = month_info['month_beg']
                period_end = month_info['month_end']
                #self.app.notify(f"{period_start} / {period_end} / {json.loads(self.app.app_state.get('project_store', {})).get('month_start', 'N/A')}")
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

            # Refresh the current report with new period data
            self._refresh_current_report()

        except Exception as e:
            self.app.log(f"Error updating app_state period: {e}")

