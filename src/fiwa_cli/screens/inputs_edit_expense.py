"""Edit Expense View - Tabbed interface showing items per user."""
from textual.containers import VerticalScroll, Vertical
from textual.widgets import Static, TabbedContent, TabPane, DataTable
from textual.app import ComposeResult
from textual import on
from fiwa_cli.components.item_input_form import ItemInputForm

from fiwa_cli.functions.loader import load_dynamic_css
import json

class EditExpenseView(VerticalScroll):
    """View for editing expenses with tabs per user showing their items."""

    # DEFAULT_CSS = """
    #
    # """

    def __init__(self, *args, **kwargs):
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
            date_range_text = f"📅 {period_label}: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
        else:
            date_range_text = "📅 Showing all expenses"

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
            AND bought_date BETWEEN ? AND ?
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
                date_range_text = f"📅 {period_label}: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
            else:
                date_range_text = "📅 Showing all expenses"

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

