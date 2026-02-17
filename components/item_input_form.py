"""Item input form component - reusable form for adding/editing items (transactions)."""
from textual.widgets import Static, Button, Input, Select, Label, SelectionList, Switch
from textual.containers import Vertical, Horizontal, Grid, ScrollableContainer
from textual.app import ComposeResult
from textual.message import Message
from datetime import datetime
import uuid
from textual.screen import ModalScreen

from textual import on

# from textual_timepiece.pickers import DatePicker, DateSelect
# from whenever import Date, days

class ItemInputForm(ModalScreen):
    """Reusable form component for adding/editing items (transactions)."""

    BINDINGS = [
        ("escape", "dismiss_form", "Close"),
    ]

    DEFAULT_CSS = """
    ItemInputForm {
        width: 100%;
        height: 100%;
        border: solid $accent;
        padding: 1;
    }

    ItemInputForm .form-title {
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
        background: $accent;
        color: $text;
        height: 3;
    }

    ItemInputForm .form-section {
        margin: 1 0;
        padding: 1;
        background: $panel;
        border: solid $primary;
    }

    ItemInputForm .section-title {
        text-style: bold;
        color: $accent;
        padding: 0 0 1 0;
    }
    
    ItemInputForm #form-label {
        text-style: bold;
        padding: 0 0 0 0;
        height: 3;
    }
    
    ItemInputForm .form-label {
        text-style: bold;
        padding: 0 0 0 0;
        height: 1;
    }

    ItemInputForm Input {
        width: 100%;
        margin: 0 0 1 0;
    }

    ItemInputForm Select {
        width: 100%;
        margin: 0 0 1 0;
    }

    ItemInputForm .form-row {
        grid-size: 2 1;
        grid-gutter: 2;
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
    }

    ItemInputForm .form-row-3 {
        grid-size: 3 1;
        grid-gutter: 1;
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
    }

    ItemInputForm .form-buttons {
        grid-size: 3 1;
        grid-gutter: 1;
        width: 100%;
        height: auto;
        margin-top: 2;
    }

    ItemInputForm #save-button {
        background: green;
        color: white;
        width: 100%;
        height: 3;
    }

    ItemInputForm #save-button:hover {
        background: darkgreen;
    }

    ItemInputForm #clear-button {
        background: orange;
        color: white;
        width: 100%;
        height: 3;
    }

    ItemInputForm #clear-button:hover {
        background: darkorange;
    }

    ItemInputForm #cancel-button {
        background: red;
        color: white;
        width: 100%;
        height: 3;
    }

    ItemInputForm #cancel-button:hover {
        background: darkred;
    }
    """

    class ItemCreated(Message):
        """Message sent when an item is created."""
        def __init__(self, item_data: dict) -> None:
            self.item_data = item_data
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._item_uuid = str(uuid.uuid4())

    def compose(self) -> ComposeResult:
        yield Static("Add Transaction", classes="form-title")

        # horizontal layout for basic info: Item Name, Price, Currency, Date:
        with Horizontal():
            with Vertical():
                yield Static("Item Name *", classes="form-label")
                yield Input(
                    placeholder="e.g., Groceries, Rent, Salary",
                    id="item-name",
                    max_length=64
                )
            with Vertical():
                yield Static("Price *", classes="form-label")
                yield Input(
                    placeholder="0.00",
                    id="item-price",
                    type="number"
                )
            with Vertical():
                yield Static("Currency *", classes="form-label")
                yield Select(
                    options=[
                        ("USD - US Dollar", "USD"),
                        ("EUR - Euro", "EUR"),
                        ("GBP - British Pound", "GBP"),
                    ],
                    value="USD",
                    id="item-currency",
                    allow_blank=False
                )
            with Vertical():
                yield Static("Date Purchased *", classes="form-label")
                yield Input(
                    placeholder="YYYY-MM-DD",
                    id="item-bought-date",
                    value=datetime.now().strftime("%Y-%m-%d")
                )

        with Horizontal():
            with Vertical():
                yield Static("Bought By *", classes="form-label")
                yield Select(
                    options=[("user 1", 1), ("user 2", 2)],
                    value=1,
                    id="item-bought-by",
                    allow_blank=False
                )
            with Vertical():
                yield Static("Bought For *", classes="form-label")
                yield Select(
                    options=[("user 1", 1), ("user 2", 2)],
                    value=1,
                    id="item-bought-for",
                    allow_blank=False
                )
            with Vertical():
                yield Static("Shared to *", classes="form-label")
                yield Input(type="number", placeholder="User share %", id="item-shared-to")
            with Vertical():
                yield Static("Labels", classes="form-label")
                yield SelectionList[int](
                                    ("Falken's Maze", 0, True),
                                    ("Black Jack", 1)
                )
        with Horizontal():
            with Vertical():
                yield Static("Note", classes="form-label")
                yield Input(
                    placeholder="Additional details (optional)",
                    id="item-note",
                    max_length=255
                )
        with Horizontal():
            with Vertical():
                yield Static("Exchange Rate", classes="form-label")
                yield Input(
                    placeholder="1.0",
                    id="item-exchange-rate",
                    value="1.0",
                    type="number"
                )
            with Vertical():
                yield Static("Exchange Rate Date", classes="form-label")
                yield Input(
                    placeholder="YYYY-MM-DD",
                    id="item-exchange-date",
                    value=datetime.now().strftime("%Y-%m-%d")
                )
            with Vertical():
                yield Static("Use Exchange API", classes="form-label")
                yield Switch(value=False, id="item-use-exchange-api")
        with Horizontal():
            with Vertical():
                yield Button("💾 Save", id="save-button")
            with Vertical():
                yield Button("🔄 Clear", id="clear-button")
            with Vertical():
                yield Button("❌ Cancel", id="cancel-button")


    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-button":
            self._save_item()
        elif event.button.id == "clear-button":
            self._clear_form()
        elif event.button.id == "cancel-button":
            self.dismiss()  # Dismiss the modal form

    def action_dismiss_form(self) -> None:
        """Action called when ESC is pressed - dismiss form without saving."""
        self.dismiss()

    def _save_item(self) -> None:
        """Validate and save the item."""
        try:
            # Get all input values
            name = self.query_one("#item-name", Input).value.strip()
            # note = self.query_one("#item-note", Input).value.strip()
            price = self.query_one("#item-price", Input).value.strip()
            currency = self.query_one("#item-currency", Select).value  # Get from Select
            # price_final = self.query_one("#item-price-final", Input).value.strip()
            # currency_final = self.query_one("#item-currency-final", Input).value.strip().upper()
            # exchange_rate = self.query_one("#item-exchange-rate", Input).value.strip()
            # exchange_date = self.query_one("#item-exchange-date", Input).value.strip()
            bought_date = self.query_one("#item-bought-date", Input).value.strip()
            # bought_by = self.query_one("#item-bought-by", Input).value.strip()
            # bought_for = self.query_one("#item-bought-for", Input).value.strip()
            # added_by = self.query_one("#item-added-by", Input).value.strip()
            # tags = self.query_one("#item-tags", Input).value.strip()

            # Validate required fields
            if not name:
                self.app.notify("Item name is required", severity="error")
                return
            if not price:
                self.app.notify("Price is required", severity="error")
                return
            if not currency:
                self.app.notify("Currency is required", severity="error")
                return
            # if not bought_by:
            #     self.app.notify("'Bought By' user is required", severity="error")
            #     return
            # if not bought_for:
            #     self.app.notify("'Bought For' user is required", severity="error")
            #     return
            # if not added_by:
            #     self.app.notify("'Added By' user is required", severity="error")
            #     return

            # Set defaults
            # if not price_final:
            #     price_final = price
            # if not currency_final:
            #     currency_final = currency

            # Build item data dictionary
            item_data = {
                'item_uuid': self._item_uuid,
                'name': name,
                # 'note': note,
                'price': float(price),
                # 'price_final': float(price_final),
                'currency': currency,
                # 'currency_final': currency_final,
                # 'exchange_rate': float(exchange_rate) if exchange_rate else 1.0,
                # 'exchange_rate_date': exchange_date,
                'bought_date': bought_date,
                # 'bought_by_id': int(bought_by),
                # 'bought_for_id': int(bought_for),
                # 'added_by_id': int(added_by),
                # 'tags': tags,  # Will be processed later (JSON array)
            }

            # Post message with item data
            self.post_message(self.ItemCreated(item_data))

        except ValueError as e:
            self.app.notify(f"Invalid input: {str(e)}", severity="error")
        except Exception as e:
            self.app.notify(f"Error saving item: {str(e)}", severity="error")

    def _clear_form(self) -> None:
        """Clear all form fields."""
        try:
            self.query_one("#item-name", Input).value = ""
            # self.query_one("#item-note", Input).value = ""
            self.query_one("#item-price", Input).value = ""
            self.query_one("#item-currency", Select).value = "USD"  # Reset to default
            # self.query_one("#item-price-final", Input).value = ""
            # self.query_one("#item-currency-final", Input).value = ""
            # self.query_one("#item-exchange-rate", Input).value = "1.0"
            # self.query_one("#item-exchange-date", Input).value = datetime.now().strftime("%Y-%m-%d")
            self.query_one("#item-bought-date", Input).value = datetime.now().strftime("%Y-%m-%d")
            # self.query_one("#item-bought-by", Input).value = ""
            # self.query_one("#item-bought-for", Input).value = ""
            # self.query_one("#item-added-by", Input).value = ""
            # self.query_one("#item-tags", Input).value = ""

            # Generate new UUID for next item
            self._item_uuid = str(uuid.uuid4())

            self.app.notify("Form cleared", severity="info")

        except Exception as e:
            self.app.log(f"Error clearing form: {e}")
