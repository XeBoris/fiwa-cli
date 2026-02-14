"""Reports screen - view financial reports and analytics."""
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Static, Button
from textual.app import ComposeResult

class ReportsScreen(ModalScreen):
    """Reports screen - view financial reports and analytics."""

    DEFAULT_CSS = """
    ReportsScreen {
        align: center middle;
    }

    ReportsScreen > Vertical {
        width: 80;
        height: 80%;
        background: $surface;
        border: solid $accent;
        padding: 2;
    }

    ReportsScreen #reports-title {
        text-style: bold;
        padding: 0 0 2 0;
        text-align: center;
    }

    ReportsScreen #reports-content {
        height: 1fr;
    }

    ReportsScreen #close-button {
        margin-top: 1;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Reports", id="reports-title")
            yield Static(
                "View financial reports and analytics.\n\n"
                "• Monthly report\n"
                "• Category breakdown\n"
                "• Spending trends\n"
                "• Export to PDF",
                id="reports-content"
            )
            yield Button("Close", id="close-button", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-button":
            self.dismiss()
