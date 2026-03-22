"""Basic Report Form - Cost Overview with per-user expense tables."""
from textual.containers import Vertical, ScrollableContainer, Horizontal
from textual.widgets import Static, TabbedContent, TabPane, DataTable, Button
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual import on
from fiwa_cli.functions.loader import load_dynamic_css


class RepayModal(ModalScreen):
    """Modal screen showing repayment calculations between users."""
    
    BINDINGS = [
        ("escape", "dismiss_modal", "Close"),
    ]
    
    def __init__(self, project_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_id = project_id
        
    def compose(self) -> ComposeResult:
        """Compose the repayment modal interface."""
        with Vertical(id="repay-modal-container"):
            yield Static("💸 Repay Overview", classes="modal-title")

            # Show current period
            period_start = self.app.app_state.get("current_period_start")
            period_end = self.app.app_state.get("current_period_end")

            if period_start and period_end:
                period_text = f"Period: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
            else:
                period_text = "All time"

            yield Static(period_text, classes="modal-period")
            yield Static("Who owes whom:", classes="modal-subtitle")
            
            with ScrollableContainer(id="repay-list-container"):
                # Calculate and display repayments
                repayments = self._calculate_repayments()
                
                if repayments:
                    for repayment in repayments:
                        debtor = repayment['debtor']
                        creditor = repayment['creditor']
                        amount = repayment['amount']
                        currency = repayment['currency']
                        
                        yield Static(
                            f"💰 {debtor} owes {creditor}: {amount:.2f} {currency}",
                            classes="repayment-item"
                        )
                else:
                    yield Static("✅ All settled! No repayments needed.", 
                               classes="repayment-settled")
            
            yield Button("OK", id="ok-button", variant="primary")
    
    def _calculate_repayments(self) -> list:
        """Calculate who owes whom based on bought_by vs bought_for.
        
        Logic:
        - If User A bought an item for User B, then B owes A
        - We aggregate all transactions to calculate net debts
        
        Returns:
            List of dicts with debtor, creditor, amount, currency
        """
        try:
            dbh = self.app._config.get("dbh")
            if not dbh:
                return []
            
            # Get period boundaries from app_state
            period_start = self.app.app_state.get("current_period_start")
            period_end = self.app.app_state.get("current_period_end")
            currency_main = self.app.app_state.get("current_project_currency_main", "USD")
            
            # Format dates for query
            start_date_str = period_start.strftime("%Y-%m-%d") if period_start else "2000-01-01"
            end_date_str = period_end.strftime("%Y-%m-%d") if period_end else "2099-12-31"

            self.app.log(f"Calculating repayments for period: {start_date_str} to {end_date_str}")

            # Query all items where bought_by != bought_for
            # This means someone bought something for someone else
            dbh.load()
            query = f"""
                SELECT bought_by_id, bought_for_id, price_final
                FROM p{dbh._db_salt}_items
                WHERE project_id = ?
                AND bought_date BETWEEN ? AND ?
                AND bought_by_id != bought_for_id
                ORDER BY bought_date DESC
            """
            
            results = dbh.execute_query(query, [
                self.project_id,
                start_date_str,
                end_date_str
            ])
            
            # Get user names for IDs
            users_query = f"""
                SELECT user_id, first_name, last_name
                FROM p{dbh._db_salt}_users
            """
            user_results = dbh.execute_query(users_query, [])

            # Create user ID to name mapping
            user_names = {}
            for row in user_results:
                user_id = row[0]
                full_name = f"{row[1]} {row[2]}"
                user_names[user_id] = full_name
            
            self.app.log(f"Loaded {len(user_names)} users for repayment calculation")
            self.app.log(f"Found {len(results)} cross-user transactions")

            dbh.close()

            # Calculate net debts between users
            # debt_matrix[debtor][creditor] = amount
            debt_matrix = {}
            
            for row in results:
                bought_by_id = row[0]  # Who paid
                bought_for_id = row[1]  # Who benefited
                amount = row[2]  # Amount in main currency
                
                # bought_for_id owes bought_by_id
                if bought_for_id not in debt_matrix:
                    debt_matrix[bought_for_id] = {}
                
                if bought_by_id not in debt_matrix[bought_for_id]:
                    debt_matrix[bought_for_id][bought_by_id] = 0.0
                
                debt_matrix[bought_for_id][bought_by_id] += amount
            
            # Simplify debts (net out mutual debts)
            simplified_debts = []
            processed_pairs = set()
            
            for debtor_id in debt_matrix:
                for creditor_id in debt_matrix[debtor_id]:
                    pair = tuple(sorted([debtor_id, creditor_id]))
                    
                    if pair in processed_pairs:
                        continue
                    
                    processed_pairs.add(pair)
                    
                    # Amount debtor owes creditor
                    debt_to_creditor = debt_matrix.get(debtor_id, {}).get(creditor_id, 0.0)
                    # Amount creditor owes debtor (reverse)
                    debt_to_debtor = debt_matrix.get(creditor_id, {}).get(debtor_id, 0.0)
                    
                    # Net debt
                    net_debt = debt_to_creditor - debt_to_debtor
                    
                    if abs(net_debt) > 0.01:  # Ignore very small amounts
                        if net_debt > 0:
                            # debtor owes creditor
                            simplified_debts.append({
                                'debtor': user_names.get(debtor_id, f"User {debtor_id}"),
                                'creditor': user_names.get(creditor_id, f"User {creditor_id}"),
                                'amount': net_debt,
                                'currency': currency_main
                            })
                        else:
                            # creditor owes debtor
                            simplified_debts.append({
                                'debtor': user_names.get(creditor_id, f"User {creditor_id}"),
                                'creditor': user_names.get(debtor_id, f"User {debtor_id}"),
                                'amount': abs(net_debt),
                                'currency': currency_main
                            })
            
            # Sort by amount descending
            simplified_debts.sort(key=lambda x: x['amount'], reverse=True)
            
            return simplified_debts
            
        except Exception as e:
            self.app.log(f"Error calculating repayments: {e}")
            self.app.notify(f"Error calculating repayments: {str(e)}", severity="error")
            return []
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "ok-button":
            self.dismiss()
    
    def action_dismiss_modal(self) -> None:
        """Handle escape key press."""
        self.dismiss()


class BasicReportForm(Vertical):
    """Cost Overview report showing expenses per user in tabbed format."""

    def compose(self) -> ComposeResult:
        """Compose the Cost Overview report interface."""
        yield Static("Cost Overview", classes="report-title")

        # Display current date selection
        period_start = self.app.app_state.get("current_period_start")
        period_end = self.app.app_state.get("current_period_end")
        period_label = self.app.app_state.get("current_period_label", "")
        period_type = self.app.app_state.get("current_period_type", "week")

        if period_start and period_end:
            date_range_text = f"📅 {period_label}: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
        else:
            date_range_text = "📅 All expenses"

        self.app.log(f"BasicReportForm compose - Period: {date_range_text}")
        yield Static(date_range_text, id="date-selection-display", classes="date-info")

        # Get project and users
        project_id = self.app.app_state.get("project_id", 0)
        project_users = self._get_project_users(project_id)

        # Get main currency for column header
        currency_main = self.app.app_state.get("current_project_currency_main", "USD")
        project_style = self.app.app_state.get("project_style", "default")

        # Get ProjectComposer instance
        dbh = self.app._config.get("dbh")
        from fiwa_cli.functions.project_composer import ProjectComposer

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

        # Wrap in ScrollableContainer for scrolling
        with ScrollableContainer(id="report-content"):
            # Create tabbed content with one tab per user
            with TabbedContent():
                for user in project_users:
                    # Check if user has at least Read permission
                    user_permission = user.get("project_perm_model", "000000")

                    if user_permission[0] != '1' or len(user_permission) < 6:
                        self.app.log(f"Skipping user {user.get('username')} - no Read permission")
                        continue

                    with TabPane(f"{user['first_name']} {user['last_name']}", id=f"tab-user-{user['user_id']}"):
                        # Fetch items for this user
                        items = self._get_user_items(user['user_id'], project_id)

                        # Apply transformations using ProjectComposer
                        if pc:
                            items = pc.get_balance_split(items)
                            items_fv = pc.get_transaction_split(items, keys=["fixed", "variable"])
                            items_daily = pc.get_transaction_split(items, keys=["daily"])
                        else:
                            items_fv = items
                            items_daily = []

                        # --- Table 1: Fixed/Variable Items ---
                        yield Static("Fixed & Variable Transactions", classes="table-section-title")
                        table_fv = DataTable(id=f"items-table-fv-{user['user_id']}")

                        table_fv.add_column("Name", width=20)
                        table_fv.add_column("Price")
                        table_fv.add_column("Curr")
                        col_final_fv = table_fv.add_column(f"Final [{currency_main}]")
                        col_date_fv = table_fv.add_column("Date")
                        table_fv.add_column("Bought by")
                        table_fv.add_column("Label")
                        table_fv.cursor_type = "row"

                        # Track totals for fixed/variable
                        total_fv = 0.0
                        revenue_fv = 0.0
                        expenses_fv = 0.0
                        bought_by_self_fv = 0.0
                        bought_by_others_fv = {}

                        for item in items_fv:
                            date_str = str(item['bought_date']).split()[0] if item['bought_date'] else ""
                            label_display = item.get('label_m', '')
                            multiplier = item.get('multiplier', 1)

                            table_fv.add_row(
                                item['name'],
                                f"{item['price']:.2f}",
                                item['currency'],
                                f"{item['price_final']:.2f}",
                                date_str,
                                f"{item['bought_by_last_name']}",
                                label_display,
                                key=f"fv-{item['item_id']}"
                            )

                            amount = item['price_final'] * multiplier
                            total_fv += amount

                            if multiplier == 1:
                                revenue_fv += item['price_final']
                            else:
                                expenses_fv += item['price_final']

                            if item['bought_by_id'] == user['user_id']:
                                bought_by_self_fv += item['price_final']
                            else:
                                buyer_name = f"{item['bought_by_first_name']} {item['bought_by_last_name']}"
                                bought_by_others_fv[buyer_name] = bought_by_others_fv.get(buyer_name, 0.0) + item['price_final']

                        table_fv.sort(col_date_fv, reverse=True)
                        yield table_fv
                        yield Static(f"Total Fixed/Variable: {total_fv:.2f} {currency_main}",
                                   classes="subtotal", id=f"total-fv-{user['user_id']}")

                        # --- Table 2: Daily Items ---
                        yield Static("Daily Transactions", classes="table-section-title")
                        table_daily = DataTable(id=f"items-table-daily-{user['user_id']}")

                        table_daily.add_column("Name", width=20)
                        table_daily.add_column("Price")
                        table_daily.add_column("Curr")
                        col_final_daily = table_daily.add_column(f"Final [{currency_main}]")
                        col_date_daily = table_daily.add_column("Date")
                        table_daily.add_column("Bought by")
                        table_daily.add_column("Label")
                        table_daily.cursor_type = "row"

                        total_daily = 0.0
                        revenue_daily = 0.0
                        expenses_daily = 0.0
                        bought_by_self_daily = 0.0
                        bought_by_others_daily = {}

                        for item in items_daily:
                            date_str = str(item['bought_date']).split()[0] if item['bought_date'] else ""
                            label_display = item.get('label_m', '')
                            multiplier = item.get('multiplier', 1)

                            table_daily.add_row(
                                item['name'],
                                f"{item['price']:.2f}",
                                item['currency'],
                                f"{item['price_final']:.2f}",
                                date_str,
                                f"{item['bought_by_last_name']}",
                                label_display,
                                key=f"daily-{item['item_id']}"
                            )

                            amount = item['price_final'] * multiplier
                            total_daily += amount

                            if multiplier == 1:
                                revenue_daily += item['price_final']
                            else:
                                expenses_daily += item['price_final']

                            if item['bought_by_id'] == user['user_id']:
                                bought_by_self_daily += item['price_final']
                            else:
                                buyer_name = f"{item['bought_by_first_name']} {item['bought_by_last_name']}"
                                bought_by_others_daily[buyer_name] = bought_by_others_daily.get(buyer_name, 0.0) + item['price_final']

                        table_daily.sort(col_date_daily, reverse=True)
                        yield table_daily
                        yield Static(f"Total Daily: {total_daily:.2f} {currency_main}",
                                   classes="subtotal", id=f"total-daily-{user['user_id']}")

                        # --- Combined Summary ---
                        total_all = total_fv + total_daily
                        total_revenue = revenue_fv + revenue_daily
                        total_expenses = expenses_fv + expenses_daily

                        breakdown_lines = [f"💰 Grand Total: {total_all:.2f} {currency_main}"]

                        # Show revenue/expense breakdown for monthly view
                        if period_type == "month":
                            breakdown_lines.append(f"  ↗ Revenue: {total_revenue:.2f} {currency_main}")
                            breakdown_lines.append(f"  ↘ Expenses: {total_expenses:.2f} {currency_main}")
                            breakdown_lines.append(f"  = Balance: {total_all:.2f} {currency_main}")

                        # Show who bought what breakdown
                        total_self = bought_by_self_fv + bought_by_self_daily
                        if total_self > 0:
                            breakdown_lines.append(f"  • Self: {total_self:.2f} {currency_main}")

                        # Merge bought_by_others from both tables
                        all_bought_by_others = {}
                        for buyer, amount in bought_by_others_fv.items():
                            all_bought_by_others[buyer] = all_bought_by_others.get(buyer, 0.0) + amount
                        for buyer, amount in bought_by_others_daily.items():
                            all_bought_by_others[buyer] = all_bought_by_others.get(buyer, 0.0) + amount

                        if all_bought_by_others:
                            for buyer, amount in sorted(all_bought_by_others.items(), key=lambda x: x[1], reverse=True):
                                breakdown_lines.append(f"  • From {buyer}: {amount:.2f} {currency_main}")

                        yield Static("\n".join(breakdown_lines),
                                   classes="user-total",
                                   id=f"total-user-{user['user_id']}")

            # Repay button INSIDE ScrollableContainer but OUTSIDE TabbedContent
            yield Button("Repay", id="repay-button", classes="repay-button")

    def on_mount(self) -> None:
        """Load CSS when component is mounted."""

        load_dynamic_css(self, "screens_reports_basic.tcss")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "repay-button":
            # Open repayment modal for the current project
            project_id = self.app.app_state.get("project_id", 0)
            self.app.push_screen(RepayModal(project_id))

    @on(DataTable.HeaderSelected)
    def on_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle column header click to sort the table."""
        table = event.data_table

        # Sort by the clicked column
        # The sort method will automatically toggle between ascending/descending
        table.sort(event.column_key)

        self.app.log(f"Sorted table by column: {event.column_key}")

    def _get_project_users(self, project_id: int) -> list:
        """Get all users for the current project.

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
        """Get items for a specific user in the current project and date range.

        Args:
            user_id: The user ID to fetch items for
            project_id: The project ID

        Returns:
            List of item dictionaries with name, bought_date, price_final, and currency
        """
        try:
            dbh = self.app._config.get("dbh")
            if not dbh:
                return []

            # Get period boundaries from app_state
            period_start = self.app.app_state.get("current_period_start")
            period_end = self.app.app_state.get("current_period_end")

            # Format dates for query
            start_date_str = period_start.strftime("%Y-%m-%d") if period_start else "2000-01-01"
            end_date_str = period_end.strftime("%Y-%m-%d") if period_end else "2099-12-31"

            self.app.log(f"Fetching items for user {user_id}, project {project_id}, " +
                        f"period: {start_date_str} to {end_date_str}")

            # Query ALL items for this user in the current period
            # Filter by bought_for_id to show expenses that belong to this user
            dbh.load()
            query = f"""
                SELECT 
                    i.item_id, 
                    i.name, 
                    i.bought_date, 
                    i.price, 
                    i.currency, 
                    i.price_final,
                    i.currency_final, 
                    i.bought_by_id, 
                    u.username as bought_by_username,
                    u.first_name as bought_by_first_name,
                    u.last_name as bought_by_last_name,
                    i.note, 
                    i.exchange_rate, 
                    i.exchange_rate_date, 
                    i.tags
                FROM p{dbh._db_salt}_items i
                LEFT JOIN p{dbh._db_salt}_users u ON i.bought_by_id = u.user_id
                WHERE i.bought_for_id = ? 
                    AND i.project_id = ?
                    AND i.bought_date >= ?
                    AND i.bought_date < ?
                ORDER BY i.bought_date DESC
            """

            results = dbh.execute_query(query, [
                user_id,
                project_id,
                start_date_str,
                end_date_str
            ])
            dbh.close()

            self.app.log(f"Found {len(results)} items for user {user_id} in period {start_date_str} to {end_date_str}")

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

            items = []
            for row in results:
                tags_raw = row[14] if row[14] else ""

                # if row starts with or ends ", remove it:
                if tags_raw.startswith('"') and tags_raw.endswith('"'):
                    tags_raw = tags_raw[1:-1]

                # Parse tags using ProjectComposer
                if pc:
                    parsed_tags = pc.parse_tags_from_string(tags_raw, label_map=label_map)
                else:
                    parsed_tags = {'c': '', 't': '', 'b': '', 'm': '', 's': []}

                # Extract main label for display
                main_label = parsed_tags.get('m', '')

                items.append({
                    'item_id': row[0],
                    'name': row[1],
                    'bought_date': row[2],
                    'price': row[3],
                    'currency': row[4],
                    'price_final': row[5],
                    'currency_final': row[6],
                    'bought_by_id': row[7],
                    'bought_by_username': row[8],
                    'bought_by_first_name': row[9],
                    'bought_by_last_name': row[10],
                    'note': row[11],
                    'exchange_rate': row[12],
                    'exchange_rate_date': row[13],
                    'tags': tags_raw,
                    'parsed_tags': parsed_tags,
                    'label_m': main_label  # Main label for display
                })

            return items

        except Exception as e:
            self.app.notify("Error fetching items for user")
            self.app.log(f"Error fetching user items: {e}")
            return []

    def refresh_data(self) -> None:
        """Refresh all DataTables with items for the current period.

        Called when the date range changes in the parent ReportsScreen.
        """
        try:
            # Update the date selection display
            period_start = self.app.app_state.get("current_period_start")
            period_end = self.app.app_state.get("current_period_end")
            period_label = self.app.app_state.get("current_period_label", "")
            period_type = self.app.app_state.get("current_period_type", "week")

            if period_start and period_end:
                date_range_text = f"📅 {period_label}: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
            else:
                date_range_text = "📅 All expenses"

            self.app.log(f"BasicReportForm refresh_data - Period: {date_range_text}")

            # Update the Static widget
            date_display = self.query_one("#date-selection-display", Static)
            date_display.update(date_range_text)

            project_id = self.app.app_state.get("project_id", 0)
            if project_id <= 0:
                return

            # Get all project users
            project_users = self._get_project_users(project_id)

            # Get main currency and project style
            currency_main = self.app.app_state.get("current_project_currency_main", "USD")
            project_style = self.app.app_state.get("project_style", "default")

            # Get ProjectComposer instance
            dbh = self.app._config.get("dbh")
            from fiwa_cli.functions.project_composer import ProjectComposer

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

            # Update each user's DataTables (both fixed/variable and daily)
            for user in project_users:
                # Check if user has at least Read permission
                user_permission = user.get("project_perm_model", "000000")
                if not user_permission or len(user_permission) < 6:
                    continue
                if user_permission[0] != '1':
                    self.app.log(f"Skipping user {user['username']} in refresh - no Read permission")
                    continue

                # Fetch items for this user
                items = self._get_user_items(user['user_id'], project_id)

                # Apply transformations
                if pc:
                    items = pc.get_balance_split(items)
                    items_fv = pc.get_transaction_split(items, keys=["fixed", "variable"])
                    items_daily = pc.get_transaction_split(items, keys=["daily"])
                else:
                    items_fv = items
                    items_daily = []

                # --- Refresh Fixed/Variable Table ---
                table_fv_id = f"items-table-fv-{user['user_id']}"
                try:
                    table_fv = self.query_one(f"#{table_fv_id}", DataTable)
                    table_fv.clear()

                    total_fv = 0.0
                    revenue_fv = 0.0
                    expenses_fv = 0.0
                    bought_by_self_fv = 0.0
                    bought_by_others_fv = {}

                    for item in items_fv:
                        date_str = str(item['bought_date']).split()[0] if item['bought_date'] else ""
                        label_display = item.get('label_m', '')
                        multiplier = item.get('multiplier', 1)

                        table_fv.add_row(
                            item['name'],
                            f"{item['price']:.2f}",
                            item['currency'],
                            f"{item['price_final']:.2f}",
                            date_str,
                            f"{item['bought_by_last_name']}",
                            label_display,
                            key=f"fv-{item['item_id']}"
                        )

                        amount = item['price_final'] * multiplier
                        total_fv += amount

                        if multiplier == 1:
                            revenue_fv += item['price_final']
                        else:
                            expenses_fv += item['price_final']

                        if item['bought_by_id'] == user['user_id']:
                            bought_by_self_fv += item['price_final']
                        else:
                            buyer_name = f"{item['bought_by_first_name']} {item['bought_by_last_name']}"
                            bought_by_others_fv[buyer_name] = bought_by_others_fv.get(buyer_name, 0.0) + item['price_final']

                    # Sort by date
                    if table_fv.columns:
                        date_column_key = list(table_fv.columns.keys())[4]
                        table_fv.sort(date_column_key, reverse=True)

                    # Update fixed/variable total
                    total_fv_widget = self.query_one(f"#total-fv-{user['user_id']}", Static)
                    total_fv_widget.update(f"Total Fixed/Variable: {total_fv:.2f} {currency_main}")

                except Exception as e:
                    self.app.log(f"Could not refresh fixed/variable table for user {user['user_id']}: {e}")

                # --- Refresh Daily Table ---
                table_daily_id = f"items-table-daily-{user['user_id']}"
                try:
                    table_daily = self.query_one(f"#{table_daily_id}", DataTable)
                    table_daily.clear()

                    total_daily = 0.0
                    revenue_daily = 0.0
                    expenses_daily = 0.0
                    bought_by_self_daily = 0.0
                    bought_by_others_daily = {}

                    for item in items_daily:
                        date_str = str(item['bought_date']).split()[0] if item['bought_date'] else ""
                        label_display = item.get('label_m', '')
                        multiplier = item.get('multiplier', 1)

                        table_daily.add_row(
                            item['name'],
                            f"{item['price']:.2f}",
                            item['currency'],
                            f"{item['price_final']:.2f}",
                            date_str,
                            f"{item['bought_by_last_name']}",
                            label_display,
                            key=f"daily-{item['item_id']}"
                        )

                        amount = item['price_final'] * multiplier
                        total_daily += amount

                        if multiplier == 1:
                            revenue_daily += item['price_final']
                        else:
                            expenses_daily += item['price_final']

                        if item['bought_by_id'] == user['user_id']:
                            bought_by_self_daily += item['price_final']
                        else:
                            buyer_name = f"{item['bought_by_first_name']} {item['bought_by_last_name']}"
                            bought_by_others_daily[buyer_name] = bought_by_others_daily.get(buyer_name, 0.0) + item['price_final']

                    # Sort by date
                    if table_daily.columns:
                        date_column_key = list(table_daily.columns.keys())[4]
                        table_daily.sort(date_column_key, reverse=True)

                    # Update daily total
                    total_daily_widget = self.query_one(f"#total-daily-{user['user_id']}", Static)
                    total_daily_widget.update(f"Total Daily: {total_daily:.2f} {currency_main}")

                except Exception as e:
                    self.app.log(f"Could not refresh daily table for user {user['user_id']}: {e}")

                # --- Update Combined Summary ---
                try:
                    total_all = total_fv + total_daily
                    total_revenue = revenue_fv + revenue_daily
                    total_expenses = expenses_fv + expenses_daily

                    breakdown_lines = [f"💰 Grand Total: {total_all:.2f} {currency_main}"]

                    # Show revenue/expense breakdown for monthly view
                    if period_type == "month":
                        breakdown_lines.append(f"  ↗ Revenue: {total_revenue:.2f} {currency_main}")
                        breakdown_lines.append(f"  ↘ Expenses: {total_expenses:.2f} {currency_main}")
                        breakdown_lines.append(f"  = Balance: {total_all:.2f} {currency_main}")

                    # Show who bought what breakdown
                    total_self = bought_by_self_fv + bought_by_self_daily
                    if total_self > 0:
                        breakdown_lines.append(f"  • Self: {total_self:.2f} {currency_main}")

                    # Merge bought_by_others from both tables
                    all_bought_by_others = {}
                    for buyer, amount in bought_by_others_fv.items():
                        all_bought_by_others[buyer] = all_bought_by_others.get(buyer, 0.0) + amount
                    for buyer, amount in bought_by_others_daily.items():
                        all_bought_by_others[buyer] = all_bought_by_others.get(buyer, 0.0) + amount

                    if all_bought_by_others:
                        for buyer, amount in sorted(all_bought_by_others.items(), key=lambda x: x[1], reverse=True):
                            breakdown_lines.append(f"  • From {buyer}: {amount:.2f} {currency_main}")

                    total_widget = self.query_one(f"#total-user-{user['user_id']}", Static)
                    total_widget.update("\n".join(breakdown_lines))

                    self.app.log(f"Refreshed tables for user {user['user_id']}: {len(items_fv)} fixed/variable, {len(items_daily)} daily")

                except Exception as e:
                    self.app.log(f"Could not update summary for user {user['user_id']}: {e}")

        except Exception as e:
            self.app.log(f"Error refreshing data tables: {e}")
