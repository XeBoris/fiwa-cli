"""Create Expense Form component - for adding expense transactions."""
from textual.widgets import Static, Button
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.message import Message
from components.item_input_form import ItemInputForm

from functions.loader import load_dynamic_css


class CreateExpenseForm(Vertical):
    """Widget for creating a new expense."""


    class ExpenseCreated(Message):
        """Message sent when an expense is created."""
        def __init__(self, expense_data: dict) -> None:
            self.expense_data = expense_data
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:
        """Load dynamic CSS and open the form modal."""
        try:
            load_dynamic_css(self, "screens_inputs_insert_expense.tcss")
        except Exception as e:
            self.app.log(f"Could not load external CSS for CreateExpenseForm: {e}")

        # Open the ItemInputForm modal
        self.app.push_screen(ItemInputForm(), callback=self._handle_item_created)

    def compose(self) -> ComposeResult:
        yield Static("Create New Expense", classes="form-title")

        with Vertical(classes="content-area"):
            yield Static("Click the button below to add a new expense transaction.", id="instructions")
            yield Button("📝 Add New Expense", id="open-form-button", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press to open modal."""
        if event.button.id == "open-form-button":
            self.app.push_screen(ItemInputForm(), callback=self._handle_item_created)

    def _handle_item_created(self, item_data) -> None:
        """Handle the item data returned from the modal."""
        if item_data is not None:
            # Post the ExpenseCreated message with the item data
            self.post_message(self.ExpenseCreated(item_data))
            self.app.notify(f"Expense '{item_data.get('name', 'Unknown')}' created!", severity="success")
        else:
            self.app.notify("Expense creation cancelled", severity="info")

