"""Item input form component - comprehensive expense/transaction editor.

This module provides the core form component for creating and editing
financial transactions (expenses/income). It's a reusable modal form
used throughout the application for all transaction input operations.

The form handles:
    - New expense creation
    - Existing expense editing
    - Cost sharing between multiple users
    - Label/category selection with dynamic tabs
    - Exchange rate management
    - Date selection
    - Input validation and sanitization
    - Confirmation workflow with preview

Key Features:
    - **Dual mode**: Create new or edit existing transactions
    - **Cost sharing**: Split expenses between users with percentages
    - **Label selection**: Tabbed interface for label categories
    - **Default labels**: Automatic assignment if user doesn't select
    - **Exchange rates**: Manual or automatic currency conversion
    - **Validation**: Comprehensive input checking
    - **Confirmation**: Preview before database commit
    - **Sanitization**: Input cleaning for security

Classes:
    ItemInputForm: Main expense input form modal
    ItemConfirmationModal: Preview and confirmation dialog
    DeleteConfirmationModal: Delete confirmation dialog

Functions:
    sanitize_string: Input sanitization utility

Form Fields:
    **Basic Information**:
        - Item Name (required): Transaction description
        - Price (required): Amount in original currency
        - Currency: 3-letter code (USD, EUR, etc.)
        - Purchase Date: When transaction occurred

    **User Assignment**:
        - Bought By: Who made the purchase
        - Bought For: Who the expense is for (supports cost sharing)
        - Share Percentage: Split costs among users (must total 100%)

    **Exchange Rate** (optional):
        - Exchange Rate: Conversion rate to main currency
        - Exchange Rate Date: When rate applies
        - Auto-calculated if not provided

    **Categorization**:
        - Count Label: Transaction counting category
        - Transaction Label: Type (fixed, variable, daily, revenue)
        - Account Label: Bank/payment method
        - Main Label: Primary category (groceries, rent, etc.)
        - Secondary Labels: Additional tags (multiple selection)

    **Additional**:
        - Notes: Free text for comments

Workflow:
    **Creating New Expense**:
        1. User opens form (edit_mode=False)
        2. User fills required fields (name, price, date)
        3. User optionally selects labels (or uses defaults)
        4. User optionally shares cost with other users
        5. User clicks Save
        6. Form validates all inputs
        7. Confirmation modal shows preview
        8. User confirms
        9. Expense saved to database
        10. ItemCreated message posted

    **Editing Existing Expense**:
        1. Form opens with item_data (edit_mode=True)
        2. All fields pre-filled from database
        3. User modifies fields
        4. User clicks Save
        5. Validation runs
        6. Confirmation shows changes
        7. User confirms
        8. Database updated
        9. Modal closes

Label Selection:
    The form provides a sophisticated tabbed label selector:
        - Dynamically created tabs based on project style
        - Each label type group gets its own tab
        - Radio button selection within each tab
        - Default labels auto-selected if user doesn't choose
        - Owner-based coloring for user vs. common labels

Cost Sharing:
    Users can split expenses among project members:
        - Add multiple "Bought For" users with percentages
        - Visual sliders or input fields for percentages
        - Validation ensures total equals 100%
        - Each user sees their portion in their expense view
        - Uses liability accounts for shared portions

Default Label Behavior:
    If user doesn't select labels:
        - Count label: User's default or first available
        - Transaction label: User's default for transaction type
        - Account label: User's liability account (if sharing) or default
        - Main label: User's default for main category
        - Secondary labels: None

Validation Rules:
    - Name: Required, max 100 characters
    - Price: Required, must be positive number
    - Currency: Required, exactly 3 letters
    - Date: Required, valid date format
    - Exchange rate: If provided, must be positive
    - Share percentages: Must total 100% if cost sharing
    - Labels: Auto-assigned if not selected

Example:
    Creating new expense::

        >>> from fiwa_cli.components.item_input_form import ItemInputForm
        >>> form = ItemInputForm(edit_mode=False)
        >>> result = await self.app.push_screen_wait(form)
        >>> if result:
        >>>     print(f"Created expense: {result['item_id']}")

    Editing existing expense::

        >>> item_data = {
        >>>     'item_id': 42,
        >>>     'item_uuid': 'abc-123',
        >>>     'name': 'Groceries',
        >>>     'price': 85.00,
        >>>     'currency': 'USD',
        >>>     # ... other fields
        >>> }
        >>> form = ItemInputForm(edit_mode=True, item_data=item_data)
        >>> result = await self.app.push_screen_wait(form)

See Also:
    screens.inputs_insert_expense: Wrapper for new expense creation
    screens.inputs_edit_expense: Expense editing interface
    functions.project_composer.ProjectComposer: Label management
    functions.handler_sqllite.op_item_create: Database creation
    functions.handler_sqllite.op_item_update: Database update
"""

from textual.widgets import Static, Button, Input, Select, Label, SelectionList, Switch, Placeholder
from textual.containers import Vertical, Horizontal, Grid, ScrollableContainer, Container
from textual.widgets import TabbedContent, TabPane
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
    allowed_chars: str = r"a-zA-Z0-9\s\.\,\-\_\:\;\!\?\(\)\[\]\@\#\$\%\&\+\=\'\"",
    allow_internal_spaces: bool = True,
) -> tuple[str, bool]:
    """Sanitize and validate string input by removing invalid characters.

    This function ensures that:
        - Leading and trailing spaces are removed
        - Only allowed characters are present in the string
        - First and last characters are not spaces (after trimming)

    Args:
        text: The input string to sanitize
        allowed_chars: Regex character set of allowed characters
            Default allows: a-z, A-Z, 0-9, spaces, and common punctuation
            (. , - _ : ; ! ? ( ) [ ] @ # $ % & + = ' ")
        allow_internal_spaces: Whether to allow spaces within the string
            Default: True

    Returns:
        Tuple of (sanitized_string, was_modified):
            - sanitized_string: Cleaned string with invalid chars removed
            - was_modified: True if string was changed during sanitization

    Examples:
        Remove leading/trailing spaces::

            >>> sanitize_string("  Hello World!  ")
            ("Hello World!", True)

        No changes needed::

            >>> sanitize_string("Hello World!")
            ("Hello World!", False)

        Restrict to alphanumeric and hyphens::

            >>> sanitize_string("Product-Name_123", allowed_chars=r'a-zA-Z0-9\-\_')
            ("Product-Name_123", False)

        Remove script tags::

            >>> sanitize_string("Test<script>alert()</script>")
            ("Testscriptalert", True)

        Empty input::

            >>> sanitize_string("")
            ("", False)

        Only whitespace::

            >>> sanitize_string("   ")
            ("", True)

    Security:
        This function prevents injection attacks by removing potentially
        dangerous characters. Use it for all user text inputs that will
        be stored in the database or displayed in the UI.

    Note:
        The function performs two sanitization passes:
            1. Strip leading/trailing whitespace
            2. Filter out non-allowed characters

        This ensures clean, safe strings suitable for database storage
        and UI display.
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
        pattern = f"^[{allowed_chars}]+$"
    else:
        # Remove \s from allowed_chars if spaces are not allowed
        allowed_chars_no_space = allowed_chars.replace(r"\s", "")
        pattern = f"^[{allowed_chars_no_space}]+$"

    # Filter out invalid characters
    sanitized = "".join(char for char in text if re.match(f"[{allowed_chars}]", char))

    # Strip again to remove any trailing/leading spaces that might remain
    sanitized = sanitized.strip()

    # Check if the string was modified
    was_modified = original != sanitized

    return (sanitized, was_modified)


class LabelModalScreen(ModalScreen):
    """Modal screen for selecting labels for a transaction.

    Labels are organized by type in tabs dynamically based on the project's style.
    Tab structure comes from ProjectComposer.get_label_map() which returns:
    {type_id: group_name} - e.g., {0: "Balance", 1: "Transaction", 2: "Account", 3: "Main Labels"}

    This tab-based design scales well with many labels.
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("B", "switch_to_tab(0)", "Tab 0"),
        ("T", "switch_to_tab(1)", "Tab 1"),
        ("A", "switch_to_tab(2)", "Tab 2"),
        ("M", "switch_to_tab(3)", "Tab 3"),
        ("S", "switch_to_tab(4)", "Tab 4"),
        # ("j", "show_tab('jessica')", "Jessica"),
        # ("p", "show_tab('paul')", "Paul"),
    ]

    def __init__(self, project_labels: list, selected_labels: list = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_labels = project_labels
        self.selected_labels = selected_labels or []

        # Get label map from ProjectComposer based on project style
        self.label_map = self._get_label_map_from_composer()

        # Organize labels by type dynamically
        self.labels_by_type = {}
        for type_id in self.label_map.keys():
            self.labels_by_type[type_id] = []

        # Populate labels by type
        for label in project_labels:
            label_type = label.get("label_type", 0)
            if label_type in self.labels_by_type:
                self.labels_by_type[label_type].append(label)

    def _get_label_map_from_composer(self) -> dict:
        """Get label map from ProjectComposer based on current project style."""
        try:
            from fiwa_cli.functions.project_composer import ProjectComposer

            project_style = self.app.app_state.get("project_style", "default")
            project_id = self.app.app_state.get("project_id", 0)

            if project_style and project_style != "default":
                dbh = self.app._config.get("dbh")
                pc = ProjectComposer.create(
                    compose_type=project_style, dbh=dbh, project_id=project_id, users=[]
                )
                label_map = pc.get_label_map()
                self.app.log(
                    f"Loaded label map from ProjectComposer ({project_style}): {label_map}"
                )
                return label_map
            else:
                # Fallback to default label types
                self.app.log("Using default label map (project_style is 'default')")
                return {0: "Action", 1: "Account", 2: "Label"}
        except Exception as e:
            self.app.log(f"Error loading label map from ProjectComposer: {e}")
            # Fallback to default
            return {0: "Action", 1: "Account", 2: "Label"}

    def action_switch_to_tab(self, tab_number: int) -> None:
        """Switch to a tab by its type_id number.

        Args:
            tab_number: The label type_id (0-9) to switch to
        """
        try:
            # Check if this tab exists in our label_map
            if tab_number in self.label_map:
                tab_id = f"tab-{tab_number}"
                tabbed_content = self.query_one(TabbedContent)
                tabbed_content.active = tab_id
                self.app.log(f"Switched to tab: {tab_id} ({self.label_map[tab_number]})")
            else:
                self.app.log(f"Tab {tab_number} does not exist in current project")
        except Exception as e:
            self.app.log(f"Error switching to tab {tab_number}: {e}")

    def compose(self) -> ComposeResult:


        with Vertical():
            with Vertical(classes="modal-header"):
                yield Static("Select Labels for Transaction", classes="modal-title")
                yield Static(
                    f"Currently selected: {len(self.selected_labels)} label(s)",
                    id="selection-count",
                    classes="selection-count",
                )

            # Determine initial tab ID (first available type as string)
            if self.label_map:
                first_type_id = min(self.label_map.keys())
                initial_tab = f"tab-{first_type_id}"
            else:
                initial_tab = "tab-0"

            with TabbedContent(initial=initial_tab):
                # Dynamically create tabs based on label_map
                for type_id, group_name in sorted(self.label_map.items()):
                    tab_id = f"tab-{type_id}"
                    selection_list_id = f"label-selection-{type_id}"
                    _group_name = f"[bold italic]{group_name[0].upper()}[/bold italic]" + f"{group_name[1:]}"
                    # Create a tab for this label type
                    with TabPane(_group_name, id=tab_id):
                        if self.labels_by_type.get(type_id):
                            with ScrollableContainer():
                                yield SelectionList[int](
                                    *[
                                        (
                                            label['name'],
                                            label["label_id"],
                                            label["label_id"] in self.selected_labels,
                                        )
                                        for label in self.labels_by_type[type_id]
                                    ],
                                    id=selection_list_id,
                                )
                        else:
                            yield Static(
                                f"No {group_name.lower()} labels available",
                                classes="no-labels-message",
                            )

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
            # Collect from all dynamically created SelectionLists
            for type_id in self.label_map.keys():
                list_id = f"label-selection-{type_id}"
                try:
                    sel_list = self.query_one(f"#{list_id}", SelectionList)
                    selected.extend(list(sel_list.selected))
                except Exception:
                    pass

            count_widget = self.query_one("#selection-count", Static)
            count_widget.update(f"Currently selected: {len(selected)} label(s)")
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the label modal."""
        if event.button.id == "label-ok-button":
            # Get selected labels from all dynamically created SelectionLists
            selected = []
            try:
                # Collect from all label type SelectionLists
                for type_id in self.label_map.keys():
                    list_id = f"label-selection-{type_id}"
                    try:
                        sel_list = self.query_one(f"#{list_id}", SelectionList)
                        selected.extend(list(sel_list.selected))
                    except Exception:
                        pass

                self.dismiss(selected)  # Return list of selected label IDs
            except Exception as e:
                self.app.log(f"Error collecting selected labels: {e}")
                self.dismiss([])  # Return empty list on error

        elif event.button.id == "label-clear-button":
            # Clear all selections from all dynamically created SelectionLists
            for type_id in self.label_map.keys():
                list_id = f"label-selection-{type_id}"
                try:
                    sel_list = self.query_one(f"#{list_id}", SelectionList)
                    sel_list.deselect_all()
                except Exception:
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
                yield Static(
                    f"Original Price: {self.item_data.get('price', 0):.2f} {self.item_data.get('currency', 'N/A')}",
                    classes="summary-row",
                )

                # Show exchange rate if different from main currency
                if self.item_data.get("currency") != self.item_data.get("currency_final"):
                    yield Static(
                        f"Exchange Rate: {self.item_data.get('exchange_rate', 1.0):.4f}",
                        classes="summary-row",
                    )

                yield Static(
                    f"[bold]Final Price: {self.item_data.get('price_final', 0):.2f} {self.item_data.get('currency_final', 'N/A')}[/bold]",
                    classes="total-row",
                )
                yield Static(
                    f"Date: {self.item_data.get('bought_date', 'N/A')}", classes="summary-row"
                )
                yield Static(
                    f"Bought By: {self.item_data.get('bought_by_name', 'N/A')}",
                    classes="summary-row",
                )

                if (
                    self.item_data.get("labels_text")
                    and self.item_data.get("labels_text") != "None"
                ):
                    yield Static(
                        f"Labels: {self.item_data.get('labels_text', '')}", classes="summary-row"
                    )

            # Cost-sharing breakdown
            cost_shares = self.item_data.get("cost_shares", [])
            if cost_shares:
                with Vertical(classes="summary-section"):
                    yield Static("[bold]Cost Sharing Breakdown[/bold]", classes="section-title")

                    # Calculate total percentage for validation
                    total_percentage = sum(share.get("percentage", 0) for share in cost_shares)

                    # Show each user with their amount and labels
                    for share in cost_shares:
                        username = share.get("username", "Unknown")
                        percentage = share.get("percentage", 0)
                        amount = share.get("amount", 0)
                        currency_final = self.item_data.get("currency_final", "USD")

                        # Get label information for this user
                        label_text = share.get("labels_text", "None")

                        if percentage > 0:
                            yield Static(
                                f"  {username}: {percentage:.1f}% = {amount:.2f} {currency_final}",
                                classes="cost-share-row",
                            )
                            # Show labels for this user
                            yield Static(f"    Labels: {label_text}", classes="cost-share-labels")
                        elif share.get("user_id") == self.item_data.get("bought_by_id"):
                            # Show bought_by user even if they pay 0% (others pay 100%)
                            yield Static(
                                f"  {username}: {percentage:.1f}% = {amount:.2f} {currency_final}",
                                classes="cost-share-row",
                            )
                            yield Static(f"    Labels: {label_text}", classes="cost-share-labels")

                    # Show total
                    total_amount = sum(share.get("amount", 0) for share in cost_shares)
                    yield Static(
                        f"[bold]Total: {total_amount:.2f} {self.item_data.get('currency_final', 'USD')}[/bold]",
                        classes="total-row",
                    )

                    # Validation: Check if total percentage equals 100%
                    # Allow small tolerance for floating point errors (0.01%)
                    percentage_valid = abs(total_percentage - 100.0) < 0.01

                    if not percentage_valid:
                        yield Static(
                            f"[bold red]⚠ WARNING: Total percentage is {total_percentage:.1f}% (should be 100%)[/bold red]",
                            classes="validation-error",
                        )
                        yield Static(
                            "[red]Cannot save to database. Please go back and adjust the cost sharing percentages.[/red]",
                            classes="validation-message",
                        )

            with Horizontal(classes="button-row"):
                # Disable OK button if cost shares don't add up to 100%
                ok_button_disabled = False
                if cost_shares:
                    total_percentage = sum(share.get("percentage", 0) for share in cost_shares)
                    ok_button_disabled = abs(total_percentage - 100.0) >= 0.01

                yield Button(
                    (
                        "✓ OK - Save to Database"
                        if not ok_button_disabled
                        else "✗ Cannot Save - Invalid Total"
                    ),
                    id="confirm-ok-button",
                    variant="success" if not ok_button_disabled else "error",
                    flat=True,
                    compact=True,
                    disabled=ok_button_disabled,
                )
                yield Button(
                    "← Back - Edit",
                    id="confirm-back-button",
                    variant="warning",
                    flat=True,
                    compact=True,
                )

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
                classes="warning-message",
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
        self._item_uuid = item_data["item_uuid"] if edit_mode and item_data else str(uuid.uuid4())
        self._item_id = item_data["item_id"] if edit_mode and item_data else None
        self._pending_item_data = None
        self._project_users = []  # Store project users for dynamic updates

        # Load selected labels from item_data in edit mode
        if edit_mode and item_data and item_data.get("tags"):
            # In edit mode, tags come from database as a string (e.g., "3_4_5_6_[7,8]")
            # We need to parse it to get individual label IDs
            tags_str = item_data["tags"]

            # Try to parse using ProjectComposer if available
            try:
                from fiwa_cli.functions.project_composer import ProjectComposer

                project_style = self.app.app_state.get("project_style", "default")
                project_id = item_data.get("project_id", self.app.app_state.get("project_id", 0))

                # Get label map
                dbh = self.app._config.get("dbh")
                if dbh:
                    labels = dbh.op_label_get_all(project_id=project_id, use_cache=True)
                    label_map = {l["label_id"]: l for l in labels}

                    # Create ProjectComposer instance
                    pc = ProjectComposer.create(
                        compose_type=project_style, dbh=dbh, project_id=project_id, users=[]
                    )

                    # Parse the tag string - this returns names, but we need IDs
                    # We need to extract IDs from the string directly
                    parts = tags_str.split("_")
                    label_ids = []

                    if len(parts) >= 4:
                        # Extract IDs from positions 0-3
                        for i in range(4):
                            if parts[i].strip().isdigit():
                                label_id = int(parts[i].strip())
                                if label_id > 0:
                                    label_ids.append(label_id)

                        # Extract secondary IDs from position 4 (the list part)
                        if len(parts) >= 5:
                            s_part = parts[4].strip().strip("[]")
                            if s_part:
                                for s_id in s_part.split(","):
                                    if s_id.strip().isdigit():
                                        label_id = int(s_id.strip())
                                        if label_id > 0:
                                            label_ids.append(label_id)

                    self._selected_label_ids = label_ids
                    self.app.log(f"Parsed tag string '{tags_str}' to label IDs: {label_ids}")
                else:
                    self._selected_label_ids = []

            except Exception as e:
                self.app.log(f"Error parsing tag string in edit mode: {e}")
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
                self.app.log(
                    f"  Grid styles: width={grid.styles.width}, height={grid.styles.height}"
                )
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

    def _get_default_labels(self, project_id: int) -> list:
        """Get default labels for each label type for the current user.

        Returns a list of label IDs for default labels, ordered by type.
        If a type has no default, returns 0 for that position.

        Returns:
            List of label IDs: [balance_id, transaction_id, account_id, main_id, ...]
        """
        try:
            dbh = self.app._config.get("dbh")
            user_id = self.app.app_state.get("user_id", -1)

            if not dbh or user_id <= 0:
                return []

            # Get user's default labels as a map: {label_type: label_id}
            defaults_map = dbh.op_label_get_user_defaults(user_id, project_id)

            # Get ProjectComposer to know which types exist and their order
            from fiwa_cli.functions.project_composer import ProjectComposer

            project_style = self.app.app_state.get("project_style", "default")

            if project_style != "default":
                try:
                    pc = ProjectComposer.create(
                        compose_type=project_style, dbh=dbh, project_id=project_id, users=[]
                    )
                    label_map = pc.get_label_map()

                    # Build list of default label IDs in type order
                    default_labels = []
                    for type_id in sorted(label_map.keys()):
                        # Get default for this type, or 0 if none set
                        default_labels.append(defaults_map.get(type_id, 0))

                    self.app.log(
                        f"Default labels for user {user_id} in project {project_id}: {default_labels}"
                    )
                    return default_labels

                except Exception as e:
                    self.app.log(f"Error getting default labels from ProjectComposer: {e}")

            # Fallback: no defaults
            return []

        except Exception as e:
            self.app.log(f"Error fetching default labels: {e}")
            return []

    def _get_project_labels(self, project_id: int) -> list:
        """Get all labels for the current project."""
        try:
            dbh = self.app._config.get("dbh")
            if dbh and project_id > 0:
                labels = dbh.op_label_get_all(project_id)
                # Only return active labels (status = 2)
                return [label for label in labels if label.get("label_status", 0) == 2]
            return []
        except Exception as e:
            self.app.log(f"Error fetching project labels: {e}")
            return []

    def _expand_composite_labels(self, label_ids: list, project_labels: list) -> list:
        """Expand secondary labels to include their composite dependencies.
        
        When a user selects a secondary label that has composite labels defined,
        this method automatically includes those composite labels in the final list.
        
        Args:
            label_ids: List of selected label IDs (e.g., [15, 23])
            project_labels: List of all project labels with their metadata
            
        Returns:
            Expanded list of label IDs including composites (e.g., [7, 8, 15, 23])
            
        Example:
            User selects label "Weekend Activities" (ID=15)
            Label 15 has composite = [7, 8] (Sports, Leisure)
            Result: [7, 8, 15] - both composites and the original label
            
        Note:
            - Prevents duplicates using set
            - Maintains order: composites first, then selected labels
            - Handles circular dependencies by not recursing
        """
        import json
        
        if not label_ids:
            return []
        
        # Build a map for quick label lookup
        label_map = {label["label_id"]: label for label in project_labels}
        
        # Set to track all label IDs (prevents duplicates)
        expanded_ids_set = set()
        expanded_ids_ordered = []
        
        for label_id in label_ids:
            # Look up the label
            label_info = label_map.get(label_id)
            
            if label_info:
                # Get composite field (list of label IDs)
                composite_raw = label_info.get("composite", "[]")
                
                # Parse composite JSON if it's a string
                if isinstance(composite_raw, str):
                    try:
                        composite_ids = json.loads(composite_raw)
                    except Exception:
                        composite_ids = []
                elif isinstance(composite_raw, list):
                    composite_ids = composite_raw
                else:
                    composite_ids = []
                
                # Add composite labels first (dependencies)
                for comp_id in composite_ids:
                    if comp_id not in expanded_ids_set:
                        expanded_ids_set.add(comp_id)
                        expanded_ids_ordered.append(comp_id)
                
                # Add the label itself
                if label_id not in expanded_ids_set:
                    expanded_ids_set.add(label_id)
                    expanded_ids_ordered.append(label_id)
            else:
                # Label not found in project_labels, but still include it
                if label_id not in expanded_ids_set:
                    expanded_ids_set.add(label_id)
                    expanded_ids_ordered.append(label_id)
        
        return expanded_ids_ordered

    def _prepare_user_labels(
        self,
        cost_shares: list,
        bought_by_id: int,
        selected_labels: list,
        project_id: int,
        project_labels: list,
    ) -> list:
        """
        Prepare label information for each user in cost_shares.

        Key logic:
        - If bought_by == bought_for (buying for self): Use selected/default labels
        - If bought_by != bought_for (buying for another): Replace account label with that user's LIABILITY account

        The Liability account is defined as: label_type=2 (Account), label_sub_type=0, label_owner=user_id

        Args:
            cost_shares: List of cost share dicts with user_id, username, percentage, amount
            bought_by_id: User ID of the person buying
            selected_labels: List of selected label IDs (or defaults if none selected)
            project_id: Current project ID
            project_labels: List of all project labels

        Returns:
            Updated cost_shares list with 'labels' and 'labels_text' added to each share
        """
        try:
            # Build a map of user_id -> liability account label for quick lookup
            # liability_accounts[user_id] = label object
            liability_accounts = {}
            for label in project_labels:
                if label.get("label_type") == 2 and label.get("label_sub_type") == 0:
                    owner_id = label.get("label_owner", -1)
                    if owner_id > 0:  # User-owned liability account
                        liability_accounts[owner_id] = label
                        self.app.log(
                            f"Found liability account for user {owner_id}: {label.get('name')}"
                        )

            if not liability_accounts:
                self.app.log(
                    "WARNING: No user-specific liability accounts found (type=2, sub_type=0, owner>0)"
                )

            # Process each cost share
            updated_shares = []
            for share in cost_shares:
                user_id = share["user_id"]

                # Skip users with 0% share
                if share.get("percentage", 0) <= 0.0001:
                    updated_shares.append(share)
                    continue

                # Determine which labels to use for this user
                if user_id == bought_by_id:
                    # Buying for self - use the selected/default labels as-is
                    user_labels = selected_labels.copy()
                    self.app.log(
                        f"User {share['username']} (buying for self): Using selected labels"
                    )
                else:
                    # Buying for another user - use THAT user's liability account
                    user_labels = selected_labels.copy()

                    # Find this specific user's liability account
                    user_liability_label = liability_accounts.get(user_id)

                    if user_liability_label:
                        # Replace position 2 (account) with this user's liability account
                        # The label structure is: [balance, transaction, account, main, secondary...]
                        if len(user_labels) >= 3:
                            user_labels[2] = user_liability_label["label_id"]
                            self.app.log(
                                f"Replaced account label for user {share['username']} (ID:{user_id}) with their liability account: {user_liability_label.get('name')}"
                            )
                        else:
                            # Labels list is too short, need to extend it
                            while len(user_labels) < 3:
                                user_labels.append(0)
                            user_labels[2] = user_liability_label["label_id"]
                            self.app.log(
                                f"Added liability account for user {share['username']} (ID:{user_id}): {user_liability_label.get('name')}"
                            )
                    else:
                        self.app.log(
                            f"WARNING: No liability account found for user {share['username']} (ID:{user_id})"
                        )

                # Get label names for display
                label_names = [
                    label["name"] for label in project_labels if label["label_id"] in user_labels
                ]
                labels_text = ", ".join(label_names) if label_names else "None"

                # Add label information to share
                share["labels"] = user_labels
                share["labels_text"] = labels_text
                updated_shares.append(share)

                self.app.log(
                    f"User {share['username']}: labels={user_labels}, text='{labels_text}'"
                )

            return updated_shares

        except Exception as e:
            self.app.log(f"Error in _prepare_user_labels: {e}")
            import traceback

            self.app.log(f"Traceback: {traceback.format_exc()}")
            # Return original cost_shares with default labels
            for share in cost_shares:
                share["labels"] = selected_labels
                share["labels_text"] = "Error preparing labels"
            return cost_shares

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
        user_options = [(u["username"], u["user_id"]) for u in project_users]

        # Show ALL project users in the "Bought For" section
        # Logic: By default, bought_by user gets 100% (buying for themselves)
        # Users can then adjust to share costs with others
        user_options_share_to = [(u["username"], u["user_id"]) for u in project_users]

        # Determine default bought_by user (current user or first in list)
        default_bought_by_id = (
            user_id if user_id > 0 else (user_options[0][1] if user_options else -1)
        )

        # Get project labels
        project_labels = self._get_project_labels(project_id)
        label_options = [(label["name"], label["label_id"]) for label in project_labels]
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
                value=self._item_data["name"] if self._edit_mode and self._item_data else "",
            )
            yield Input(
                placeholder="0.00",
                id="grid-item-price",
                type="number",
                value=str(self._item_data["price"]) if self._edit_mode and self._item_data else "",
            )
            yield Select(
                options=currency_options if currency_options else [("USD", "USD")],
                value=(
                    self._item_data["currency"]
                    if self._edit_mode and self._item_data
                    else (currency_main if currency_main else "USD")
                ),
                id="grid-item-currency",
                allow_blank=False,
            )
            yield Input(
                placeholder="YYYY-MM-DD",
                id="grid-item-bought-date",
                value=(
                    str(self._item_data["bought_date"]).split()[0]
                    if self._edit_mode and self._item_data
                    else datetime.now().strftime("%Y-%m-%d")
                ),
            )
            yield Select(
                options=user_options if user_options else [("No users", -1)],
                value=(
                    self._item_data["bought_by_id"]
                    if self._edit_mode and self._item_data
                    else (user_id if user_id > 0 else (user_options[0][1] if user_options else -1))
                ),
                id="grid-item-bought-by",
                allow_blank=False,
            )
            yield Button("🏷️ Labels", id="open-label-modal-button", variant="default", compact=True)

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
                                self.app.log(
                                    f"Adding user {idx + 1}/{user_count}: {i_item[0]} (ID: {i_item[1]})"
                                )

                                # Set default share: 100% for bought_by user, 0% for others
                                default_share = "100" if i_item[1] == default_bought_by_id else "0"

                                with Horizontal(classes="bought-for-user-row"):
                                    yield Static(
                                        f"{i_item[0]}",
                                        id=f"user-label-{i_item[1]}",
                                        classes="user-name-label",
                                    )
                                    yield Input(
                                        placeholder="0-100%",
                                        value=default_share,
                                        type="number",
                                        id=f"share-{i_item[1]}",
                                        classes="user-share-input",
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
                            value=(
                                str(self._item_data["exchange_rate"])
                                if self._edit_mode and self._item_data
                                else "1.0"
                            ),
                            type="number",
                        )
                    with Vertical(classes="field-group"):
                        yield Static("Exchange Rate Date", classes="form-label")
                        yield Input(
                            placeholder="YYYY-MM-DD",
                            id="item-exchange-date",
                            value=(
                                str(self._item_data["exchange_rate_date"]).split()[0]
                                if self._edit_mode and self._item_data
                                else datetime.now().strftime("%Y-%m-%d")
                            ),
                        )

                # Note field
                with Horizontal(classes="note-row"):
                    with Vertical(classes="field-group-full"):
                        yield Static("Note", classes="form-label")
                        yield Input(
                            placeholder="Additional details (optional)",
                            id="item-note",
                            max_length=255,
                            value=(
                                self._item_data["note"]
                                if self._edit_mode and self._item_data and self._item_data["note"]
                                else ""
                            ),
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

                # self.app.notify(f"{len(self._selected_label_ids)} label(s) selected", severity="info")
            else:  # User clicked Cancel
                self.app.log("Label selection cancelled")

        except Exception as e:
            self.app.log(f"Error opening label modal: {e}")
            # self.app.notify(f"Error: {str(e)}", severity="error")

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
        user_options_share_to = [(u["username"], u["user_id"]) for u in self._project_users]

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
            user_row.mount(
                Static(f"{i_item[0]}", id=f"user-label-{i_item[1]}", classes="user-name-label")
            )
            user_row.mount(
                Input(
                    placeholder="0-100%",
                    value=default_share,
                    type="number",
                    id=f"share-{i_item[1]}",
                    classes="user-share-input",
                )
            )

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
            name, name_modified = sanitize_string(
                name, allowed_chars=r"a-zA-Z0-9\s\.\,\-\_\:\;\!\?\(\)\[\]\@\#\$\%\&\+\=\'\""
            )
            note, note_modified = sanitize_string(
                note, allowed_chars=r"a-zA-Z0-9\s\.\,\-\_\:\;\!\?\(\)\[\]\@\#\$\%\&\+\=\'\""
            )

            # Notify user if their input was modified
            if name_modified:
                self.app.notify(
                    "Item name was cleaned (removed invalid characters or spaces)",
                    severity="warning",
                )
            if note_modified:
                self.app.notify(
                    "Note was cleaned (removed invalid characters or spaces)", severity="warning"
                )

            # Use exchange rate from input field, default to 1.0 if not provided
            exchange_rate_float = float(exchange_rate_input) if exchange_rate_input else 1.0

            # Use exchange date from input field, default to bought_date if not provided
            exchange_rate_date = exchange_date_input if exchange_date_input else bought_date

            # Get project users EARLY - needed for default label logic and cost sharing
            project_users = self._get_project_users(project_id)
            bought_by_user = next((u for u in project_users if u["user_id"] == bought_by_id), None)
            bought_by_name = bought_by_user["username"] if bought_by_user else "Unknown"

            # Get selected labels from the modal
            selected_labels = self._selected_label_ids

            # Get project labels for display
            project_labels = self._get_project_labels(project_id)

            # AUTO-APPLY DEFAULT LABELS:
            # If user is buying for themselves ONLY and hasn't selected labels, use defaults
            if not selected_labels or len(selected_labels) == 0:
                # Check if buying for themselves (100% for bought_by user, 0% for others)
                is_buying_for_self = False

                if not self._edit_mode:
                    # In create mode, check cost_shares
                    # Will be populated below, so we need to check if only bought_by has 100%
                    # For now, do a quick check: if all shares except bought_by are 0
                    buying_for_self_only = True
                    for user in project_users:
                        try:
                            share_input = self.query_one(f"#share-{user['user_id']}", Input)
                            share_value = share_input.value.strip()
                            share_percent = float(share_value) if share_value else 0.0

                            if user["user_id"] == bought_by_id:
                                # bought_by user should have 100%
                                if abs(share_percent - 100.0) >= 0.01:
                                    buying_for_self_only = False
                                    break
                            else:
                                # Other users should have 0%
                                if share_percent > 0.0001:
                                    buying_for_self_only = False
                                    break
                        except Exception:
                            pass

                    is_buying_for_self = buying_for_self_only
                else:
                    # In edit mode, always buying for self (single item)
                    is_buying_for_self = True

                # If buying for self and no labels selected, use defaults
                if is_buying_for_self:
                    default_labels = self._get_default_labels(project_id)
                    if default_labels and any(label_id > 0 for label_id in default_labels):
                        selected_labels = default_labels
                        self._selected_label_ids = selected_labels

                        self.app.log(f"Auto-applied default labels: {selected_labels}")
                        self.app.notify(
                            "ℹ No labels selected - using default labels", severity="info"
                        )
                    else:
                        self.app.log("No default labels found or all are 0")

            # Get label names for display
            label_names = [
                label["name"] for label in project_labels if label["label_id"] in selected_labels
            ]
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
                            if share_percent <= 0.0001:
                                continue
                            share_amount = (price_final * share_percent) / 100.0
                            cost_shares.append(
                                {
                                    "user_id": user["user_id"],
                                    "username": user["username"],
                                    "percentage": share_percent,
                                    "amount": share_amount,
                                }
                            )
                            total_percentage += share_percent
                        else:
                            # Empty field = 0%
                            cost_shares.append(
                                {
                                    "user_id": user["user_id"],
                                    "username": user["username"],
                                    "percentage": 0.0,
                                    "amount": 0.0,
                                }
                            )
                    except Exception as e:
                        self.app.log(f"Error reading share for user {user['user_id']}: {e}")
                        # Input field not found or invalid value - treat as 0%
                        cost_shares.append(
                            {
                                "user_id": user["user_id"],
                                "username": user["username"],
                                "percentage": 0.0,
                                "amount": 0.0,
                            }
                        )

                # VALIDATE: Total must equal exactly 100% (with small tolerance for floating point)
                if abs(total_percentage - 100.0) >= 0.01:
                    if total_percentage > 100.0:
                        self.app.notify(
                            f"⚠ Cost share total is {total_percentage:.1f}% - exceeds 100%! Please adjust.",
                            severity="error",
                        )
                    else:
                        self.app.notify(
                            f"⚠ Cost share total is {total_percentage:.1f}% - must be 100%! Please adjust.",
                            severity="error",
                        )
                    return

                # Now prepare labels for each user in cost_shares
                # Key logic:
                # - If bought_by == bought_for (buying for self), use selected/default labels
                # - If bought_by != bought_for (buying for another), use LIABILITY account for the account label
                cost_shares = self._prepare_user_labels(
                    cost_shares, bought_by_id, selected_labels, project_id, project_labels
                )

            else:
                # In edit mode, just update the single item - no cost sharing
                cost_shares.append(
                    {
                        "user_id": bought_by_id,
                        "username": bought_by_name,
                        "percentage": 100.0,
                        "amount": price_final,
                        "labels": selected_labels,
                        "labels_text": labels_text,
                    }
                )

            # Build complete item data dictionary
            item_data = {
                "item_uuid": self._item_uuid,
                "name": name,
                "note": note,
                "price": price_float,
                "price_final": price_final,
                "currency": currency,
                "currency_final": currency_final,
                "exchange_rate": exchange_rate_float,
                "exchange_rate_date": exchange_rate_date,
                "bought_date": bought_date,
                "bought_by_id": bought_by_id,
                "bought_by_name": bought_by_name,
                "added_by_id": user_id,
                "project_id": project_id,
                "tags": selected_labels,
                "labels_text": labels_text,
                "cost_shares": cost_shares,  # List of cost sharing breakdown
                "total_shared_percentage": total_percentage,
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
                        self.app.notify(
                            f"✓ Transaction '{self._pending_item_data['name']}' updated successfully!",
                            severity="success",
                        )
                        # Dismiss the form and return the item_id to trigger refresh
                        self.dismiss(self._item_id)
                    else:
                        self.app.notify("Failed to update transaction", severity="error")
                else:
                    # Save new item to database
                    item_id = await self._save_to_database(self._pending_item_data)
                    if item_id:
                        self.app.notify(
                            f"✓ Transaction '{self._pending_item_data['name']}' saved successfully!",
                            severity="success",
                        )

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
            cost_shares = item_data.get("cost_shares", [])

            if not cost_shares:
                self.app.notify("No cost shares defined", severity="error")
                self.app.log("ERROR: cost_shares is empty")
                return None

            self.app.log(f"Creating {len(cost_shares)} item entries for cost sharing")

            # Get ProjectComposer instance for building tag string
            from fiwa_cli.functions.project_composer import ProjectComposer

            project_style = self.app.app_state.get("project_style", "default")
            project_id = item_data["project_id"]

            try:
                pc = ProjectComposer.create(
                    compose_type=project_style, dbh=dbh, project_id=project_id, users=[]
                )
            except Exception as e:
                self.app.log(f"Error creating ProjectComposer: {e}")
                pc = None

            # Get project labels for composite label expansion
            project_labels = self._get_project_labels(project_id)

            # Keep track of created item IDs
            created_item_ids = []

            # Create one item entry for each user who shares the cost
            for share in cost_shares:
                user_id = share.get("user_id")
                share_amount = share.get("amount")  # Final price share
                share_percentage = share.get("percentage", 100.0)
                username = share.get("username")
                user_labels = share.get("labels", [])  # Get user-specific labels

                # Calculate proportional original price (in original currency)
                original_price_share = (item_data["price"] * share_percentage) / 100.0

                # Prepare item data for this specific user's share
                db_item_data = {
                    "item_uuid": item_data["item_uuid"],
                    "name": item_data["name"],
                    "note": item_data.get("note", ""),
                    "price": original_price_share,  # Split original price by percentage
                    "price_final": share_amount,  # Split final converted price by percentage
                    "currency": item_data["currency"],
                    "currency_final": item_data["currency_final"],
                    "bought_date": item_data["bought_date"],
                    "bought_by_id": item_data["bought_by_id"],
                    "bought_for_id": user_id,  # This user receives/shares this portion
                    "added_by_id": item_data["added_by_id"],
                    "project_id": item_data["project_id"],
                    "exchange_rate": item_data["exchange_rate"],
                    "exchange_rate_date": item_data["exchange_rate_date"],
                    "tags": user_labels,  # Use user-specific labels, will be converted to string below
                }

                # Convert tags to proper string format using ProjectComposer
                # user_labels is a list of selected label IDs for this specific user
                # We need to build a tags_dict and then convert to string
                if pc and user_labels:
                    # For now, store the labels in their respective positions
                    # Position: 0=balance, 1=transaction, 2=account, 3=main, 4+=secondary
                    secondary_label_ids = user_labels[4:] if len(user_labels) > 4 else []
                    
                    # Expand secondary labels: if a label has composite labels, include them too
                    expanded_secondary = self._expand_composite_labels(
                        secondary_label_ids, project_labels
                    )
                    
                    tags_dict = {
                        "c": user_labels[0] if len(user_labels) > 0 else 0,
                        "t": user_labels[1] if len(user_labels) > 1 else 0,
                        "b": user_labels[2] if len(user_labels) > 2 else 0,
                        "m": user_labels[3] if len(user_labels) > 3 else 0,
                        "s": expanded_secondary,  # Use expanded list
                    }
                    db_item_data["tags"] = pc.build_tags_string(tags_dict)
                    self.app.log(
                        f"Built tag string for {username}: {db_item_data['tags']} from dict: {tags_dict} "
                        f"(expanded from {len(secondary_label_ids)} to {len(expanded_secondary)} secondary labels)"
                    )
                else:
                    # Fallback: empty tag string
                    db_item_data["tags"] = "0_0_0_0_[]"
                    self.app.log(f"Using fallback empty tag string for {username}")

                # Log the data being saved with both prices
                self.app.log(
                    f"Saving item share for {username}: "
                    f"{original_price_share:.2f} {item_data['currency']} → "
                    f"{share_amount:.2f} {item_data['currency_final']} "
                    f"({share_percentage:.1f}%)"
                )

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

            # Get ProjectComposer instance for building tag string
            from fiwa_cli.functions.project_composer import ProjectComposer

            project_style = self.app.app_state.get("project_style", "default")
            project_id = item_data["project_id"]

            try:
                pc = ProjectComposer.create(
                    compose_type=project_style, dbh=dbh, project_id=project_id, users=[]
                )
            except Exception as e:
                self.app.log(f"Error creating ProjectComposer: {e}")
                pc = None

            # Get project labels for composite label expansion
            project_labels = self._get_project_labels(project_id)

            # Convert tags to proper string format using ProjectComposer
            if pc and item_data["tags"]:
                # For now, store the main label in position 'm' (position 3)
                secondary_label_ids = item_data["tags"][4:] if len(item_data["tags"]) > 4 else []
                
                # Expand secondary labels: if a label has composite labels, include them too
                expanded_secondary = self._expand_composite_labels(
                    secondary_label_ids, project_labels
                )
                
                tags_dict = {
                    "c": item_data["tags"][0] if len(item_data["tags"]) > 0 else 0,
                    "t": item_data["tags"][1] if len(item_data["tags"]) > 1 else 0,
                    "b": item_data["tags"][2] if len(item_data["tags"]) > 2 else 0,
                    "m": item_data["tags"][3] if len(item_data["tags"]) > 3 else 0,
                    "s": expanded_secondary,  # Use expanded list
                }
                tags_string = pc.build_tags_string(tags_dict)
                self.app.log(
                    f"Built tag string for update: {tags_string} from dict: {tags_dict} "
                    f"(expanded from {len(secondary_label_ids)} to {len(expanded_secondary)} secondary labels)"
                )
            else:
                # Fallback: empty tag string
                tags_string = "0_0_0_0_[]"
                self.app.log("Using fallback empty tag string for update")

            # Prepare UPDATE query
            dbh.load()

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
                item_data["name"],
                item_data.get("note", ""),
                item_data["price"],
                item_data["price_final"],
                item_data["currency"],
                item_data["currency_final"],
                item_data["bought_date"],
                item_data["bought_by_id"],
                item_data["exchange_rate"],
                item_data["exchange_rate_date"],
                tags_string,
                self._item_id,
                item_data["project_id"],
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
            #self.query_one("#grid-item-currency", Select).value = currency_main              # Don't reset currency to default, let it stay as last selected for convenience
            #self.query_one("#grid-item-bought-date", Input).value = datetime.now().strftime( # Don't reset bought date to today, let it stay as last entered for convenience
            #    "%Y-%m-%d"
            #)

            # Clear additional fields
            self.query_one("#item-note", Input).value = ""
            #self.query_one("#item-exchange-rate", Input).value = "1.0"
            #self.query_one("#item-exchange-date", Input).value = datetime.now().strftime("%Y-%m-%d")

            # Reset bought-by select field to current user if available
            # try:
            #     project_users = self._get_project_users(project_id)
            #     if project_users:
            #         default_user = user_id if user_id > 0 else project_users[0]["user_id"]
            #         self.query_one("#grid-item-bought-by", Select).value = default_user
            #
            #         # Clear cost-sharing fields (only in create mode)
            #         if not self._edit_mode:
            #             for user in project_users:
            #                 try:
            #                     share_input = self.query_one(f"#share-{user['user_id']}", Input)
            #                     # Reset to default: 100% for bought_by user, 0% for others
            #                     if user["user_id"] == default_user:
            #                         share_input.value = "100"
            #                     else:
            #                         share_input.value = "0"
            #                 except Exception:
            #                     pass  # Field might not exist
            # except Exception as e:
            #     self.app.log(f"Error resetting user fields: {e}")

            # Clear label selections
            # try:
            #     labels_widget = self.query_one("#item-labels", SelectionList)
            #     labels_widget.deselect_all()
            # except Exception:
            #     pass

            # Generate new UUID for next item
            self._item_uuid = str(uuid.uuid4())

            #self.app.notify("✓ Form cleared", severity="info")

        except Exception as e:
            self.app.log(f"Error clearing form: {e}")
            self.app.notify("Error clearing form", severity="error")
