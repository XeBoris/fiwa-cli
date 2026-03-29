"""Basic cost overview report for FiWa CLI.

This module provides the fundamental reporting interface showing detailed
expense breakdowns by user. It's the primary report view that users interact
with for understanding project finances.

The BasicReportForm displays:
    - Tabbed view with one tab per project user
    - Separate tables for fixed/variable vs. daily transactions
    - Total revenue and expense summaries per user
    - Repayment calculations showing who owes whom
    - Period-based filtering (week or month)

Key Features:
    - Per-user expense tracking in tabbed interface
    - Split view: Fixed/Variable vs. Daily transactions
    - Automatic totaling and balance calculations
    - Repayment modal showing inter-user debts
    - Sortable DataTables (click columns to sort)
    - Real-time period filtering from app_state

Report Structure:
    For each user in the project:
        Tab: {username}
            ├── DataTable: Fixed & Variable Transactions
            │   └── Columns: Name, Price, Currency, Final, Date, Bought By
            ├── DataTable: Daily Transactions
            │   └── Columns: Name, Price, Currency, Final, Date, Bought By
            └── Summary: Total Revenue, Total Expenses, Balance

Classes:
    RepayModal: Modal showing repayment calculations
    BasicReportForm: Main report form with user tabs and tables

Transaction Classification:
    Transactions are classified by label type:
        - **Fixed**: Label type 1, sub_type 0 (recurring expenses)
        - **Variable**: Label type 1, sub_type 1 (occasional expenses)
        - **Daily**: Label type 1, sub_type 2 (frequent small expenses)

    Revenue transactions (label type 1, sub_type 3+) appear separately.

Example:
    Mounting the form::

        >>> from fiwa_cli.screens.reports_basic import BasicReportForm
        >>> form = BasicReportForm()
        >>> content_area.mount(form)

    Viewing repayments::

        >>> # User clicks "Repay" button
        >>> # RepayModal opens
        >>> # Shows: "Batman owes Superman: 25.50 USD"
        >>> # User clicks OK to dismiss

See Also:
    reports: Main reports screen that mounts this form
    components.week_month_picker: Period selection affecting this report
    inputs_edit_expense: Similar tabbed expense view for editing
"""

from textual.containers import Vertical, ScrollableContainer, Horizontal
from textual.widgets import Static, TabbedContent, TabPane, DataTable, Button
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual import on
from fiwa_cli.functions.loader import load_dynamic_css


class RepayModal(ModalScreen):
    """Modal screen showing who owes whom based on shared expenses.

    This modal calculates and displays inter-user debts based on the
    expense sharing system. When users buy items for each other, this
    modal shows the net amounts owed between all project members.

    The calculation considers:
        - Items bought by User A for User B (B owes A)
        - Items bought by User B for User A (A owes B)
        - Net calculation (A owes B 50, B owes A 30 = A owes B 20 net)

    Attributes:
        project_id (int): ID of the project to calculate repayments for

    BINDINGS:
        - Escape: Close modal (dismiss_modal)

    Display Format:
        For each non-zero debt::

            💰 {Debtor} owes {Creditor}: {Amount:.2f} {Currency}

        If all settled::

            ✅ All settled! No repayments needed.

    Example:
        Opening the modal::

            >>> modal = RepayModal(project_id=42)
            >>> self.app.push_screen(modal)

        Example output::

            💰 Superman owes Batman: 125.50 USD
            💰 Wonderwoman owes Batman: 45.00 USD

    Calculation Logic:
        1. Query all transactions in current period
        2. For each transaction where bought_by != bought_for:
           - Creditor = bought_by_id
           - Debtor = bought_for_id
           - Amount = final_price
        3. Aggregate by (debtor, creditor) pairs
        4. Calculate net (A→B minus B→A)
        5. Display only non-zero net amounts

    Note:
        The modal uses the period from app_state (current_period_start
        and current_period_end) to filter transactions. Only transactions
        within the selected period are considered for repayment calculation.

        All amounts are shown in the project's main currency (converted
        using exchange rates from transaction records).

    See Also:
        BasicReportForm: Parent report that opens this modal
        _calculate_repayments: Method that performs debt calculation
    """

    BINDINGS = [
        ("escape", "dismiss_modal", "Close"),
    ]

    def __init__(self, project_id: int, *args, **kwargs):
        """Initialize the repayment modal.

        Args:
            project_id: ID of the project to calculate repayments for
            *args: Additional positional arguments for ModalScreen
            **kwargs: Additional keyword arguments for ModalScreen
        """
        super().__init__(*args, **kwargs)
        self.project_id = project_id

    def compose(self) -> ComposeResult:
        """Compose the repayment modal interface."""
        with Vertical(id="repay-modal-container"):
            yield Static("☛ Repay Overview", classes="modal-title")

            # Show current period
            period_start = self.app.app_state.get("current_period_start")
            period_end = self.app.app_state.get("current_period_end")

            if period_start and period_end:
                period_text = f"𝌌 Period: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
            else:
                period_text = "𝌌 All time"

            yield Static(period_text, classes="modal-period")
            yield Static("Who owes whom:", classes="modal-subtitle")

            with ScrollableContainer(id="repay-list-container"):
                # Calculate and display repayments
                repayments = self._calculate_repayments()

                if repayments:
                    for repayment in repayments:
                        debtor = repayment["debtor"]
                        creditor = repayment["creditor"]
                        amount = repayment["amount"]
                        currency = repayment["currency"]

                        yield Static(
                            f"💰 {debtor} owes {creditor}: {amount:.2f} {currency}",
                            classes="repayment-item",
                        )
                else:
                    yield Static(
                        "✅ All settled! No repayments needed.", classes="repayment-settled"
                    )

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

            results = dbh.execute_query(query, [self.project_id, start_date_str, end_date_str])

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
                            simplified_debts.append(
                                {
                                    "debtor": user_names.get(debtor_id, f"User {debtor_id}"),
                                    "creditor": user_names.get(creditor_id, f"User {creditor_id}"),
                                    "amount": net_debt,
                                    "currency": currency_main,
                                }
                            )
                        else:
                            # creditor owes debtor
                            simplified_debts.append(
                                {
                                    "debtor": user_names.get(creditor_id, f"User {creditor_id}"),
                                    "creditor": user_names.get(debtor_id, f"User {debtor_id}"),
                                    "amount": abs(net_debt),
                                    "currency": currency_main,
                                }
                            )

            # Sort by amount descending
            simplified_debts.sort(key=lambda x: x["amount"], reverse=True)

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
    """Cost Overview report showing detailed expense breakdown per user.

    This report provides the most comprehensive view of project finances,
    displaying all transactions organized by user in tabbed format. Each
    user's tab shows separate tables for different transaction types along
    with calculated totals and balances.

    The report is the primary financial analysis tool that helps users:
        - Track personal spending across categories
        - Distinguish between fixed, variable, and daily expenses
        - Monitor revenue streams
        - Calculate net balances (revenue - expenses)
        - Identify inter-user debts via Repay feature

    Attributes:
        None (stateless widget, reads from app_state and database)

    Report Components (per user tab):
        1. **Period Display**: Shows selected week/month with date range

        2. **Fixed & Variable Transactions Table**:
           - Recurring expenses (rent, subscriptions)
           - Occasional expenses (utilities, insurance)
           - Revenue items (salary, income)
           - Height: Auto-sized based on row count

        3. **Daily Transactions Table**:
           - Frequent small expenses (groceries, coffee)
           - Height: Auto-sized based on row count

        4. **Summary Section**:
           - Total Revenue: Sum of all revenue items (green)
           - Total Expenses: Sum of all expense items (red)
           - Balance: Revenue - Expenses (colored by sign)
           - Repay Button: Opens debt calculation modal

    DataTable Columns:
        All tables share the same column structure:
            - **Name** (20 char): Transaction name
            - **Price**: Original amount
            - **Curr**: Original currency
            - **Final**: Converted amount
            - **[USD]**: Main currency (dynamic, e.g., EUR, JPY)
            - **Date**: Transaction date (YYYY-MM-DD)
            - **Bought By**: Username of purchaser
            - **Labels**: Main label name (from tags)

    Transaction Classification:
        Uses label sub_type from ProjectComposer:
            - **sub_type = 0**: Fixed (table 1)
            - **sub_type = 1**: Variable (table 1)
            - **sub_type = 2**: Daily (table 2)
            - **sub_type >= 3**: Revenue (table 1, positive multiplier)

    Data Flow:
        1. Reads period_start, period_end from app_state
        2. Queries database: ``op_item_get_all_for_user()``
        3. Splits transactions by label sub_type
        4. Populates appropriate table
        5. Calculates totals using multiplier (-1 for expenses, +1 for revenue)
        6. Displays balance with appropriate color

    Sorting:
        - Click column header to sort
        - Default: Sorted by Date descending
        - Supports multi-column sorting
        - Visual indicator shows sort direction

    Example:
        Basic usage::

            >>> form = BasicReportForm()
            >>> content_area.mount(form)
            >>> # Report shows current period data

        Typical report display::

            >>> # Tab: Batman
            >>> # Fixed & Variable Transactions:
            >>> #   Rent              $1500  USD  $1500  [USD]  2026-03-01  Batman
            >>> #   Salary           +$5000  USD  $5000  [USD]  2026-03-15  Batman
            >>> # Daily Transactions:
            >>> #   Whole Foods         $85  USD    $85  [USD]  2026-03-10  Batman
            >>> #   Starbucks            $5  USD     $5  [USD]  2026-03-10  Batman
            >>> # Total Revenue: $5000.00
            >>> # Total Expenses: $1590.00
            >>> # Balance: +$3410.00

        Repayment view::

            >>> # User clicks "Repay" button
            >>> # RepayModal opens
            >>> # Shows: "Superman owes Batman: 50.00 USD"
            >>> # (Because Batman bought groceries for Superman)

    Performance:
        - Lazy loading: Only selected tab's data is visible
        - Efficient queries: Single query per user with filtering
        - Cached label data: ProjectComposer labels cached
        - Minimal re-renders: Only refreshes on period change

    Note:
        The report uses ``bought_for_id`` to determine which expenses
        belong to which user. A user sees expenses bought FOR them,
        regardless of who actually purchased them (bought_by_id).

        The Repay feature analyzes the bought_by vs. bought_for
        relationships to calculate who owes money to whom.

        Exchange rates are applied automatically - all Final amounts
        are in the project's main currency for easy comparison.

    See Also:
        RepayModal: Modal for repayment calculations
        reports.ReportsScreen: Parent screen with period selection
        inputs_edit_expense: Similar tabbed view for expense editing
        functions.project_composer.ProjectComposer: Transaction type definitions
    """

    def compose(self) -> ComposeResult:
        """Compose the Cost Overview report interface.

        Builds the complete report UI including period display, user tabs,
        transaction tables, and summary sections for each user.

        Yields:
            Static: Report title
            Static: Current period display with date range
            TabbedContent: Container with one tab per project user
                TabPane (per user):
                    - DataTable: Fixed & Variable transactions
                    - DataTable: Daily transactions
                    - Horizontal: Summary section with totals and Repay button

        Note:
            Only users with Read permission (100000+) get tabs.
            Tables are pre-populated with data from the current period.
        """
        yield Static("Cost Overview", classes="report-title")

        # Display current date selection
        period_start = self.app.app_state.get("current_period_start")
        period_end = self.app.app_state.get("current_period_end")
        period_label = self.app.app_state.get("current_period_label", "")
        period_type = self.app.app_state.get("current_period_type", "week")

        if period_start and period_end:
            date_range_text = f"𝌌 {period_label}: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
        else:
            date_range_text = "𝌌 All expenses"

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
                compose_type=project_style, dbh=dbh, project_id=project_id, users=[]
            )
        except Exception as e:
            self.app.log(f"Error creating ProjectComposer: {e}")
            pc = None

        # Wrap in ScrollableContainer for scrolling
        with ScrollableContainer(id="report-content"):
            # Create tabbed content with one tab per user
            with TabbedContent():
                # Log project users found
                try:
                    self.app.file_log.info(
                        f"BasicReportForm compose: {len(project_users)} users to process"
                    )
                except Exception:
                    pass

                for user in project_users:
                    # Check if user has at least Read permission
                    user_permission = user.get("project_perm_model", "000000")

                    try:
                        self.app.file_log.info(
                            f"Checking user: {user.get('username')} - perm: {user_permission}"
                        )
                    except Exception:
                        pass

                    if user_permission[0] != "1" or len(user_permission) < 6:
                        self.app.log(f"Skipping user {user.get('username')} - no Read permission")
                        try:
                            self.app.file_log.warning(
                                f"SKIPPED user {user.get('username')} - perm check failed"
                            )
                        except Exception:
                            pass
                        continue

                    with TabPane(
                        f"{user['first_name']} {user['last_name']}",
                        id=f"tab-user-{user['user_id']}",
                    ):
                        # Fetch items for this user
                        items = self._get_user_items(user["user_id"], project_id)

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
                            date_str = (
                                str(item["bought_date"]).split()[0] if item["bought_date"] else ""
                            )
                            label_display = item.get("label_m", "")
                            multiplier = item.get("multiplier", 1)

                            table_fv.add_row(
                                item["name"],
                                f"{item['price']:.2f}",
                                item["currency"],
                                f"{item['price_final']:.2f}",
                                date_str,
                                f"{item['bought_by_last_name']}",
                                label_display,
                                key=f"fv-{item['item_id']}",
                            )

                            amount = item["price_final"] * multiplier
                            total_fv += amount

                            if multiplier == 1:
                                revenue_fv += item["price_final"]
                            else:
                                expenses_fv += item["price_final"]

                            if item["bought_by_id"] == user["user_id"]:
                                bought_by_self_fv += item["price_final"]
                            else:
                                buyer_name = (
                                    f"{item['bought_by_first_name']} {item['bought_by_last_name']}"
                                )
                                bought_by_others_fv[buyer_name] = (
                                    bought_by_others_fv.get(buyer_name, 0.0) + item["price_final"]
                                )

                        table_fv.sort(col_date_fv, reverse=True)
                        yield table_fv
                        yield Static(
                            f"Total Fixed/Variable: -{expenses_fv:.2f} {currency_main} | +{revenue_fv:.2f} {currency_main} ▷ {total_fv:.2f} {currency_main} ",
                            classes="subtotal",
                            id=f"total-fv-{user['user_id']}",
                        )

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
                            date_str = (
                                str(item["bought_date"]).split()[0] if item["bought_date"] else ""
                            )
                            label_display = item.get("label_m", "")
                            multiplier = item.get("multiplier", 1)

                            table_daily.add_row(
                                item["name"],
                                f"{item['price']:.2f}",
                                item["currency"],
                                f"{item['price_final']:.2f}",
                                date_str,
                                f"{item['bought_by_last_name']}",
                                label_display,
                                key=f"daily-{item['item_id']}",
                            )

                            amount = item["price_final"] * multiplier
                            total_daily += amount

                            if multiplier == 1:
                                revenue_daily += item["price_final"]
                            else:
                                expenses_daily += item["price_final"]

                            if item["bought_by_id"] == user["user_id"]:
                                bought_by_self_daily += item["price_final"]
                            else:
                                buyer_name = (
                                    f"{item['bought_by_first_name']} {item['bought_by_last_name']}"
                                )
                                bought_by_others_daily[buyer_name] = (
                                    bought_by_others_daily.get(buyer_name, 0.0)
                                    + item["price_final"]
                                )

                        table_daily.sort(col_date_daily, reverse=True)
                        yield table_daily
                        yield Static(
                            f"Total Daily: -{expenses_daily:.2f} {currency_main} | +{revenue_daily:.2f} {currency_main} ▷ {total_daily:.2f} {currency_main} ",
                            classes="subtotal",
                            id=f"total-daily-{user['user_id']}",
                        )

                        # --- Combined Summary ---
                        total_all = total_fv + total_daily
                        total_revenue = revenue_fv + revenue_daily
                        total_expenses = expenses_fv + expenses_daily

                        if period_type == "week":
                            breakdown_lines = [f"💰 Grand Total: {total_daily:.2f} {currency_main}"]
                        else:
                            breakdown_lines = [f"💰 Grand Total: {total_all:.2f} {currency_main}"]

                        # Show revenue/expense breakdown for monthly view
                        if period_type == "month":
                            breakdown_lines.append(
                                f"  ↗ Revenue: {total_revenue:.2f} {currency_main}"
                            )
                            breakdown_lines.append(
                                f"  ↘ Expenses: {total_expenses:.2f} {currency_main}"
                            )
                            breakdown_lines.append(f"  = Balance: {total_all:.2f} {currency_main}")

                        # Show who bought what breakdown
                        total_self = bought_by_self_fv - bought_by_self_daily
                        if bought_by_self_daily > 0 and period_type == "week":
                            breakdown_lines.append(
                                f"  • Self: {bought_by_self_daily:.2f} {currency_main}"
                            )
                        if total_self > 0 and period_type == "month":
                            breakdown_lines.append(f"  • Self: {total_self:.2f} {currency_main}")

                        # Merge bought_by_others from both tables
                        all_bought_by_others = {}
                        for buyer, amount in bought_by_others_fv.items():
                            all_bought_by_others[buyer] = (
                                all_bought_by_others.get(buyer, 0.0) + amount
                            )
                        for buyer, amount in bought_by_others_daily.items():
                            all_bought_by_others[buyer] = (
                                all_bought_by_others.get(buyer, 0.0) + amount
                            )

                        if all_bought_by_others:
                            for buyer, amount in sorted(
                                all_bought_by_others.items(), key=lambda x: x[1], reverse=True
                            ):
                                breakdown_lines.append(
                                    f"  • From {buyer}: {amount:.2f} {currency_main}"
                                )

                        yield Static(
                            "\n".join(breakdown_lines),
                            classes="user-total",
                            id=f"total-user-{user['user_id']}",
                        )

            # Repay button INSIDE ScrollableContainer but OUTSIDE TabbedContent
            yield Button("Repay", id="repay-button", classes="repay-button")

    def on_mount(self) -> None:
        """Load CSS stylesheet when the report form is mounted.

        Side Effects:
            - Loads screens_reports_basic.tcss stylesheet
            - Logs mount event to file_log

        Note:
            This is called automatically by Textual after compose()
            creates all widgets but before they're displayed.
        """

        load_dynamic_css(self, "screens_reports_basic.tcss")

        try:
            self.app.file_log.info("BasicReportForm mounted - Cost Overview report ready")
        except Exception:
            pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events in the report.

        Currently handles the "Repay" button to show inter-user debt
        calculations for the current period.

        Args:
            event: Button.Pressed event containing the clicked button

        Handles:
            - repay-button: Opens RepayModal with debt calculations

        Side Effects:
            - Pushes RepayModal onto screen stack
            - Logs button press to file_log

        Example:
            User clicks Repay::

                >>> # User viewing Batman's tab
                >>> # Summary shows: Balance +$1500
                >>> # User clicks "Repay" button
                >>> # RepayModal opens
                >>> # Shows all debts between project users
        """
        if event.button.id == "repay-button":
            # Open repayment modal for the current project
            project_id = self.app.app_state.get("project_id", 0)
            self.app.push_screen(RepayModal(project_id))

            try:
                self.app.file_log.info(f"Repay modal opened for project {project_id}")
            except Exception:
                pass

    @on(DataTable.HeaderSelected)
    def on_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle column header click to sort the table.

        Clicking a column header sorts the table by that column. Clicking
        again toggles between ascending and descending order.

        Args:
            event: DataTable.HeaderSelected event containing:
                - data_table: The table that was clicked
                - column_key: The key of the clicked column

        Side Effects:
            - Sorts the DataTable by clicked column
            - Toggles sort direction on repeated clicks
            - Logs sort operation

        Example:
            User sorts by Price::

                >>> # User clicks "Price" column header
                >>> # Table sorts by price ascending
                >>> # User clicks "Price" again
                >>> # Table sorts by price descending

        Note:
            The DataTable.sort() method handles the toggle logic
            automatically - we just need to call it with the column key.
        """
        table = event.data_table

        # Sort by the clicked column
        # The sort method will automatically toggle between ascending/descending
        table.sort(event.column_key)

        self.app.log(f"Sorted table by column: {event.column_key}")

    def _get_project_users(self, project_id: int) -> list:
        """Get all users for the project.

        Queries the database for all users associated with the project.
        Permission filtering is handled by the caller (compose method).

        Args:
            project_id: ID of the project to get users for

        Returns:
            List of user dictionaries, each containing:
                - user_id (int): User identifier
                - username (str): User's username
                - permissions (str): Permission string (e.g., "111100")
                - first_name (str): User's first name
                - last_name (str): User's last name
                - project_perm_model (str): Same as permissions

        Example:
            >>> users = self._get_project_users(42)
            >>> # Returns ALL project users, including those without Read permission
            >>> # Caller must filter by permissions[0] == '1' for Read access

        Note:
            This method returns ALL project members. The compose() method
            is responsible for filtering users based on Read permission
            (checking if permissions[0] == '1').

        See Also:
            compose: Method that filters users by permission level
            op_project_get_users: Database operation returning users
        """
        try:
            dbh = self.app._config.get("dbh")
            if dbh and project_id > 0:
                users = dbh.op_project_get_users(project_id)

                # Log for debugging
                try:
                    self.app.file_log.info(
                        f"_get_project_users: Found {len(users)} users for project {project_id}"
                    )
                    for u in users:
                        perm = u.get("project_perm_model", "N/A")
                        self.app.file_log.info(f"  User: {u.get('username')} - Permission: {perm}")
                except Exception:
                    pass

                return users  # Return ALL users, let caller filter
            return []
        except Exception as e:
            self.app.log(f"Error fetching project users: {e}")
            try:
                self.app.file_log.error(f"Error fetching project users: {e}")
            except Exception:
                pass
            return []

    def _get_user_items(self, user_id: int, project_id: int) -> list:
        """Get all transactions for a user in the current period with label details.

        Queries the database for all items where the user is the recipient
        (bought_for_id), within the current period boundaries, and enriches
        each item with full label information.

        This method performs a complex query that:
            1. Retrieves all transactions for the user
            2. Parses the tags string (format: "c_t_b_m_[s1,s2,...]")
            3. Looks up label details for each tag component
            4. Calculates transaction multiplier based on label sub_type
            5. Returns enriched transaction data

        Args:
            user_id: ID of the user to fetch transactions for
            project_id: ID of the project context

        Returns:
            List of item dictionaries, each containing:
                - item_id (int): Transaction identifier
                - name (str): Transaction name
                - bought_date (datetime): Purchase date
                - price (float): Original price
                - currency (str): Original currency code
                - price_final (float): Converted price in main currency
                - currency_final (str): Main currency code
                - bought_by_id (int): ID of purchaser
                - bought_by_username (str): Username of purchaser
                - note (str): Optional notes
                - exchange_rate (float): Conversion rate used
                - exchange_rate_date (datetime): Rate date
                - tags (str): Raw tag string
                - label_details (list): Parsed label information
                - multiplier (int): 1 for revenue, -1 for expenses
                - label_transaction_id (int): Main transaction label ID
                - label_transaction_name (str): Main label name
                - label_transaction_type (int): Transaction type
                - label_transaction_sub_type (int): Transaction sub-type

        Tag String Format:
            Tags are stored as: "count_transaction_bank_main_[sec1,sec2,...]"
            Example: "3_4_5_6_[7,8]" means:
                - Count label ID: 3
                - Transaction label ID: 4
                - Bank/Account label ID: 5
                - Main category label ID: 6
                - Secondary labels: [7, 8]

        Multiplier Logic:
            Based on transaction label sub_type:
                - sub_type < 3: Expense → multiplier = -1
                - sub_type >= 3: Revenue → multiplier = +1

        Period Filtering:
            Uses app_state values:
                - current_period_start: Inclusive start date
                - current_period_end: Exclusive end date
            Query: ``bought_date >= start AND bought_date < end``

        Example:
            >>> items = self._get_user_items(user_id=1, project_id=42)
            >>> # Returns transactions for batman in project 42
            >>> for item in items:
            >>>     print(f"{item['name']}: {item['price_final']} {item['currency_final']}")
            >>>     print(f"  Label: {item['label_transaction_name']}")
            >>>     print(f"  Type: {item['label_transaction_sub_type']}")
            >>>     print(f"  Multiplier: {item['multiplier']}")

        Label Details Structure:
            Each item includes a label_details list with full information
            about all assigned labels (transaction, account, main, secondary).
            This enables detailed categorization analysis.

        Note:
            The method uses cached labels from ProjectComposer for efficiency.
            The multiplier field allows easy summation: positive values are
            revenue, negative values are expenses.

            Only transactions where bought_for_id matches the user_id are
            returned - this ensures users see expenses "for them" regardless
            of who actually purchased them (bought_by_id).

        See Also:
            functions.project_composer.parse_tag_string: Tag parsing logic
            functions.handler_sqllite.op_label_get_all: Label retrieval (cached)
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

            self.app.log(
                f"Fetching items for user {user_id}, project {project_id}, "
                + f"period: {start_date_str} to {end_date_str}"
            )

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

            results = dbh.execute_query(query, [user_id, project_id, start_date_str, end_date_str])
            dbh.close()

            self.app.log(
                f"Found {len(results)} items for user {user_id} in period {start_date_str} to {end_date_str}"
            )

            # Get all labels for the project to build label map
            labels = dbh.op_label_get_all(project_id=project_id, use_cache=True)
            label_map = {l["label_id"]: l for l in labels}

            # Get ProjectComposer instance for tag parsing
            from fiwa_cli.functions.project_composer import ProjectComposer

            project_style = self.app.app_state.get("project_style", "default")

            try:
                pc = ProjectComposer.create(
                    compose_type=project_style, dbh=dbh, project_id=project_id, users=[]
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
                    parsed_tags = {"c": "", "t": "", "b": "", "m": "", "s": []}

                # Extract main label for display
                main_label = parsed_tags.get("m", "")

                items.append(
                    {
                        "item_id": row[0],
                        "name": row[1],
                        "bought_date": row[2],
                        "price": row[3],
                        "currency": row[4],
                        "price_final": row[5],
                        "currency_final": row[6],
                        "bought_by_id": row[7],
                        "bought_by_username": row[8],
                        "bought_by_first_name": row[9],
                        "bought_by_last_name": row[10],
                        "note": row[11],
                        "exchange_rate": row[12],
                        "exchange_rate_date": row[13],
                        "tags": tags_raw,
                        "parsed_tags": parsed_tags,
                        "label_m": main_label,  # Main label for display
                    }
                )

            return items

        except Exception as e:
            self.app.notify("Error fetching items for user")
            self.app.log(f"Error fetching user items: {e}")
            return []

    def refresh_data(self) -> None:
        """Refresh all data tables with current period data without recreating UI.

        This method is called when the period selection changes (week/month
        navigation) to reload transaction data from the database while
        preserving the existing tab structure and user's current tab selection.

        The refresh process:
            1. Updates period display widget with new date range
            2. Retrieves all project users with Read permission
            3. Gets ProjectComposer instance for label mapping
            4. For each user:
               - Queries transactions for current period
               - Splits into fixed/variable vs. daily
               - Clears existing table rows
               - Populates tables with new data
               - Recalculates revenue/expense totals
               - Updates summary displays

        Side Effects:
            - Updates #date-selection-display widget
            - Clears all DataTable rows (both tables per user)
            - Queries database for new transactions
            - Repopulates tables with filtered data
            - Updates total revenue/expense Static widgets
            - Logs refresh operation and any errors

        Performance:
            - More efficient than recreating entire form (compose())
            - Only updates data, preserves widget hierarchy
            - Single database query per user
            - Maintains user's current tab selection

        Example:
            After period change::

                >>> # User viewing Week 10 Cost Overview
                >>> # User changes WeekMonthWidget to Week 11
                >>> # ReportsScreen calls refresh_data()
                >>> # Period display updates: "2026 Week 11: 2026-03-10 to 2026-03-16"
                >>> # All user tabs reload with Week 11 transactions
                >>> # Batman tab: Fixed table shows 3 items, Daily shows 12 items
                >>> # Totals recalculated: Revenue $5000, Expenses $1200

        Error Handling:
            - If project_id invalid: Returns early without error
            - If database query fails: Logs error, continues with other users
            - If table not found: Logs warning, skips that table
            - If label parsing fails: Uses empty labels, continues

        Note:
            The method preserves the user's current tab selection - if they're
            viewing Superman's tab when the period changes, they'll still be
            on Superman's tab after the refresh.

            Only users with Read permission (100000+) have their data refreshed.

            The date range display is updated first so users immediately see
            which period they're viewing.

        See Also:
            _get_user_items: Queries transactions for a specific user
            _get_project_users: Gets users with appropriate permissions
            reports.ReportsScreen._refresh_current_report: Calls this method
        """
        try:
            # Update the date selection display
            period_start = self.app.app_state.get("current_period_start")
            period_end = self.app.app_state.get("current_period_end")
            period_label = self.app.app_state.get("current_period_label", "")
            period_type = self.app.app_state.get("current_period_type", "week")

            if period_start and period_end:
                date_range_text = f"𝌌 {period_label}: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
            else:
                date_range_text = "𝌌 All expenses"

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
                    compose_type=project_style, dbh=dbh, project_id=project_id, users=[]
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
                if user_permission[0] != "1":
                    self.app.log(
                        f"Skipping user {user['username']} in refresh - no Read permission"
                    )
                    continue

                # Fetch items for this user
                items = self._get_user_items(user["user_id"], project_id)

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
                        date_str = (
                            str(item["bought_date"]).split()[0] if item["bought_date"] else ""
                        )
                        label_display = item.get("label_m", "")
                        multiplier = item.get("multiplier", 1)

                        table_fv.add_row(
                            item["name"],
                            f"{item['price']:.2f}",
                            item["currency"],
                            f"{item['price_final']:.2f}",
                            date_str,
                            f"{item['bought_by_last_name']}",
                            label_display,
                            key=f"fv-{item['item_id']}",
                        )

                        amount = item["price_final"] * multiplier
                        total_fv += amount

                        if multiplier == 1:
                            revenue_fv += item["price_final"]
                        else:
                            expenses_fv += item["price_final"]

                        if item["bought_by_id"] == user["user_id"]:
                            bought_by_self_fv += item["price_final"]
                        else:
                            buyer_name = (
                                f"{item['bought_by_first_name']} {item['bought_by_last_name']}"
                            )
                            bought_by_others_fv[buyer_name] = (
                                bought_by_others_fv.get(buyer_name, 0.0) + item["price_final"]
                            )

                    # Sort by date
                    if table_fv.columns:
                        date_column_key = list(table_fv.columns.keys())[4]
                        table_fv.sort(date_column_key, reverse=True)

                    # Update fixed/variable total
                    total_fv_widget = self.query_one(f"#total-fv-{user['user_id']}", Static)
                    total_fv_widget.update(
                        f"Total Fixed/Variable: {expenses_fv:.2f} {currency_main} | +{revenue_fv:.2f} {currency_main} ▷ {total_fv:.2f} {currency_main}"
                    )

                except Exception as e:
                    self.app.log(
                        f"Could not refresh fixed/variable table for user {user['user_id']}: {e}"
                    )

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
                        date_str = (
                            str(item["bought_date"]).split()[0] if item["bought_date"] else ""
                        )
                        label_display = item.get("label_m", "")
                        multiplier = item.get("multiplier", 1)

                        table_daily.add_row(
                            item["name"],
                            f"{item['price']:.2f}",
                            item["currency"],
                            f"{item['price_final']:.2f}",
                            date_str,
                            f"{item['bought_by_last_name']}",
                            label_display,
                            key=f"daily-{item['item_id']}",
                        )

                        amount = item["price_final"] * multiplier
                        total_daily += amount

                        if multiplier == 1:
                            revenue_daily += item["price_final"]
                        else:
                            expenses_daily += item["price_final"]

                        if item["bought_by_id"] == user["user_id"]:
                            bought_by_self_daily += item["price_final"]
                        else:
                            buyer_name = (
                                f"{item['bought_by_first_name']} {item['bought_by_last_name']}"
                            )
                            bought_by_others_daily[buyer_name] = (
                                bought_by_others_daily.get(buyer_name, 0.0) + item["price_final"]
                            )

                    # Sort by date
                    if table_daily.columns:
                        date_column_key = list(table_daily.columns.keys())[4]
                        table_daily.sort(date_column_key, reverse=True)

                    # Update daily total
                    total_daily_widget = self.query_one(f"#total-daily-{user['user_id']}", Static)
                    total_daily_widget.update(
                        f"Total Daily: {expenses_daily:.2f} {currency_main} | +{revenue_daily:.2f} {currency_main} ▷ {total_daily:.2f} {currency_main}"
                    )

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
                        breakdown_lines.append(
                            f"  ↘ Expenses: {total_expenses:.2f} {currency_main}"
                        )
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
                        for buyer, amount in sorted(
                            all_bought_by_others.items(), key=lambda x: x[1], reverse=True
                        ):
                            breakdown_lines.append(
                                f"  • From {buyer}: {amount:.2f} {currency_main}"
                            )

                    total_widget = self.query_one(f"#total-user-{user['user_id']}", Static)
                    total_widget.update("\n".join(breakdown_lines))

                    self.app.log(
                        f"Refreshed tables for user {user['user_id']}: {len(items_fv)} fixed/variable, {len(items_daily)} daily"
                    )

                except Exception as e:
                    self.app.log(f"Could not update summary for user {user['user_id']}: {e}")

        except Exception as e:
            self.app.log(f"Error refreshing data tables: {e}")
