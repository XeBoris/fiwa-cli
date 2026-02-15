# settings_label_page.py
from textual.widgets import Static, Button, Input, DataTable
from textual.containers import Vertical, Horizontal, Container
from textual.app import ComposeResult
from textual.message import Message
from datetime import datetime

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
        table.add_columns("ID", "Name", "Description", "Status", "Type", "Actions")

        # Populate table with existing labels
        for label in self._labels:
            status_text = self._get_status_text(label['label_status'])
            label_type_text = self._get_action_type(label['label_type'])
            table.add_row(
                str(label['label_id']),
                label['name'],
                label['description'][:30] + "..." if len(label['description']) > 30 else label['description'],
                status_text,
                label_type_text,
                "Edit"
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
        row_key = event.coordinate.row
        col_key = event.coordinate.column

        # Get the row data
        row = table.get_row(row_key)
        label_id_str = str(row[0])

        # If "Actions" column clicked, toggle status
        if col_key == 4:  # Actions column
            # Check if this is a NEW label or existing label
            if label_id_str == "NEW":
                self.app.notify("Cannot toggle status of unsaved labels. Save first.", severity="warning")
                return

            try:
                label_id = int(label_id_str)
                self._toggle_label_status(label_id, table, row_key)
            except ValueError:
                self.app.notify("Invalid label ID", severity="error")
                return

    def _toggle_label_status(self, label_id: int, table: DataTable, row_key) -> None:
        """Cycle through label statuses: Active -> Deactivated -> Marked for Deletion -> Active."""
        # Find the label
        label = next((l for l in self._labels if l['label_id'] == label_id), None)
        if not label:
            return

        # Get current status
        current_status = label.get('label_status', 2)

        # Cycle: 2 (Active) -> 1 (Deactivated) -> 0 (Deleted) -> 2 (Active)
        if current_status == 2:
            new_status = 1
        elif current_status == 1:
            new_status = 0
        else:
            new_status = 2

        # Update in memory
        label['label_status'] = new_status

        # Track the modification
        if label_id not in self._modified_labels:
            self._modified_labels[label_id] = {}
        self._modified_labels[label_id]['label_status'] = new_status

        # Update table display
        row = list(table.get_row(row_key))
        row[3] = self._get_status_text(new_status)
        table.remove_row(row_key)
        table.add_row(row[0], row[1], row[2], row[3], row[4], key=row_key)

        self.app.notify(f"Label status changed to: {self._get_status_text(new_status)}", severity="info")

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
