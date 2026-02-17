"""Create Expense Form component - for adding expense transactions."""
from textual.widgets import Static, Button
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.message import Message
from components.item_input_form import ItemInputForm


class CreateExpenseForm(Vertical):
    """Widget for creating a new expense."""

    DEFAULT_CSS = """
    CreateExpenseForm {
        width: 100%;
        height: 100%;
    }

    CreateExpenseForm .form-title {
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
        background: $accent;
        color: $text;
    }
    
    CreateExpenseForm .content-area {
        padding: 2;
        height: 1fr;
    }
    
    CreateExpenseForm #open-form-button {
        width: 40;
        height: 5;
        # margin: 2 auto;
        background: $primary;
    }
    
    CreateExpenseForm #open-form-button:hover {
        background: $primary-lighten-1;
    }
    """

    class ExpenseCreated(Message):
        """Message sent when an expense is created."""
        def __init__(self, expense_data: dict) -> None:
            self.expense_data = expense_data
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        yield Static("Create New Expense", classes="form-title")

        with Vertical(classes="content-area"):
            yield Static("Click the button below to add a new expense transaction.", id="instructions")
            yield Button("📝 Add New Expense", id="open-form-button", variant="primary")

    def on_mount(self) -> None:
        """Handle button press to open modal."""
        self.app.push_screen(ItemInputForm(), callback=self._handle_item_created)

    def _handle_item_created(self, item_data) -> None:
        """Handle the item data returned from the modal."""
        if item_data is not None:
            # Post the ExpenseCreated message with the item data
            self.post_message(self.ExpenseCreated(item_data))
            self.app.notify(f"Expense '{item_data.get('name', 'Unknown')}' created!", severity="success")
        else:
            self.app.notify("Expense creation cancelled", severity="info")

