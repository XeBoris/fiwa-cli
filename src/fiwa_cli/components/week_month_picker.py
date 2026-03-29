"""Week/Month picker widget for period navigation.

This widget provides a compact interface for navigating through weeks or months
with previous/next buttons and displays the current year and period.
"""

from textual.widgets import Static, Button, Select
from textual.widget import Widget
from textual.containers import Grid, Vertical
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from datetime import datetime

from fiwa_cli.functions.loader import load_dynamic_css


class WeekMonthWidget(Widget):
    """A widget for navigating through weeks or months.

    Provides a grid layout with navigation buttons (◀ ▶) and displays
    the current year and week/month number. Sends messages when the
    period changes or when navigation buttons are pressed.

    Attributes:
        period_type (str): Either "week" or "month" - determines display mode
        current_year (int): The currently displayed year
        current_week (int): The currently displayed week number (1-53)
        current_month (int): The currently displayed month number (1-12)

    Messages:
        PeriodChanged: Posted when the user navigates to a different period

    Example:
        >>> picker = WeekMonthWidget()
        >>> picker.period_type = "month"
        >>> picker.update_display()
    """

    # Reactive properties for dynamic updates
    period_type: reactive[str] = reactive("week")
    current_year: reactive[int] = reactive(datetime.now().year)
    current_week: reactive[int] = reactive(datetime.now().isocalendar()[1])
    current_month: reactive[int] = reactive(datetime.now().month)

    # Inline CSS: not needed
    # DEFAULT_CSS = """
    # """

    class PeriodChanged(Message):
        """Message sent when the period changes via navigation.

        Attributes:
            period_type (str): "week" or "month"
            year (int): The new year
            week (int): The new week number (if period_type is "week")
            month (int): The new month number (if period_type is "month")
        """

        def __init__(
            self, period_type: str, year: int, week: int = None, month: int = None
        ) -> None:
            self.period_type = period_type
            self.year = year
            self.week = week
            self.month = month
            super().__init__()

        # except:
        #     # Fallback if app_state is not yet available
        #     return None

    def __init__(
        self,
        initial_year: int = None,
        initial_week: int = None,
        initial_month: int = None,
        period_type: str = "week",
        *args,
        **kwargs,
    ):
        """Initialize the week/month picker widget.

        Args:
            initial_year (int, optional): Starting year. Defaults to current year.
            initial_week (int, optional): Starting week number (1-53). Defaults to current week.
            initial_month (int, optional): Starting month number (1-12). Defaults to current month.
            period_type (str, optional): Display mode - "week" or "month". Defaults to "week".
            *args: Additional positional arguments for Widget
            **kwargs: Additional keyword arguments for Widget
        """
        super().__init__(*args, **kwargs)

        # Initialize with provided values or current date
        today = datetime.now()
        self.current_year = initial_year if initial_year is not None else today.year
        self.current_week = initial_week if initial_week is not None else today.isocalendar()[1]
        self.current_month = initial_month if initial_month is not None else today.month
        self.period_type = period_type

    def compose(self) -> ComposeResult:
        """Build the widget's visual structure.

        Creates a vertical layout with:
        - Period type dropdown (Week/Month) - centered above
        - 2×2 grid layout below:
          [◀] [▶]
          [Year] [Week/Month]

        Yields:
            Widget: The vertical container with dropdown and grid
        """
        with Vertical(classes="week-month-picker-container"):
            # Period type selector dropdown - centered above grid
            yield Select(
                options=[("Week", "week"), ("Month", "month")],
                value=self.period_type,
                id="wm-period-select",
                allow_blank=False,
                prompt="Period",
            )

            # Navigation grid below dropdown
            with Grid(id="week-month-picker-grid", classes="week-month-picker"):
                yield Button(
                    "◀",
                    id="wm-period-prev",
                    variant="default",
                    classes="wm-nav-button",
                    compact=True,
                )
                yield Button(
                    "▶",
                    id="wm-period-next",
                    variant="default",
                    classes="wm-nav-button",
                    compact=True,
                )
                yield Static(str(self.current_year), id="wm-period-year", classes="wm-display")

                # Display week or month based on period_type
                if self.period_type == "week":
                    yield Static(
                        f"W{self.current_week}", id="wm-period-value", classes="wm-display"
                    )
                else:
                    yield Static(
                        f"M{self.current_month:02d}", id="wm-period-value", classes="wm-display"
                    )

    def on_mount(self) -> None:
        """Called after widget is mounted - set Select widget value and load CSS."""
        # Try to load external CSS file if app_state is available
        load_dynamic_css(self, css_filename="components_week_month_picker.tcss")

        # Set Select widget initial value
        try:
            select_widget = self.query_one("#wm-period-select", Select)
            select_widget.value = self.period_type
        except Exception as e:
            self.app.log(f"Error setting Select value: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle navigation button presses.

        Args:
            event: The button press event containing which button was clicked
        """
        if event.button.id == "wm-period-prev":
            self._navigate_period(-1)
            event.stop()  # Prevent event from bubbling up
        elif event.button.id == "wm-period-next":
            self._navigate_period(1)
            event.stop()  # Prevent event from bubbling up

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle period type dropdown changes.

        Args:
            event: The select change event containing the new value
        """
        if event.select.id == "wm-period-select":
            self.period_type = event.value
            self.update_display()
            event.stop()  # Prevent event from bubbling up

    def _navigate_period(self, direction: int) -> None:
        """Navigate to the previous or next period.

        Handles year boundaries automatically. For weeks, handles years with
        52 or 53 weeks correctly. For months, wraps at 12.

        Args:
            direction (int): -1 for previous period, 1 for next period
        """
        if self.period_type == "week":
            self.current_week += direction

            # Handle year boundaries for weeks
            if self.current_week < 1:
                # Going back from week 1 - move to previous year's last week
                # Need to find the last week that actually belongs to the previous year
                # Some years have 52 weeks, some have 53
                from datetime import date

                self.current_year -= 1

                # Find the last week that belongs to this year
                # Start from Dec 28 (guaranteed to be in the year) and work backwards
                test_date = date(self.current_year, 12, 28)
                iso_cal = test_date.isocalendar()

                # If Dec 28 belongs to next year, go back a week
                if iso_cal[0] > self.current_year:
                    # Dec 28 is in next year's W01, so find last week of current year
                    test_date = date(self.current_year, 12, 21)
                    iso_cal = test_date.isocalendar()

                self.current_week = iso_cal[1]

            elif self.current_week > 52:
                # Going forward - check if week 53 exists for this year
                from datetime import date

                last_day = date(self.current_year, 12, 31)
                max_week = last_day.isocalendar()[1]
                if self.current_week > max_week:
                    # Week doesn't exist, move to next year's week 1
                    self.current_year += 1
                    self.current_week = 1
        else:  # month
            self.current_month += direction

            # Handle year boundaries for months
            if self.current_month < 1:
                self.current_year -= 1
                self.current_month = 12
            elif self.current_month > 12:
                self.current_year += 1
                self.current_month = 1

        # Update the display
        self.update_display()

        # Post message about period change
        self.post_message(
            self.PeriodChanged(
                period_type=self.period_type,
                year=self.current_year,
                week=self.current_week if self.period_type == "week" else None,
                month=self.current_month if self.period_type == "month" else None,
            )
        )

    def update_display(self) -> None:
        """Update the display widgets with current period values.

        Updates the year and week/month displays to reflect the current
        values. Should be called after changing period_type or after
        setting values programmatically.
        """
        try:
            # Update Select widget
            select_widget = self.query_one("#wm-period-select", Select)
            select_widget.value = self.period_type

            # Update year display
            year_widget = self.query_one("#wm-period-year", Static)
            year_widget.update(str(self.current_year))

            # Update week/month display based on current period_type
            value_widget = self.query_one("#wm-period-value", Static)
            if self.period_type == "week":
                value_widget.update(f"W{self.current_week}")
            else:
                value_widget.update(f"M{self.current_month:02d}")
        except Exception as e:
            # Widget might not be mounted yet
            self.app.log(f"Error updating WeekMonthWidget display: {e}")

    def set_period(self, year: int, week: int = None, month: int = None) -> None:
        """Programmatically set the displayed period.

        Args:
            year (int): The year to display
            week (int, optional): The week number (1-53) if period_type is "week"
            month (int, optional): The month number (1-12) if period_type is "month"

        Example:
            >>> picker.set_period(2026, week=10)
            >>> picker.set_period(2026, month=3)
        """
        self.current_year = year
        if week is not None:
            self.current_week = week
        if month is not None:
            self.current_month = month
        self.update_display()

    def watch_period_type(self, old_value: str, new_value: str) -> None:
        """React to period_type changes.

        Called automatically when period_type reactive property changes.
        Updates the display to show week or month format.

        Args:
            old_value: Previous period type
            new_value: New period type ("week" or "month")
        """
        self.update_display()
