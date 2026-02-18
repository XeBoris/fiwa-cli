"""Inputs screen - add transactions and items."""
from textual.containers import Vertical, Horizontal, ScrollableContainer, Grid
from textual.widgets import Static, Button, Select
from textual.app import ComposeResult
from components import FiwaHeader
import datetime
# from components.item_input_form import ItemInputForm

from .base import ReactiveScreen

from .inputs_insert_expense import CreateExpenseForm


class InputsScreen(ReactiveScreen):
    """Inputs screen - add transactions and items."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mounted = False

        # Initialize period tracking
        self._current_period_type = "week"  # "week" or "month"
        self._current_year = datetime.date.today().year
        self._current_week = datetime.date.today().isocalendar()[1]
        self._current_month = datetime.date.today().month

    DEFAULT_CSS = """
    InputsScreen {
        layout: vertical;
    }

    InputsScreen #inputs-body {
        layout: horizontal;
        height: 1fr;
    }

    InputsScreen #inputs-sidebar {
        width: 27;
        background: $panel;
        border-right: solid $accent;
        padding: 1;
        scrollbar-size: 4 1;
    }

    InputsScreen .menu-section {
        text-style: bold;
        padding: 1 0 0 0;
        color: $accent;
    }
    
    InputsScreen #inputs-sidebar.new-item-button {
        width: 40%;
        margin: 0 0 1 0;
        border: none
    }
    
    InputsScreen #period-select {
        max-height: 3;
        align: center middle;
        width: 18;
        margin: 0 0;
    }
    
    InputsScreen #period-navigation {
        grid-size: 2 2;
        grid-gutter: 0;
        width: 20;
        height: 10;
        margin: 0 0;
    }
    
    InputsScreen #period-navigation Button {
        width: 100%;
        height: 1;
        content-align: center middle;
        text-align: center;
        border: none;
    }
    
    InputsScreen #period-navigation Static {
        width: 100%;
        height: 1;
        content-align: center middle;
        text-align: center;
    }
    
    InputsScreen #period-year {
        text-style: bold;
    }
    
    InputsScreen #period-value {
        text-style: bold;
        color: $accent;
    }
    
    # InputsScreen #inputs-sidebar Button {
    #     width: 13;
    #     height: 3;
    #     margin: 0 0 1 0;
    #     padding: 0 1;
    #     border: solid $accent;
    # }

    InputsScreen #inputs-content-area {
        width: 1fr;
        height: 100%;
        padding: 0;
        scrollbar-size: 3 1;
    }

    InputsScreen #inputs-title {
        text-style: bold;
        padding: 0 0 2 0;
        text-align: center;
    }

    SettingsScreen #back-button {
        margin-top: 1;
        width: 100%;
    }
    
    # InputsScreen .info-panel {
    #     background: $panel;
    #     padding: 2;
    #     margin: 0 0 2 0;
    #     border: solid $accent;
    # }
    # 
    # InputsScreen .info-row {
    #     padding: 0 0 1 0;
    # }
    """

    def compose(self) -> ComposeResult:
        yield FiwaHeader(
            user=self.app.app_state["user_name"],
            projects=self.app.app_state["project_names"],
            project_id=self.app.app_state["project_id"],
            project_ids=self.app.app_state["project_ids"]
        )
        yield Static("Inputs - Add Transaction", id="inputs-title")

        with Horizontal(id="inputs-body"):
            # Left sidebar with quick actions
            with ScrollableContainer(id="inputs-sidebar"):
                yield Static("Quick Actions", classes="menu-section")
                yield Button("New", id="new-item-button", variant="success", compact=True, flat=True)
                yield Button("Edit", id="edit-item-button", variant="success", compact=True, flat=True)

                yield Static("Period", classes="menu-section")
                yield Select(options=[
                            ("Week", "week"),
                            ("Month", "month")
                                    ],
                             value="week",
                             id="period-select",
                             allow_blank=False
                            )

                # Period navigation grid: [← | Year | Week/Month | →]
                with Grid(id="period-navigation"):
                    yield Button("◀", id="period-prev", variant="default", compact=True, flat=True)
                    yield Button("▶", id="period-next", variant="default", compact=True, flat=True)
                    yield Static(str(self._current_year), id="period-year")
                    yield Static(f"W{self._current_week}", id="period-value")



                # yield Button("View Recent", id="view-recent-button", variant="default")
                # yield Button("Import CSV", id="import-csv-button", variant="default")
                #
                # yield Static("Statistics", classes="menu-section")
                # yield Static("[bold]Today:[/bold] 0 items", classes="info-row")
                # yield Static("[bold]This Month:[/bold] 0 items", classes="info-row")

                # Always show Back button
                yield Button("Back", id="back-button", variant="primary")

            # Right content area with input form
            with ScrollableContainer(id="inputs-content-area"):
                # Info panel showing current context
                project_id = self.app.app_state.get("project_id", 0)
                project_names = self.app.app_state.get("project_names", [])
                project_ids = self.app.app_state.get("project_ids", [])
                user_name = self.app.app_state.get("user_name", "Guest")
                user_id = self.app.app_state.get("user_id", -1)

                # Find project name
                project_name = "No Project"
                if project_id in project_ids:
                    idx = project_ids.index(project_id)
                    project_name = project_names[idx]

                with Vertical(classes="info-panel", id="info-panel"):
                    yield Static(f"[bold]Current Project:[/bold] {project_name}", classes="info-row")
                    yield Static(f"[bold]User:[/bold] {user_name} (ID: {user_id})", classes="info-row")
                    yield Static(f"[bold]Project ID:[/bold] {project_id}", classes="info-row")




                # yield ItemInputForm()

    def _get_info_panel(self):
        """Generate info panel showing current context."""
        project_id = self.app.app_state.get("project_id", 0)
        project_names = self.app.app_state.get("project_names", [])
        project_ids = self.app.app_state.get("project_ids", [])
        user_name = self.app.app_state.get("user_name", "Guest")
        user_id = self.app.app_state.get("user_id", -1)

        # Find project name
        project_name = "No Project"
        if project_id in project_ids:
            idx = project_ids.index(project_id)
            project_name = project_names[idx]

        # Return a Vertical with children via compose pattern
        panel = Vertical(classes="info-panel")
        # Compose the children directly
        panel._children = [
            Static(f"[bold]Current Project:[/bold] {project_name}", classes="info-row"),
            Static(f"[bold]User:[/bold] {user_name} (ID: {user_id})", classes="info-row"),
            Static(f"[bold]Project ID:[/bold] {project_id}", classes="info-row")
        ]
        return panel

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        super().on_mount()
        self._mounted = True
        self.app.log("InputsScreen mounted")

        # Initialize app_state with current period
        self._update_app_state_period()

        # Pre-fill user IDs if logged in
        user_id = self.app.app_state.get("user_id", -1)
        if user_id > 0:
            try:
                form = self.query_one(ItemInputForm)
                form.query_one("#item-bought-by").value = str(user_id)
                form.query_one("#item-bought-for").value = str(user_id)
                form.query_one("#item-added-by").value = str(user_id)
            except Exception as e:
                self.app.log(f"Could not pre-fill user IDs: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "back-button":
            self._return_to_main_screen()
        elif event.button.id == "new-item-button":
            # self._clear_and_refocus()
            self.show_create_input_form()
        elif event.button.id == "period-prev":
            self._navigate_period(-1)
        elif event.button.id == "period-next":
            self._navigate_period(1)
        elif event.button.id == "view-recent-button":
            self.app.notify("View Recent - Coming soon!", severity="info")
        elif event.button.id == "import-csv-button":
            self.app.notify("Import CSV - Coming soon!", severity="info")

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle period selection changes."""
        if event.select.id == "period-select":
            self._current_period_type = event.value
            self.app.log(f"Period type changed to: {self._current_period_type}")

            # Update the display
            self._update_period_display()

            # Update app_state
            self._update_app_state_period()

    def show_create_input_form(self) -> None:
        """Show the create project form in the content area."""
        content_area = self.query_one("#inputs-content-area", ScrollableContainer)
        content_area.remove_children()
        content_area.mount(CreateExpenseForm())


    # def on_item_input_form_item_created(self, message: ItemInputForm.ItemCreated) -> None:
    #     """Handle the ItemCreated message from ItemInputForm."""
    #     if message.item_data is None:
    #         # User cancelled
    #         self.app.notify("Item entry cancelled", severity="info")
    #         return
    #
    #     try:
    #         # Get current project and user info
    #         project_id = self.app.app_state.get("project_id", 0)
    #         user_id = self.app.app_state.get("user_id", -1)
    #
    #         if project_id <= 0:
    #             self.app.notify("No project selected", severity="error")
    #             return
    #
    #         if user_id <= 0:
    #             self.app.notify("Not logged in", severity="error")
    #             return
    #
    #         # Add project_id to item data
    #         message.item_data['project_id'] = project_id
    #
    #         # TODO: Save to database
    #         # dbh = self.app._config["dbh"]
    #         # item_id = dbh.op_item_create(message.item_data)
    #
    #         # For now, just show success message
    #         self.app.notify(
    #             f"Item '{message.item_data['name']}' created! (DB save pending)",
    #             severity="success"
    #         )
    #
    #         # Log the item data for debugging
    #         self.app.log(f"Item data: {message.item_data}")
    #
    #         # Clear the form for next entry
    #         form = self.query_one(ItemInputForm)
    #         form._clear_form()
    #
    #     except Exception as e:
    #         self.app.notify(f"Error creating item: {str(e)}", severity="error")
    #         self.app.log(f"Error in on_item_input_form_item_created: {e}")
    #
    # def _clear_and_refocus(self) -> None:
    #     """Clear the form and refocus for new entry."""
    #     try:
    #         form = self.query_one(ItemInputForm)
    #         form._clear_form()
    #     except Exception as e:
    #         self.app.log(f"Error clearing form: {e}")

    def _return_to_main_screen(self) -> None:
        """Pop all screens to return to the main screen."""
        try:
            while len(self.app.screen_stack) > 1:
                self.app.pop_screen()
        except Exception as e:
            self.app.log(f"Error returning to main screen: {e}")

    def _navigate_period(self, direction: int) -> None:
        """
        Navigate to the previous or next period.

        Args:
            direction: -1 for previous, 1 for next
        """
        if self._current_period_type == "week":
            self._current_week += direction

            # Handle year boundaries for weeks
            if self._current_week < 1:
                self._current_year -= 1
                # Get last week of previous year
                last_day = datetime.date(self._current_year, 12, 31)
                self._current_week = last_day.isocalendar()[1]
            elif self._current_week > 52:
                # Check if week 53 exists for this year
                last_day = datetime.date(self._current_year, 12, 31)
                max_week = last_day.isocalendar()[1]
                if self._current_week > max_week:
                    self._current_year += 1
                    self._current_week = 1
        else:  # month
            self._current_month += direction

            # Handle year boundaries for months
            if self._current_month < 1:
                self._current_year -= 1
                self._current_month = 12
            elif self._current_month > 12:
                self._current_year += 1
                self._current_month = 1

        # Update the display
        self._update_period_display()

        # Update app_state
        self._update_app_state_period()

        # Log the change
        if self._current_period_type == "week":
            self.app.log(f"Navigated to: {self._current_year} Week {self._current_week}")
        else:
            self.app.log(f"Navigated to: {self._current_year} Month {self._current_month}")

    def _update_period_display(self) -> None:
        """Update the period display widgets with current values."""
        try:
            # Update year
            year_widget = self.query_one("#period-year", Static)
            year_widget.update(str(self._current_year))

            # Update week/month value
            value_widget = self.query_one("#period-value", Static)
            if self._current_period_type == "week":
                value_widget.update(f"W{self._current_week}")
            else:
                # Format month with leading zero
                value_widget.update(f"M{self._current_month:02d}")
        except Exception as e:
            self.app.log(f"Error updating period display: {e}")

    def _update_app_state_period(self) -> None:
        """Update app_state with current period selection."""
        try:
            # Calculate date range based on period type
            if self._current_period_type == "week":
                # Calculate week boundaries
                from functions.compute_time import TimeClass
                tc = TimeClass()
                week_info = tc.cmp_week_by_number(self._current_year, self._current_week)

                period_start = week_info['week_beg']
                period_end = week_info['week_end']
                period_label = f"{self._current_year} Week {self._current_week}"
            else:  # month
                # Calculate month boundaries
                from functions.compute_time import TimeClass
                tc = TimeClass()
                month_info = tc.cmp_month_by_number(self._current_year, self._current_month)

                period_start = month_info['month_beg']
                period_end = month_info['month_end']
                period_label = f"{self._current_year} {month_info['month_name']}"

            # Update app_state with period information
            self.app.app_state["current_period_type"] = self._current_period_type
            self.app.app_state["current_period_year"] = self._current_year
            self.app.app_state["current_period_week"] = self._current_week
            self.app.app_state["current_period_month"] = self._current_month
            self.app.app_state["current_period_start"] = period_start
            self.app.app_state["current_period_end"] = period_end
            self.app.app_state["current_period_label"] = period_label

            self.app.log(f"Updated app_state period: {period_label} ({period_start} to {period_end})")

        except Exception as e:
            self.app.log(f"Error updating app_state period: {e}")

    def update_displays(self) -> None:
        """Update displays when app_state changes."""
        try:
            # Update header
            header = self.query_one(FiwaHeader)
            header.user = self.app.app_state["user_name"]
            header.projects = self.app.app_state["project_names"]
            header.project_id = self.app.app_state["project_id"]
            header.project_ids = self.app.app_state["project_ids"]
        except Exception as e:
            self.app.log(f"Error updating header: {e}")

        # Update info panel if project or user changed
        try:
            # Get current values
            project_id = self.app.app_state.get("project_id", 0)
            project_names = self.app.app_state.get("project_names", [])
            project_ids = self.app.app_state.get("project_ids", [])
            user_name = self.app.app_state.get("user_name", "Guest")
            user_id = self.app.app_state.get("user_id", -1)

            # Find project name
            project_name = "No Project"
            if project_id in project_ids:
                idx = project_ids.index(project_id)
                project_name = project_names[idx]

            # Update the info panel directly
            info_panel = self.query_one("#info-panel", Vertical)
            info_statics = list(info_panel.query(Static))

            if len(info_statics) >= 3:
                info_statics[0].update(f"[bold]Current Project:[/bold] {project_name}")
                info_statics[1].update(f"[bold]User:[/bold] {user_name} (ID: {user_id})")
                info_statics[2].update(f"[bold]Project ID:[/bold] {project_id}")
        except Exception as e:
            self.app.log(f"Error updating info panel: {e}")
