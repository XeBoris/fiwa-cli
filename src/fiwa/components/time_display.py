"""Time display widget."""
from datetime import datetime

from textual.widgets import Static


class TimeDisplay(Static):
    """A widget to display the time."""

    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        self.update_time()
        self.set_interval(1, self.update_time)

    def update_time(self) -> None:
        """Method to update the time to the current time."""
        self.update(datetime.now().strftime("%b %d %Y %H:%M:%S"))
