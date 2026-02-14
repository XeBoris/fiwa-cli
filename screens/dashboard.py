"""Dashboard screen - financial overview."""
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Static, Button
from textual.app import ComposeResult


class DashboardScreen(ModalScreen):
    """Dashboard screen - overview of financial data."""

    DEFAULT_CSS = """
    DashboardScreen {
        align: center middle;
    }

    DashboardScreen > Vertical {
        width: 80;
        height: 80%;
        background: $surface;
        border: solid $accent;
        padding: 2;
    }

    DashboardScreen #dashboard-title {
        text-style: bold;
        padding: 0 0 2 0;
        text-align: center;
    }

    DashboardScreen #dashboard-content {
        height: 1fr;
    }

    DashboardScreen #close-button {
        margin-top: 1;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Dashboard", id="dashboard-title")
            yield Static(
                "Financial overview will be displayed here.\n\n"
                "• Total balance\n"
                "• Recent transactions\n"
                "• Monthly spending\n"
                "• Budget status",
                id="dashboard-content"
            )
            yield Button("Close", id="close-button", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-button":
            self.dismiss()
