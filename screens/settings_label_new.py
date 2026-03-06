# settings_label_new.py
from textual.widgets import Static, Button, Input, Switch, Placeholder, Select
from textual.containers import Vertical, Horizontal, ScrollableContainer, Grid
from textual.app import ComposeResult
from textual.message import Message
from textual import on

from functions.loader import load_dynamic_css

class CreateLabelForm(Vertical):
    """Widget for creating a new label."""

    # DEFAULT_CSS = """
    #
    # """

    class LabelCreated(Message):
        """Message sent when a label is created."""
        def __init__(self, label_data: dict) -> None:
            self.label_data = label_data
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_label_type = 2  # Default to label type: Label

    def on_mount(self) -> None:
        load_dynamic_css(self, "screens_settings_label_new.tcss")

    def compose(self) -> ComposeResult:

        project_id = self.app.app_state.get("project_id", 0)
        user_id = self.app.app_state.get("user_id", -1)

        # Get project details from database
        project_info = None
        if project_id and user_id > 0:
            dbh = self.app._config["dbh"]
            all_projects = dbh.op_project_get_info(user_id)
            self.app.log(f"Retrieved {len(all_projects)} projects for user {user_id}")
            project_info = next((p for p in all_projects if p["project_id"] == project_id), None)
            if project_info:
                self.app.log(f"Found project: {project_info.get('project_name', 'Unknown')}")
            else:
                self.app.log(f"No project found with id {project_id}")

        yield Static("Create New Label", classes="form-title")

        # Show current project name as header
        if project_info:
            current_name = project_info.get("project_name", "Unknown Project")
            yield Static(f"Currently Editing: {current_name}", classes="current-project-header")
        else:
            yield Static("No Project Loaded", classes="current-project-header")

        with ScrollableContainer(id="form-content"):
            with Grid(id="action-grid"):
                # row 1
                yield Static("Label Name *", classes="form-label")
                yield Static("Description", classes="form-label")
                yield Static("Action", classes="form-label")

                # row 2
                yield Input(placeholder="Enter label name",
                            id="new-label-name",
                            compact=True)
                yield Input(placeholder="Enter description", id="new-label-description",
                            compact=True)
                yield Select(options=[("Action", 0), ("Account", 1), ("Label", 2)],
                             id="label-type-select",
                             value=self._selected_label_type,
                             compact=True)

                # row 3
                yield Static()
                yield Static("Label Status: ", classes="form-label")
                yield Switch(id="new-label-activated", value=True)

            with Grid(id="grid-label-create"):
                yield Button("Create", id="label-create-button")
                yield Button("Reset", id="label-reset-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "label-reset-button":
            self._reset_inputs()
        elif event.button.id == "label-create-button":
            self._create_label()

    def _reset_inputs(self) -> None:
        """Reset all input fields to their initial state."""
        try:
            # Clear label name input
            self.query_one("#new-label-name", Input).value = ""

            # Clear description input
            self.query_one("#new-label-description", Input).value = ""

            # Reset action select to default (Account = "1")
            self.query_one("#label-type-select", Select).value = "1"
            self._selected_label_type = 1

            # Reset switch to off (inactive)
            self.query_one("#new-label-activated", Switch).value = False

            self.app.notify("Form reset successfully", severity="info")

        except Exception as e:
            self.app.log(f"Error resetting inputs: {e}")
            self.app.notify("Error resetting form fields", severity="error")

    def _create_label(self) -> None:
        """Validate and create the label."""
        project_id = self.app.app_state.get("project_id", 0)

        if project_id <= 0:
            self.app.notify("No project selected", severity="error")
            return

        try:
            name = self.query_one("#new-label-name", Input).value.strip()
            description = self.query_one("#new-label-description", Input).value.strip()
            switch_value = self.query_one("#new-label-activated", Switch).value
            select_label = self.query_one("#label-type-select", Select)
            self._selected_label_type = int(select_label.value)
            if switch_value is True:
                label_status = 2  # Active
            else:
                label_status = 1  # Inactive
        except Exception as e:
            self.app.log(f"Error getting input values: {e}")
            self.app.notify("Error reading input fields", severity="error")
            return

        if not name:
            self.app.notify("Label name is required", severity="error")
            return

        # Create label data
        label_data = {
            'name': name,
            'description': description,
            'label_status': label_status,  # Now correctly uses the integer value
            'label_type': self._selected_label_type,
            'composite': []
        }

        # Save to database
        try:
            dbh = self.app._config["dbh"]
            label_id = dbh.op_label_create(label_data, project_id)

            self.app.log(f"Created label: {name} (ID: {label_id})")
            self.app.notify(f"Label '{name}' created successfully!", severity="information")

            # Add label_id to the data
            label_data['label_id'] = label_id

            # Post message
            self.post_message(self.LabelCreated(label_data))

        except ValueError as e:
            self.app.notify(f"Failed to create label: {str(e)}", severity="error")
        except Exception as e:
            self.app.notify(f"Error creating label: {str(e)}", severity="error")
