"""Calendar widget for date selection."""
from datetime import datetime, timedelta
from textual.widgets import Static, Button
from textual.containers import Grid, Vertical
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.message import Message
from textual.reactive import reactive


class CalendarWidget(ModalScreen):
    """Calendar widget for selecting dates."""

    # Configuration: True = week starts on Monday, False = week starts on Sunday
    WEEK_STARTS_MONDAY = True

    BINDINGS = [
        ("escape", "dismiss_calendar", "Close"),
    ]

    DEFAULT_CSS = """
    
    CalendarWidget {
        align: left top;
        offset: 18 0;
    }
    
    CalendarWidget > Vertical {
        width: 35;
        height: auto;
        margin: 3 0 0 25;
        background: $surface;
        border: solid $accent;
        padding: 1;
        max-height: 20;
    }
    
    CalendarWidget .calendar-title {
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
        color: $accent;
        height: 1;
    }
    
    CalendarWidget .calendar-header {
        grid-size: 7 1;
        grid-gutter: 0;
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
    }
    
    CalendarWidget .nav-button {
        width: 10%;
        height: 2;
        min-height: 1;
        background: $accent;
        color: $text;
        padding: 0;
    }
    
    CalendarWidget .nav-button:hover {
        background: $accent-lighten-1;
    }
    
    CalendarWidget .today-button {
        width: 100%;
        height: 1;
        min-height: 1;
        background: $primary;
        color: $text;
        column-span: 5;
        padding: 0;
    }
    
    CalendarWidget .today-button:hover {
        background: $primary-lighten-1;
    }
    
    CalendarWidget .weekday-header {
        grid-size: 7 1;
        grid-gutter: 0;
        width: 100%;
        height: 1;
        margin: 0 0 0 0;
    }
    
    CalendarWidget .weekday-label {
        text-align: center;
        text-style: bold;
        width: 100%;
        height: 1;
        background: $panel;
        padding: 0;
    }
    
    CalendarWidget .calendar-grid {
        grid-size: 7 6;
        grid-gutter: 0;
        width: 100%;
        height: auto;
    }
    
    CalendarWidget .day-button {
        width: 100%;
        height: 2;
        min-height: 2;
        background: $panel;
        padding: 0;
        content-align: center middle;
    }
    
    CalendarWidget .day-button:hover {
        background: $accent;
    }
    
    CalendarWidget .day-today {
        background: $success;
        color: $text;
        text-style: bold;
    }
    
    CalendarWidget .day-today:hover {
        background: $success-darken-1;
    }
    
    CalendarWidget .day-other-month {
        background: $surface;
        color: $text-muted;
    }
    
    CalendarWidget .day-selected {
        background: $primary;
        color: $text;
        text-style: bold;
        border: thick white;
    }
    """

    class DateSelected(Message):
        """Message sent when a date is selected."""
        def __init__(self, selected_date: datetime) -> None:
            self.selected_date = selected_date
            super().__init__()

    def __init__(self, initial_date: datetime = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_date = initial_date if initial_date else datetime.now()
        self.today = datetime.now()
        self.selected_date = None
        # Set to first day of current month for display
        self.display_date = self.current_date.replace(day=1)

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Select Date", classes="calendar-title")

            # Navigation header with prev/next month and today button
            with Grid(classes="calendar-header"):
                yield Button("◀", id="prev-month", classes="nav-button")
                yield Button("Today", id="today-button", classes="today-button")
                yield Button("▶", id="next-month", classes="nav-button")

            # Month/Year display
            month_year = self.display_date.strftime("%B %Y")
            yield Static(month_year, id="month-year-display", classes="calendar-title")

            # Weekday headers
            with Grid(classes="weekday-header"):
                if self.WEEK_STARTS_MONDAY:
                    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                else:
                    weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

                for day in weekdays:
                    yield Static(day, classes="weekday-label")

            # Calendar grid with days
            with Grid(classes="calendar-grid", id="calendar-grid"):
                yield from self._generate_calendar_days()

    def _generate_calendar_days(self):
        """Generate buttons for all days in the current month view."""
        year = self.display_date.year
        month = self.display_date.month

        # Get first day of the month
        first_day = self.display_date

        # Determine the weekday of the first day (0=Monday, 6=Sunday or 0=Sunday, 6=Saturday)
        if self.WEEK_STARTS_MONDAY:
            first_weekday = first_day.weekday()  # 0=Monday
        else:
            first_weekday = (first_day.weekday() + 1) % 7  # 0=Sunday

        # Get last day of current month
        if month == 12:
            next_month = first_day.replace(year=year+1, month=1, day=1)
        else:
            next_month = first_day.replace(month=month+1, day=1)
        last_day = next_month - timedelta(days=1)
        days_in_month = last_day.day

        # Get days from previous month to fill the first week
        days_from_prev = first_weekday
        if month == 1:
            prev_month_date = first_day.replace(year=year-1, month=12, day=1)
        else:
            prev_month_date = first_day.replace(month=month-1, day=1)

        # Get last day of previous month
        prev_month_last = first_day - timedelta(days=1)
        prev_month_days = prev_month_last.day

        # Add days from previous month
        for i in range(days_from_prev):
            day_num = prev_month_days - days_from_prev + i + 1
            date = prev_month_date.replace(day=day_num)
            button = Button(
                str(day_num),
                id=f"day-{date.strftime('%Y-%m-%d')}",
                classes="day-button day-other-month"
            )
            yield button

        # Add days of current month
        for day in range(1, days_in_month + 1):
            date = first_day.replace(day=day)
            classes = "day-button"

            # Check if this is today
            if (date.year == self.today.year and
                date.month == self.today.month and
                date.day == self.today.day):
                classes += " day-today"

            button = Button(
                str(day),
                id=f"day-{date.strftime('%Y-%m-%d')}",
                classes=classes
            )
            yield button

        # Calculate how many days we've shown
        total_shown = days_from_prev + days_in_month

        # Fill remaining cells with next month days
        remaining = 42 - total_shown  # 6 rows * 7 days = 42
        if remaining > 7:
            remaining = remaining - 7  # Only show 5 rows if possible

        for day in range(1, remaining + 1):
            date = next_month.replace(day=day)
            button = Button(
                str(day),
                id=f"day-{date.strftime('%Y-%m-%d')}",
                classes="day-button day-other-month"
            )
            yield button

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "prev-month":
            self._change_month(-1)
        elif event.button.id == "next-month":
            self._change_month(1)
        elif event.button.id == "today-button":
            self._jump_to_today()
        elif event.button.id and event.button.id.startswith("day-"):
            self._select_date(event.button.id)

    def action_dismiss_calendar(self) -> None:
        """Action called when ESC is pressed - dismiss calendar without selecting a date."""
        self.dismiss(None)

    def _change_month(self, delta: int) -> None:
        """Change the displayed month."""
        current_month = self.display_date.month
        current_year = self.display_date.year

        new_month = current_month + delta
        new_year = current_year

        if new_month > 12:
            new_month = 1
            new_year += 1
        elif new_month < 1:
            new_month = 12
            new_year -= 1

        self.display_date = self.display_date.replace(year=new_year, month=new_month, day=1)
        self._refresh_calendar()

    def _jump_to_today(self) -> None:
        """Jump to today's date and select it."""
        self.display_date = self.today.replace(day=1)
        self._refresh_calendar()
        # Optionally auto-select today
        # self._select_date(f"day-{self.today.strftime('%Y-%m-%d')}")

    def _select_date(self, button_id: str) -> None:
        """Select a date and dismiss the calendar."""
        # Extract date from button ID (format: "day-YYYY-MM-DD")
        date_str = button_id.replace("day-", "")
        selected_date = datetime.strptime(date_str, "%Y-%m-%d")

        # Return the selected date and close the calendar
        self.dismiss(selected_date)

    def _refresh_calendar(self) -> None:
        """Refresh the calendar display."""
        # Update month/year display
        month_year = self.display_date.strftime("%B %Y")
        try:
            month_display = self.query_one("#month-year-display", Static)
            month_display.update(month_year)
        except Exception:
            pass

        # Regenerate calendar grid
        try:
            grid = self.query_one("#calendar-grid", Grid)
            grid.remove_children()
            grid.mount_all(self._generate_calendar_days())
        except Exception as e:
            self.app.log(f"Error refreshing calendar: {e}")
