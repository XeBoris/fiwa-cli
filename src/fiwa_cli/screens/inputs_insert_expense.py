"""Expense creation form for FiWa CLI.

This module provides a simple wrapper around the ItemInputForm component
for creating new expense transactions. It automatically opens the input
modal when mounted and handles the creation workflow.

The form integrates with:
    - ItemInputForm: Core expense input widget with all fields
    - Database: Saves expenses via op_item_create()
    - Label system: Allows label/category selection
    - Cost sharing: Supports splitting expenses between users

Key Features:
    - Automatic modal opening on mount
    - Integration with ItemInputForm component
    - Expense validation and confirmation
    - Database persistence
    - Default label assignment

Classes:
    CreateExpenseForm: Wrapper form that launches ItemInputForm modal

Example:
    Mounting the form::

        >>> from fiwa_cli.screens.inputs_insert_expense import CreateExpenseForm
        >>> form = CreateExpenseForm()
        >>> content_area.mount(form)
        >>> # ItemInputForm modal opens automatically

    User workflow::

        >>> # User clicks "New" in InputsScreen
        >>> # CreateExpenseForm mounted
        >>> # ItemInputForm modal opens immediately
        >>> # User fills expense details
        >>> # User clicks Save
        >>> # Confirmation modal shows
        >>> # User confirms
        >>> # Expense written to database
        >>> # Modal closes, ExpenseCreated message posted

See Also:
    components.item_input_form.ItemInputForm: Core input component
    inputs.InputsScreen: Parent screen that mounts this form
    inputs_edit_expense: Editing existing expenses
"""

from textual.widgets import Static, Button
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.message import Message
from fiwa_cli.components.item_input_form import ItemInputForm

from fiwa_cli.functions.loader import load_dynamic_css


class CreateExpenseForm(Vertical):
    """Wrapper form for creating new expenses via ItemInputForm modal.

    This widget provides a simple container that automatically launches
    the ItemInputForm modal when mounted. It serves as a bridge between
    the InputsScreen sidebar navigation and the core expense input widget.

    The workflow:
        1. Form is mounted in InputsScreen content area
        2. on_mount() automatically opens ItemInputForm modal
        3. User fills expense details in modal
        4. User saves, modal closes with result
        5. _handle_item_created() processes the result
        6. ExpenseCreated message posted to parent

    Attributes:
        None (stateless wrapper)

    Messages:
        ExpenseCreated: Emitted when expense is successfully created
            - Attributes:
                - expense_data (dict): Complete expense information

    Auto-Launch Behavior:
        When this form is mounted, it immediately opens ItemInputForm
        as a modal dialog. This provides a streamlined UX where clicking
        "New" in the sidebar directly opens the input form.

    Example:
        Basic usage::

            >>> form = CreateExpenseForm()
            >>> content_area.mount(form)
            >>> # ItemInputForm modal opens automatically

        Handling creation::

            >>> def on_create_expense_form_expense_created(self, message):
            >>>     expense = message.expense_data
            >>>     self.app.file_log.info(f"Expense created: {expense['name']}")

        User creates groceries expense::

            >>> # Form mounted → ItemInputForm opens
            >>> # User fills:
            >>> #   Name: "Whole Foods"
            >>> #   Price: 85.00 USD
            >>> #   Date: 2026-03-29
            >>> #   Labels: Groceries (main), Chase Credit (account)
            >>> # User clicks Save
            >>> # Confirmation modal shows all details + labels
            >>> # User clicks Confirm
            >>> # Expense saved to database
            >>> # Modal closes
            >>> # ExpenseCreated message posted

    Note:
        This is a thin wrapper - all the actual input functionality
        is in ItemInputForm. This pattern allows the same input form
        to be used in different contexts (new expense, edit expense).

        The automatic modal opening on mount provides a better UX than
        requiring the user to click an additional "Add" button.

    See Also:
        components.item_input_form.ItemInputForm: Core input widget
        inputs.InputsScreen: Parent screen with sidebar
        inputs_edit_expense.EditExpenseView: Editing existing expenses
    """

    class ExpenseCreated(Message):
        """Message sent when an expense is successfully created.

        Posted after the ItemInputForm modal closes with a successful
        result (user confirmed the expense details).

        Attributes:
            expense_data (dict): Dictionary containing:
                - item_id: Database ID of created expense
                - name: Expense name
                - price: Original price
                - currency: Original currency
                - date: Purchase date
                - All other expense fields

        Example:
            >>> def on_create_expense_form_expense_created(self, message):
            >>>     item_id = message.expense_data['item_id']
            >>>     self.notify(f"Expense {item_id} created!")
        """

        def __init__(self, expense_data: dict) -> None:
            """Initialize ExpenseCreated message.

            Args:
                expense_data: Complete expense information dictionary
            """
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
            yield Static(
                "Click the button below to add a new expense transaction.", id="instructions"
            )
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
            self.app.notify(
                f"Expense '{item_data.get('name', 'Unknown')}' created!", severity="success"
            )
        else:
            self.app.notify("Expense creation cancelled", severity="info")
