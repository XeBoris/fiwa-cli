"""Calendar screen for date selection."""
from datetime import date

from textual.screen import ModalScreen
from textual.app import ComposeResult
from widgets.calendar import Calendar


class CalendarScreen(ModalScreen):
    """Screen with a calendar."""

    def __init__(self, initial_date: date | None = None) -> None:
        super().__init__()
        self.initial_date = initial_date or date.today()

    def compose(self) -> ComposeResult:
        yield Calendar(initial_date=self.initial_date)

    def on_calendar_date_selected(self, event: Calendar.DateSelected) -> None:
        """Called when a date is selected."""
        self.dismiss(event.selected_date)
