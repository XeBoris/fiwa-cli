"""Item input form component - reusable form for adding/editing items (transactions)."""
from textual.widgets import Static, Button, Input, Select, Label, SelectionList, Switch, Placeholder
from textual.containers import Vertical, Horizontal, Grid, ScrollableContainer
from textual.app import ComposeResult
from textual.message import Message
from datetime import datetime
import uuid
from textual.screen import ModalScreen

from textual import on

# from textual_timepiece.pickers import DatePicker, DateSelect
# from whenever import Date, days

class ItemConfirmationModal(ModalScreen):
    """Modal screen to confirm item creation before saving to database."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    ItemConfirmationModal {
        align: center middle;
        background: $background 80%;
    }
    
    ItemConfirmationModal > Vertical {
        width: 60;
        height: auto;
        background: $panel;
        border: thick $accent;
        padding: 2;
    }
    
    ItemConfirmationModal .modal-title {
        text-style: bold;
        text-align: center;
        color: $accent;
        padding: 0 0 1 0;
    }
    
    ItemConfirmationModal .summary-section {
        padding: 1 0;
        border: solid $primary;
        margin: 1 0;
    }
    
    ItemConfirmationModal .summary-row {
        padding: 0 1;
    }
    
    ItemConfirmationModal .button-row {
        layout: horizontal;
        height: 10;
        align: center middle;
        padding: 1 0 0 0;
    }
    
    ItemConfirmationModal #confirm-ok-button {
        background: green;
        color: white;
        margin: 0 1;
    }
    
    ItemConfirmationModal #confirm-back-button {
        background: orange;
        color: white;
        margin: 0 1;
    }
    """

    def __init__(self, item_data: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_data = item_data

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Confirm Transaction", classes="modal-title")

            with Vertical(classes="summary-section"):
                yield Static("[bold]Transaction Summary:[/bold]", classes="summary-row")
                yield Static(f"Name: {self.item_data.get('name', 'N/A')}", classes="summary-row")
                yield Static(f"Price: {self.item_data.get('price', 0):.2f} {self.item_data.get('currency', 'N/A')}", classes="summary-row")
                yield Static(f"Final Price: {self.item_data.get('price_final', 0):.2f} {self.item_data.get('currency_final', 'N/A')}", classes="summary-row")
                yield Static(f"Date: {self.item_data.get('bought_date', 'N/A')}", classes="summary-row")
                yield Static(f"Bought By: {self.item_data.get('bought_by_name', 'N/A')}", classes="summary-row")
                yield Static(f"Bought For: {self.item_data.get('bought_for_name', 'N/A')}", classes="summary-row")
                if self.item_data.get('note'):
                    yield Static(f"Note: {self.item_data.get('note', '')}", classes="summary-row")
                if self.item_data.get('labels_text'):
                    yield Static(f"Labels: {self.item_data.get('labels_text', '')}", classes="summary-row")

            with Horizontal(classes="button-row"):
                yield Button("✓ OK - Save to Database", id="confirm-ok-button", variant="success")
                yield Button("← Back - Edit", id="confirm-back-button", variant="warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the confirmation modal."""
        if event.button.id == "confirm-ok-button":
            self.dismiss(True)  # Return True to indicate save
        elif event.button.id == "confirm-back-button":
            self.dismiss(False)  # Return False to indicate cancel

    def action_cancel(self) -> None:
        """Handle ESC key press."""
        self.dismiss(False)

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
        background: $background 95%;
    }

    ItemInputForm .form-title {
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
        background: $accent;
        color: $text;
        height: 2;
    }

    # ItemInputForm .form-section {
    #     margin: 1 0;
    #     padding: 1;
    #     background: $panel;
    #     border: solid $primary;
    # }

    # ItemInputForm .section-title {
    #     text-style: bold;
    #     color: $accent;
    #     padding: 0 0 1 0;
    # }
    
    # ItemInputForm #form-label {
    #     text-style: bold;
    #     padding: 0 0 0 0;
    #     height: 3;
    # }
    # 
    # ItemInputForm .form-label {
    #     text-style: bold;
    #     padding: 0 0 0 0;
    #     height: 1;
    #     border: none;
    # }
    # 
    # ItemInputForm Input {
    #     width: 100%;
    #     margin: 0 0 1 0;
    # }
    
    
    # ItemInputForm .item-name {
    #     border: none;
    #     height: 2;
    # }
    # 
    # ItemInputForm .item-price {
    #     width: 30;
    #     border: none;
    # }

    # ItemInputForm Select {
    #     width: 100%;
    #     margin: 0 0 1 0;
    # }



    # ItemInputForm .form-row {
    #     grid-size: 2 1;
    #     grid-gutter: 2;
    #     width: 100%;
    #     height: auto;
    #     margin: 0 0 1 0;
    # }
    # 
    # 
    # ItemInputForm .form-row-3 {
    #     grid-size: 3 1;
    #     grid-gutter: 1;
    #     width: 100%;
    #     height: auto;
    #     margin: 0 0 1 0;
    # }

    ItemInputForm .form-buttons {
        grid-size: 3 1;
        grid-gutter: 1;
        width: 100%;
        height: auto;
        margin-top: 2;
    }
    
    ItemInputForm .button-row {
        border: round $accent;
        background: $surface;
        layout: horizontal;
        align: center bottom;
        height: 7;
        width: 100%;
        margin: 0 0 0 0;
        padding: 0;
    }
    
    ItemInputForm .button-row Vertical {
        width: 1fr;
        height: 100%;
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
    
    ItemInputForm .form-grid-row-1 {
        border: round $accent;
        background: $surface;
        grid-size: 6 2;
        grid-gutter: 0;
        grid-columns: 1fr 15 12 1fr 1fr 1fr;
        width: 100%;
        height: auto;
        margin: 0 0 0 0;
    }
    
    ItemInputForm .form-grid-row-2 {
        grid-size: 6 2;
        grid-gutter: 0;
        grid-columns: 20 20 1fr 1fr 1fr 1fr;
        width: 100%;
        height: auto;
        margin: 0 0 1 0;
    }
    
    ItemInputForm .form-grid-label {
        text-style: bold;
        padding: 0 0 0 0;
        width: 20;
        height: 3;
    }
    # row 1
    ItemInputForm #grid-item-name {
        width: 100%;
        border: solid $primary;
        height: 3;
    }
    ItemInputForm #grid-item-price {
        width: 100%;
        border: solid $primary;
        height: 3;
    }
    ItemInputForm #grid-item-currency {
        width: 100%;
        border: none;
        height: 3;
    }
    ItemInputForm #grid-item-bought-date {
        width: 100%;
        border: solid $primary;
        height: 3;
    }
    ItemInputForm #grid-item-exchange-date {
        width: 100%;
        border: solid $primary;
        height: 3;
    }
    ItemInputForm #grid-item-exchange-rate {
        width: 100%;
        border: solid $primary;
        height: 3;
    }

    ItemInputForm #grid-item-bought-by {
        width: 100%;
        border: none;
        height: 4;
    }

    # row 2    
    ItemInputForm #bought-for-horizontal-wrapper {
        layout: horizontal;
        width: 100%;
        height: auto;
        margin: 0 0 0 0;
    } 
    
    ItemInputForm #bought-for-scroll {
        width: 35;
        height: 20;
        margin: 0 0;
        border: round $accent;
        background: $surface;
    }
    
    ItemInputForm #additional-content-wrapper {
        width: 1fr;  /* Takes remaining space after 35-width bought-for-scroll */
        height: auto;
        margin: 0 0 0 2;  /* 2 units left margin for spacing */
        padding: 0;
        border: round $accent;
        background: $surface;
    }
    
    ItemInputForm #bought-for-wrapper {
        width: 100%;
        height: 100%;
        min-height: 100%;
        padding: 0;
        margin: 0 0;
    }
    
    ItemInputForm #bought-for-title {
        height: 2;
        width: 100%;
        text-style: bold;
        color: $text;
        background: $accent;
        padding: 0;
        margin: 0 0 0 0;
    }
    
    ItemInputForm .bought-for-user-row {
        layout: horizontal;
        height: 4;
        width: 100%;
        margin: 0 0 0 0;
    }
    
    ItemInputForm .user-name-label {
        height: 3;
        width: 15;
        padding: 0 1 0 0;
        background: $surface;
        content-align: left middle;
    }
    
    ItemInputForm .user-share-input {
        height: 3;
        width: 15;
        border: solid $primary;
    }
    
    ItemInputForm #bought-for-container {
        width: 35;
        height: auto;
        padding: 1;
        border: $accent;
        background: $panel;
    }
    
    ItemInputForm #bought-for-no-users {
        height: 3;
        width: 100%;
        padding: 1;
        color: $warning;
    }
    ItemInputForm .bought-for-spacer {
    height: 5;  /* Forces extra height to trigger scroll */
    width: 100%;
}
    """

    class ItemCreated(Message):
        """Message sent when an item is created and saved to database."""
        def __init__(self, item_id: int, item_data: dict) -> None:
            self.item_id = item_id
            self.item_data = item_data
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._item_uuid = str(uuid.uuid4())
        self._pending_item_data = None
        self._project_users = []  # Store project users for dynamic updates

    def on_mount(self) -> None:
        """Called when the form is mounted - check if bought-for-grid exists."""
        try:
            self.app.log("=== ItemInputForm on_mount called ===")

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

        yield Static(f"Add Transaction - {user_name}", classes="form-title")

        # Get currencies from project
        currency_main = self.app.app_state.get("current_project_currency_main", "USD")
        currency_list = self.app.app_state.get("current_project_currency_list", [])

        # Build currency options (main currency first, then additional currencies)
        currency_options = [(currency_main, currency_main)]
        for curr in currency_list:
            if curr != currency_main:
                currency_options.append((curr, curr))

        # Get project users
        project_users = self._get_project_users(project_id)
        self._project_users = project_users  # Store for later use
        user_options = [(u['username'], u['user_id']) for u in project_users]

        # Initially show ALL project users in the "Bought For" section
        # The list will be dynamically filtered when user selects "Bought By"
        user_options_share_to = [(u['username'], u['user_id']) for u in project_users if u["user_id"] != user_id]

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
            yield Static("Placeholder", classes="form-grid-label")
            # row 2
            yield Input(
                placeholder="e.g., Groceries, Rent, Salary",
                id="grid-item-name",
                max_length=64
            )
            yield Input(
                placeholder="0.00",
                id="grid-item-price",
                type="number"
            )
            yield Select(
                options=currency_options if currency_options else [("USD", "USD")],
                value=currency_main if currency_main else "USD",
                id="grid-item-currency",
                allow_blank=False
            )
            yield Input(
                placeholder="YYYY-MM-DD",
                id="grid-item-bought-date",
                value=datetime.now().strftime("%Y-%m-%d")
            )
            yield Select(
                options=user_options if user_options else [("No users", -1)],
                value=user_id if user_id > 0 else (user_options[0][1] if user_options else -1),
                id="grid-item-bought-by",
                allow_blank=False
            )
            yield Placeholder()

        # Wrap "Bought For" section - use simple Vertical + Horizontal layout (more stable than Grid)
        user_count = len(user_options_share_to)

        self.app.log(f"=== BOUGHT FOR SECTION DEBUG ===")
        self.app.log(f"user_count: {user_count}")
        self.app.log(f"user_options_share_to: {user_options_share_to}")

        with Horizontal(id="bought-for-horizontal-wrapper"):
            # left side: Bought For title and user list
            if user_count > 0:
                self.app.log(f"Creating Vertical layout with {user_count} users")

                with ScrollableContainer(id="bought-for-scroll"):
                    v = Vertical(id="bought-for-wrapper")
                    #v.styles.height = 5 + user_count*3
                    with v:
                        # Title
                        yield Static("Bought For *", id="bought-for-title")
                        self.app.log("Yielded bought-for-title")

                        # Add each user as a Horizontal row
                        for idx, i_item in enumerate(user_options_share_to):
                            self.app.log(f"Adding user {idx + 1}/{user_count}: {i_item[0]} (ID: {i_item[1]})")
                            with Horizontal(classes="bought-for-user-row"):
                                yield Static(f"{i_item[0]}", id=f"user-label-{i_item[1]}", classes="user-name-label")
                                yield Input(
                                    placeholder="0-100%",
                                    value="0",
                                    type="number",
                                    id=f"share-{i_item[1]}",
                                    classes="user-share-input"
                                )
                        self.app.log("Finished adding all users")
                    yield Static("", classes="bought-for-spacer")
            else:
                self.app.log("No users - creating fallback container")
                with Vertical(id="bought-for-scroll"):
                    yield Static("Bought For *", id="bought-for-title", classes="form-grid-label")
                    yield Static("No users available", id="bought-for-no-users", classes="form-grid-label")

            # Right side: Additional content (fills remaining width)
            with Vertical(id="additional-content-wrapper"):
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
                with Horizontal():
                    with Vertical():
                        yield Static("Note", classes="form-label")
                        yield Input(
                            placeholder="Additional details (optional)",
                            id="item-note",
                            max_length=255
                        )


                with Horizontal(classes="button-row"):
                    with Vertical():
                        yield Button("💾 Save", id="save-button")
                    with Vertical():
                        yield Button("🔄 Clear", id="clear-button")
                    with Vertical():
                        yield Button("❌ Cancel", id="cancel-button")


        #     with Vertical():
        #         yield Static("Labels", classes="form-label")
        #         if label_options:
        #             yield SelectionList[int](*[(name, lid, False) for name, lid in label_options], id="item-labels")
        #         else:
        #             yield Static("No labels available", classes="form-label")
        #
        # with Horizontal():
        #     with Vertical():
        #         yield Static("Note", classes="form-label")
        #         yield Input(
        #             placeholder="Additional details (optional)",
        #             id="item-note",
        #             max_length=255
        #         )
        # with Horizontal():
        #     with Vertical():
        #         yield Static("Exchange Rate", classes="form-label")
        #         yield Input(
        #             placeholder="1.0",
        #             id="item-exchange-rate",
        #             value="1.0",
        #             type="number"
        #         )
        #     with Vertical():
        #         yield Static("Exchange Rate Date", classes="form-label")
        #         yield Input(
        #             placeholder="YYYY-MM-DD",
        #             id="item-exchange-date",
        #             value=datetime.now().strftime("%Y-%m-%d")
        #         )



    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save-button":
            await self._save_item()
        elif event.button.id == "clear-button":
            self._clear_form()
        elif event.button.id == "cancel-button":
            self.dismiss()  # Dismiss the modal form

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle select widget changes."""
        if event.select.id == "grid-item-bought-by":
            # User changed the "bought by" selection
            selected_user_id = event.value
            self._update_bought_for_section(selected_user_id)

    def _update_bought_for_section(self, exclude_user_id: int) -> None:
        """Update the 'Bought For' section to exclude the selected 'bought by' user."""
        try:
            # Rebuild with updated user list (excluding the selected user)
            user_options_share_to = [
                (u['username'], u['user_id'])
                for u in self._project_users
                if u['user_id'] != exclude_user_id
            ]

            user_count = len(user_options_share_to)
            self.app.log(f"Updated 'Bought For' section, excluding user {exclude_user_id}, {user_count} users remaining")

            # Try to find and remove the old grid
            try:
                old_grid = self.query_one("#bought-for-grid")
                old_grid.remove()
            except:
                try:
                    old_container = self.query_one("#bought-for-container")
                    old_container.remove()
                except:
                    self.app.log("No existing bought-for grid/container found")

            # Find the parent to mount the new grid
            parent = self.query_one("ItemInputForm")

            if user_count > 0:
                # Create new Grid
                new_grid = Grid(id="bought-for-grid")

                # Add title
                new_grid.mount(Static("Bought For *", id="bought-for-title", classes="form-grid-label"))

                # Add users
                for i_item in user_options_share_to:
                    new_grid.mount(Static(f"{i_item[0]}", id=f"user-label-{i_item[1]}", classes="user-name-label"))
                    new_grid.mount(Input(
                        placeholder="0-100%",
                        value="0",
                        type="number",
                        id=f"share-{i_item[1]}",
                        classes="user-share-input"
                    ))

                # Mount the new grid after the first Grid
                grids = list(parent.query(Grid))
                if len(grids) > 0:
                    parent.mount(new_grid, after=grids[0])
                else:
                    parent.mount(new_grid)
            else:
                # Create vertical container with no users message
                new_container = Vertical(id="bought-for-container")
                new_container.mount(Static("Bought For *", id="bought-for-title", classes="form-grid-label"))
                new_container.mount(Static("No users available", id="bought-for-no-users", classes="form-grid-label"))

                # Mount after first grid
                grids = list(parent.query(Grid))
                if len(grids) > 0:
                    parent.mount(new_container, after=grids[0])
                else:
                    parent.mount(new_container)

        except Exception as e:
            self.app.log(f"Error updating bought-for section: {e}")
            import traceback
            self.app.log(f"Traceback: {traceback.format_exc()}")

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
            name = self.query_one("#item-name", Input).value.strip()
            note = self.query_one("#item-note", Input).value.strip()
            price = self.query_one("#item-price", Input).value.strip()
            currency = self.query_one("#item-currency", Select).value
            exchange_rate = self.query_one("#item-exchange-rate", Input).value.strip()
            exchange_date = self.query_one("#item-exchange-date", Input).value.strip()
            bought_date = self.query_one("#item-bought-date", Input).value.strip()
            bought_by_id = self.query_one("#item-bought-by", Select).value
            bought_for_id = self.query_one("#item-bought-for", Select).value

            # Get selected labels
            try:
                labels_widget = self.query_one("#item-labels", SelectionList)
                selected_labels = list(labels_widget.selected)

                # Get label names for display
                project_labels = self._get_project_labels(project_id)
                label_names = [label['name'] for label in project_labels if label['label_id'] in selected_labels]
                labels_text = ", ".join(label_names) if label_names else "None"
            except:
                selected_labels = []
                labels_text = "None"

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
            if bought_for_id <= 0:
                self.app.notify("'Bought For' user is required", severity="error")
                return

            # Convert and calculate
            price_float = float(price)
            exchange_rate_float = float(exchange_rate) if exchange_rate else 1.0
            price_final = price_float * exchange_rate_float
            currency_final = currency_main  # Use project's main currency for final price

            # Get user names for display
            project_users = self._get_project_users(project_id)
            bought_by_name = next((f"{u['first_name']} {u['last_name']}" for u in project_users if u['user_id'] == bought_by_id), "Unknown")
            bought_for_name = next((f"{u['first_name']} {u['last_name']}" for u in project_users if u['user_id'] == bought_for_id), "Unknown")

            bought_by_user_name = next((f"{u['username']}" for u in project_users if u['user_id'] == bought_by_id), "Unknown")
            bought_for_user_name = next((f"{u['username']}" for u in project_users if u['user_id'] == bought_for_id), "Unknown")

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
                'exchange_rate_date': exchange_date if exchange_date else datetime.now().strftime("%Y-%m-%d"),
                'bought_date': bought_date,
                'bought_by_id': bought_by_id,
                'bought_for_id': bought_for_id,
                'added_by_id': user_id,  # Current user adds the item
                'project_id': project_id,
                'tags': selected_labels,  # List of label IDs
                # Extra fields for display in confirmation
                'bought_by_name': bought_by_name,
                'bought_for_name': bought_for_name,
                'labels_text': labels_text
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

    async def _show_confirmation_and_save(self) -> None:
        """Show confirmation modal and handle the save process."""
        try:
            # Show the confirmation modal and wait for result
            result = await self.app.push_screen_wait(ItemConfirmationModal(self._pending_item_data))

            if result:  # User clicked OK
                # Save to database
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

        Returns:
            item_id if successful, None otherwise
        """
        try:
            dbh = self.app._config.get("dbh")
            if not dbh:
                self.app.notify("Database connection not available", severity="error")
                self.app.log("ERROR: Database handler not available in _config")
                return None

            # Remove display-only fields before saving
            db_item_data = {k: v for k, v in item_data.items()
                           if k not in ['bought_by_name', 'bought_for_name', 'labels_text']}

            # Convert tags list to JSON string
            import json
            db_item_data['tags'] = json.dumps(db_item_data['tags'])

            # Log the data being saved
            self.app.log(f"Attempting to save item to database: {db_item_data['name']}")
            self.app.log(f"Item data keys: {list(db_item_data.keys())}")

            # Save to database
            item_id = dbh.op_item_create(db_item_data)

            self.app.log(f"op_item_create returned: {item_id}")

            if item_id:
                self.app.log(f"✓ Item saved to database with ID: {item_id}")
                return item_id
            else:
                self.app.notify("Failed to save item to database", severity="error")
                self.app.log("ERROR: op_item_create returned None/False")
                return None

        except Exception as e:
            self.app.notify(f"Database error: {str(e)}", severity="error")
            self.app.log(f"EXCEPTION in _save_to_database: {e}")
            import traceback
            self.app.log(f"Traceback: {traceback.format_exc()}")
            return None


    def _clear_form(self) -> None:
        """Clear all form fields."""
        try:
            # Get default values
            project_id = self.app.app_state.get("project_id", 0)
            user_id = self.app.app_state.get("user_id", -1)
            currency_main = self.app.app_state.get("current_project_currency_main", "USD")

            # Clear input fields
            self.query_one("#item-name", Input).value = ""
            self.query_one("#item-note", Input).value = ""
            self.query_one("#item-price", Input).value = ""
            self.query_one("#item-currency", Select).value = currency_main
            self.query_one("#item-exchange-rate", Input).value = "1.0"
            self.query_one("#item-exchange-date", Input).value = datetime.now().strftime("%Y-%m-%d")
            self.query_one("#item-bought-date", Input).value = datetime.now().strftime("%Y-%m-%d")

            # Reset select fields to current user if available
            try:
                project_users = self._get_project_users(project_id)
                if project_users:
                    default_user = user_id if user_id > 0 else project_users[0]['user_id']
                    self.query_one("#item-bought-by", Select).value = default_user
                    self.query_one("#item-bought-for", Select).value = default_user
            except:
                pass

            # Clear label selections
            try:
                labels_widget = self.query_one("#item-labels", SelectionList)
                labels_widget.deselect_all()
            except:
                pass

            # Generate new UUID for next item
            self._item_uuid = str(uuid.uuid4())

            self.app.notify("Form cleared", severity="info")

        except Exception as e:
            self.app.log(f"Error clearing form: {e}")
