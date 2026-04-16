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
from fiwa_cli.functions.project_composer import ProjectComposer
from fiwa_cli.components.spending_tracker import SpendingTrackerWidget

class AdvReportForm(Vertical):
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

            >>> form = AdvReportForm()
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
        """Compose the Advanced Report interface with spending tracker heatmap.

        Builds a monthly spending tracker visualization (GitHub-style heatmap)
        for each user showing daily transaction patterns.

        Yields:
            Static: Report title
            Static: Current period display (must be monthly)
            TabbedContent: Container with one tab per project user
                TabPane (per user):
                    - SpendingTrackerWidget: 7×5 calendar heatmap
                    - Summary: Monthly totals and statistics

        Note:
            This report ONLY works with monthly period selection.
            Week selection will show a message to switch to monthly view.
            Only users with Read permission (100000+) get tabs.
        """
        yield Static("Advanced Cost Report - Monthly Spending Tracker", classes="report-title")

        # Display current date selection - MUST BE MONTHLY
        period_start = self.app.app_state.get("current_period_start")
        period_end = self.app.app_state.get("current_period_end")
        period_label = self.app.app_state.get("current_period_label", "")
        period_type = self.app.app_state.get("current_period_type", "month")

        if period_start and period_end:
            date_range_text = f"𝌌 {period_label}: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
        else:
            date_range_text = "𝌌 Select a period"

        self.app.log(f"AdvReportForm compose - Period: {date_range_text}, Type: {period_type}")
        yield Static(date_range_text, id="date-selection-display", classes="date-info")

        # Check if period type is monthly (required for this report)
        if period_type != "month":
            yield Static(
                "⚠️  This report requires MONTHLY view.\n\nPlease select 'Monthly' in the period picker.",
                classes="warning-message"
            )
            return

        # Get project and users
        project_id = self.app.app_state.get("project_id", 0)
        project_users = self._get_project_users(project_id)

        # for user in project_users:
        #     items = self._get_user_items(user["user_id"], project_id)
        #
        #     self.app.app_state["stats"].set_items(items=items)
        #     df = self.app.app_state["stats"]._items_df
        #     self.app.file_log.info(f"list of {len(df)} parsed to df for user {user["user_id"]}")
        #     self.app.file_log.info(df.head(3))
        #     self.app.file_log.info(df.columns)
        #     k = self.app.app_state["stats"].aggregate_daily_df()
        #     self.app.file_log.info(str(k))

        # Get main currency for column header
        currency_main = self.app.app_state.get("current_project_currency_main", "USD")
        project_style = self.app.app_state.get("project_style", "default")

        # Get ProjectComposer instance
        dbh = self.app._config.get("dbh")

        labels = dbh.op_label_get_all(project_id=project_id, use_cache=True)
        label_map = {l["label_id"]: l for l in labels}

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
                for user in project_users:
                    # Check if user has at least Read permission
                    user_permission = user.get("project_perm_model", "000000")

                    if user_permission[0] != "1" or len(user_permission) < 6:
                        self.app.log(f"Skipping user {user.get('username')} - no Read permission")
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
                            items_daily = pc.get_transaction_split(items, keys=["daily"])
                            items_fv = pc.get_transaction_split(items, keys=["fixed", "variable"])

                            items_parsed = pc.parse_item_list(items, label_map=label_map)
                        else:
                            items_daily = []
                            items_fv = []


                        # --- Spending Tracker Heatmap (GitHub-style) ---
                        if period_start and period_end:
                            # Build daily aggregation data for the tracker
                            stats = self.app.app_state.get("stats")
                            if stats:
                                stats.set_items(items=items_parsed)
                                daily_agg_data = stats.aggregate_daily_df()
                                period_totals, account_summary, fixed_variable_details, home_daily_details, travel_daily_details = stats.aggr_period()
                            else:
                                daily_agg_data = []
                                period_totals = {}
                                account_summary = []
                            
                            self.app.file_log.info(str(daily_agg_data))
                            self.app.file_log.info(f"Period totals: {str(period_totals)}")
                            
                            # Create horizontal container for tracker and account summary
                            with Horizontal(classes="tracker-summary-container"):
                                # Left side: Spending Tracker
                                with Vertical(classes="tracker-section"):
                                    yield Static("📊 Daily Spending Pattern", classes="section-subtitle")
                                    tracker = SpendingTrackerWidget(
                                        daily_data=daily_agg_data,
                                        period_start=period_start,
                                        period_end=period_end
                                    )
                                    yield tracker
                                
                                # Vertical separator
                                # yield Vertical(classes="vertical-separator")
                                
                                # Right side: Account Summary
                                with Vertical(classes="account-summary-section"):
                                    yield Static("💳 Account Summary", classes="section-subtitle")
                                    
                                    # Build account summary display
                                    if account_summary:
                                        summary_text = []
                                        for entry in account_summary:
                                            label = entry.get("label", "Unknown")
                                            value = entry.get("value", 0.0)
                                            
                                            # Format with appropriate symbols
                                            if label == "Savings (EoM)":
                                                symbol = "💰"
                                                color_class = "summary-savings"
                                            elif label in ["Daily Home", "Daily Travel"]:
                                                symbol = "🏠" if "Home" in label else "✈️"
                                                color_class = "summary-daily"
                                            else:
                                                symbol = "√"
                                                color_class = "summary-account"
                                            
                                            # Format value with sign
                                            value_str = f"{value:+.2f}" if value != 0 else "0.00"
                                            summary_text.append(f"{symbol} {label}: {value_str} {currency_main}")
                                        
                                        yield Static(
                                            "\n".join(summary_text),
                                            classes="account-summary-content",
                                            id=f"account-summary-{user['user_id']}"
                                        )
                                    else:
                                        yield Static(
                                            "No account data available",
                                            classes="account-summary-empty"
                                        )
                                    
                                    # Add period totals breakdown
                                    if period_totals:
                                        yield Static("", classes="summary-spacer")
                                        yield Static("📈 Period Breakdown", classes="section-subtitle-small")
                                        
                                        totals_text = []
                                        total_fv = period_totals.get("total_fv", 0.0)
                                        total_daily = period_totals.get("total_daily", 0.0)
                                        total_daily_home = period_totals.get("total_daily_home", 0.0)
                                        total_daily_trav = period_totals.get("total_daily_trav", 0.0)
                                        
                                        totals_text.append(f"Fixed/Variable: {total_fv:+.2f} {currency_main}")
                                        totals_text.append(f"Daily Total: {total_daily:+.2f} {currency_main}")
                                        totals_text.append(f"  • Home: {total_daily_home:+.2f} {currency_main}")
                                        totals_text.append(f"  • Travel: {total_daily_trav:+.2f} {currency_main}")
                                        
                                        yield Static(
                                            "\n".join(totals_text),
                                            classes="period-totals-content"
                                        )

                        # Summary display
                        yield Static("Spending Summary", classes="table-section-title")

                        summary_lines = [
                            f"",
                            f"Daily Transactions: {len(items_daily)}",
                            f"Fixed/Variable Transactions: {len(items_fv)}",
                        ]

                        yield Static(
                            "\n".join(summary_lines),
                            classes="user-total",
                            id=f"total-user-{user['user_id']}",
                        )


    def on_mount(self) -> None:
        """Load CSS stylesheet when the report form is mounted.

        Side Effects:
            - Loads screens_reports_adv.tcss stylesheet
            - Loads components_spending_tracker.tcss stylesheet
            - Logs mount event to file_log

        Note:
            This is called automatically by Textual after compose()
            creates all widgets but before they're displayed.
        """

        load_dynamic_css(self, "screens_reports_adv.tcss")
        load_dynamic_css(self, "components_spending_tracker.tcss")

        try:
            self.app.file_log.info("AdvReportForm mounted - Cost Overview report ready with spending tracker")
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

            # Use new op_item_get() function instead of manual query
            raw_items = dbh.op_item_get(
                user_id=user_id,
                project_id=project_id,
                start_date=start_date_str,
                end_date=end_date_str,
                include_user_info=True
            )

            self.app.file_log.info(
                f"Found {len(raw_items)} items for user {user_id} in period {start_date_str} to {end_date_str}"
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

            # Use bulk parsing instead of manual loop
            if pc:
                items = pc.parse_item_list(raw_items=raw_items, label_map=label_map)
            else:
                # Fallback: add empty parsed_tags to each item
                items = []
                for raw_item in raw_items:
                    item = raw_item.copy()
                    item["parsed_tags"] = {"c": "", "t": "", "b": "", "m": "", "s": []}
                    item["label_m"] = ""
                    items.append(item)

            return items

        except Exception as e:
            self.app.notify(f"Error fetching items: {str(e)}", severity="error")
            self.app.log(f"ERROR in _get_user_items: {e}")
            try:
                self.app.file_log.error(f"Error fetching user items for user_id={user_id}, project_id={project_id}: {e}")
                import traceback
                self.app.file_log.error(traceback.format_exc())
            except Exception:
                pass
            return []

    def refresh_data(self) -> None:
        """Refresh spending tracker and account summary with current period data.

        This method is called when the period selection changes to reload
        transaction data from the database while preserving the existing
        tab structure and user's current tab selection.

        The refresh process for AdvReportForm:
            1. Updates period display widget with new date range
            2. Retrieves all project users with Read permission
            3. Gets ProjectComposer instance for label mapping
            4. For each user:
               - Queries transactions for current period
               - Splits into daily vs. fixed/variable
               - Updates SpendingTrackerWidget with new heatmap data
               - Recalculates account summary using aggr_period()
               - Updates account summary and period breakdown displays
               - Updates monthly summary totals

        Side Effects:
            - Updates #date-selection-display widget
            - Updates SpendingTrackerWidget heatmap
            - Updates #account-summary-{user_id} Static widgets
            - Updates #total-user-{user_id} summary widgets
            - Queries database for new transactions
            - Logs refresh operation and any errors

        Performance:
            - More efficient than recreating entire form (compose())
            - Only updates data, preserves widget hierarchy
            - Single database query per user
            - Maintains user's current tab selection

        Example:
            After period change::

                >>> # User viewing March 2026 Summary
                >>> # User changes WeekMonthWidget to April 2026
                >>> # ReportsScreen calls refresh_data()
                >>> # Period display updates: "2026 Month 04: 2026-03-25 to 2026-04-24"
                >>> # SpendingTrackerWidget refreshes with April data
                >>> # Account summary recalculates for April
                >>> # Monthly totals update

        Error Handling:
            - If project_id invalid: Returns early without error
            - If database query fails: Logs error, continues with other users
            - If widgets not found: Logs warning, skips that update
            - If label parsing fails: Uses empty labels, continues

        Note:
            This method is specifically for AdvReportForm which shows:
                - SpendingTrackerWidget (GitHub-style heatmap)
                - Account Summary (breakdown by account)
                - Period Breakdown (fixed/variable and daily totals)

            Unlike BasicReportForm, this doesn't update DataTables.
            It updates the spending tracker visualization and summary displays.

            Only users with Read permission (100000+) have their data refreshed.

        See Also:
            _get_user_items: Queries transactions for a specific user
            _get_project_users: Gets users with appropriate permissions
            reports.ReportsScreen._refresh_current_report: Calls this method
            components.spending_tracker.SpendingTrackerWidget.update_data: Updates heatmap
        """
        try:
            # Update the date selection display
            period_start = self.app.app_state.get("current_period_start")
            period_end = self.app.app_state.get("current_period_end")
            period_label = self.app.app_state.get("current_period_label", "")
            period_type = self.app.app_state.get("current_period_type", "month")

            if period_start and period_end:
                date_range_text = f"𝌌 {period_label}: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
            else:
                date_range_text = "𝌌 All expenses"

            self.app.log(f"AdvReportForm refresh_data - Period: {date_range_text}")

            # Update the Static widget
            try:
                date_display = self.query_one("#date-selection-display", Static)
                date_display.update(date_range_text)
            except Exception as e:
                self.app.log(f"Could not update date display: {e}")

            # Check if we're in monthly view (required for AdvReportForm)
            if period_type != "month":
                self.app.log("AdvReportForm requires monthly view - skipping refresh")
                return

            project_id = self.app.app_state.get("project_id", 0)
            if project_id <= 0:
                self.app.log("Invalid project_id - skipping refresh")
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

            # Update each user's spending tracker and account summary
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

                user_id = user["user_id"]
                self.app.log(f"Refreshing AdvReport for user {user_id}")

                # Fetch items for this user
                items = self._get_user_items(user_id, project_id)

                # Apply transformations
                if pc:
                    items = pc.get_balance_split(items)
                    items_parsed = pc.parse_item_list(items, label_map={})
                    items_daily = pc.get_transaction_split(items_parsed, keys=["daily"])
                    items_fv = pc.get_transaction_split(items_parsed, keys=["fixed", "variable"])
                else:
                    items_parsed = items
                    items_daily = []
                    items_fv = []

                # --- Refresh Spending Tracker & Account Summary ---
                try:
                    # Get stats instance and compute aggregations
                    stats = self.app.app_state.get("stats")
                    if stats and items_parsed:
                        stats.set_items(items=items_parsed)
                        daily_agg_data = stats.aggregate_daily_df()
                        period_totals, account_summary, fixed_variable_details, home_daily_details, travel_daily_details = stats.aggr_period()

                        # Update SpendingTrackerWidget
                        try:
                            # Find the tracker for this specific user's tab
                            tab_pane = self.query_one(f"#tab-user-{user_id}", TabPane)
                            tracker_widgets = list(tab_pane.query(SpendingTrackerWidget))
                            
                            if tracker_widgets:
                                tracker_widgets[0].update_data(
                                    daily_data=daily_agg_data,
                                    period_start=period_start,
                                    period_end=period_end
                                )
                                self.app.log(f"Updated spending tracker for user {user_id}")
                        except Exception as e:
                            self.app.log(f"Could not update spending tracker for user {user_id}: {e}")

                        # Update Account Summary
                        try:
                            account_summary_widget = self.query_one(f"#account-summary-{user_id}", Static)
                            
                            if account_summary:
                                summary_text = []
                                for entry in account_summary:
                                    label = entry.get("label", "Unknown")
                                    value = entry.get("value", 0.0)
                                    
                                    # Format with appropriate symbols
                                    if label == "Savings (EoM)":
                                        symbol = "💰"
                                    elif label in ["Daily Home", "Daily Travel"]:
                                        symbol = "📍" if "Home" in label else "✈️"
                                    else:
                                        symbol = "🏦"
                                    
                                    # Format value with sign
                                    value_str = f"{value:+.2f}" if value != 0 else "0.00"
                                    summary_text.append(f"{symbol} {label}: {value_str} {currency_main}")
                                
                                account_summary_widget.update("\n".join(summary_text))
                                self.app.log(f"Updated account summary for user {user_id}")
                        except Exception as e:
                            self.app.log(f"Could not update account summary for user {user_id}: {e}")

                        # Update Monthly Summary totals
                        try:
                            total_daily = sum(item.get("price_final", 0) * item.get("multiplier", -1) for item in items_daily)
                            total_fv = sum(item.get("price_final", 0) * item.get("multiplier", -1) for item in items_fv)
                            total_all = total_daily + total_fv

                            revenue_daily = sum(item.get("price_final", 0) for item in items_daily if item.get("multiplier", -1) == 1)
                            revenue_fv = sum(item.get("price_final", 0) for item in items_fv if item.get("multiplier", -1) == 1)
                            total_revenue = revenue_daily + revenue_fv

                            expenses_daily = sum(item.get("price_final", 0) for item in items_daily if item.get("multiplier", -1) == -1)
                            expenses_fv = sum(item.get("price_final", 0) for item in items_fv if item.get("multiplier", -1) == -1)
                            total_expenses = expenses_daily + expenses_fv

                            summary_lines = [
                                f"",
                                f"",
                                f"Daily Transactions: {len(items_daily)}",
                                f"Fixed/Variable Transactions: {len(items_fv)}",
                            ]

                            total_widget = self.query_one(f"#total-user-{user_id}", Static)
                            total_widget.update("\n".join(summary_lines))
                            
                            self.app.log(f"Updated monthly summary for user {user_id}")
                        except Exception as e:
                            self.app.log(f"Could not update monthly summary for user {user_id}: {e}")

                except Exception as e:
                    self.app.log(f"Error processing stats for user {user_id}: {e}")

            self.app.log("AdvReportForm refresh_data completed")

        except Exception as e:
            self.app.log(f"Error refreshing AdvReportForm: {e}")
            try:
                self.app.file_log.error(f"Error refreshing AdvReportForm: {e}")
                import traceback
                self.app.file_log.error(traceback.format_exc())
            except Exception:
                pass
