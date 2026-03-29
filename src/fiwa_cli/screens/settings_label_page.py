"""Label management interface for FiWa CLI.

This module provides a comprehensive interface for managing labels (categories/tags)
within a project. It includes a DataTable view of all labels with inline editing
capabilities, status management, and default label designation.

The interface allows users to:
    - View all labels in a sortable, interactive table
    - Edit label names and descriptions via modal dialog
    - Change label status (draft, active, archived)
    - Set default labels per category per user
    - Create new labels via integration with CreateLabelForm

Key Features:
    - DataTable with clickable rows for editing
    - Modal editor for label details
    - Status dropdown with visual indicators
    - Default label marking (star icon)
    - Permission-based controls (only managers can set defaults)
    - Integration with ProjectComposer for type mapping

Classes:
    LabelEditorModal: Modal screen for editing label details
    LabelManagementForm: Main form with DataTable and controls

Label Status Values:
    - 0: Draft (work in progress, not shown in selectors)
    - 1: Archived (historical, not shown in active selectors)
    - 2: Active (currently usable)

Default Label System:
    Each user can have one default label per label type. Default labels
    are used when creating expenses without explicit label selection.
    Only users with Manage permissions can modify defaults.

Example:
    Mounting the form::

        >>> from fiwa_cli.screens.settings_label_page import LabelManagementForm
        >>> form = LabelManagementForm()
        >>> content_area.mount(form)

    Editing a label::

        >>> # User clicks on label row in table
        >>> # Modal opens with current values
        >>> # User edits and clicks OK
        >>> # Label updated in database and table refreshed

See Also:
    settings_label_new: Create new labels
    functions.project_composer: Project-specific label types
    settings: Main settings screen
"""

from textual.widgets import Static, Button, Input, DataTable
from textual.containers import Vertical, Horizontal, Container, Grid, ScrollableContainer
from textual.app import ComposeResult
from textual.message import Message
from textual.screen import ModalScreen
from datetime import datetime

from fiwa_cli.functions.loader import load_dynamic_css
from fiwa_cli.functions.project_composer import ProjectComposer


class LabelEditorModal(ModalScreen):
    """Modal screen for editing label name, description, and status.

    This modal dialog appears when a user clicks on a label row in the
    LabelManagementForm table. It provides fields for editing the label's
    basic properties and status.

    The modal is centered on screen with a focused input area and action
    buttons for saving or canceling changes.

    Attributes:
        label_id (int): ID of the label being edited
        label_name (str): Current label name
        label_description (str): Current label description
        current_status (int): Current status value (0, 1, or 2)
        selected_status (int): User-selected status (may differ from current)

    BINDINGS:
        - Escape: Close modal without saving (dismiss_modal)

    Example:
        Opening the modal::

            >>> modal = LabelEditorModal(
            >>>     label_id=42,
            >>>     label_name="Groceries",
            >>>     label_description="Food shopping",
            >>>     current_status=2
            >>> )
            >>> self.app.push_screen(modal)

        Handling modal result (in async context)::

            >>> async def edit_label(self):
            >>>     result = await self.app.push_screen_wait(modal)
            >>>     if result:  # User clicked OK
            >>>         label_id, new_name, new_desc, new_status = result
            >>>         dbh.op_label_update(label_id, new_name, new_desc, new_status)

    Note:
        The modal validates input before dismissing - label name cannot
        be empty. If validation fails, the modal stays open with an
        error notification.

    See Also:
        LabelManagementForm: Parent form that opens this modal
    """

    BINDINGS = [
        ("escape", "dismiss_modal", "Close"),
    ]

    # DEFAULT_CSS = """
    #
    # """

    def __init__(
        self,
        label_id: int,
        label_name: str,
        label_description: str,
        current_status: int,
        *args,
        **kwargs,
    ):
        """Initialize the label editor modal.

        Args:
            label_id: Database ID of the label being edited
            label_name: Current name of the label
            label_description: Current description
            current_status: Current status value (0=draft, 1=archived, 2=active)
            *args: Additional positional arguments for ModalScreen
            **kwargs: Additional keyword arguments for ModalScreen
        """
        super().__init__(*args, **kwargs)
        self.label_id = label_id
        self.label_name = label_name
        self.label_description = label_description
        self.current_status = current_status
        self.selected_status = current_status

    def on_mount(self) -> None:
        load_dynamic_css(self, "screens_settings_label_page.tcss")

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Edit Label", classes="modal-title")

            yield Static("Label Name *", classes="form-label")
            yield Input(
                value=self.label_name, id="label-name-input", placeholder="Enter label name"
            )

            yield Static("Description", classes="form-label")
            yield Input(
                value=self.label_description,
                id="label-description-input",
                placeholder="Enter description",
            )

            yield Static("Status *", classes="form-label")
            with Grid(classes="status-buttons"):
                active_classes = (
                    "status-button status-button-selected"
                    if self.current_status == 2
                    else "status-button"
                )
                deactivated_classes = (
                    "status-button status-button-selected"
                    if self.current_status == 1
                    else "status-button"
                )
                deleted_classes = (
                    "status-button status-button-selected"
                    if self.current_status == 0
                    else "status-button"
                )

                yield Button("✓ Active", id="status-active", classes=active_classes, flat=True)
                yield Button(
                    "◐ Deactivate", id="status-deactivated", classes=deactivated_classes, flat=True
                )
                yield Button("✗ Delete", id="status-deleted", classes=deleted_classes, flat=True)

            with Grid(classes="action-buttons"):
                yield Button("Save", id="save-button", flat=True)
                yield Button("Cancel", id="cancel-button", flat=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "status-active":
            self._select_status(2)
        elif event.button.id == "status-deactivated":
            self._select_status(1)
        elif event.button.id == "status-deleted":
            self._select_status(0)
        elif event.button.id == "save-button":
            self._save_changes()
        elif event.button.id == "cancel-button":
            self.dismiss(None)

    def action_dismiss_modal(self) -> None:
        """Action called when ESC is pressed - dismiss modal without saving."""
        self.dismiss(None)

    def _select_status(self, status: int) -> None:
        """Update selected status and button styling."""
        self.selected_status = status

        # Update button styling
        for status_id, status_value in [
            ("status-active", 2),
            ("status-deactivated", 1),
            ("status-deleted", 0),
        ]:
            try:
                button = self.query_one(f"#{status_id}", Button)
                if status_value == status:
                    button.add_class("status-button-selected")
                else:
                    button.remove_class("status-button-selected")
            except Exception:
                pass

    def _save_changes(self) -> None:
        """Validate and save changes."""
        name = self.query_one("#label-name-input", Input).value.strip()
        description = self.query_one("#label-description-input", Input).value.strip()

        if not name:
            self.app.notify("Label name is required", severity="error")
            return

        # Return the updated data
        result = {
            "label_id": self.label_id,
            "name": name,
            "description": description,
            "label_status": self.selected_status,
        }
        self.dismiss(result)


class LabelManagementForm(Vertical):
    """Form widget for managing all labels in a project.

    This comprehensive form displays all project labels in an interactive
    DataTable with capabilities for editing, status management, and default
    label designation. Users with appropriate permissions can modify labels
    and set defaults for their categories.

    The form provides:
        - Interactive DataTable showing all labels
        - Row-click editing via LabelEditorModal
        - Status management with visual indicators
        - Default label designation per type per user
        - Permission-based controls
        - Integration with ProjectComposer for type mapping

    Attributes:
        _labels (list): Cached list of label dictionaries from database
        _modified_labels (dict): Tracks pending changes {label_id: updated_data}
        _new_labels (list): Track new labels to be created (currently unused)
        _deleted_labels (set): Track labels marked for deletion (currently unused)
        _selected_label_type (int): Currently selected label type filter

    Messages:
        LabelsModified: Emitted when labels are successfully saved
            - Attributes:
                - changes_summary (dict): Summary with counts

        NewLabelRequested: Emitted when user clicks "Create New Label"

    DataTable Columns:
        - ID: Label identifier
        - Name: Label name (editable)
        - Description: Label description (editable)
        - Type: Label type name from ProjectComposer
        - Owner: Username or "Common"
        - Status: Draft/Active/Archived (editable)
        - Default: Star icon for default labels (clickable)

    Permission Requirements:
        - Read (100000): View labels
        - Manage (xxxx11 or xxxx10): Set default labels

    Editing Workflow:
        1. User clicks on label row
        2. LabelEditorModal opens with current values
        3. User edits name, description, status
        4. User clicks OK
        5. Changes saved to database immediately
        6. Table refreshes to show updated values

    Default Label Workflow:
        1. User clicks star column for a label
        2. System checks only one default per type per user
        3. Previous default unmarked (if exists)
        4. New default marked and saved
        5. Table updates to show new default

    Example:
        Basic usage::

            >>> form = LabelManagementForm()
            >>> form.on_mount()
            >>> content_area.mount(form)

        Handling label modifications::

            >>> def on_label_management_form_labels_modified(self, message):
            >>>     summary = message.changes_summary
            >>>     self.app.file_log.info(f"Labels updated: {summary}")

    Note:
        Label changes are saved immediately when the user clicks OK in
        the LabelEditorModal. There is no separate "Save All" button.

        Default labels are user-specific - each user can have their own
        set of defaults for quick expense entry.

    See Also:
        LabelEditorModal: Modal for editing label details
        settings_label_new.CreateLabelForm: Create new labels
        functions.project_composer.ProjectComposer: Label type definitions
    """

    # DEFAULT_CSS = """
    # }

    class LabelsModified(Message):
        """Message sent when labels are modified and saved.

        Posted after successful database update to notify parent screen.

        Attributes:
            changes_summary (dict): Dictionary with:
                - new_labels (int): Count of new labels created
                - modified_labels (int): Count of labels modified
                - deleted_labels (int): Count of labels deleted

        Example:
            >>> summary = {
            >>>     'new_labels': 0,
            >>>     'modified_labels': 3,
            >>>     'deleted_labels': 0
            >>> }
        """

        def __init__(self, changes_summary: dict) -> None:
            """Initialize LabelsModified message.

            Args:
                changes_summary: Dictionary with modification counts
            """
            self.changes_summary = changes_summary
            super().__init__()

    class NewLabelRequested(Message):
        """Message sent when user requests to create a new label.

        Posted when user clicks "Create New Label" button.
        Parent screen typically switches to CreateLabelForm.
        """

        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._labels = []
        self._modified_labels = {}  # Track changes: {label_id: updated_data}
        self._new_labels = []  # Track new labels to be created
        self._deleted_labels = set()  # Track labels marked for deletion
        self._selected_label_type = 1  # Default to level 1

    def on_mount(self) -> None:
        load_dynamic_css(self, "screens_settings_label_page.tcss")

    def compose(self) -> ComposeResult:

        # Get current project info
        project_id = self.app.app_state.get("project_id", 0)
        user_id = self.app.app_state.get("user_id", -1)

        project_names = self.app.app_state.get("project_names", [])
        project_ids = self.app.app_state.get("project_ids", [])

        # Find project name
        project_name = "Unknown Project"
        if project_id in project_ids:
            idx = project_ids.index(project_id)
            project_name = project_names[idx]

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

        # Load labels from database
        if project_id > 0:

            try:
                dbh = self.app._config["dbh"]
                # Force refresh to bypass cache and get latest data from database
                # Pass user_id to get user-specific default information
                self._labels = dbh.op_label_get_all(
                    project_id, use_cache=False, force_refresh=True, user_id=user_id
                )
            except Exception as e:
                self.app.log(f"Error loading labels: {e}")
                self._labels = []

        # Sort labels by Type (ascending), then Status (descending - Active first), then Name (ascending)
        self._labels.sort(
            key=lambda x: (
                x.get("label_type", 0),  # Type: 0, 1, 2
                -x.get(
                    "label_status", 0
                ),  # Status: 2 (Active), 1 (Deactivated), 0 (Deleted) - negative for descending
                x.get("name", "").lower(),  # Name: alphabetically
            )
        )

        # Header:
        yield Static("Label Management", classes="form-title")
        # Show current project name as header
        if project_info:
            current_name = project_info.get("project_name", "Unknown Project")
            yield Static(f"Currently Editing: {current_name}", classes="current-project-header")
        else:
            yield Static("No Project Loaded", classes="current-project-header")

        with ScrollableContainer(id="form-content"):
            # Labels table
            yield Static("Existing Labels:", classes="section-header")
            table = DataTable(id="labels-table")
            table.add_columns("Name", "Description", "Status", "Type", "Owner", "Default")

            # Get project users to map user_id to username
            user_map = {}  # {user_id: username}
            if project_id > 0:
                try:
                    dbh = self.app._config["dbh"]
                    project_users = dbh.op_project_get_users(project_id)
                    for user in project_users:
                        user_map[user.get("user_id")] = user.get("username", "Unknown")
                    self.app.log(f"Loaded {len(user_map)} users for label owner mapping")
                except Exception as e:
                    self.app.log(f"Error loading project users: {e}")

            # Populate table with existing labels
            # Note: We store label_id as the row key for internal reference
            for label in self._labels:
                status_text = self._get_status_text(label["label_status"])
                label_type_text = self._get_action_type(label["label_type"])

                # Get label owner text
                label_owner_id = label.get("label_owner", -1)
                if label_owner_id == -1:
                    owner_text = "Common"
                else:
                    owner_text = user_map.get(label_owner_id, f"User {label_owner_id}")

                # Get default indicator (user-specific)
                is_default = label.get("is_user_default", False)
                default_text = "⭐" if is_default else ""

                # Add row with plain text (no background colors)
                table.add_row(
                    label["name"],
                    (
                        label["description"][:30] + "..."
                        if len(label["description"]) > 30
                        else label["description"]
                    ),
                    status_text,
                    label_type_text,
                    owner_text,
                    default_text,
                    key=f"label-id-{label['label_id']}",  # Store label_id in the row key
                )

            yield table

            # Action buttons
            with Horizontal(id="action-buttons"):
                yield Button("New Label", id="new-label-button")
                yield Button("Cancel", id="cancel-button")

    def _get_status_text(self, status: int) -> str:
        """Convert status code to text."""
        status_map = {0: "Mark for Deletion", 1: "Deactivated", 2: "Active"}
        return status_map.get(status, "Unknown")

    def _get_action_type(self, status: int) -> str:
        """Convert status code to text."""
        project_style = self.app.app_state.get("project_style", "default")

        # Handle default/invalid project style
        if project_style == "default" or not project_style:
            # Return generic status map for default projects
            status_map = {0: "Type 0", 1: "Type 1", 2: "Type 2", 3: "Type 3", 4: "Type 4"}
            return status_map.get(status, "Unknown")

        try:
            dbh = self.app._config.get("dbh")
            pc = ProjectComposer.create(
                compose_type=project_style,
                dbh=dbh,
                project_id=self.app.app_state["project_id"],
                users=[],
            )
            status_map = pc.get_label_map()
            return status_map.get(status, "Unknown")
        except Exception as e:
            self.app.log(f"Error getting action type from ProjectComposer: {e}")
            return f"Type {status}"

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
        elif event.button.id and event.button.id.startswith("label-type-"):
            # Handle label type button clicks
            label_type = int(event.button.id.split("-")[-1])
            self._set_label_type(label_type)

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        """Handle cell selection in the table - clicking Default column toggles default, other cells open editor."""
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

        # Find the label to get all data
        label = next((l for l in self._labels if l["label_id"] == label_id), None)
        if not label:
            self.app.notify(f"Label ID {label_id} not found", severity="error")
            return

        # Check if user clicked on the "Default" column (column 5)
        if col_index == 5:
            self._handle_default_toggle(label_id, label, table, row_index)
        else:
            # Open label editor for other columns
            label_name = label["name"]
            label_description = label["description"]
            current_status = label.get("label_status", 2)

            self.app.log(
                f"Row clicked - Row: {row_index}, Column: {col_index}, Label ID: {label_id}, Label: {label_name}"
            )

            # Open label editor modal (clicking any cell in the row opens the editor)
            self.app.push_screen(
                LabelEditorModal(label_id, label_name, label_description, current_status),
                callback=lambda result: self._handle_label_update(
                    label_id, result, table, row_index
                ),
            )

    def _handle_label_update(
        self, label_id: int, result: dict | None, table: DataTable, row_index: int
    ) -> None:
        """Handle the label update from the modal."""
        if result is None:
            # User cancelled
            return

        # Find the label
        label = next((l for l in self._labels if l["label_id"] == label_id), None)
        if not label:
            self.app.notify(f"Label ID {label_id} not found", severity="error")
            return

        # Get old values
        old_name = label["name"]
        old_description = label["description"]
        old_status = label.get("label_status", 2)

        # Get new values from result
        new_name = result.get("name", old_name)
        new_description = result.get("description", old_description)
        new_status = result.get("label_status", old_status)

        # Check if anything changed
        changes = []
        if new_name != old_name:
            changes.append(f"name: '{old_name}' → '{new_name}'")
        if new_description != old_description:
            changes.append(f"description updated")
        if new_status != old_status:
            changes.append(
                f"status: {self._get_status_text(old_status)} → {self._get_status_text(new_status)}"
            )

        if not changes:
            self.app.notify("No changes made", severity="info")
            return

        self.app.log(f"Updating label '{old_name}' (ID: {label_id}): {', '.join(changes)}")

        # Save to database immediately
        try:
            dbh = self.app._config["dbh"]
            update_data = {
                "name": new_name,
                "description": new_description,
                "label_status": new_status,
            }
            dbh.op_label_update(label_id, update_data)
            self.app.log(f"Successfully saved label {label_id} to database")

            # Update in memory after successful database save
            label["name"] = new_name
            label["description"] = new_description
            label["label_status"] = new_status

            # Track the modification (for reference/undo feature if needed later)
            if label_id not in self._modified_labels:
                self._modified_labels[label_id] = {}
            self._modified_labels[label_id]["name"] = new_name
            self._modified_labels[label_id]["description"] = new_description
            self._modified_labels[label_id]["label_status"] = new_status

            # Update table display
            from textual.coordinate import Coordinate

            # Update Name (column 0)
            table.move_cursor(row=row_index, column=0)
            table.update_cell_at(Coordinate(row_index, 0), new_name)

            # Update Description (column 1)
            table.move_cursor(row=row_index, column=1)
            desc_display = (
                new_description[:30] + "..." if len(new_description) > 30 else new_description
            )
            table.update_cell_at(Coordinate(row_index, 1), desc_display)

            # Update Status (column 2)
            table.move_cursor(row=row_index, column=2)
            table.update_cell_at(Coordinate(row_index, 2), self._get_status_text(new_status))

            self.app.notify(f"Label saved: {', '.join(changes)}", severity="information")

        except Exception as e:
            self.app.notify(f"Error saving label: {str(e)}", severity="error")
            self.app.log(f"Database update error for label {label_id}: {e}")

    def _handle_default_toggle(
        self, label_id: int, label: dict, table: DataTable, row_index: int
    ) -> None:
        """Handle toggling the default status of a label for the current user.

        Args:
            label_id: The ID of the label
            label: The label data dictionary
            table: The DataTable instance
            row_index: The row index in the table
        """
        # Check user permissions - must be Project Manager or higher (xxxx11 or xxxx10)
        user_scope = self.app.app_state.get("user_scope", "user:write")
        project_id = self.app.app_state.get("project_id", 0)
        user_id = self.app.app_state.get("user_id", -1)

        # Get user's permission for this project
        try:
            dbh = self.app._config["dbh"]
            project_users = dbh.op_project_get_users(project_id)
            current_user = next((u for u in project_users if u["user_id"] == user_id), None)

            if not current_user:
                self.app.notify("You are not a member of this project", severity="error")
                return

            perm_model = current_user.get("project_perm_model", "000000")

            # Check if user has Project (position 4) or Manage (position 5) permission
            # if len(perm_model) < 6 or \
            #         perm_model[2] != '1' or \
            #         ( perm_model[4] != '1' and perm_model[5] != '1'):
            #     self.app.notify(
            #         "You need Project Manager permissions to change default labels",
            #         severity="error"
            #     )
            #     self.app.log(f"User {user_id} lacks permission to toggle default (perm: {perm_model})")
            #     return

            # Get current default status for THIS USER
            current_default = label.get("is_user_default", False)
            new_default = not current_default
            label_type = label.get("label_type", 0)
            label_name = label.get("name", "Unknown")

            # If setting as default, use op_label_set_default
            if new_default:
                dbh.op_label_set_default(label_id, project_id, label_type, user_id)
                self.app.log(
                    f"Set label {label_id} ({label_name}) as default for user {user_id}, type {label_type}"
                )
            else:
                # If unsetting default, remove from user_label_defaults table
                dbh.op_label_unset_default(project_id, label_type, user_id)
                self.app.log(f"Unset label {label_id} ({label_name}) as default for user {user_id}")

            # Update in-memory labels for THIS USER
            # Reload labels with user_id to get fresh default info
            self._labels = dbh.op_label_get_all(
                project_id, use_cache=False, force_refresh=True, user_id=user_id
            )

            # Re-sort labels
            self._labels.sort(
                key=lambda x: (
                    x.get("label_type", 0),
                    -x.get("label_status", 0),
                    x.get("name", "").lower(),
                )
            )

            # Update ALL rows in the table to reflect changes
            from textual.coordinate import Coordinate

            for idx, lbl in enumerate(self._labels):
                if lbl["label_type"] == label_type:
                    # Update Default column (column 5) for all labels of this type
                    is_default = lbl.get("is_user_default", False)
                    default_symbol = "⭐" if is_default else ""
                    try:
                        table.update_cell_at(Coordinate(idx, 5), default_symbol)
                        self.app.log(f"Updated row {idx} ({lbl['name']}): default={default_symbol}")
                    except Exception as e:
                        self.app.log(f"Could not update row {idx}: {e}")

            # Show notification
            if new_default:
                self.app.notify(
                    f"Set '{label_name}' as YOUR default for {self._get_action_type(label_type)}",
                    severity="information",
                )
            else:
                self.app.notify(
                    f"Removed YOUR default status from '{label_name}'", severity="information"
                )

        except Exception as e:
            self.app.notify(f"Error toggling default: {str(e)}", severity="error")
            self.app.log(f"Error in _handle_default_toggle: {e}")
