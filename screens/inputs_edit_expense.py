"""Edit Expense View - Tabbed interface showing items per user."""
from textual.containers import VerticalScroll, Vertical
from textual.widgets import Static, TabbedContent, TabPane, DataTable
from textual.app import ComposeResult


class EditExpenseView(VerticalScroll):
    """View for editing expenses with tabs per user showing their items."""

    DEFAULT_CSS = """
    EditExpenseView {
        width: 100%;
        height: 100%;
    }

    EditExpenseView .form-title {
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
        background: $accent;
        color: $text;
    }

    EditExpenseView TabbedContent {
        height: auto;
        margin: 1 0;
    }

    EditExpenseView TabPane {
        padding: 1;
    }

    EditExpenseView DataTable {
        height: 25;
        max-height: 25;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        yield Static("Edit Expenses", classes="form-title")

        # Get project and users
        project_id = self.app.app_state.get("project_id", 0)
        project_users = self._get_project_users(project_id)

        # Create tabbed content with one tab per user
        with TabbedContent():
            for user in project_users:
                with TabPane(f"{user['first_name']} {user['last_name']}", id=f"tab-user-{user['user_id']}"):
                    # Create DataTable for this user's items
                    table = DataTable(id=f"items-table-{user['user_id']}")
                    table.add_columns("Item Name", "Final Price", "Currency", "Purchase Date")
                    table.cursor_type = "row"

                    # Fetch items for this user
                    items = self._get_user_items(user['user_id'], project_id)
                    for item in items:
                        # Extract date only (remove time if present)
                        date_str = str(item['bought_date']).split()[0] if item['bought_date'] else ""

                        table.add_row(
                            item['name'],
                            f"{item['price_final']:.2f}",
                            item['currency'],
                            date_str
                        )

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
        try:
            dbh = self.app._config.get("dbh")
            if not dbh:
                return []

            # Get period boundaries from app_state
            period_start = self.app.app_state.get("current_period_start")
            period_end = self.app.app_state.get("current_period_end")

            # Query ALL items for this user in the current period (no LIMIT)
            dbh.load()
            query = f"""
                SELECT name, bought_date, price, currency, price_final
                FROM p{dbh._db_salt}_items
                WHERE bought_by_id = ? 
                AND project_id = ?
                AND bought_date BETWEEN ? AND ?
                ORDER BY bought_date DESC
            """

            results = dbh.execute_query(query, [
                user_id,
                project_id,
                period_start.strftime("%Y-%m-%d") if period_start else "2000-01-01",
                period_end.strftime("%Y-%m-%d") if period_end else "2099-12-31"
            ])
            dbh.close()

            items = []
            for row in results:
                items.append({
                    'name': row[0],
                    'bought_date': row[1],
                    'price': row[2],
                    'currency': row[3],
                    'price_final': row[4]
                })

            return items

        except Exception as e:
            self.app.log(f"Error fetching user items: {e}")
            return []

    def refresh_tables(self) -> None:
        """Refresh all DataTables with items for the current period."""
        try:
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

                        table.add_row(
                            item['name'],
                            f"{item['price_final']:.2f}",
                            item['currency'],
                            date_str
                        )

                    self.app.log(f"Refreshed table for user {user['user_id']}: {len(items)} items")

                except Exception as e:
                    self.app.log(f"Could not refresh table for user {user['user_id']}: {e}")

        except Exception as e:
            self.app.log(f"Error refreshing data tables: {e}")
