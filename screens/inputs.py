"""Inputs screen - add transactions and items."""
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Static, Button
from textual.app import ComposeResult

class InputsScreen(ModalScreen):
    """Inputs screen - add transactions and items."""

    DEFAULT_CSS = """
    InputsScreen {
        align: center middle;
    }

    InputsScreen > Vertical {
        width: 80;
        height: 80%;
        background: $surface;
        border: solid $accent;
        padding: 2;
    }

    InputsScreen #inputs-title {
        text-style: bold;
        padding: 0 0 2 0;
        text-align: center;
    }

    InputsScreen #inputs-content {
        height: 1fr;
    }

    InputsScreen #close-button {
        margin-top: 1;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Inputs", id="inputs-title")
            yield Static(
                "Add new transactions here.\n\n"
                "• Add expense\n"
                "• Add income\n"
                "• Quick entry\n"
                "• Import from file",
                id="inputs-content"
            )
            yield Button("Close", id="close-button", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-button":
            self.dismiss()
