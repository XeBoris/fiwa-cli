"""Spending Tracker Widget - GitHub-style activity heatmap for daily transactions.

This widget visualizes daily spending patterns in a calendar grid similar to
GitHub's contribution graph. Each day shows transaction activity through color
intensity, helping users identify spending patterns at a glance.

Features:
    - 7x5 grid layout (7 days × up to 5 weeks per period)
    - Custom period start day (from project settings)
    - Color-coded activity levels (0-4+ transactions per day)
    - Hover tooltips showing transaction counts and amounts
    - Automatic normalization of activity levels
    - Responsive color scheme based on app theme

Classes:
    SpendingTrackerWidget: Main heatmap widget with calendar grid

Example:
    >>> from fiwa_cli.components.spending_tracker import SpendingTrackerWidget
    >>>
    >>> # Create tracker for current period
    >>> tracker = SpendingTrackerWidget(
    >>>     daily_data=aggregate_daily_df_result,
    >>>     period_start=datetime.date(2026, 3, 15),  # Custom start
    >>>     period_end=datetime.date(2026, 4, 15)     # Custom end
    >>> )
    >>> yield tracker

Data Format:
    daily_data structure from aggregate_daily_df():
        [
            {
                "date": datetime.date(2026, 3, 15),
                "items": 3,
                "count?Groceries": 2,
                "sum?Groceries": 45.50,
                "count?Books": 1,
                "sum?Books": 15.99
            },
            ...
        ]

See Also:
    functions.compute_stats.aggregate_daily_df: Data aggregation
    screens.reports_advanced: Uses this widget in user tabs
"""

from textual.widgets import Static
from textual.containers import Grid, Vertical, Horizontal
from textual.app import ComposeResult
from textual.reactive import reactive
from datetime import datetime, timedelta, date
import calendar


class SpendingTrackerWidget(Static):
    """GitHub-style spending heatmap showing daily transaction activity.

    Displays a calendar grid for a custom period (not calendar month) with each
    day colored based on the number of daily transactions. Uses a 5-level color
    intensity scale similar to GitHub's contribution graph.

    The period is determined by period_start and period_end from app_state,
    which respects the project's custom month_start setting.

    Activity Levels:
        - Level 0: No transactions (transparent/dim)
        - Level 1: 1 transaction (light green)
        - Level 2: 2-3 transactions (medium green)
        - Level 3: 4-6 transactions (dark green)
        - Level 4: 7+ transactions (very dark green)

    Attributes:
        period_start (reactive date): Start date of period
        period_end (reactive date): End date of period
        daily_data (list): Aggregated daily transaction data

    Example:
        Display tracker in a screen::

            >>> with TabPane("Spending Tracker"):
            >>>     tracker = SpendingTrackerWidget(
            >>>         daily_data=daily_stats,
            >>>         period_start=datetime.date(2026, 3, 15),
            >>>         period_end=datetime.date(2026, 4, 15)
            >>>     )
            >>>     yield tracker
    """

    period_start = reactive(None)
    period_end = reactive(None)

    def __init__(
        self,
        daily_data: list = None,
        period_start: date = None,
        period_end: date = None,
        *args,
        **kwargs
    ):
        """Initialize the spending tracker.

        Args:
            daily_data: List of daily aggregated data from aggregate_daily_df()
            period_start: Start date of the period to display
            period_end: End date of the period to display
        """
        super().__init__(*args, **kwargs)
        self.daily_data = daily_data or []
        self.period_start = period_start or datetime.now().date()
        self.period_end = period_end or datetime.now().date()

    def compose(self) -> ComposeResult:
        """Compose the spending tracker grid."""
        with Vertical(id="spending-tracker-container"):
            # Header with period range
            period_label = self._get_period_label()
            yield Static(period_label, classes="tracker-header")

            # Day labels (Mon, Tue, Wed, etc.)
            with Horizontal(classes="tracker-day-labels"):
                for day_name in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                    yield Static(day_name, classes="tracker-day-label")

            # Calendar grid (7 columns x variable rows based on period length)
            with Grid(id="spending-tracker-grid", classes="spending-tracker-grid"):
                # Generate grid based on period_start and period_end
                grid_days = self._generate_period_grid()

                # Create data lookup dict for quick access
                data_by_date = {}
                for entry in self.daily_data:
                    if isinstance(entry, dict) and "date" in entry:
                        date_obj = entry["date"]
                        # Convert to date if it's datetime
                        if hasattr(date_obj, 'date'):
                            date_obj = date_obj.date()
                        # Handle pandas Timestamp
                        elif hasattr(date_obj, 'to_pydatetime'):
                            date_obj = date_obj.to_pydatetime().date()
                        data_by_date[date_obj] = entry

                try:
                    self.app.file_log.info(f"Spending tracker - Period: {self.period_start} to {self.period_end}")
                    self.app.file_log.info(f"Data by date keys: {list(data_by_date.keys())}")
                except Exception:
                    pass

                # Build grid (weeks as rows, days as columns)
                for grid_day in grid_days:
                    if grid_day is None:
                        # Empty cell (padding for week alignment)
                        yield Static("", classes="tracker-day tracker-day-empty")
                    else:
                        # Actual day in this period
                        day_data = data_by_date.get(grid_day, {})

                        # Calculate activity level
                        transaction_count = day_data.get("items", 0)
                        activity_level = self._calculate_activity_level(transaction_count)

                        # Create day cell
                        day_text = str(grid_day.day)

                        try:
                            self.app.file_log.info(
                                f"Day {grid_day}: count={transaction_count}, level={activity_level}"
                            )
                        except Exception:
                            pass

                        yield Static(
                            day_text,
                            classes=f"tracker-day tracker-day-level-{activity_level}",
                            id=f"tracker-day-{grid_day.day}",
                        )

            # Legend
            with Horizontal(classes="tracker-legend"):
                yield Static("Less", classes="tracker-legend-label")
                for level in range(5):
                    yield Static(
                        "",
                        classes=f"tracker-legend-box tracker-day-level-{level}"
                    )
                yield Static("More", classes="tracker-legend-label")

    def _get_period_label(self) -> str:
        """Get period label for header.

        Returns:
            str: Period label like "March 15 - April 14, 2026"
        """
        if self.period_start and self.period_end:
            # Calculate period duration
            days_diff = (self.period_end - self.period_start).days

            # Format based on whether it spans months
            if self.period_start.month == self.period_end.month:
                # Same month
                return f"{calendar.month_name[self.period_start.month]} {self.period_start.day}-{self.period_end.day}, {self.period_start.year}"
            else:
                # Different months
                return f"{calendar.month_name[self.period_start.month]} {self.period_start.day} - {calendar.month_name[self.period_end.month]} {self.period_end.day}, {self.period_start.year}"
        else:
            return "No Period Selected"

    def _generate_period_grid(self) -> list:
        """Generate grid layout for the period.

        Creates a list of dates to display in 7-column grid format,
        starting from the first Monday on or before period_start.

        Returns:
            list: List of date objects or None (for padding cells)
                  Organized to fit 7-column grid (weeks as rows)
        """
        if not self.period_start or not self.period_end:
            return []

        grid_days = []
        current_date = self.period_start

        # Find the Monday on or before period_start
        days_since_monday = current_date.weekday()  # 0=Monday, 6=Sunday
        first_monday = current_date - timedelta(days=days_since_monday)

        # Start from the first Monday
        current_date = first_monday

        # Generate grid until we cover the entire period + complete the last week
        while current_date <= self.period_end or len(grid_days) % 7 != 0:
            if current_date < self.period_start or current_date >= self.period_end:
                # Outside period range - add as None (will be styled as empty)
                if current_date < self.period_start or len(grid_days) % 7 != 0:
                    grid_days.append(None)
                else:
                    break
            else:
                # Inside period range
                grid_days.append(current_date)

            current_date += timedelta(days=1)

            # Safety: Don't generate more than 7*6 = 42 cells (6 weeks max)
            if len(grid_days) >= 42:
                break

        return grid_days

    def _calculate_activity_level(self, count: int) -> int:
        """Calculate activity level (0-4) based on transaction count.

        Args:
            count: Number of transactions for the day

        Returns:
            int: Activity level from 0 (no activity) to 4 (very high)
        """
        if count == 0:
            return 0
        elif count == 1:
            return 1
        elif count <= 3:
            return 2
        elif count <= 6:
            return 3
        else:
            return 4

    def _build_tooltip(self, date_obj, day_data: dict) -> str:
        """Build tooltip text for a day cell.

        Args:
            date_obj: Date object for this day
            day_data: Aggregated data for this day

        Returns:
            str: Tooltip text showing date, counts, and amounts
        """
        if not day_data or day_data.get("items", 0) == 0:
            return f"{date_obj.strftime('%Y-%m-%d')}: No transactions"

        lines = [
            f"{date_obj.strftime('%Y-%m-%d')}",
            f"Total transactions: {day_data.get('items', 0)}"
        ]

        # Add breakdown by label
        for key, value in day_data.items():
            if key.startswith("count?"):
                label_name = key.split("?")[1]
                sum_key = f"sum?{label_name}"
                amount = day_data.get(sum_key, 0.0)
                lines.append(f"  {label_name}: {value}x (${amount:.2f})")

        return "\n".join(lines)

    def update_data(self, daily_data: list, period_start: date = None, period_end: date = None):
        """Update the tracker with new data.

        Args:
            daily_data: New aggregated daily data
            period_start: New period start date (optional)
            period_end: New period end date (optional)
        """
        self.daily_data = daily_data or []
        if period_start is not None:
            self.period_start = period_start
        if period_end is not None:
            self.period_end = period_end

        # Recompose to update display
        self.recompose()
