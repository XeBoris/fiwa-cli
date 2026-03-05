"""Reports screen - view financial reports and analytics."""
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Static, Button
from textual.app import ComposeResult

from functions.loader import load_dynamic_css


class ReportsScreen(ModalScreen):
    """Reports screen - view financial reports and analytics."""
    def on_mount(self) -> None:
        load_dynamic_css(self, "screens_reports.tcss")
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
