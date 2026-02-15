# settings_label_page.py
from textual.widgets import Static, Button, Input, DataTable
from textual.containers import Vertical, Horizontal, Container
from textual.app import ComposeResult
from textual.message import Message
from textual.screen import ModalScreen
from datetime import datetime

class StatusSelectorModal(ModalScreen):
    """Modal screen for selecting label status."""

    DEFAULT_CSS = """
    StatusSelectorModal {
        align: center middle;
    }
    
    StatusSelectorModal > Vertical {
        width: 50;
        height: auto;
        background: $surface;
        border: solid $accent;
        padding: 2;
    }
    
    StatusSelectorModal .modal-title {
        text-style: bold;
        text-align: center;
        padding: 0 0 2 0;
        color: $accent;
    }
    
    StatusSelectorModal .current-status {
        text-align: center;
        padding: 1 0;
        margin: 0 0 2 0;
        background: $panel;
    }
    
    StatusSelectorModal Button {
        width: 100%;
        height: 3;
        margin: 1 0;
    }
    
    StatusSelectorModal #status-active {
        background: green;
        color: white;
    }
    
    StatusSelectorModal #status-active:hover {
        background: darkgreen;
    }
    
    StatusSelectorModal #status-deactivated {
        background: orange;
        color: white;
    }
    
    StatusSelectorModal #status-deactivated:hover {
        background: darkorange;
    }
    
    StatusSelectorModal #status-deleted {
        background: red;
        color: white;
    }
    
    StatusSelectorModal #status-deleted:hover {
        background: darkred;
    }
    
    StatusSelectorModal #status-cancel {
        background: $panel;
        border: solid $accent;
    }
    """

    def __init__(self, label_name: str, current_status: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_name = label_name
        self.current_status = current_status

    def compose(self) -> ComposeResult:
        status_text = {0: "Mark for Deletion", 1: "Deactivated", 2: "Active"}
        current = status_text.get(self.current_status, "Unknown")

        with Vertical():
            yield Static("Change Label Status", classes="modal-title")
            yield Static(f"Label: {self.label_name}", classes="current-status")
            yield Static(f"Current Status: {current}", classes="current-status")

            yield Button("✓ Active", id="status-active")
            yield Button("◐ Deactivated", id="status-deactivated")
            yield Button("✗ Mark for Deletion", id="status-deleted")
            yield Button("Cancel", id="status-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press and return the selected status."""
        if event.button.id == "status-active":
            self.dismiss(2)  # Active
        elif event.button.id == "status-deactivated":
            self.dismiss(1)  # Deactivated
        elif event.button.id == "status-deleted":
            self.dismiss(0)  # Mark for Deletion
        elif event.button.id == "status-cancel":
            self.dismiss(None)  # No change

class LabelManagementForm(Vertical):
    """Widget for managing labels in a project."""

    DEFAULT_CSS = """
    LabelManagementForm {
        width: 100%;
        height: auto;
    }

    LabelManagementForm .form-title {
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
        background: $accent;
        color: $text;
    }
    
    LabelManagementForm .section-header {
        text-style: bold;
        padding: 0 0;
        color: $accent;
    }

    LabelManagementForm DataTable {
        height: 5;
        margin: 0 0 1 0;
    }
    
    LabelManagementForm .add-label-section {
        background: $panel;
        padding: 2;
        margin: 0 0 2 0;
        border: solid $accent;
    }

    LabelManagementForm .form-label {
        padding: 1 0 0 0;
        text-style: bold;
    }

    LabelManagementForm Input {
        margin: 0 0 1 0;
        width: 100%;
    }

    LabelManagementForm Button {
        min-width: 20;
        height: 3;
        margin: 1;
    }
    
    LabelManagementForm #action-buttons {
        height: auto;
        margin-top: 2;
        width: 100%;
        align: center middle;
        layout: horizontal;
    }
    
    LabelManagementForm #new-label-button {
        background: blue;
        color: white;
        width: 25;
        height: 3;
    }

    LabelManagementForm #new-label-button:hover {
        background: darkblue;
    }
    
    LabelManagementForm #save-button {
        background: green;
        color: white;
        width: 25;
        height: 3;
    }

    LabelManagementForm #save-button:hover {
        background: darkgreen;
    }
    
    LabelManagementForm #cancel-button {
        background: red;
        color: white;
        width: 25;
        height: 3;
    }

    LabelManagementForm #cancel-button:hover {
        background: darkred;
    }
    
    LabelManagementForm #add-label-button {
        background: blue;
        color: white;
        width: 25;
        height: 3;
        margin-top: 1;
    }

    LabelManagementForm #add-label-button:hover {
        background: darkblue;
    }
    
    LabelManagementForm .label-type-buttons {
        height: 5;
        width: 100%;
        margin: 1 0;
    }
    
    LabelManagementForm .label-type-button {
        width: 15;
        height: 3;
        margin: 0 1;
        background: $panel;
        border: solid $accent;
    }
    
    LabelManagementForm .label-type-button-selected {
        background: $success;
        color: $text;
        border: solid $success;
    }
    """

    class LabelsModified(Message):
        """Message sent when labels are modified."""
        def __init__(self, changes_summary: dict) -> None:
            self.changes_summary = changes_summary
            super().__init__()

    class NewLabelRequested(Message):
        """Message sent when user wants to create a new label."""
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._labels = []
        self._modified_labels = {}  # Track changes: {label_id: updated_data}
        self._new_labels = []  # Track new labels to be created
        self._deleted_labels = set()  # Track labels marked for deletion
        self._selected_label_type = 1  # Default to level 1

    def compose(self) -> ComposeResult:
        yield Static("Label Management", classes="form-title")

        # Get current project info
        project_id = self.app.app_state.get("project_id", 0)
        project_names = self.app.app_state.get("project_names", [])
        project_ids = self.app.app_state.get("project_ids", [])

        # Find project name
        project_name = "Unknown Project"
        if project_id in project_ids:
            idx = project_ids.index(project_id)
            project_name = project_names[idx]

        yield Static(f"Project: {project_name}", classes="section-header")

        # Load labels from database
        if project_id > 0:
            try:
                dbh = self.app._config["dbh"]
                self._labels = dbh.op_label_get_all(project_id)
            except Exception as e:
                self.app.log(f"Error loading labels: {e}")
                self._labels = []

        # Labels table
        yield Static("Existing Labels:", classes="section-header")
        table = DataTable(id="labels-table")
        table.add_columns("Name", "Description", "Status", "Type", "Actions")

        # Populate table with existing labels
        # Note: We store label_id as the row key for internal reference
        for label in self._labels:
            status_text = self._get_status_text(label['label_status'])
            label_type_text = self._get_action_type(label['label_type'])
            table.add_row(
                label['name'],
                label['description'][:30] + "..." if len(label['description']) > 30 else label['description'],
                status_text,
                label_type_text,
                "Edit",
                key=f"label-id-{label['label_id']}"  # Store label_id in the row key
            )

        yield table

        # Action buttons
        with Horizontal(id="action-buttons"):
            yield Button("New Label", id="new-label-button")
            yield Button("Save All Changes", id="save-button")
            yield Button("Cancel", id="cancel-button")

    def _get_status_text(self, status: int) -> str:
        """Convert status code to text."""
        status_map = {
            0: "Mark for Deletion",
            1: "Deactivated",
            2: "Active"
        }
        return status_map.get(status, "Unknown")

    def _get_action_type(self, status: int) -> str:
        """Convert status code to text."""
        status_map = {
            0: "Action",
            1: "Account",
            2: "Label"
        }
        return status_map.get(status, "Unknown")

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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-button":
            self.app.notify("Label management cancelled", severity="info")
        elif event.button.id == "new-label-button":
            # Post message to switch to CreateLabelForm
            self.post_message(self.NewLabelRequested())
        elif event.button.id == "add-label-button":
            self._add_new_label()
        elif event.button.id == "save-button":
            self._save_all_changes()
        elif event.button.id and event.button.id.startswith("label-type-"):
            # Handle label type button clicks
            label_type = int(event.button.id.split("-")[-1])
            self._set_label_type(label_type)

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Handle cell selection in the table."""
        table = event.data_table
        row_index = event.coordinate.row
        col_index = event.coordinate.column

        # Get the row key from the event's cell_key
        row_key = event.cell_key.row_key

        # Extract label_id from the row key (format: "label-id-{id}")
        try:
            label_id_str = str(row_key.value).replace("label-id-", "")
            label_id = int(label_id_str)
        except (ValueError, AttributeError) as e:
            self.app.notify(f"Cannot extract label ID: {e}", severity="error")
            return

        # Get the row data
        try:
            row = table.get_row_at(row_index)
            label_name = str(row[0])  # Name is now the first column
            current_status_text = str(row[2])  # Status is now the third column (index 2)
        except Exception as e:
            self.app.notify(f"Invalid row index: {e}", severity="error")
            return

        self.app.log(f"Cell clicked - Row: {row_index}, Column: {col_index}, Label ID: {label_id}, Label: {label_name}")

        # If "Status" column clicked, show status selector modal
        if col_index == 2:  # Status column (Name, Description, Status, Type, Actions) - now index 2
            # Find the label to get current status
            label = next((l for l in self._labels if l['label_id'] == label_id), None)
            if not label:
                self.app.notify(f"Label ID {label_id} not found", severity="error")
                return

            current_status = label.get('label_status', 2)

            # Show modal and handle the result
            self.app.push_screen(
                StatusSelectorModal(label_name, current_status),
                callback=lambda new_status: self._handle_status_change(
                    label_id, new_status, table, row_index
                )
            )


    def _handle_status_change(self, label_id: int, new_status: int | None, table: DataTable, row_index: int) -> None:
        """Handle the status change from the modal."""
        if new_status is None:
            # User cancelled
            return

        # Find the label
        label = next((l for l in self._labels if l['label_id'] == label_id), None)
        if not label:
            self.app.notify(f"Label ID {label_id} not found", severity="error")
            return

        current_status = label.get('label_status', 2)

        # No change
        if new_status == current_status:
            self.app.notify("Status unchanged", severity="info")
            return

        current_status_text = self._get_status_text(current_status)
        new_status_text = self._get_status_text(new_status)

        self.app.log(f"Changing status for '{label['name']}' (ID: {label_id}): {current_status_text} -> {new_status_text}")

        # Update in memory
        label['label_status'] = new_status

        # Track the modification
        if label_id not in self._modified_labels:
            self._modified_labels[label_id] = {}
        self._modified_labels[label_id]['label_status'] = new_status

        # Update table display - update the specific cell in the Status column
        # Move cursor to the cell and update it
        from textual.coordinate import Coordinate
        table.move_cursor(row=row_index, column=2)  # Status is now column 2 (Name, Description, Status, Type, Actions)
        table.update_cell_at(Coordinate(row_index, 2), new_status_text)

        self.app.notify(
            f"'{label['name']}' status: {current_status_text} → {new_status_text}",
            severity="information"
        )

    def _save_all_changes(self) -> None:
        """Save all changes to the database."""
        project_id = self.app.app_state.get("project_id", 0)

        if project_id <= 0:
            self.app.notify("No project selected", severity="error")
            return

        dbh = self.app._config["dbh"]
        changes_count = 0
        errors = []

        try:
            # Create new labels
            for new_label in self._new_labels:
                try:
                    label_id = dbh.op_label_create(new_label, project_id)
                    changes_count += 1
                    self.app.log(f"Created label: {new_label['name']} (ID: {label_id})")
                except Exception as e:
                    errors.append(f"Failed to create '{new_label['name']}': {str(e)}")

            # Update modified labels
            for label_id, changes in self._modified_labels.items():
                try:
                    dbh.op_label_update(label_id, changes)
                    changes_count += 1
                    self.app.log(f"Updated label ID: {label_id}")
                except Exception as e:
                    errors.append(f"Failed to update label {label_id}: {str(e)}")

            # Show results
            if errors:
                self.app.notify(f"Saved with errors: {len(errors)} failed", severity="warning")
                for error in errors:
                    self.app.log(error)
            else:
                self.app.notify(f"Successfully saved {changes_count} changes!", severity="information")

            # Post message about changes
            summary = {
                'total_changes': changes_count,
                'new_labels': len(self._new_labels),
                'modified_labels': len(self._modified_labels),
                'errors': len(errors)
            }
            self.post_message(self.LabelsModified(summary))

        except Exception as e:
            self.app.notify(f"Error saving changes: {str(e)}", severity="error")
