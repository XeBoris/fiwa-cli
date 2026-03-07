"""Reports screen - view financial reports and analytics with sidebar navigation."""
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Button
from textual.app import ComposeResult
from components import FiwaHeader
from components.week_month_picker import WeekMonthWidget

from .reports_basic import BasicReportForm

from functions.loader import load_dynamic_css

from .base import ReactiveScreen
import datetime
#from datetime import datetime, timedelta



class ReportsScreen(ReactiveScreen):
    """Reports screen - view financial reports and analytics with sidebar navigation."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_login_state = self.app.app_state.get("is_logged_in", False)
        self._mounted = False

        # Initialize period tracking
        self._current_period_type = "week"  # "week" or "month"
        self._current_year = datetime.date.today().year
        self._current_week = datetime.date.today().isocalendar()[1]
        self._current_month = datetime.date.today().month

        # # Initialize date range (default: current month)
        # today = datetime.now()
        # self.period_start = today.replace(day=1)
        # # Last day of current month
        # if today.month == 12:
        #     self.period_end = today.replace(day=31)
        # else:
        #     self.period_end = (today.replace(month=today.month + 1, day=1) - timedelta(days=1))

    def compose(self) -> ComposeResult:
        """Create the reports screen layout with sidebar and content area."""
        yield FiwaHeader(
            user=self.app.app_state["user_name"],
            projects=self.app.app_state["project_names"],
            project_id=self.app.app_state["project_id"],
            project_ids=self.app.app_state["project_ids"]
        )

        with Horizontal(id="reports-body"):
            # Left sidebar with navigation
            with ScrollableContainer(id="reports-sidebar"):
                # Date range picker at the top of sidebar
                yield Static("Select Period:", classes="menu-section")
                yield WeekMonthWidget(id="reports-date-picker")
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
                yield Static("Select a report type from the sidebar", classes="reports-placeholder")

    def on_mount(self) -> None:
        """Called when screen is mounted. Set up watchers and load CSS."""
        super().on_mount()

        load_dynamic_css(self, css_filename="screens_reports.tcss")

        self._mounted = True
        self.app.log("ReportsScreen mounted")

        # Initialize app_state with current period
        self._update_app_state_period()

        # Initialize WeekMonthWidget with current values
        # try:
        #     week_month_widget = self.query_one(WeekMonthWidget)
        #     week_month_widget.period_type = self._current_period_type
        #     week_month_widget.current_year = self._current_year
        #     week_month_widget.current_week = self._current_week
        #     week_month_widget.current_month = self._current_month
        #     week_month_widget.update_display()
        #     self.app.log("WeekMonthWidget initialized")
        # except Exception as e:
        #     self.app.log(f"Could not initialize WeekMonthWidget: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle sidebar button clicks to load different reports."""
        if event.button.id == "menu-back-button":
            self._return_to_main_screen()
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

        # Refresh current report if one is loaded
        self._refresh_current_report()

    def _refresh_current_report(self) -> None:
        """Refresh the currently displayed report with new date range."""

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