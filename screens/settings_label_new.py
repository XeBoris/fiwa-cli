# settings_label_new.py
from textual.widgets import Static, Button, Input, Switch, Placeholder, Select
from textual.containers import Vertical, Horizontal, ScrollableContainer, Grid
from textual.app import ComposeResult
from textual.message import Message

from textual import on

class CreateLabelForm(Vertical):
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
    
    CreateLabelForm #action-grid {
        grid-size: 3 3;
        grid-columns: 1fr 1fr 1fr;
        grid-gutter: 1 1;
        grid-rows: 3 3 3;
        align: center middle;
        margin-top: 0;
        margin-left: 1;
        margin-right: 1;
        width: 100%;
        height: 12;
    }
    
    CreateLabelForm #new-label-name {
        align: left middle;
        width: 100%;
        height: 2;
    }
    CreateLabelForm #new-label-description {
        width: 100%;
        height: 2;
    }
    
    CreateLabelForm #label-type-select {
        width: 100%;
        height: 2;
    }
    CreateLabelForm #new-label-activated {
        height: 100%;
        align: right middle;
        margin: 0 0 0 0;
    }
    
    
    CreateLabelForm #grid-label-create {
        grid-size: 2 1;
        grid-columns: 1fr 1fr;
        grid-gutter: 1;
        height: 10;
        margin-top: 0;
        width: 100%;
    }
    
    CreateLabelForm #label-create-button {
        background: green;
        color: white;
        width: 20;
        height: 3;
        margin: 0 1;
    }

    CreateLabelForm #label-create-button:hover {
        background: darkgreen;
    }

    CreateLabelForm #label-reset-button {
        background: red;
        color: white;
        width: 20;
        height: 3;
        margin: 0 1;
    }

    CreateLabelForm #label-reset-button:hover {
        background: darkred;
    }
    
    
    

    
    # CreateLabelForm .label-type-buttons {
    #     height: auto;
    #     width: 100%;
    #     margin: 1 0 2 0;
    # }
    # 
    # CreateLabelForm .label-type-button {
    #     width: 15;
    #     height: 3;
    #     margin: 0 1;
    #     background: $panel;
    #     border: solid $accent;
    # }
    # 
    # CreateLabelForm .label-type-button-selected {
    #     background: $success;
    #     color: $text;
    #     border: solid $success;
    # }
    # 
    # CreateLabelForm #action-buttons {
    #     height: auto;
    #     margin-top: 2;
    #     width: 100%;
    # }
    # 
    # CreateLabelForm #create-button {
    #     background: green;
    #     color: white;
    #     width: 20;
    #     height: 3;
    #     margin: 0 1;
    # }
    # 
    # CreateLabelForm #create-button:hover {
    #     background: darkgreen;
    # }
    # 
    # CreateLabelForm #cancel-button {
    #     background: red;
    #     color: white;
    #     width: 20;
    #     height: 3;
    #     margin: 0 1;
    # }
    # 
    # CreateLabelForm #cancel-button:hover {
    #     background: darkred;
    # }
    """

    class LabelCreated(Message):
        """Message sent when a label is created."""
        def __init__(self, label_data: dict) -> None:
            self.label_data = label_data
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_label_type = 2  # Default to label type: Label

    def compose(self) -> ComposeResult:
        yield Static("Create New Label", classes="form-title")

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
