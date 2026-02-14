"""Calendar widget for selecting dates."""
from datetime import datetime, date, timedelta
from calendar import monthcalendar, month_name

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, Grid
from textual.widgets import Button, Static
from textual.widget import Widget
from textual.message import Message


class Calendar(Widget):
    """A calendar widget for date selection."""

    DEFAULT_CSS = """
    Calendar {
        width: auto;
        height: auto;
        border: solid $accent;
        padding: 1;
    }

    Calendar #calendar-header {
        layout: horizontal;
        height: 3;
        align: center middle;
    }

    Calendar #month-display {
        content-align: center middle;
        width: 20;
        text-style: bold;
    }

    Calendar #prev-month, Calendar #next-month {
        min-width: 3;
    }

    Calendar #weekday-header {
        layout: horizontal;
        height: 1;
        margin-bottom: 1;
    }

    Calendar .weekday-label {
        width: 4;
        content-align: center middle;
        text-style: bold;
        color: $text-muted;
    }

    Calendar #calendar-grid {
        layout: grid;
        grid-size: 7;
        grid-gutter: 0;
        height: auto;
    }

    Calendar .day-button {
        width: 4;
        height: 1;
        min-width: 4;
        border: none;
        background: transparent;
        color: $text;
    }

    Calendar .day-button:hover {
        background: $accent 30%;
    }

    Calendar .day-button.selected {
        background: $accent;
        color: $text;
        text-style: bold;
    }

    Calendar .day-button.empty {
        color: $text-muted 30%;
    }

    Calendar .day-button.today {
        text-style: bold;
        color: $success;
    }
    """

    class DateSelected(Message):
        """Posted when a date is selected."""

        def __init__(self, selected_date: date) -> None:
            super().__init__()
            self.selected_date = selected_date

    def __init__(self, initial_date: date | None = None) -> None:
        super().__init__()
        self.current_date = initial_date or date.today()
        self.selected_date = self.current_date
        self.today = date.today()

    def compose(self) -> ComposeResult:
        """Compose the calendar widget."""
        with Vertical():
            # Header with month navigation
            with Horizontal(id="calendar-header"):
                yield Button("◀", id="prev-month")
                yield Static(self._get_month_display(), id="month-display")
                yield Button("▶", id="next-month")

            # Weekday labels
            with Horizontal(id="weekday-header"):
                for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
                    yield Static(day, classes="weekday-label")

            # Calendar grid
            yield Grid(*self._get_day_buttons(), id="calendar-grid")

    def _get_month_display(self) -> str:
        """Get the current month and year display string."""
        return f"{month_name[self.current_date.month]} {self.current_date.year}"

    def _get_day_buttons(self) -> list[Button]:
        """Generate buttons for all days in the current month."""
        buttons = []
        # monthcalendar returns weeks, Monday is the first day (0)
        weeks = monthcalendar(self.current_date.year, self.current_date.month)

        for week in weeks:
            for day in week:
                if day == 0:
                    # Empty day (placeholder)
                    btn = Button("", id=f"day-empty-{len(buttons)}", classes="day-button empty")
                    btn.disabled = True
                else:
                    day_date = date(self.current_date.year, self.current_date.month, day)
                    btn_id = f"day-{day}"
                    classes = ["day-button"]

                    # Mark as selected
                    if day_date == self.selected_date:
                        classes.append("selected")

                    # Mark as today
                    if day_date == self.today:
                        classes.append("today")

                    btn = Button(str(day), id=btn_id, classes=" ".join(classes))

                buttons.append(btn)

        return buttons

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "prev-month":
            self._change_month(-1)
        elif button_id == "next-month":
            self._change_month(1)
        elif button_id and button_id.startswith("day-") and not button_id.startswith("day-empty"):
            # Extract day number from button ID
            day = int(button_id.split("-")[1])
            self.selected_date = date(self.current_date.year, self.current_date.month, day)
            self._refresh_calendar()
            # Post message that a date was selected
            self.post_message(self.DateSelected(self.selected_date))

    def _change_month(self, delta: int) -> None:
        """Change the displayed month by delta months."""
        # Calculate new month
        month = self.current_date.month + delta
        year = self.current_date.year

        # Handle year transitions
        if month > 12:
            month = 1
            year += 1
        elif month < 1:
            month = 12
            year -= 1

        # Set to the 1st of the new month
        self.current_date = date(year, month, 1)

        # If selected date is not in this month, reset selection to 1st
        if self.selected_date.month != month or self.selected_date.year != year:
            self.selected_date = self.current_date

        self._refresh_calendar()

    def _refresh_calendar(self) -> None:
        """Refresh the calendar display."""
        # Update month display
        month_display = self.query_one("#month-display", Static)
        month_display.update(self._get_month_display())

        # Remove old calendar grid and create new one
        old_grid = self.query_one("#calendar-grid", Grid)
        old_grid.remove()

        # Mount new grid
        new_grid = Grid(*self._get_day_buttons(), id="calendar-grid")
        self.mount(new_grid)

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        pass
