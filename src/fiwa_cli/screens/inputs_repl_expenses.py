"""Replicate Expenses View - Replicate fixed costs to the next month."""
from textual.containers import Vertical, ScrollableContainer, Horizontal
from textual.widgets import Static, TabbedContent, TabPane, DataTable, Button, Checkbox
from textual.app import ComposeResult
from textual import on
from fiwa_cli.functions.loader import load_dynamic_css
import datetime
import uuid


class ReplicateExpensesView(Vertical):
    """View for replicating fixed expenses to the next month.

    Shows fixed costs for the selected month in a tab-based view (one tab per user).
    Users can update dates to next month and write replicated items to database.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._updated_items = {}  # Store updated items per user: {user_id: [items]}
        self._selected_items = {}  # Store selected items per user: {user_id: {item_id: bool}}

    def compose(self) -> ComposeResult:
        """Compose the replicate expenses interface."""
        yield Static("Replicate Fixed Expenses", classes="replicate-title")

        # Display current month selection
        period_start = self.app.app_state.get("current_period_start")
        period_end = self.app.app_state.get("current_period_end")
        period_label = self.app.app_state.get("current_period_label", "")
        period_type = self.app.app_state.get("current_period_type", "week")

        # Only work with monthly data
        if period_type != "month":
            yield Static(
                "⚠ Please select 'Month' in the period picker to use the replication feature.",
                classes="warning-message"
            )
            return

        if period_start and period_end:
            date_range_text = f"📅 Replicating from: {period_label}"
        else:
            date_range_text = "📅 No period selected"

        yield Static(date_range_text, id="replicate-date-display", classes="date-info")

        # Get project and users
        project_id = self.app.app_state.get("project_id", 0)
        project_users = self._get_project_users(project_id)
        currency_main = self.app.app_state.get("current_project_currency_main", "USD")

        # Wrap in ScrollableContainer
        with ScrollableContainer(id="replicate-content"):
            # Create tabbed content with one tab per user
            with TabbedContent():
                for user in project_users:
                    # Check Read permission
                    user_permission = user.get("project_perm_model", "000000")
                    if not user_permission or len(user_permission) < 6:
                        continue
                    if user_permission[0] != '1':
                        self.app.log(f"Skipping user {user['username']} - no Read permission")
                        continue

                    with TabPane(f"{user['first_name']} {user['last_name']}",
                                id=f"tab-user-{user['user_id']}"):
                        # Fetch fixed items for this user
                        items = self._get_fixed_items(user['user_id'], project_id)

                        # Initialize selected items for this user
                        if user['user_id'] not in self._selected_items:
                            self._selected_items[user['user_id']] = {}

                        # Create DataTable
                        table = DataTable(id=f"replicate-table-{user['user_id']}")

                        # Add columns
                        table.add_column("Select")
                        table.add_column("Item Name", width=20)
                        col_cost = table.add_column("Cost")
                        table.add_column("Trans. Label")
                        table.add_column("Account")
                        table.add_column("Main Label")
                        col_date = table.add_column("Date")
                        table.add_column("Status")

                        table.cursor_type = "row"

                        # Add rows for fixed items
                        for item in items:
                            date_str = str(item['bought_date']).split()[0] if item['bought_date'] else ""

                            # Mark item as selected by default (since we show fixed items)
                            self._selected_items[user['user_id']][item['item_id']] = True

                            table.add_row(
                                "✓",  # Selected by default
                                item['name'],
                                f"{item['price_final']:.2f} {currency_main}",
                                item.get('label_t', ''),
                                item.get('label_b', ''),
                                item.get('label_m', ''),
                                date_str,
                                "Original",
                                key=f"orig-{item['item_id']}"
                            )

                        yield table

                        # Action buttons
                        with Horizontal(classes="action-buttons"):
                            yield Button("Update to Next Month",
                                       id=f"update-month-{user['user_id']}",
                                       variant="primary")
                            yield Button("Write to Database",
                                       id=f"write-db-{user['user_id']}",
                                       variant="success")

    def on_mount(self) -> None:
        """Load CSS when component is mounted."""
        load_dynamic_css(self, "screens_inputs_repl_expenses.tcss")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id and event.button.id.startswith("update-month-"):
            user_id = int(event.button.id.replace("update-month-", ""))
            self._update_to_next_month(user_id)
        elif event.button.id and event.button.id.startswith("write-db-"):
            user_id = int(event.button.id.replace("write-db-", ""))
            self._write_to_database(user_id)

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection to toggle item selection."""
        table = event.data_table
        row_key = event.row_key.value

        # Extract user_id from table ID
        table_id = str(table.id)
        if table_id.startswith("replicate-table-"):
            user_id = int(table_id.replace("replicate-table-", ""))

            # Extract item_id from row key (only toggle original items)
            if row_key.startswith("orig-"):
                item_id = int(row_key.split("-")[1])

                # Toggle selection
                current = self._selected_items.get(user_id, {}).get(item_id, False)
                self._selected_items[user_id][item_id] = not current

                # Get the Select column key (first column)
                select_col_key = list(table.columns.keys())[0]

                # Update display
                if self._selected_items[user_id][item_id]:
                    table.update_cell(row_key, select_col_key, "✓")
                else:
                    table.update_cell(row_key, select_col_key, "")

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

    def _get_fixed_items(self, user_id: int, project_id: int) -> list:
        """Get fixed items for a specific user in the selected month.

        Args:
            user_id: The user ID
            project_id: The project ID

        Returns:
            List of fixed items with parsed labels
        """
        try:
            dbh = self.app._config.get("dbh")
            if not dbh:
                return []

            # Get period boundaries from app_state (should be month)
            period_start = self.app.app_state.get("current_period_start")
            period_end = self.app.app_state.get("current_period_end")

            # Format dates for query
            start_date_str = period_start.strftime("%Y-%m-%d") if period_start else "2000-01-01"
            end_date_str = period_end.strftime("%Y-%m-%d") if period_end else "2099-12-31"

            # Query fixed items only
            dbh.load()
            query = f"""
                SELECT 
                    i.item_id, 
                    i.item_uuid,
                    i.name, 
                    i.bought_date, 
                    i.price, 
                    i.currency, 
                    i.price_final,
                    i.currency_final, 
                    i.bought_by_id,
                    i.bought_for_id,
                    i.added_by_id,
                    i.note, 
                    i.exchange_rate, 
                    i.exchange_rate_date, 
                    i.tags
                FROM p{dbh._db_salt}_items i
                WHERE i.bought_for_id = ? 
                    AND i.project_id = ?
                    AND i.bought_date >= ?
                    AND i.bought_date < ?
                ORDER BY i.bought_date ASC
            """

            results = dbh.execute_query(query, [user_id, project_id, start_date_str, end_date_str])
            dbh.close()

            # Get all labels for parsing
            labels = dbh.op_label_get_all(project_id=project_id, use_cache=True)
            label_map = {l['label_id']: l for l in labels}

            # Get ProjectComposer for parsing
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

            # Parse items and filter to only fixed
            items = []
            for row in results:
                tags_raw = row[14] if row[14] else ""

                # Remove quotes if present
                if tags_raw.startswith('"') and tags_raw.endswith('"'):
                    tags_raw = tags_raw[1:-1]

                # Parse tags
                if pc:
                    parsed_tags = pc.parse_tags_from_string(tags_raw, label_map=label_map)
                else:
                    parsed_tags = {'c': '', 't': '', 'b': '', 'm': '', 's': []}

                # Only include items with transaction type "fixed"
                if parsed_tags.get('t', '') == 'fixed':
                    items.append({
                        'item_id': row[0],
                        'item_uuid': row[1],
                        'name': row[2],
                        'bought_date': row[3],
                        'price': row[4],
                        'currency': row[5],
                        'price_final': row[6],
                        'currency_final': row[7],
                        'bought_by_id': row[8],
                        'bought_for_id': row[9],
                        'added_by_id': row[10],
                        'note': row[11],
                        'exchange_rate': row[12],
                        'exchange_rate_date': row[13],
                        'tags': tags_raw,
                        'parsed_tags': parsed_tags,
                        'label_t': parsed_tags.get('t', ''),
                        'label_b': parsed_tags.get('b', ''),
                        'label_m': parsed_tags.get('m', '')
                    })

            self.app.log(f"Found {len(items)} fixed items for user {user_id}")
            return items

        except Exception as e:
            self.app.log(f"Error fetching fixed items: {e}")
            return []

    def _check_existing_items_in_month(
        self,
        user_id: int,
        project_id: int,
        year: int,
        month: int,
        selected_items: list,
        dbh,
    ) -> list:
        """Check if any selected items already exist in the target month.

        We compare by: name, bought_by_id, bought_for_id, price_final, currency_final, tags, and target date.
        Returns a list of items that would be duplicates.
        """
        try:
            import calendar

            # Compute month boundaries
            month_start = datetime.date(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            month_end = datetime.date(year, month, last_day)

            # Fetch existing items for the target month
            dbh.load()
            query = f"""
                SELECT name, bought_by_id, bought_for_id, price_final, currency_final, tags, bought_date
                FROM p{dbh._db_salt}_items
                WHERE project_id = ?
                AND bought_for_id = ?
                AND bought_date BETWEEN ? AND ?
            """
            results = dbh.execute_query(query, [project_id, user_id, month_start, month_end])
            dbh.close()

            # Build a set of existing item keys
            existing_keys = set()
            for row in results:
                name, bought_by_id, bought_for_id, price_final, currency_final, tags, bought_date = row
                date_str = str(bought_date).split()[0]
                key = (name, bought_by_id, bought_for_id, float(price_final), currency_final, tags, date_str)
                existing_keys.add(key)

            # Build duplicate list
            duplicates = []
            for item in selected_items:
                # Compute target date in next month
                original_date = datetime.datetime.strptime(
                    str(item['bought_date']).split()[0],
                    "%Y-%m-%d"
                ).date()
                try:
                    target_date = original_date.replace(year=year, month=month)
                except ValueError:
                    target_date = original_date.replace(
                        year=year,
                        month=month,
                        day=min(original_date.day, last_day)
                    )

                key = (
                    item['name'],
                    item['bought_by_id'],
                    item['bought_for_id'],
                    float(item['price_final']),
                    item['currency_final'],
                    item['tags'],
                    target_date.strftime("%Y-%m-%d"),
                )
                if key in existing_keys:
                    duplicates.append(item)

            return duplicates

        except Exception as e:
            self.app.log(f"Error checking duplicates for replication: {e}")
            return []

    def _update_to_next_month(self, user_id: int) -> None:
        """Update the selected fixed items to next month and display in table."""
        try:
            # Get the current month's period
            period_start = self.app.app_state.get("current_period_start")
            if not period_start:
                self.app.notify("No period selected", severity="error")
                return

            # Calculate next month
            current_year = period_start.year
            current_month = period_start.month

            if current_month == 12:
                next_month = 1
                next_year = current_year + 1
            else:
                next_month = current_month + 1
                next_year = current_year

            # Get the table
            table = self.query_one(f"#replicate-table-{user_id}", DataTable)

            # Get current fixed items
            project_id = self.app.app_state.get("project_id", 0)
            items = self._get_fixed_items(user_id, project_id)

            # Filter to only selected items
            selected_items = [
                item for item in items
                if self._selected_items.get(user_id, {}).get(item['item_id'], False)
            ]

            if not selected_items:
                self.app.notify("No items selected for replication", severity="warning")
                return

            # Check if items already exist in next month
            dbh = self.app._config.get("dbh")
            existing_duplicates = self._check_existing_items_in_month(
                user_id, project_id, next_year, next_month, selected_items, dbh
            )

            if existing_duplicates:
                # Show warning with duplicate items
                duplicate_names = [item['name'] for item in existing_duplicates[:5]]
                if len(existing_duplicates) > 5:
                    duplicate_names.append(f"... and {len(existing_duplicates) - 5} more")

                self.app.notify(
                    f"⚠ Warning: {len(existing_duplicates)} items already exist in {next_year}-{next_month:02d}!\n" +
                    f"Items: {', '.join(duplicate_names)}",
                    severity="error",
                    timeout=8
                )
                self.app.log(f"Blocked replication: {len(existing_duplicates)} duplicates found in target month")
                return

            # Clear previous updated items for this user
            self._updated_items[user_id] = []

            # Remove previous "new" rows from table
            rows_to_remove = [key for key in table.rows.keys() if str(key.value).startswith("new-")]
            for row_key in rows_to_remove:
                table.remove_row(row_key)

            # Add new rows to table for next month items
            for item in selected_items:
                # Parse original date
                original_date = datetime.datetime.strptime(
                    str(item['bought_date']).split()[0],
                    "%Y-%m-%d"
                ).date()

                # Calculate new date (same day, next month)
                try:
                    new_date = original_date.replace(year=next_year, month=next_month)
                except ValueError:
                    # Handle day overflow (e.g., Jan 31 -> Feb 28)
                    import calendar
                    last_day = calendar.monthrange(next_year, next_month)[1]
                    new_date = original_date.replace(
                        year=next_year,
                        month=next_month,
                        day=min(original_date.day, last_day)
                    )

                # Create updated item data
                updated_item = {
                    **item,
                    'item_uuid': str(uuid.uuid4()),  # New UUID
                    'bought_date': new_date.strftime("%Y-%m-%d"),
                    'exchange_rate_date': new_date.strftime("%Y-%m-%d"),
                    'original_item_id': item['item_id']
                }

                self._updated_items[user_id].append(updated_item)

                # Add to table with different styling
                table.add_row(
                    "✓",
                    item['name'],
                    f"{item['price_final']:.2f} {item['currency_final']}",
                    item.get('label_t', ''),
                    item.get('label_b', ''),
                    item.get('label_m', ''),
                    new_date.strftime("%Y-%m-%d"),
                    "Updated",
                    key=f"new-{item['item_id']}"
                )

            self.app.notify(
                f"Updated {len(selected_items)} items to {next_year}-{next_month:02d}",
                severity="information"
            )
            self.app.log(f"Updated {len(selected_items)} items for user {user_id} to next month")

        except Exception as e:
            self.app.log(f"Error updating to next month: {e}")
            self.app.notify(f"Error: {str(e)}", severity="error")

    def _write_to_database(self, user_id: int) -> None:
        """Write the updated items to the database."""
        try:
            # Get updated items for this user
            updated_items = self._updated_items.get(user_id, [])

            if not updated_items:
                self.app.notify("No updated items to write. Click 'Update to Next Month' first.",
                              severity="warning")
                return

            # Get database handler
            dbh = self.app._config.get("dbh")
            if not dbh:
                self.app.notify("Database connection not available", severity="error")
                return

            # Write each item to database
            created_count = 0
            for item in updated_items:
                # Prepare item data for op_item_create
                item_data = {
                    'item_uuid': item['item_uuid'],
                    'name': item['name'],
                    'note': item.get('note', ''),
                    'price': item['price'],
                    'price_final': item['price_final'],
                    'currency': item['currency'],
                    'currency_final': item['currency_final'],
                    'bought_date': item['bought_date'],
                    'bought_by_id': item['bought_by_id'],
                    'bought_for_id': item['bought_for_id'],
                    'added_by_id': self.app.app_state.get("user_id", item['added_by_id']),
                    'project_id': self.app.app_state.get("project_id", 0),
                    'exchange_rate': item['exchange_rate'],
                    'exchange_rate_date': item['exchange_rate_date'],
                    'tags': item['tags']
                }

                # Create item in database
                item_id = dbh.op_item_create(item_data)

                if item_id:
                    created_count += 1
                    self.app.log(f"Created replicated item with ID: {item_id}")

            # Clear updated items after writing
            self._updated_items[user_id] = []

            # Remove "Updated" rows from table
            table = self.query_one(f"#replicate-table-{user_id}", DataTable)
            rows_to_remove = [key for key in table.rows.keys() if str(key.value).startswith("new-")]
            for row_key in rows_to_remove:
                table.remove_row(row_key)

            self.app.notify(
                f"✓ Successfully wrote {created_count} items to database!",
                severity="success"
            )

        except Exception as e:
            self.app.log(f"Error writing to database: {e}")
            self.app.notify(f"Error: {str(e)}", severity="error")

    @on(DataTable.HeaderSelected)
    def on_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle column header click to sort the table."""
        table = event.data_table
        table.sort(event.column_key)
        self.app.log(f"Sorted table by column: {event.column_key}")

    def refresh_data(self) -> None:
        """Refresh the view when period changes."""
        try:
            # Get period type
            period_type = self.app.app_state.get("current_period_type", "week")

            # Only works with monthly view
            if period_type != "month":
                self.app.notify("Please switch to monthly view for replication", severity="info")
                return

            # Get project users and refresh each table
            project_id = self.app.app_state.get("project_id", 0)
            project_users = self._get_project_users(project_id)
            currency_main = self.app.app_state.get("current_project_currency_main", "USD")

            for user in project_users:
                # Check permission
                user_permission = user.get("project_perm_model", "000000")
                if not user_permission or len(user_permission) < 6:
                    continue
                if user_permission[0] != '1':
                    continue

                # Try to find and refresh table
                try:
                    table = self.query_one(f"#replicate-table-{user['user_id']}", DataTable)
                    table.clear()

                    # Fetch fixed items
                    items = self._get_fixed_items(user['user_id'], project_id)

                    # Re-add rows
                    for item in items:
                        date_str = str(item['bought_date']).split()[0] if item['bought_date'] else ""

                        table.add_row(
                            "✓",
                            item['name'],
                            f"{item['price_final']:.2f} {currency_main}",
                            item.get('label_t', ''),
                            item.get('label_b', ''),
                            item.get('label_m', ''),
                            date_str,
                            "Original",
                            key=f"orig-{item['item_id']}"
                        )

                    # Clear updated items for this user
                    if user['user_id'] in self._updated_items:
                        self._updated_items[user['user_id']] = []

                except Exception as e:
                    self.app.log(f"Could not refresh table for user {user['user_id']}: {e}")

        except Exception as e:
            self.app.log(f"Error refreshing replicate view: {e}")
