"""Inputs screen - add transactions and items."""
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.widgets import Static, Button
from textual.app import ComposeResult
from components import FiwaHeader
# from components.item_input_form import ItemInputForm

from .base import ReactiveScreen

from .inputs_insert_expense import CreateExpenseForm

class InputsScreen(ReactiveScreen):
    """Inputs screen - add transactions and items."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mounted = False

    DEFAULT_CSS = """
    InputsScreen {
        layout: vertical;
    }

    InputsScreen #inputs-body {
        layout: horizontal;
        height: 1fr;
    }

    InputsScreen #inputs-sidebar {
        width: auto;
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

    InputsScreen #inputs-sidebar Button {
        width: 100%;
        height: 3;
        margin: 0 0 1 0;
        padding: 0 1;
        border: solid $accent;
    }

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
                yield Button("New Item", id="new-item-button", variant="success")
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
        elif event.button.id == "view-recent-button":
            self.app.notify("View Recent - Coming soon!", severity="info")
        elif event.button.id == "import-csv-button":
            self.app.notify("Import CSV - Coming soon!", severity="info")

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

