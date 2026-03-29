"""Expense editing interface for FiWa CLI.

This module provides a comprehensive tabbed interface for viewing and editing
existing expenses. It displays all expenses for the selected period in
per-user tabs with interactive DataTables.

The editing interface features:
    - Period-filtered expense display (week or month)
    - Tabbed view with one tab per project user
    - Sortable DataTables (click column headers)
    - Row-click editing via ItemInputForm modal
    - Real-time period updates from WeekMonthWidget
    - Label display with transaction categorization

Key Features:
    - Per-user expense organization in tabs
    - Period-based filtering from app_state
    - Interactive row selection for editing
    - Inline editing via ItemInputForm modal
    - Automatic refresh on period changes
    - Sortable columns
    - Label information display

Classes:
    EditExpenseView: Main editing interface with tabbed DataTables

Data Display:
    Each user tab shows a DataTable with columns:
        - Name: Expense/transaction name (15 char width)
        - Price: Original price in original currency
        - Curr: Original currency code
        - Final: Converted price in main currency
        - [MAIN]: Main currency code (e.g., USD, EUR)
        - Date: Transaction date
        - Label: Main category label name
        - Account: Bank/account label name

    All expenses where bought_for_id matches the user are shown,
    regardless of who purchased them (bought_by_id).

Period Filtering:
    Expenses are filtered by:
        - project_id: Current project
        - bought_for_id: Each user sees their own expenses
        - bought_date: Between period_start and period_end

    The period is controlled by WeekMonthWidget in the InputsScreen
    sidebar and automatically updates when changed.

Editing Workflow:
    1. User selects their tab
    2. User clicks on expense row
    3. ItemInputForm modal opens with pre-filled data
    4. User modifies fields (price, date, labels, etc.)
    5. User clicks Save
    6. Confirmation modal shows updated details
    7. User confirms
    8. Database updated
    9. Table refreshes to show changes

Example:
    Mounting the view::

        >>> from fiwa_cli.screens.inputs_edit_expense import EditExpenseView
        >>> view = EditExpenseView()
        >>> content_area.mount(view)

    Typical usage::

        >>> # User in InputsScreen
        >>> # Clicks "Edit" button
        >>> # EditExpenseView appears
        >>> # Tabs shown: [Batman] [Superman]
        >>> # Batman tab selected (default)
        >>> # Table shows:
        >>> #   Groceries  $85  USD  $85  [USD]  2026-03-15  Food  Chase
        >>> #   Coffee     $5   USD  $5   [USD]  2026-03-15  Food  Cash
        >>> # User clicks "Groceries" row
        >>> # ItemInputForm modal opens with:
        >>> #   Name: Groceries
        >>> #   Price: 85.00
        >>> #   Currency: USD
        >>> #   Date: 2026-03-15
        >>> #   Labels: Food (main), Chase (account)
        >>> # User changes price to $90
        >>> # User clicks Save
        >>> # Confirmation modal shows updated price
        >>> # User confirms
        >>> # Database updated
        >>> # Table refreshes, now shows $90

    Period change integration::

        >>> # User viewing March expenses
        >>> # User changes WeekMonthWidget to April
        >>> # on_week_month_widget_period_changed fires in InputsScreen
        >>> # InputsScreen calls view.refresh_tables()
        >>> # All tabs reload with April expenses
        >>> # Batman tab now shows different data

Performance:
    - Lazy tab loading: Only active tab's data is visible
    - Efficient queries: Single query per user
    - Minimal re-renders: Only refreshes on period change or edit
    - Sorted by default: Date descending (newest first)

Note:
    The view is tightly integrated with the period selection in InputsScreen.
    When the user changes the week/month in the sidebar, this view automatically
    refreshes to show expenses for the new period.

    Editing is done via ItemInputForm modal in "edit mode", which pre-fills
    all fields with existing expense data. The same ItemInputForm is used
    for both creating and editing expenses.

See Also:
    inputs.InputsScreen: Parent screen with period picker
    inputs_insert_expense: Creating new expenses
    components.item_input_form.ItemInputForm: Core input/edit widget
    reports_basic.BasicReportForm: Similar tabbed expense display
"""
from textual.containers import VerticalScroll, Vertical
from textual.widgets import Static, TabbedContent, TabPane, DataTable
from textual.app import ComposeResult
from textual import on
from fiwa_cli.components.item_input_form import ItemInputForm

from fiwa_cli.functions.loader import load_dynamic_css
import json

class EditExpenseView(VerticalScroll):
    """Tabbed expense editing interface with per-user DataTables.

    This widget displays all expenses for the selected period organized
    by user in tabs. Each tab contains a DataTable with all expenses for
    that user, allowing easy viewing and editing.

    The view provides:
        - Period-filtered expense display
        - One tab per project user
        - Sortable DataTables
        - Row-click editing
        - Automatic refresh on period changes
        - Label information display

    Attributes:
        None (stateless widget, reads from app_state)

    Tab Structure:
        For each project user:
            Tab: {First Name} {Last Name}
                └── DataTable: All expenses bought for this user

    DataTable Columns:
        - Name (15 char): Transaction name
        - Price: Original price amount
        - Curr: Original currency code
        - Final: Converted price in main currency
        - [MAIN]: Main currency column header
        - Date: Transaction date (YYYY-MM-DD)
        - Label: Main category label
        - Account: Bank/account label

    Row Keys:
        Each row has key format: "{item_id}" (e.g., "42")
        This allows efficient row lookup for editing.

    Sorting:
        - Click any column header to sort
        - Default: Sorted by Date descending
        - Toggle: Click again for reverse order
        - Visual indicator shows current sort

    Editing:
        Row click → ItemInputForm modal:
            1. User clicks row
            2. on_row_selected() fires
            3. ItemInputForm modal opens in "edit mode"
            4. Form pre-filled with expense data
            5. User modifies and saves
            6. Database updated
            7. refresh_tables() called
            8. Table shows updated data

    Period Integration:
        Uses app_state for filtering:
            - current_period_start: Inclusive start date
            - current_period_end: Exclusive end date
            - current_period_label: Display label (e.g., "2026 Week 10")

        When period changes in InputsScreen:
            - InputsScreen._refresh_data_tables() called
            - Calls this view's refresh_tables()
            - All tabs reload with new period data

    Example:
        Basic usage::

            >>> view = EditExpenseView()
            >>> content_area.mount(view)

        User edits expense::

            >>> # Batman's tab active
            >>> # Table shows 5 expenses for March
            >>> # User clicks "Groceries - $85" row
            >>> # ItemInputForm opens with all fields filled
            >>> # User changes:
            >>> #   Price: 85 → 90
            >>> #   Label: Food → Groceries
            >>> # User saves
            >>> # Database updated
            >>> # Table refreshes, row now shows:
            >>> #   Groceries  $90  USD  $90  [USD]  2026-03-15  Groceries  Chase

        Period change::

            >>> # Viewing March (Week 11)
            >>> # User changes to Week 12
            >>> # refresh_tables() called automatically
            >>> # All tabs reload with Week 12 data

    Performance:
        - Lazy loading: Only active tab renders initially
        - Single query per user
        - Efficient refresh: Only updates data, preserves UI
        - Maintains tab selection during refresh

    Note:
        The view shows expenses "bought for" each user, not necessarily
        "bought by" them. This is important for cost sharing - if Batman
        buys groceries for Superman, it appears in Superman's tab.

        The refresh_tables() method is called from the parent InputsScreen
        when the period changes, ensuring data stays synchronized.

    See Also:
        inputs.InputsScreen: Parent screen with period picker
        components.item_input_form.ItemInputForm: Editing modal
        reports_basic.BasicReportForm: Similar tabbed display with totals
    """

    # DEFAULT_CSS = """
    #
    # """

    def __init__(self, *args, **kwargs):
        """Initialize the edit expense view.

        Args:
            *args: Positional arguments passed to parent VerticalScroll
            **kwargs: Keyword arguments passed to parent VerticalScroll
        """
        super().__init__(*args, **kwargs)

    def on_mount(self) -> None:
        """Load dynamic CSS when the view is mounted."""
        try:
            load_dynamic_css(self, "screens_inputs_edit_expense.tcss")
        except Exception as e:
            self.app.log(f"Could not load external CSS for EditExpenseView: {e}")

    def compose(self) -> ComposeResult:
        yield Static("Edit Expenses", classes="form-title")

        # Display current date selection
        period_start = self.app.app_state.get("current_period_start")
        period_end = self.app.app_state.get("current_period_end")
        period_label = self.app.app_state.get("current_period_label", "")

        if period_start and period_end:
            date_range_text = f"𝌌 {period_label}: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
        else:
            date_range_text = "𝌌 Showing all expenses"

        self.app.log(f"EditExpenseView compose - Period: {date_range_text}")
        yield Static(date_range_text, id="date-selection-display", classes="date-info")

        # Get project and users
        project_id = self.app.app_state.get("project_id", 0)
        project_users = self._get_project_users(project_id)

        # Get main currency for column header
        currency_main = self.app.app_state.get("current_project_currency_main", "USD")

        # Create tabbed content with one tab per user
        with TabbedContent():
            for user in project_users:
                with TabPane(f"{user['first_name']} {user['last_name']}", id=f"tab-user-{user['user_id']}"):
                    # Create DataTable for this user's items
                    table = DataTable(id=f"items-table-{user['user_id']}")

                    # Add columns and store the keys
                    #col_id = table.add_column("ID")
                    col_name = table.add_column("Name", width=15)
                    col_price = table.add_column("Price")
                    col_currency = table.add_column("Currency")
                    col_final = table.add_column(f"Final [{currency_main}]")
                    col_date = table.add_column("Date")
                    col_label = table.add_column("Labels")

                    table.zebra_stripes = True
                    table.fixed_columns = 1

                    table.cursor_type = "row"

                    # Fetch items for this user
                    items = self._get_user_items(user['user_id'], project_id)
                    for item in items:
                        # Extract date only (remove time if present)
                        date_str = str(item['bought_date']).split()[0] if item['bought_date'] else ""

                        # Get transaction label name (already extracted in _get_user_items)
                        label_names = item.get("label_d", "")

                        # Add row with all price information
                        table.add_row(
                            #str(item['item_id']),
                            item['name'],
                            f"{item['price']:.2f}",  # Original price
                            item['currency'],  # Original currency
                            f"{item['price_final']:.2f}",  # Converted price in main currency
                            date_str,
                            label_names,  # Show transaction label name
                            key=str(item['item_id'])  # Use item_id as row key
                        )

                    # Sort by Date column by default (descending - newest first)
                    # Use the column key object, not the string
                    table.sort(col_date, reverse=True)

                    yield table

    def _get_project_users(self, project_id: int) -> list:
        """
        Get all users for the current project.

        Args:
            project_id: The project ID to fetch users for

        Returns:
            List of user dictionaries with user_id, first_name, last_name
        """
        try:
            dbh = self.app._config.get("dbh")
            if dbh and project_id > 0:
                users = dbh.op_project_get_users(project_id)
                return users
            return []
        except Exception as e:
            self.app.log(f"Error fetching project users: {e}")
            return []

    def _get_user_items(self, user_id: int, project_id: int) -> list:
        """
        Get items for a specific user in a project.

        Args:
            user_id: The user ID
            project_id: The project ID

        Returns:
            List of item dictionaries with name, bought_date, price_final, and currency
        """
#        try:
        dbh = self.app._config.get("dbh")
        if not dbh:
            return []

        # Get period boundaries from app_state
        period_start = self.app.app_state.get("current_period_start")
        period_end = self.app.app_state.get("current_period_end")

        # Format dates for query
        start_date_str = period_start.strftime("%Y-%m-%d") if period_start else "2000-01-01"
        end_date_str = period_end.strftime("%Y-%m-%d") if period_end else "2099-12-31"

        self.app.log(f"EditExpenseView: Fetching items for user {user_id}, project {project_id}, " +
                    f"period: {start_date_str} to {end_date_str}")

        # Query ALL items for this user in the current period (no LIMIT)
        # Filter by bought_for_id to show expenses that belong to this user
        # (their share), regardless of who physically paid (bought_by_id)
        dbh.load()
        query = f"""
            SELECT item_id, name, bought_date, price, currency, price_final, currency_final, 
                   bought_by_id, note, exchange_rate, exchange_rate_date, tags
            FROM p{dbh._db_salt}_items
            WHERE bought_for_id = ? 
            AND project_id = ?
            AND bought_date >= ?
            AND bought_date < ?
            ORDER BY bought_date DESC
        """

        results = dbh.execute_query(query, [
            user_id,
            project_id,
            start_date_str,
            end_date_str
        ])

        self.app.log(f"EditExpenseView: Found {len(results)} items for user {user_id} in period")

        # Fetch all project users once for label owner mapping
        project_users = self._get_project_users(project_id)
        user_map = {u['user_id']: u['username'] for u in project_users}
        self.app.log(f"User map for label owners: {user_map}")

        # Get all labels for the project to build label map
        labels = dbh.op_label_get_all(project_id=project_id, use_cache=True)
        label_map = {l['label_id']: l for l in labels}

        # Get ProjectComposer instance for tag parsing
        from fiwa_cli.functions.project_composer import ProjectComposer
        project_style = self.app.app_state.get("project_style", "default")

        try:
            pc = ProjectComposer.create(
                compose_type=project_style,
                dbh=dbh,
                project_id=project_id,
                users=[]
            )
        except Exception as e:
            self.app.log(f"Error creating ProjectComposer: {e}")
            pc = None

        # Build items list with parsed transactional labels
        items = []
        for row in results:
            tags_raw = row[11] if row[11] else ""

            # Use ProjectComposer to parse tags if available
            if pc:
                parsed_tags = pc.parse_tags_from_string(tags_raw, label_map=label_map)
            else:
                # Fallback: empty parsed tags
                parsed_tags = {'c': '', 't': '', 'b': '', 'm': '', 's': []}

            # Extract transaction label name
            # transaction_label_name = ""
            # if parsed_tags['transaction_id']:
            #     label_info = label_map.get(parsed_tags['transaction_id'])
            #     if label_info:
            #         transaction_label_name = label_info.get('name', f"Unknown Label {parsed_tags['transaction_id']}")
            #     else:
            #         transaction_label_name = f"Unknown Label {parsed_tags['transaction_id']}"

            items.append({
                'item_id': row[0],
                'name': row[1],
                'bought_date': row[2],
                'price': row[3],
                'currency': row[4],
                'price_final': row[5],
                'currency_final': row[6],
                'bought_by_id': row[7],
                'note': row[8],
                'exchange_rate': row[9],
                'exchange_rate_date': row[10],
                'tags': tags_raw,
                # 'parsed_tags': parsed_tags,
                'label_d': parsed_tags["m"]  # Transaction label name for display
            })

        dbh.close()
        self.app.log(f"Returning {len(items)} items with enriched label details")

        return items

        # except Exception as e:
        #     self.app.log(f"Error fetching user items: {e}")
        #     return []

    def _update_date_display(self) -> None:
        """Update the date selection display with current period."""
        try:
            period_start = self.app.app_state.get("current_period_start")
            period_end = self.app.app_state.get("current_period_end")
            period_label = self.app.app_state.get("current_period_label", "")

            if period_start and period_end:
                date_range_text = f"𝌌 {period_label}: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
            else:
                date_range_text = "𝌌 Showing all expenses"

            self.app.log(f"EditExpenseView refresh - Period: {date_range_text}")

            # Update the Static widget
            date_display = self.query_one("#date-selection-display", Static)
            date_display.update(date_range_text)

        except Exception as e:
            self.app.log(f"Error updating date display: {e}")

    def refresh_tables(self) -> None:
        """Refresh all DataTables with items for the current period."""
        try:
            # Update the date selection display
            self._update_date_display()

            project_id = self.app.app_state.get("project_id", 0)
            if project_id <= 0:
                return

            # Get all project users
            project_users = self._get_project_users(project_id)

            # Update each user's DataTable
            for user in project_users:
                table_id = f"items-table-{user['user_id']}"
                try:
                    table = self.query_one(f"#{table_id}", DataTable)

                    # Clear existing rows
                    table.clear()

                    # Fetch new items for the current period
                    items = self._get_user_items(user['user_id'], project_id)

                    # Add rows to the table
                    for item in items:
                        # Extract date only (remove time if present)
                        date_str = str(item['bought_date']).split()[0] if item['bought_date'] else ""

                        # Get transaction label name (already extracted in _get_user_items)
                        label_names = str(item["label_d"])

                        table.add_row(
                            #str(item['item_id']),
                            item['name'],
                            f"{item['price']:.2f}",  # Original price
                            item['currency'],  # Original currency
                            f"{item['price_final']:.2f}",  # Converted price in main currency
                            date_str,
                            label_names,
                            key=str(item['item_id'])
                        )

                    # Sort by Date column by default (descending - newest first)
                    # Get the last column key (Date column is the 6th column, index 5)
                    if table.columns:
                        date_column_key = list(table.columns.keys())[5]  # Date is the 6th column (index 5)
                        table.sort(date_column_key, reverse=True)

                    self.app.log(f"Refreshed table for user {user['user_id']}: {len(items)} items")

                except Exception as e:
                    self.app.log(f"Could not refresh table for user {user['user_id']}: {e}")

        except Exception as e:
            self.app.log(f"Error refreshing data tables: {e}")

    @on(DataTable.HeaderSelected)
    def on_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle column header click to sort the table."""
        table = event.data_table

        # Sort by the clicked column
        # The sort method will automatically toggle between ascending/descending
        table.sort(event.column_key)

        self.app.log(f"Sorted table by column: {event.column_key}")

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle double-click on a row to edit the item."""
        # Get the item_id from the row key
        item_id = int(event.row_key.value)
        self.app.log(f"Row selected with item_id: {item_id}")

        # Use run_worker to properly handle push_screen_wait
        self.run_worker(self._handle_edit_item(item_id))

    async def _handle_edit_item(self, item_id: int) -> None:
        """Handle editing an item in a worker context."""
        try:
            # Fetch the full item data
            item_data = self._get_item_by_id(item_id)
            if not item_data:
                self.app.notify(f"Could not fetch item {item_id}", severity="error")
                return

            # Open ItemInputForm in edit mode
            result = await self.app.push_screen_wait(
                ItemInputForm(edit_mode=True, item_data=item_data)
            )

            # Handle the result
            if result == "deleted":
                # Item was deleted
                self.app.log(f"Item {item_id} was deleted")
                self.refresh_tables()
                # Success notification already shown in ItemInputForm
            elif result:
                # Item was updated (result is the item_id)
                self.app.log(f"Item {item_id} was updated")
                self.refresh_tables()
                # Success notification already shown in ItemInputForm

        except Exception as e:
            self.app.log(f"Error handling row selection: {e}")
            self.app.notify(f"Error: {str(e)}", severity="error")

    def _get_item_by_id(self, item_id: int) -> dict:
        """Get a single item by its ID with all details."""
        try:
            dbh = self.app._config.get("dbh")
            if not dbh:
                return None

            project_id = self.app.app_state.get("project_id", 0)

            dbh.load()
            query = f"""
                SELECT item_id, item_uuid, name, note, price, price_final, currency, currency_final,
                       bought_date, bought_by_id, bought_for_id, added_by_id, project_id,
                       exchange_rate, exchange_rate_date, tags
                FROM p{dbh._db_salt}_items
                WHERE item_id = ? AND project_id = ?
            """

            results = dbh.execute_query(query, [item_id, project_id])
            dbh.close()

            if not results:
                return None

            row = results[0]
            return {
                'item_id': row[0],
                'item_uuid': row[1],
                'name': row[2],
                'note': row[3],
                'price': row[4],
                'price_final': row[5],
                'currency': row[6],
                'currency_final': row[7],
                'bought_date': row[8],
                'bought_by_id': row[9],
                'bought_for_id': row[10],
                'added_by_id': row[11],
                'project_id': row[12],
                'exchange_rate': row[13],
                'exchange_rate_date': row[14],
                'tags': row[15]
            }

        except Exception as e:
            self.app.log(f"Error fetching item {item_id}: {e}")
            return None

