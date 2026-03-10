"""Item input form component - reusable form for adding/editing items (transactions)."""
from textual.widgets import Static, Button, Input, Select, Label, SelectionList, Switch, Placeholder
from textual.containers import Vertical, Horizontal, Grid, ScrollableContainer, Container
from textual.app import ComposeResult
from textual.message import Message
from datetime import datetime
import uuid
from textual.screen import ModalScreen
import re

from textual import on

from fiwa_cli.functions.loader import load_dynamic_css

# from textual_timepiece.pickers import DatePicker, DateSelect
# from whenever import Date, days


def sanitize_string(
    text: str,
    allowed_chars: str = r'a-zA-Z0-9\s\.\,\-\_\:\;\!\?\(\)\[\]\@\#\$\%\&\+\=\'\"',
    allow_internal_spaces: bool = True
) -> tuple[str, bool]:
    """
    Sanitize and validate a string by removing invalid characters and trimming spaces.

    This function ensures that:
    - Leading and trailing spaces are removed
    - Only allowed characters are present in the string
    - First and last characters are not spaces (after trimming)

    Args:
        text: The input string to sanitize
        allowed_chars: Regex character set of allowed characters (default: a-z, A-Z, 0-9,
                      and common punctuation marks like . , - _ : ; ! ? ( ) [ ] @ # $ % & + = ' ")
        allow_internal_spaces: Whether to allow spaces within the string (default: True)

    Returns:
        A tuple of (sanitized_string, was_modified):
        - sanitized_string: The cleaned string with invalid characters removed and spaces trimmed
        - was_modified: Boolean indicating if the string was changed during sanitization

    Examples:
        >>> sanitize_string("  Hello World!  ")
        ("Hello World!", True)

        >>> sanitize_string("Hello World!")
        ("Hello World!", False)

        >>> sanitize_string("Product-Name_123", allowed_chars=r'a-zA-Z0-9\-\_')
        ("Product-Name_123", False)

        >>> sanitize_string("Test<script>alert()</script>")
        ("Testscriptalert", True)
    """
    if not text:
        return ("", False)

    # Store original for comparison
    original = text

    # First, strip leading and trailing whitespace
    text = text.strip()

    # If empty after stripping, return empty string
    if not text:
        return ("", original != "")

    # Build the regex pattern
    if allow_internal_spaces:
        pattern = f'^[{allowed_chars}]+$'
    else:
        # Remove \s from allowed_chars if spaces are not allowed
        allowed_chars_no_space = allowed_chars.replace(r'\s', '')
        pattern = f'^[{allowed_chars_no_space}]+$'

    # Filter out invalid characters
    sanitized = ''.join(char for char in text if re.match(f'[{allowed_chars}]', char))

    # Strip again to remove any trailing/leading spaces that might remain
    sanitized = sanitized.strip()

    # Check if the string was modified
    was_modified = (original != sanitized)

    return (sanitized, was_modified)


class LabelModalScreen(ModalScreen):
    """Modal screen for selecting labels for a transaction.

    Labels are organized by type in tabs:
    - Type 0: Transactional labels
    - Type 1: Konto (Account) labels
    - Type 2: Category labels

    This tab-based design scales well with many labels.
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]


    def __init__(self, project_labels: list, selected_labels: list = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_labels = project_labels
        self.selected_labels = selected_labels or []

        # Organize labels by type
        self.labels_by_type = {
            0: [],  # Transactional
            1: [],  # Konto
            2: []   # Category
        }

        for label in project_labels:
            label_type = label.get('label_type', 0)
            if label_type in self.labels_by_type:
                self.labels_by_type[label_type].append(label)

    def compose(self) -> ComposeResult:
        from textual.widgets import TabbedContent, TabPane

        with Vertical():
            with Vertical(classes="modal-header"):
                yield Static("Select Labels for Transaction", classes="modal-title")
                yield Static(f"Currently selected: {len(self.selected_labels)} label(s)",
                           id="selection-count", classes="selection-count")

            with TabbedContent(initial="tab-transactional"):
                # Tab 1: Transactional Labels (Type 0)
                with TabPane("🔄 Transactional", id="tab-transactional"):
                    if self.labels_by_type[0]:
                        with ScrollableContainer():
                            yield SelectionList[int](
                                *[(label['name'], label['label_id'], label['label_id'] in self.selected_labels)
                                  for label in self.labels_by_type[0]],
                                id="label-selection-transactional"
                            )
                    else:
                        yield Static("No transactional labels available", classes="no-labels-message")

                # Tab 2: Konto Labels (Type 1)
                with TabPane("💼 Konto", id="tab-konto"):
                    if self.labels_by_type[1]:
                        with ScrollableContainer():
                            yield SelectionList[int](
                                *[(label['name'], label['label_id'], label['label_id'] in self.selected_labels)
                                  for label in self.labels_by_type[1]],
                                id="label-selection-konto"
                            )
                    else:
                        yield Static("No konto labels available", classes="no-labels-message")

                # Tab 3: Category Labels (Type 2)
                with TabPane("📁 Category", id="tab-category"):
                    if self.labels_by_type[2]:
                        with ScrollableContainer():
                            yield SelectionList[int](
                                *[(label['name'], label['label_id'], label['label_id'] in self.selected_labels)
                                  for label in self.labels_by_type[2]],
                                id="label-selection-category"
                            )
                    else:
                        yield Static("No category labels available", classes="no-labels-message")

            with Horizontal(classes="button-row"):
                yield Button("🗑️ Clear All", id="label-clear-button", variant="warning")
                yield Button("✓ OK", id="label-ok-button", variant="success")
                yield Button("✗ Cancel", id="label-cancel-button", variant="error")

    def on_mount(self) -> None:
        """Load CSS and update selection count when mounted."""
        try:
            load_dynamic_css(self, "components_label_modal.tcss")
        except Exception as e:
            self.app.log(f"Could not load CSS for LabelModalScreen: {e}")
        self._update_selection_count()

    def on_selection_list_selected_changed(self, event: SelectionList.SelectedChanged) -> None:
        """Update selection count when selection changes."""
        self._update_selection_count()

    def _update_selection_count(self) -> None:
        """Update the selection count display."""
        try:
            selected = []
            # Collect from all three lists
            for list_id in ["label-selection-transactional", "label-selection-konto", "label-selection-category"]:
                try:
                    sel_list = self.query_one(f"#{list_id}", SelectionList)
                    selected.extend(list(sel_list.selected))
                except:
                    pass

            count_widget = self.query_one("#selection-count", Static)
            count_widget.update(f"Currently selected: {len(selected)} label(s)")
        except:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the label modal."""
        if event.button.id == "label-ok-button":
            # Get selected labels from all three SelectionLists
            selected = []
            try:
                # Collect from transactional labels
                try:
                    sel_list = self.query_one("#label-selection-transactional", SelectionList)
                    selected.extend(list(sel_list.selected))
                except:
                    pass

                # Collect from konto labels
                try:
                    sel_list = self.query_one("#label-selection-konto", SelectionList)
                    selected.extend(list(sel_list.selected))
                except:
                    pass

                # Collect from category labels
                try:
                    sel_list = self.query_one("#label-selection-category", SelectionList)
                    selected.extend(list(sel_list.selected))
                except:
                    pass

                self.dismiss(selected)  # Return list of selected label IDs
            except Exception as e:
                self.app.log(f"Error collecting selected labels: {e}")
                self.dismiss([])  # Return empty list on error

        elif event.button.id == "label-clear-button":
            # Clear all selections
            for list_id in ["label-selection-transactional", "label-selection-konto", "label-selection-category"]:
                try:
                    sel_list = self.query_one(f"#{list_id}", SelectionList)
                    sel_list.deselect_all()
                except:
                    pass
            self._update_selection_count()

        elif event.button.id == "label-cancel-button":
            self.dismiss(None)  # Return None to indicate cancellation

    def action_cancel(self) -> None:
        """Handle ESC key press."""
        self.dismiss(None)


class ItemConfirmationModal(ModalScreen):
    """Modal screen to confirm item creation before saving to database.

    Shows transaction summary including:
    - Item details (name, price, currency)
    - Final price in project's main currency
    - Cost-sharing breakdown if costs are split between users
    - Labels attached to the transaction
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]


    def __init__(self, item_data: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_data = item_data

    def on_mount(self) -> None:
        """Load CSS when modal is mounted."""
        try:
            load_dynamic_css(self, "components_item_confirmation_modal.tcss")
        except Exception as e:
            self.app.log(f"Could not load CSS for ItemConfirmationModal: {e}")

    def compose(self) -> ComposeResult:
        # Debug logging
        self.app.log("=== ItemConfirmationModal compose called ===")
        self.app.log(f"item_data keys: {list(self.item_data.keys())}")
        self.app.log(f"name: {self.item_data.get('name')}")
        self.app.log(f"price: {self.item_data.get('price')}")
        self.app.log(f"currency: {self.item_data.get('currency')}")
        self.app.log(f"cost_shares: {self.item_data.get('cost_shares')}")

        with Vertical():
            yield Static("Confirm Transaction", classes="modal-title")

            # Basic transaction info
            with Vertical(classes="summary-section"):
                yield Static("[bold]Transaction Summary[/bold]", classes="section-title")
                yield Static(f"Item: {self.item_data.get('name', 'N/A')}", classes="summary-row")
                yield Static(f"Original Price: {self.item_data.get('price', 0):.2f} {self.item_data.get('currency', 'N/A')}",
                           classes="summary-row")

                # Show exchange rate if different from main currency
                if self.item_data.get('currency') != self.item_data.get('currency_final'):
                    yield Static(f"Exchange Rate: {self.item_data.get('exchange_rate', 1.0):.4f}",
                               classes="summary-row")

                yield Static(f"[bold]Final Price: {self.item_data.get('price_final', 0):.2f} {self.item_data.get('currency_final', 'N/A')}[/bold]",
                           classes="total-row")
                yield Static(f"Date: {self.item_data.get('bought_date', 'N/A')}", classes="summary-row")
                yield Static(f"Bought By: {self.item_data.get('bought_by_name', 'N/A')}", classes="summary-row")

                if self.item_data.get('labels_text') and self.item_data.get('labels_text') != "None":
                    yield Static(f"Labels: {self.item_data.get('labels_text', '')}", classes="summary-row")

            # Cost-sharing breakdown
            cost_shares = self.item_data.get('cost_shares', [])
            if cost_shares:
                with Vertical(classes="summary-section"):
                    yield Static("[bold]Cost Sharing Breakdown[/bold]", classes="section-title")

                    # Calculate total percentage for validation
                    total_percentage = sum(share.get('percentage', 0) for share in cost_shares)

                    for share in cost_shares:
                        username = share.get('username', 'Unknown')
                        percentage = share.get('percentage', 0)
                        amount = share.get('amount', 0)
                        currency_final = self.item_data.get('currency_final', 'USD')

                        if percentage > 0:
                            yield Static(
                                f"  {username}: {percentage:.1f}% = {amount:.2f} {currency_final}",
                                classes="cost-share-row"
                            )
                        elif share.get('user_id') == self.item_data.get('bought_by_id'):
                            # Show bought_by user even if they pay 0% (others pay 100%)
                            yield Static(
                                f"  {username}: {percentage:.1f}% = {amount:.2f} {currency_final}",
                                classes="cost-share-row"
                            )

                    # Show total
                    total_amount = sum(share.get('amount', 0) for share in cost_shares)
                    yield Static(
                        f"[bold]Total: {total_amount:.2f} {self.item_data.get('currency_final', 'USD')}[/bold]",
                        classes="total-row"
                    )

                    # Validation: Check if total percentage equals 100%
                    # Allow small tolerance for floating point errors (0.01%)
                    percentage_valid = abs(total_percentage - 100.0) < 0.01

                    if not percentage_valid:
                        yield Static(
                            f"[bold red]⚠ WARNING: Total percentage is {total_percentage:.1f}% (should be 100%)[/bold red]",
                            classes="validation-error"
                        )
                        yield Static(
                            "[red]Cannot save to database. Please go back and adjust the cost sharing percentages.[/red]",
                            classes="validation-message"
                        )

            with Horizontal(classes="button-row"):
                # Disable OK button if cost shares don't add up to 100%
                ok_button_disabled = False
                if cost_shares:
                    total_percentage = sum(share.get('percentage', 0) for share in cost_shares)
                    ok_button_disabled = abs(total_percentage - 100.0) >= 0.01

                yield Button(
                    "✓ OK - Save to Database" if not ok_button_disabled else "✗ Cannot Save - Invalid Total",
                    id="confirm-ok-button",
                    variant="success" if not ok_button_disabled else "error",
                    flat=True,
                    compact=True,
                    disabled=ok_button_disabled
                )
                yield Button("← Back - Edit", id="confirm-back-button", variant="warning", flat=True, compact=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the confirmation modal."""
        if event.button.id == "confirm-ok-button":
            self.dismiss(True)  # Return True to indicate save
        elif event.button.id == "confirm-back-button":
            self.dismiss(False)  # Return False to indicate cancel

    def action_cancel(self) -> None:
        """Handle ESC key press."""
        self.dismiss(False)


class DeleteConfirmationModal(ModalScreen):
    """Modal screen for confirming item deletion.

    Shows a warning dialog with the item name and asks for user confirmation
    before proceeding with deletion. This prevents accidental deletions.
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]


    def __init__(self, item_name: str):
        super().__init__()
        self.item_name = item_name

    def on_mount(self) -> None:
        """Load CSS when modal is mounted."""
        try:
            load_dynamic_css(self, "components_delete_confirmation_modal.tcss")
        except Exception as e:
            self.app.log(f"Could not load CSS for DeleteConfirmationModal: {e}")

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("⚠️ DELETE EXPENSE ⚠️", classes="warning-title")
            yield Static(
                f"Are you sure you want to delete:\n\n'{self.item_name}'?\n\nThis action cannot be undone!",
                classes="warning-message"
            )
            with Horizontal(classes="button-row"):
                yield Button("Delete", id="confirm-delete", variant="error")
                yield Button("Cancel", id="cancel-delete", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the confirmation modal."""
        if event.button.id == "confirm-delete":
            self.dismiss(True)  # User confirmed
        else:
            self.dismiss(False)  # User cancelled

    def action_cancel(self) -> None:
        """Handle ESC key press."""
        self.dismiss(False)


class ItemInputForm(ModalScreen):
    """Reusable form component for adding/editing items (transactions)."""

    BINDINGS = [
        ("escape", "dismiss_form", "Close"),
    ]


    class ItemCreated(Message):
        """Message sent when an item is created and saved to database."""
        def __init__(self, item_id: int, item_data: dict) -> None:
            self.item_id = item_id
            self.item_data = item_data
            super().__init__()

    def __init__(self, edit_mode: bool = False, item_data: dict = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._edit_mode = edit_mode
        self._item_data = item_data  # Store item data for edit mode
        self._item_uuid = item_data['item_uuid'] if edit_mode and item_data else str(uuid.uuid4())
        self._item_id = item_data['item_id'] if edit_mode and item_data else None
        self._pending_item_data = None
        self._project_users = []  # Store project users for dynamic updates

        # Load selected labels from item_data in edit mode
        if edit_mode and item_data and item_data.get('tags'):
            import json
            try:
                # Parse tags if it's a JSON string
                if isinstance(item_data['tags'], str):
                    self._selected_label_ids = json.loads(item_data['tags'])
                else:
                    self._selected_label_ids = item_data['tags']
            except:
                self._selected_label_ids = []
        else:
            self._selected_label_ids = []

    def on_mount(self) -> None:
        """Called when the form is mounted - load CSS and check widgets."""
        self.app.log("=== ItemInputForm on_mount called ===")

        # Load CSS with detailed logging
        try:
            self.app.log("Attempting to load CSS: components_item_input_form.tcss")
            load_dynamic_css(self, "components_item_input_form.tcss")
            self.app.log("✓ CSS load completed (check logs above for success/failure)")
        except Exception as e:
            self.app.log(f"✗ EXCEPTION loading CSS for ItemInputForm: {e}")

        try:

            # Update label button if labels are pre-selected (edit mode)
            if self._selected_label_ids:
                try:
                    button = self.query_one("#open-label-modal-button", Button)
                    button.label = f"🏷️ Labels ({len(self._selected_label_ids)})"
                except Exception as e:
                    self.app.log(f"Could not update label button: {e}")

            # Try to find the bought-for grid
            try:
                grid = self.query_one("#bought-for-grid")
                self.app.log(f"✓ Found bought-for-grid on mount: {grid}")
                self.app.log(f"  Grid children count: {len(list(grid.children))}")
                self.app.log(f"  Grid styles: width={grid.styles.width}, height={grid.styles.height}")
            except Exception as e:
                self.app.log(f"✗ Could not find bought-for-grid on mount: {e}")

            # List all grids
            all_grids = list(self.query(Grid))
            self.app.log(f"Total grids found: {len(all_grids)}")
            for idx, g in enumerate(all_grids):
                self.app.log(f"  Grid {idx}: id={g.id}, children={len(list(g.children))}")

        except Exception as e:
            self.app.log(f"Error in on_mount: {e}")

    def _get_project_users(self, project_id: int) -> list:
        """Get all users for the current project."""
        try:
            dbh = self.app._config.get("dbh")
            if dbh and project_id > 0:
                users = dbh.op_project_get_users(project_id)
                return users
            return []
        except Exception as e:
            self.app.log(f"Error fetching project users: {e}")
            return []

    def _get_project_labels(self, project_id: int) -> list:
        """Get all labels for the current project."""
        try:
            dbh = self.app._config.get("dbh")
            if dbh and project_id > 0:
                labels = dbh.op_label_get_all(project_id)
                # Only return active labels (status = 2)
                return [label for label in labels if label.get('label_status', 0) == 2]
            return []
        except Exception as e:
            self.app.log(f"Error fetching project labels: {e}")
            return []

    def compose(self) -> ComposeResult:
        # Get project data from app_state
        project_id = self.app.app_state.get("project_id", 0)
        user_id = self.app.app_state.get("user_id", -1)
        user_name = self.app.app_state.get("user_name", "Guest")

        # Different title for edit vs create mode
        if self._edit_mode:
            yield Static(f"Edit Transaction - {user_name}", classes="form-title")
        else:
            yield Static(f"Add Transaction - {user_name}", classes="form-title")

        # Get currencies from project
        currency_main = self.app.app_state.get("current_project_currency_main", "USD")
        currency_list = self.app.app_state.get("current_project_currency_list", [])

        # Build currency options:
        # - Main currency first (bold)
        # - Other currencies after (italic)
        currency_options = [(f"[bold]{currency_main}[/bold]", currency_main)]
        for curr in currency_list:
            if curr != currency_main:
                currency_options.append((f"[italic]{curr}[/italic]", curr))

        # Get project users
        project_users = self._get_project_users(project_id)
        self._project_users = project_users  # Store for later use
        user_options = [(u['username'], u['user_id']) for u in project_users]

        # Show ALL project users in the "Bought For" section
        # Logic: By default, bought_by user gets 100% (buying for themselves)
        # Users can then adjust to share costs with others
        user_options_share_to = [(u['username'], u['user_id']) for u in project_users]

        # Determine default bought_by user (current user or first in list)
        default_bought_by_id = user_id if user_id > 0 else (user_options[0][1] if user_options else -1)

        # Get project labels
        project_labels = self._get_project_labels(project_id)
        label_options = [(label['name'], label['label_id']) for label in project_labels]
        #
        with Grid(classes="form-grid-row-1"):
            # row 1
            yield Static("Item Name *", classes="form-grid-label")
            yield Static("Price *", classes="form-grid-label")
            yield Static("Currency *", classes="form-grid-label")
            yield Static("Date Purchased *", classes="form-grid-label")
            yield Static("Bought by *", classes="form-grid-label")
            yield Static("", classes="form-grid-label")
            # row 2
            yield Input(
                placeholder="e.g., Groceries, Rent, Salary",
                id="grid-item-name",
                max_length=64,
                value=self._item_data['name'] if self._edit_mode and self._item_data else ""
            )
            yield Input(
                placeholder="0.00",
                id="grid-item-price",
                type="number",
                value=str(self._item_data['price']) if self._edit_mode and self._item_data else ""
            )
            yield Select(
                options=currency_options if currency_options else [("USD", "USD")],
                value=self._item_data['currency'] if self._edit_mode and self._item_data else (currency_main if currency_main else "USD"),
                id="grid-item-currency",
                allow_blank=False
            )
            yield Input(
                placeholder="YYYY-MM-DD",
                id="grid-item-bought-date",
                value=str(self._item_data['bought_date']).split()[0] if self._edit_mode and self._item_data else datetime.now().strftime("%Y-%m-%d")
            )
            yield Select(
                options=user_options if user_options else [("No users", -1)],
                value=self._item_data['bought_by_id'] if self._edit_mode and self._item_data else (user_id if user_id > 0 else (user_options[0][1] if user_options else -1)),
                id="grid-item-bought-by",
                allow_blank=False
            )
            yield Button("🏷️ Labels",
                         id="open-label-modal-button",
                         variant="default",
                         compact=True)

        # Main horizontal layout - different for create vs edit mode
        with Horizontal(id="bought-for-horizontal-wrapper"):
            # Left side: Bought For section (only in create mode)
            if not self._edit_mode:
                user_count = len(user_options_share_to)

                self.app.log(f"=== BOUGHT FOR SECTION DEBUG ===")
                self.app.log(f"user_count: {user_count}")
                self.app.log(f"user_options_share_to: {user_options_share_to}")

                if user_count > 0:
                    self.app.log(f"Creating Vertical layout with {user_count} users")

                    with ScrollableContainer(id="bought-for-scroll"):
                        with Vertical(id="bought-for-wrapper"):
                            # Title (using class, not ID to avoid duplicates when rebuilding)
                            yield Static("Bought For *", classes="bought-for-title")
                            self.app.log("Yielded bought-for-title")

                            # Add each user as a Horizontal row
                            for idx, i_item in enumerate(user_options_share_to):
                                self.app.log(f"Adding user {idx + 1}/{user_count}: {i_item[0]} (ID: {i_item[1]})")

                                # Set default share: 100% for bought_by user, 0% for others
                                default_share = "100" if i_item[1] == default_bought_by_id else "0"

                                with Horizontal(classes="bought-for-user-row"):
                                    yield Static(f"{i_item[0]}", id=f"user-label-{i_item[1]}", classes="user-name-label")
                                    yield Input(
                                        placeholder="0-100%",
                                        value=default_share,
                                        type="number",
                                        id=f"share-{i_item[1]}",
                                        classes="user-share-input"
                                    )
                            self.app.log("Finished adding all users")
                else:
                    self.app.log("No users - creating fallback container")
                    with ScrollableContainer(id="bought-for-scroll"):
                        with Vertical(id="bought-for-wrapper"):
                            yield Static("Bought For *", classes="bought-for-title")
                            yield Static("No users available", classes="bought-for-no-users")

            # Right side: Exchange rate, date, and note fields (always shown)
            with Vertical(id="additional-content-wrapper"):
                # Exchange Rate
                with Horizontal(classes="exchange-rate-row"):
                    with Vertical(classes="field-group"):
                        yield Static("Exchange Rate", classes="form-label")
                        yield Input(
                            placeholder="1.0",
                            id="item-exchange-rate",
                            value=str(self._item_data['exchange_rate']) if self._edit_mode and self._item_data else "1.0",
                            type="number"
                        )
                    with Vertical(classes="field-group"):
                        yield Static("Exchange Rate Date", classes="form-label")
                        yield Input(
                            placeholder="YYYY-MM-DD",
                            id="item-exchange-date",
                            value=str(self._item_data['exchange_rate_date']).split()[0] if self._edit_mode and self._item_data else datetime.now().strftime("%Y-%m-%d")
                        )

                # Note field
                with Horizontal(classes="note-row"):
                    with Vertical(classes="field-group-full"):
                        yield Static("Note", classes="form-label")
                        yield Input(
                            placeholder="Additional details (optional)",
                            id="item-note",
                            max_length=255,
                            value=self._item_data['note'] if self._edit_mode and self._item_data and self._item_data['note'] else ""
                        )

        with Horizontal(classes="button-row"):
            yield Button("💾 Save", id="save-button")
            yield Button("🔄 Clear", id="clear-button")
            # Show Delete button only in edit mode
            if self._edit_mode:
                yield Button("🗑️ Delete", id="delete-button", variant="error")
            yield Button("❌ Cancel", id="cancel-button")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-button":
            await self._save_item()
        elif event.button.id == "clear-button":
            self._clear_form()
        elif event.button.id == "delete-button":
            await self._delete_item()
        elif event.button.id == "cancel-button":
            self.dismiss()  # Dismiss the modal form
        elif event.button.id == "open-label-modal-button":
            # Use run_worker to properly handle push_screen_wait
            self.run_worker(self._open_label_modal())

    async def _open_label_modal(self) -> None:
        """Open the label selection modal and handle the result."""
        try:
            # Get project labels
            project_id = self.app.app_state.get("project_id", 0)
            project_labels = self._get_project_labels(project_id)

            # Open modal with current selections (now in worker context)
            result = await self.app.push_screen_wait(
                LabelModalScreen(project_labels, self._selected_label_ids)
            )

            if result is not None:  # User clicked OK (result is list of label IDs)
                self._selected_label_ids = result
                self.app.log(f"Selected labels: {self._selected_label_ids}")

                # Update button text to show count
                button = self.query_one("#open-label-modal-button", Button)
                if len(self._selected_label_ids) > 0:
                    button.label = f"🏷️ Labels ({len(self._selected_label_ids)})"
                else:
                    button.label = "🏷️ Select Labels"

                #self.app.notify(f"{len(self._selected_label_ids)} label(s) selected", severity="info")
            else:  # User clicked Cancel
                self.app.log("Label selection cancelled")

        except Exception as e:
            self.app.log(f"Error opening label modal: {e}")
            #self.app.notify(f"Error: {str(e)}", severity="error")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select widget changes."""
        if event.select.id == "grid-item-bought-by":
            # User changed the "bought by" selection
            selected_user_id = event.value
            # Only update bought-for section if not in edit mode (section doesn't exist in edit mode)
            if not self._edit_mode:
                self._update_bought_for_section(selected_user_id)

    def _update_bought_for_section(self, selected_bought_by_id: int) -> None:
        """Update the 'Bought For' section when bought_by user changes.

        Logic: The bought_by user should automatically get 100% share (buying for themselves).
        All other users get 0% by default. Users can then adjust percentages to share costs.

        Args:
            selected_bought_by_id: The user ID of the person selected in "Bought By"
        """
        self.app.log(f"Updating 'Bought For' section, bought_by user: {selected_bought_by_id}")

        # Include ALL users in the bought-for section
        user_options_share_to = [
            (u['username'], u['user_id'])
            for u in self._project_users
        ]

        self.app.log(f"All users for bought-for: {user_options_share_to}")

        user_count = len(user_options_share_to)

        # Update Section:
        wrapper = self.query_one("#bought-for-wrapper", Vertical)

        # Remove all children
        wrapper.remove_children()
        # Force a refresh to ensure children are removed
        wrapper.refresh()

        # Rebuild the content
        # Add title (no ID to avoid duplicates when rebuilding)
        title = Static("Bought For *", classes="bought-for-title")
        wrapper.mount(title)

        # Add users
        for i_item in user_options_share_to:
            # Set share: 100% for bought_by user, 0% for others
            default_share = "100" if i_item[1] == selected_bought_by_id else "0"

            # Create user row container
            user_row = Horizontal(classes="bought-for-user-row")

            # Mount the row to wrapper first
            wrapper.mount(user_row)

            # Then mount children to the row
            user_row.mount(Static(
                f"{i_item[0]}",
                id=f"user-label-{i_item[1]}",
                classes="user-name-label"
            ))
            user_row.mount(Input(
                placeholder="0-100%",
                value=default_share,
                type="number",
                id=f"share-{i_item[1]}",
                classes="user-share-input"
            ))

            self.app.log(f"Added user {i_item[0]} with share {default_share}%")

        self.app.log(f"✓ Successfully updated bought-for section with {user_count} users")


    def action_dismiss_form(self) -> None:
        """Action called when ESC is pressed - dismiss form without saving."""
        self.dismiss()

    async def _save_item(self) -> None:
        """Validate and prepare item data, then show confirmation modal."""
        try:
            # Get project and user data
            project_id = self.app.app_state.get("project_id", 0)
            user_id = self.app.app_state.get("user_id", -1)
            currency_main = self.app.app_state.get("current_project_currency_main", "USD")

            # Get all input values
            name = self.query_one("#grid-item-name", Input).value.strip()
            price = self.query_one("#grid-item-price", Input).value.strip()
            currency = self.query_one("#grid-item-currency", Select).value
            bought_date = self.query_one("#grid-item-bought-date", Input).value.strip()
            bought_by_id = self.query_one("#grid-item-bought-by", Select).value

            # Get exchange rate and date from input fields (correct IDs: item-exchange-*, not grid-item-exchange-*)
            exchange_rate_input = self.query_one("#item-exchange-rate", Input).value.strip()
            exchange_date_input = self.query_one("#item-exchange-date", Input).value.strip()
            note = self.query_one("#item-note", Input).value.strip()

            # Sanitize name and note to remove invalid characters and trim spaces
            # Allow alphanumeric, spaces, and common punctuation
            name, name_modified = sanitize_string(name, allowed_chars=r'a-zA-Z0-9\s\.\,\-\_\:\;\!\?\(\)\[\]\@\#\$\%\&\+\=\'\"')
            note, note_modified = sanitize_string(note, allowed_chars=r'a-zA-Z0-9\s\.\,\-\_\:\;\!\?\(\)\[\]\@\#\$\%\&\+\=\'\"')

            # Notify user if their input was modified
            if name_modified:
                self.app.notify("Item name was cleaned (removed invalid characters or spaces)", severity="warning")
            if note_modified:
                self.app.notify("Note was cleaned (removed invalid characters or spaces)", severity="warning")

            # Use exchange rate from input field, default to 1.0 if not provided
            exchange_rate_float = float(exchange_rate_input) if exchange_rate_input else 1.0

            # Use exchange date from input field, default to bought_date if not provided
            exchange_rate_date = exchange_date_input if exchange_date_input else bought_date

            # Get selected labels from the modal
            selected_labels = self._selected_label_ids

            # Get label names for display
            project_labels = self._get_project_labels(project_id)
            label_names = [label['name'] for label in project_labels if label['label_id'] in selected_labels]
            labels_text = ", ".join(label_names) if label_names else "None"

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
            if bought_by_id <= 0:
                self.app.notify("'Bought By' user is required", severity="error")
                return

            # Convert price
            price_float = float(price)


            price_final = price_float * exchange_rate_float
            currency_final = currency_main

            # Get project users for name lookup
            project_users = self._get_project_users(project_id)
            bought_by_user = next((u for u in project_users if u['user_id'] == bought_by_id), None)
            bought_by_name = bought_by_user['username'] if bought_by_user else "Unknown"

            # Collect cost-sharing data from bought-for section (only in create mode)
            cost_shares = []
            total_percentage = 0.0

            if not self._edit_mode:
                # Collect shares from ALL users (including bought_by user)
                # Validate that user inputs sum to exactly 100%
                for user in project_users:
                    try:
                        share_input = self.query_one(f"#share-{user['user_id']}", Input)
                        share_value = share_input.value.strip()

                        if share_value:
                            share_percent = float(share_value)
                            share_amount = (price_final * share_percent) / 100.0
                            cost_shares.append({
                                'user_id': user['user_id'],
                                'username': user['username'],
                                'percentage': share_percent,
                                'amount': share_amount
                            })
                            total_percentage += share_percent
                        else:
                            # Empty field = 0%
                            cost_shares.append({
                                'user_id': user['user_id'],
                                'username': user['username'],
                                'percentage': 0.0,
                                'amount': 0.0
                            })
                    except Exception as e:
                        self.app.log(f"Error reading share for user {user['user_id']}: {e}")
                        # Input field not found or invalid value - treat as 0%
                        cost_shares.append({
                            'user_id': user['user_id'],
                            'username': user['username'],
                            'percentage': 0.0,
                            'amount': 0.0
                        })

                # VALIDATE: Total must equal exactly 100% (with small tolerance for floating point)
                if abs(total_percentage - 100.0) >= 0.01:
                    if total_percentage > 100.0:
                        self.app.notify(f"⚠ Cost share total is {total_percentage:.1f}% - exceeds 100%! Please adjust.", severity="error")
                    else:
                        self.app.notify(f"⚠ Cost share total is {total_percentage:.1f}% - must be 100%! Please adjust.", severity="error")
                    return
            else:
                # In edit mode, just update the single item - no cost sharing
                cost_shares.append({
                    'user_id': bought_by_id,
                    'username': bought_by_name,
                    'percentage': 100.0,
                    'amount': price_final
                })

            # Build complete item data dictionary
            item_data = {
                'item_uuid': self._item_uuid,
                'name': name,
                'note': note,
                'price': price_float,
                'price_final': price_final,
                'currency': currency,
                'currency_final': currency_final,
                'exchange_rate': exchange_rate_float,
                'exchange_rate_date': exchange_rate_date,
                'bought_date': bought_date,
                'bought_by_id': bought_by_id,
                'bought_by_name': bought_by_name,
                'added_by_id': user_id,
                'project_id': project_id,
                'tags': selected_labels,
                'labels_text': labels_text,
                'cost_shares': cost_shares,  # List of cost sharing breakdown
                'total_shared_percentage': total_percentage,
            }

            # Store item data for confirmation
            self._pending_item_data = item_data

            # Show confirmation modal using run_worker for proper async context
            self.run_worker(self._show_confirmation_and_save())

        except ValueError as e:
            self.app.notify(f"Invalid input: {str(e)}", severity="error")
        except Exception as e:
            self.app.notify(f"Error saving item: {str(e)}", severity="error")
            self.app.log(f"Error in _save_item: {e}")
            import traceback
            self.app.log(f"Traceback: {traceback.format_exc()}")

    async def _show_confirmation_and_save(self) -> None:
        """Show confirmation modal and handle the save process."""
        try:
            # Show the confirmation modal and wait for result
            result = await self.app.push_screen_wait(ItemConfirmationModal(self._pending_item_data))

            if result:  # User clicked OK
                if self._edit_mode:
                    # Update existing item in database
                    success = await self._update_in_database(self._pending_item_data)
                    if success:
                        self.app.notify(f"✓ Transaction '{self._pending_item_data['name']}' updated successfully!", severity="success")
                        # Dismiss the form and return the item_id to trigger refresh
                        self.dismiss(self._item_id)
                    else:
                        self.app.notify("Failed to update transaction", severity="error")
                else:
                    # Save new item to database
                    item_id = await self._save_to_database(self._pending_item_data)
                    if item_id:
                        self.app.notify(f"✓ Transaction '{self._pending_item_data['name']}' saved successfully!", severity="success")

                        # Post message to notify parent screens that item was created
                        self.post_message(self.ItemCreated(item_id, self._pending_item_data))

                        # Clear the pending data
                        self._pending_item_data = None

                        # Clear the form for next entry
                        self._clear_form()

                        # Generate new UUID
                        self._item_uuid = str(uuid.uuid4())
                    else:
                        self.app.notify("Failed to save transaction", severity="error")
            else:
                # User clicked Back - they can continue editing the form
                self.app.log("User clicked back, continuing to edit")

        except Exception as e:
            self.app.notify(f"Error in confirmation: {str(e)}", severity="error")
            self.app.log(f"Error in _show_confirmation_and_save: {e}")

    async def _save_to_database(self, item_data: dict) -> int:
        """Save the item to the database using op_item_create.

        For cost-sharing transactions, this creates one item entry for each user
        who shares the cost, with their respective share amounts.

        Returns:
            item_id of the first created item if successful, None otherwise
        """
        try:
            dbh = self.app._config.get("dbh")
            if not dbh:
                self.app.notify("Database connection not available", severity="error")
                self.app.log("ERROR: Database handler not available in _config")
                return None

            # Get cost shares - each user gets their own item entry
            cost_shares = item_data.get('cost_shares', [])

            if not cost_shares:
                self.app.notify("No cost shares defined", severity="error")
                self.app.log("ERROR: cost_shares is empty")
                return None

            self.app.log(f"Creating {len(cost_shares)} item entries for cost sharing")

            # Keep track of created item IDs
            created_item_ids = []

            # Create one item entry for each user who shares the cost
            for share in cost_shares:
                user_id = share.get('user_id')
                share_amount = share.get('amount')  # Final price share
                share_percentage = share.get('percentage', 100.0)
                username = share.get('username')

                # Calculate proportional original price (in original currency)
                original_price_share = (item_data['price'] * share_percentage) / 100.0

                # Prepare item data for this specific user's share
                db_item_data = {
                    'item_uuid': item_data['item_uuid'],
                    'name': item_data['name'],
                    'note': item_data.get('note', ''),
                    'price': original_price_share,  # Split original price by percentage
                    'price_final': share_amount,  # Split final converted price by percentage
                    'currency': item_data['currency'],
                    'currency_final': item_data['currency_final'],
                    'bought_date': item_data['bought_date'],
                    'bought_by_id': item_data['bought_by_id'],
                    'bought_for_id': user_id,  # This user receives/shares this portion
                    'added_by_id': item_data['added_by_id'],
                    'project_id': item_data['project_id'],
                    'exchange_rate': item_data['exchange_rate'],
                    'exchange_rate_date': item_data['exchange_rate_date'],
                    'tags': item_data['tags'],  # Convert to JSON below
                }

                # Convert tags list to JSON string
                import json
                db_item_data['tags'] = json.dumps(db_item_data['tags'])

                # Log the data being saved with both prices
                self.app.log(f"Saving item share for {username}: "
                           f"{original_price_share:.2f} {item_data['currency']} → "
                           f"{share_amount:.2f} {item_data['currency_final']} "
                           f"({share_percentage:.1f}%)")

                # Save to database
                item_id = dbh.op_item_create(db_item_data)

                if item_id:
                    created_item_ids.append(item_id)
                    self.app.log(f"✓ Item share saved with ID: {item_id} for user {username}")
                else:
                    self.app.log(f"ERROR: Failed to save item share for user {username}")

            # Return the first item ID if any were created
            if created_item_ids:
                self.app.log(f"✓ Successfully saved {len(created_item_ids)} item entries")
                return created_item_ids[0]
            else:
                self.app.notify("Failed to save any item entries to database", severity="error")
                self.app.log("ERROR: No items were successfully created")
                return None

        except Exception as e:
            self.app.notify(f"Database error: {str(e)}", severity="error")
            self.app.log(f"EXCEPTION in _save_to_database: {e}")
            import traceback
            self.app.log(f"Traceback: {traceback.format_exc()}")
            return None

    async def _update_in_database(self, item_data: dict) -> bool:
        """Update an existing item in the database.

        In edit mode, we only update the single item (no cost sharing changes).

        Returns:
            True if successful, False otherwise
        """
        try:
            dbh = self.app._config.get("dbh")
            if not dbh:
                self.app.notify("Database connection not available", severity="error")
                return False

            # Prepare UPDATE query
            dbh.load()

            import json
            tags_json = json.dumps(item_data['tags'])

            query = f"""
                UPDATE p{dbh._db_salt}_items
                SET name = ?,
                    note = ?,
                    price = ?,
                    price_final = ?,
                    currency = ?,
                    currency_final = ?,
                    bought_date = ?,
                    bought_by_id = ?,
                    exchange_rate = ?,
                    exchange_rate_date = ?,
                    tags = ?
                WHERE item_id = ? AND project_id = ?
            """

            params = [
                item_data['name'],
                item_data.get('note', ''),
                item_data['price'],
                item_data['price_final'],
                item_data['currency'],
                item_data['currency_final'],
                item_data['bought_date'],
                item_data['bought_by_id'],
                item_data['exchange_rate'],
                item_data['exchange_rate_date'],
                tags_json,
                self._item_id,
                item_data['project_id']
            ]

            dbh.execute_query(query, params)
            dbh.close()

            self.app.log(f"✓ Item {self._item_id} updated successfully")
            return True

        except Exception as e:
            self.app.notify(f"Database error: {str(e)}", severity="error")
            self.app.log(f"EXCEPTION in _update_in_database: {e}")
            import traceback
            self.app.log(f"Traceback: {traceback.format_exc()}")
            return False

    async def _delete_item(self) -> None:
        """Delete the item from the database after confirmation.

        Only available in edit mode. Shows a confirmation dialog before deletion.
        """
        try:
            if not self._edit_mode or not self._item_id:
                self.app.notify("Cannot delete: Not in edit mode", severity="error")
                return

            # Get item name for confirmation message
            item_name = self.query_one("#grid-item-name", Input).value.strip()

            # Show confirmation modal
            confirm = await self.app.push_screen_wait(DeleteConfirmationModal(item_name))

            if not confirm:
                self.app.notify("Deletion cancelled", severity="info")
                return

            # User confirmed - proceed with deletion
            dbh = self.app._config.get("dbh")
            if not dbh:
                self.app.notify("Database connection not available", severity="error")
                return

            project_id = self.app.app_state.get("project_id", 0)

            # Delete from database using the dedicated operation
            success = dbh.op_item_delete(self._item_id, project_id)

            if success:
                self.app.log(f"✓ Item {self._item_id} ('{item_name}') deleted successfully")
                self.app.notify(f"Expense '{item_name}' deleted successfully!", severity="success")

                # Dismiss the form and return a special value to indicate deletion
                self.dismiss("deleted")
            else:
                self.app.notify(f"Failed to delete expense '{item_name}'", severity="error")

        except ValueError as e:
            # Validation error (item not found, wrong project, etc.)
            self.app.notify(f"Validation error: {str(e)}", severity="error")
            self.app.log(f"Validation error in _delete_item: {e}")
        except Exception as e:
            self.app.notify(f"Error deleting item: {str(e)}", severity="error")
            self.app.log(f"EXCEPTION in _delete_item: {e}")
            import traceback
            self.app.log(f"Traceback: {traceback.format_exc()}")


    def _clear_form(self) -> None:
        """Clear all form fields."""
        try:
            # Get default values
            project_id = self.app.app_state.get("project_id", 0)
            user_id = self.app.app_state.get("user_id", -1)
            currency_main = self.app.app_state.get("current_project_currency_main", "USD")

            # Clear main input fields (correct IDs: grid-item-*, not item-*)
            self.query_one("#grid-item-name", Input).value = ""
            self.query_one("#grid-item-price", Input).value = ""
            self.query_one("#grid-item-currency", Select).value = currency_main
            self.query_one("#grid-item-bought-date", Input).value = datetime.now().strftime("%Y-%m-%d")

            # Clear additional fields
            self.query_one("#item-note", Input).value = ""
            self.query_one("#item-exchange-rate", Input).value = "1.0"
            self.query_one("#item-exchange-date", Input).value = datetime.now().strftime("%Y-%m-%d")

            # Reset bought-by select field to current user if available
            try:
                project_users = self._get_project_users(project_id)
                if project_users:
                    default_user = user_id if user_id > 0 else project_users[0]['user_id']
                    self.query_one("#grid-item-bought-by", Select).value = default_user

                    # Clear cost-sharing fields (only in create mode)
                    if not self._edit_mode:
                        for user in project_users:
                            try:
                                share_input = self.query_one(f"#share-{user['user_id']}", Input)
                                # Reset to default: 100% for bought_by user, 0% for others
                                if user['user_id'] == default_user:
                                    share_input.value = "100"
                                else:
                                    share_input.value = "0"
                            except:
                                pass  # Field might not exist
            except Exception as e:
                self.app.log(f"Error resetting user fields: {e}")

            # Clear label selections
            try:
                labels_widget = self.query_one("#item-labels", SelectionList)
                labels_widget.deselect_all()
            except:
                pass

            # Generate new UUID for next item
            self._item_uuid = str(uuid.uuid4())

            self.app.notify("✓ Form cleared", severity="info")

        except Exception as e:
            self.app.log(f"Error clearing form: {e}")
            self.app.notify("Error clearing form", severity="error")
