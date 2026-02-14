# settings_label_new.py
from textual.widgets import Static, Button, Input
from textual.containers import Vertical, Horizontal, ScrollableContainer
from textual.app import ComposeResult
from textual.message import Message

class CreateLabelForm(ScrollableContainer):
    """Widget for creating a new label."""

    DEFAULT_CSS = """
    CreateLabelForm {
        width: 100%;
        height: 100%;
    }

    CreateLabelForm .form-title {
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
        background: $accent;
        color: $text;
    }

    CreateLabelForm .form-label {
        padding: 1 0 0 0;
        text-style: bold;
    }

    CreateLabelForm Input {
        margin: 0 0 1 0;
        width: 100%;
    }

    CreateLabelForm .label-type-buttons {
        height: auto;
        width: 100%;
        margin: 1 0 2 0;
    }

    CreateLabelForm .label-type-button {
        width: 15;
        height: 3;
        margin: 0 1;
        background: $panel;
        border: solid $accent;
    }

    CreateLabelForm .label-type-button-selected {
        background: $success;
        color: $text;
        border: solid $success;
    }

    CreateLabelForm #action-buttons {
        height: auto;
        margin-top: 2;
        width: 100%;
    }

    CreateLabelForm #create-button {
        background: green;
        color: white;
        width: 20;
        height: 3;
        margin: 0 1;
    }

    CreateLabelForm #create-button:hover {
        background: darkgreen;
    }

    CreateLabelForm #cancel-button {
        background: red;
        color: white;
        width: 20;
        height: 3;
        margin: 0 1;
    }

    CreateLabelForm #cancel-button:hover {
        background: darkred;
    }
    """

    class LabelCreated(Message):
        """Message sent when a label is created."""
        def __init__(self, label_data: dict) -> None:
            self.label_data = label_data
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_label_type = 1  # Default to level 1

    def compose(self) -> ComposeResult:
        yield Static("Create New Label", classes="form-title")

        yield Static("Label Name *", classes="form-label")
        yield Input(placeholder="Enter label name", id="new-label-name")

        yield Static("Description", classes="form-label")
        yield Input(placeholder="Enter description", id="new-label-description")

        yield Static("Label Type *", classes="form-label")
        # with Horizontal(classes="label-type-buttons"):
        #     yield Button("Level 0", id="label-type-0", classes="label-type-button")
        #     yield Button("Level 1", id="label-type-1", classes="label-type-button label-type-button-selected")
        #     yield Button("Level 2", id="label-type-2", classes="label-type-button")

        with Horizontal(id="action-buttons"):
            yield Button("Create", id="create-button")
            yield Button("Cancel", id="cancel-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-button":
            self.app.notify("Label creation cancelled", severity="info")
        elif event.button.id == "create-button":
            self._create_label()
        elif event.button.id and event.button.id.startswith("label-type-"):
            # Handle label type button clicks
            label_type = int(event.button.id.split("-")[-1])
            self._set_label_type(label_type)

    def _set_label_type(self, label_type: int) -> None:
        """Set the selected label type and update button styling."""
        self._selected_label_type = label_type
        self.app.log(f"Label type selected: {label_type}")

        # Update button styling to show selection
        for i in range(3):
            try:
                button = self.query_one(f"#label-type-{i}", Button)
                if i == label_type:
                    button.add_class("label-type-button-selected")
                else:
                    button.remove_class("label-type-button-selected")
            except Exception as e:
                self.app.log(f"Error updating button style: {e}")

        self.app.notify(f"Label type set to: Level {label_type}", severity="info")

    def _create_label(self) -> None:
        """Validate and create the label."""
        project_id = self.app.app_state.get("project_id", 0)

        if project_id <= 0:
            self.app.notify("No project selected", severity="error")
            return

        try:
            name = self.query_one("#new-label-name", Input).value.strip()
            description = self.query_one("#new-label-description", Input).value.strip()
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
            'label_status': 2,  # Active
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
