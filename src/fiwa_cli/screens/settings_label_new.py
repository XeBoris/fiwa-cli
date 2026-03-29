"""Label creation interface for FiWa CLI.

This module provides the form for creating new labels (categories/tags) within
a project. Labels are used to categorize transactions and can be owned by
individual users or shared as common project-wide labels.

The label system supports different label types based on project style:
    - Balance labels: For balance categorization
    - Transaction labels: For transaction categorization
    - Account labels: For account/bank categorization
    - Main category labels: Primary expense categories
    - Secondary labels: Sub-categories or tags

Key Features:
    - Dynamic label type selection based on project style
    - User ownership vs. common (project-wide) labels
    - Label status management (draft, active, archived)
    - Default label designation per category per user
    - Integration with ProjectComposer for style-specific labels

Classes:
    CreateLabelForm: Form widget for creating new labels

Label Ownership:
    - **Common labels (owner_id = -1)**: Shared by all project users
    - **User labels (owner_id > 0)**: Owned by specific user, private to them

Example:
    Mounting the form::

        >>> from fiwa_cli.screens.settings_label_new import CreateLabelForm
        >>> form = CreateLabelForm()
        >>> content_area.mount(form)

    Handling label creation::

        >>> @on(CreateLabelForm.LabelCreated)
        >>> def on_label_created(self, message):
        >>>     label_data = message.label_data
        >>>     self.app.file_log.info(f"New label: {label_data['name']}")

See Also:
    settings_label_page: Manage existing labels
    functions.project_composer: Project-specific label structures
    settings: Main settings screen
"""

from textual.widgets import Static, Button, Input, Switch, Placeholder, Select
from textual.containers import Vertical, Horizontal, ScrollableContainer, Grid
from textual.app import ComposeResult
from textual.message import Message
from textual import on

from fiwa_cli.functions.loader import load_dynamic_css


class CreateLabelForm(Vertical):
    """Form widget for creating new labels/categories.

    This widget provides a form for creating labels with support for:
        - Dynamic label type selection based on project style
        - User ownership or common (project-wide) designation
        - Status selection (draft, active, archived)
        - Default label marking for quick selection

    The form integrates with ProjectComposer to get available label types
    for the current project style (e.g., ExpenseTracker shows different
    types than Vacation projects).

    Attributes:
        _selected_label_type (int | None): Currently selected label type ID
        _selected_label_owner (int): Selected owner ID (-1 for common)
        _default_label_type (int | None): Cached default type for reset

    Messages:
        LabelCreated: Emitted when label is successfully created
            - Attributes:
                - label_data (dict): Complete label information

    Form Fields:
        - **Label Name** (required): Descriptive name, max 50 characters
        - **Label Type** (required): Dropdown of available types
        - **Label Sub-Type**: For hierarchical categorization
        - **Label Owner**: User or "common" designation
        - **Label Status**: Draft (0), Active (2), or Archived (1)
        - **Set as Default**: Checkbox to mark as default for this type

    Label Types (ExpenseTracker example):
        - Type 0: Balance (sub_types: Asset, Liability, Equity)
        - Type 1: Transaction (sub_types: Revenue, Expense)
        - Type 2: Account (sub_types: Bank, Credit Card, Cash)
        - Type 3: Main Category (sub_types: Groceries, Entertainment, etc.)
        - Type 4: Secondary Tags (sub_types: Urgent, Recurring, etc.)

    Validation:
        - Label name is required
        - Label type must be selected
        - Only one default label per type per user
        - Label owner must be valid user ID or -1

    Example:
        Creating a common label::

            >>> # User fills form:
            >>> #   Name: "Groceries"
            >>> #   Type: "Main Category"
            >>> #   Owner: "common"
            >>> #   Status: "Active"
            >>> #   Default: True
            >>> # Clicks "Create"
            >>> # → Label created with owner_id=-1

        Creating a user-specific label::

            >>> # User fills form:
            >>> #   Name: "Wayne Credit Card"
            >>> #   Type: "Account"
            >>> #   Owner: "batman"
            >>> #   Status: "Active"
            >>> # → Label created with owner_id=batman's ID

    Note:
        Default labels are used for quick expense entry - when a user
        doesn't explicitly select labels, the system uses their default
        labels for each category.

        The label sub_type system allows hierarchical categorization
        (e.g., Account → Credit Card → specific card name).

    See Also:
        settings_label_page.LabelManagementForm: Manage existing labels
        functions.project_composer.ProjectComposer: Project-specific label types
        functions.handler_sqllite.SQLLiteHandler.op_label_create: Database operation
    """

    # DEFAULT_CSS = """
    #
    # """

    class LabelCreated(Message):
        """Message sent when a label is successfully created.

        Posted to parent screen after validation, for database insertion.

        Attributes:
            label_data (dict): Dictionary containing:
                - name (str): Label name
                - description (str): Optional description
                - label_type (int): Type ID from ProjectComposer
                - label_sub_type (int): Sub-type ID (-1 for default)
                - label_status (int): Status (0=draft, 1=archived, 2=active)
                - label_owner (int): Owner user ID (-1 for common)
                - label_default (bool): Whether this is a default label
                - composite (str | None): For future composite labels

        Example:
            Receiving the message::

                >>> def on_create_label_form_label_created(self, message):
                >>>     label_id = dbh.op_label_create(
                >>>         message.label_data,
                >>>         project_id
                >>>     )
        """

        def __init__(self, label_data: dict) -> None:
            """Initialize the LabelCreated message.

            Args:
                label_data: Complete label information dictionary
            """
            self.label_data = label_data
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_label_type = None  # Will be set dynamically in compose
        self._selected_label_owner = -1  # Default to common (project-wide)
        self._default_label_type = None  # Store default for reset functionality

    def on_mount(self) -> None:
        load_dynamic_css(self, "screens_settings_label_new.tcss")

    def compose(self) -> ComposeResult:

        project_id = self.app.app_state.get("project_id", 0)
        user_id = self.app.app_state.get("user_id", -1)
        project_style = self.app.app_state.get("project_style", "default")

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

        # Get label type options dynamically from ProjectComposer
        label_type_options = []
        try:
            if project_style and project_style != "default":
                from fiwa_cli.functions.project_composer import ProjectComposer

                dbh = self.app._config["dbh"]
                pc = ProjectComposer.create(
                    compose_type=project_style, dbh=dbh, project_id=project_id, users=[]
                )
                label_map = pc.get_label_map()

                # Convert label_map to options list: [(group_name, type_id), ...]
                label_type_options = [
                    (group_name, type_id) for type_id, group_name in sorted(label_map.items())
                ]

                self.app.log(f"Loaded dynamic label types for {project_style}: {label_map}")
            else:
                # Fallback to default label types if no style or default style
                label_type_options = [("Action", 0), ("Account", 1), ("Label", 2)]
                self.app.log("Using default label types")
        except Exception as e:
            self.app.log(f"Error loading label map from ProjectComposer: {e}")
            # Fallback to default
            label_type_options = [("Action", 0), ("Account", 1), ("Label", 2)]

        # Set default label type to the first available option if not already set
        if self._selected_label_type is None and label_type_options:
            self._default_label_type = label_type_options[0][1]  # Get the type_id from first option
            self._selected_label_type = self._default_label_type
        elif self._selected_label_type is None:
            # Absolute fallback
            self._default_label_type = 2
            self._selected_label_type = 2

        # Get project users for label owner dropdown
        label_owner_options = [("Common (Project-wide)", -1)]  # Default option
        if project_id and user_id > 0:
            try:
                dbh = self.app._config["dbh"]
                project_users = dbh.op_project_get_users(project_id)

                # Add each user as an option
                for user in project_users:
                    username = user.get("username", "Unknown")
                    user_id_val = user.get("user_id", -1)
                    label_owner_options.append((username, user_id_val))

                self.app.log(f"Loaded {len(project_users)} users for label owner dropdown")
            except Exception as e:
                self.app.log(f"Error loading project users: {e}")

        with ScrollableContainer(id="form-content"):
            with Grid(id="action-grid"):
                # row 1
                yield Static("Label Name *", classes="form-label")
                yield Static("Description", classes="form-label")
                yield Static("Label Type", classes="form-label")
                yield Static("Label Owner", classes="form-label")

                # row 2
                yield Input(placeholder="Enter label name", id="new-label-name", compact=True)
                yield Input(
                    placeholder="Enter description", id="new-label-description", compact=True
                )
                yield Select(
                    options=label_type_options,
                    id="label-type-select",
                    value=self._selected_label_type,
                    compact=True,
                )
                yield Select(
                    options=label_owner_options,
                    id="label-owner-select",
                    value=self._selected_label_owner,
                    compact=True,
                )
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

            # Reset label type select to the default determined from label map
            default_type = self._default_label_type if self._default_label_type is not None else 2
            self.query_one("#label-type-select", Select).value = default_type
            self._selected_label_type = default_type

            # Reset label owner to Common (project-wide = "-1")
            self.query_one("#label-owner-select", Select).value = -1
            self._selected_label_owner = -1

            # Reset switch to on (active)
            self.query_one("#new-label-activated", Switch).value = True

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

            # Get label type from select
            select_label = self.query_one("#label-type-select", Select)
            self._selected_label_type = int(select_label.value)

            # Get label owner from select
            select_owner = self.query_one("#label-owner-select", Select)
            self._selected_label_owner = int(select_owner.value)

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
            "name": name,
            "description": description,
            "label_owner": self._selected_label_owner,
            "label_status": label_status,
            "label_type": self._selected_label_type,
            "label_sub_type": -1,  # Default sub-type (user cannot choose for now)
            "composite": [],
        }

        # Save to database
        try:
            dbh = self.app._config["dbh"]
            label_id = dbh.op_label_create(label_data, project_id)

            # Log with ownership information
            if self._selected_label_owner == -1:
                ownership_msg = "Common (Project-wide)"
            else:
                ownership_msg = f"Owned by user_id: {self._selected_label_owner}"

            self.app.log(f"Created label: {name} (ID: {label_id}, Owner: {ownership_msg})")
            self.app.notify(f"Label '{name}' created successfully!", severity="information")

            # Add label_id to the data
            label_data["label_id"] = label_id

            # Post message
            self.post_message(self.LabelCreated(label_data))

        except ValueError as e:
            self.app.notify(f"Failed to create label: {str(e)}", severity="error")
        except Exception as e:
            self.app.notify(f"Error creating label: {str(e)}", severity="error")
