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

        pc = ProjectComposer.create(
            compose_type=project_style,
            dbh=dbh,
            project_id=project_id,
            users=[]
        )


        # Wrap in ScrollableContainer for scrolling
        with ScrollableContainer(id="report-content"):
            # Create tabbed content with one tab per user
            with TabbedContent():
                for user in project_users:
                    # Check if user has at least Read permission (first character must be '1')
                    user_permission = user.get("project_perm_model", "000000")

                    if user_permission[0] != '1' or len(user_permission) < 6:
                        # User doesn't have Read permission, skip
                        self.app.log(f"Skipping user {user['username']} - no Read permission ({user_permission})")
                        continue

                    with TabPane(f"{user['first_name']} {user['last_name']}", id=f"tab-user-{user['user_id']}"):
                        # Create DataTable for this user's items
                        table = DataTable(id=f"items-table-{user['user_id']}")

                        # Add columns and store keys
                        col_name = table.add_column("Name")
                        col_price = table.add_column("Price")
                        col_currency = table.add_column("Currency")
                        col_final = table.add_column(f"Final [{currency_main}]")
                        col_date = table.add_column("Date")
                        col_bought_by = table.add_column("Bought by")
                        col_label = table.add_column("Label")

                        table.cursor_type = "row"

                        # Fetch items for this user
                        items = self._get_user_items(user['user_id'], project_id)
                        k = pc.get(items)
                        print(str(k))
                        # Calculate totals with breakdown: who bought what for whom
                        total_final = 0.0
                        bought_by_self = 0.0  # I bought for myself
                        bought_by_others = {}  # Others bought for me: {buyer_name: amount}

                        for item in items:
                            # Extract date only (remove time if present)
                            date_str = str(item['bought_date']).split()[0] if item['bought_date'] else ""

                            # Get main label for display
                            label_display = item.get('label_m', '')

                            # Add row with all price information
                            table.add_row(
                                item['name'],
                                f"{item['price']:.2f}",
                                item['currency'],
                                f"{item['price_final']:.2f}",
                                date_str,
                                f"{item['bought_by_last_name']}",
                                label_display,
                                key=str(item['item_id'])
                            )

                            # Track totals
                            amount = item['price_final']
                            total_final += amount

                            # Breakdown: who bought this?
                            if item['bought_by_id'] == user['user_id']:
                                # I bought it for myself
                                bought_by_self += amount
                            else:
                                # Someone else bought it for me
                                buyer_name = f"{item['bought_by_first_name']} {item['bought_by_last_name']}"
                                if buyer_name not in bought_by_others:
                                    bought_by_others[buyer_name] = 0.0
                                bought_by_others[buyer_name] += amount

                        # Sort by Date column by default (descending - newest first)
                        table.sort(col_date, reverse=True)

                        yield table

                        # Show total breakdown for this user INSIDE the tab
                        breakdown_lines = [f"💰 Total: {total_final:.2f} {currency_main}"]

                        if bought_by_self > 0:
                            breakdown_lines.append(f"  • Self: {bought_by_self:.2f} {currency_main}")

                        if bought_by_others:
                            for buyer, amount in sorted(bought_by_others.items(), key=lambda x: x[1], reverse=True):
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
                    AND i.bought_date BETWEEN ? AND ?
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

            # Get main currency
            currency_main = self.app.app_state.get("current_project_currency_main", "USD")

            # Update each user's DataTable
            for user in project_users:
                # Check if user has at least Read permission (first character must be '1')
                user_permission = user.get("project_perm_model", "000000")

                if user_permission[0] != '1' or len(user_permission) < 6:
                    # User doesn't have Read permission, skip
                    self.app.log(f"Skipping user {user['username']} in refresh - no Read permission ({user_permission})")
                    continue

                table_id = f"items-table-{user['user_id']}"
                try:
                    table = self.query_one(f"#{table_id}", DataTable)

                    # Clear existing rows
                    table.clear()

                    # Fetch new items for the current period
                    items = self._get_user_items(user['user_id'], project_id)

                    # Calculate totals with breakdown: who bought what for whom
                    total_final = 0.0
                    bought_by_self = 0.0  # I bought for myself
                    bought_by_others = {}  # Others bought for me: {buyer_name: amount}

                    # Add rows to the table
                    for item in items:
                        # Extract date only (remove time if present)
                        date_str = str(item['bought_date']).split()[0] if item['bought_date'] else ""

                        # Get main label for display
                        label_display = item.get('label_m', '')

                        table.add_row(
                            # str(item['item_id']),
                            item['name'],
                            f"{item['price']:.2f}",
                            item['currency'],
                            f"{item['price_final']:.2f}",
                            date_str,
                            f"{item['bought_by_last_name']}",
                            label_display,
                            key=str(item['item_id'])
                        )

                        # Track totals
                        amount = item['price_final']
                        total_final += amount

                        # Breakdown: who bought this?
                        if item['bought_by_id'] == user['user_id']:
                            # I bought it for myself
                            bought_by_self += amount
                        else:
                            # Someone else bought it for me
                            buyer_name = f"{item['bought_by_first_name']} {item['bought_by_last_name']}"
                            if buyer_name not in bought_by_others:
                                bought_by_others[buyer_name] = 0.0
                            bought_by_others[buyer_name] += amount

                    # Sort by Date column by default (descending - newest first)
                    # Get the Date column key (5th column, index 4 since we don't have ID column here)
                    if table.columns:
                        date_column_key = list(table.columns.keys())[4]  # Date is the 5th column (index 4)
                        table.sort(date_column_key, reverse=True)

                    # Update total display with breakdown
                    try:
                        total_widget = self.query_one(f"#total-user-{user['user_id']}", Static)

                        breakdown_lines = [f"💰 Total: {total_final:.2f} {currency_main}"]

                        if bought_by_self > 0:
                            breakdown_lines.append(f"  • Self: {bought_by_self:.2f} {currency_main}")

                        if bought_by_others:
                            for buyer, amount in sorted(bought_by_others.items(), key=lambda x: x[1], reverse=True):
                                breakdown_lines.append(f"  • From {buyer}: {amount:.2f} {currency_main}")

                        total_widget.update("\n".join(breakdown_lines))
                    except:
                        pass

                    self.app.log(f"Refreshed table for user {user['user_id']}: {len(items)} items")

                except Exception as e:
                    self.app.log(f"Could not refresh table for user {user['user_id']}: {e}")

        except Exception as e:
            self.app.log(f"Error refreshing data tables: {e}")
