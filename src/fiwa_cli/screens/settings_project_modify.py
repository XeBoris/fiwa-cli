# settings_project_modify.py
from textual.widgets import Static, Button, Input, TextArea, Checkbox, Label, Rule, Switch
from textual.containers import Vertical, Horizontal, Grid, ScrollableContainer, Container
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.message import Message
import json

from fiwa_cli.functions.loader import load_dynamic_css


def translate_permissions(permission_string: str) -> str:
    """Translate permission string to human-readable format.

    Args:
        permission_string: 6-character string like "110000"

    Returns:
        Human-readable string like "Read, Create" or "No permissions"

    Example:
        "110000" -> "Read, Create"
        "111111" -> "Read, Create, Update, Delete, Project, Manage"
        "000000" -> "No permissions"
    """
    permission_map = {
        0: "Read",
        1: "Create",
        2: "Update",
        3: "Delete",
        4: "Project",
        5: "Manage"
    }

    # Ensure string is 6 characters, pad with zeros if needed
    perms = permission_string.ljust(6, '0')

    # Collect enabled permissions
    enabled = []
    for idx, flag in enumerate(perms[:6]):
        if flag == '1':
            enabled.append(permission_map[idx])

    # Return formatted string
    if not enabled:
        return "No permissions"

    return ", ".join(enabled)


class ModifyProjectForm(Vertical):
    """Widget for modifying the currently loaded project."""

    # DEFAULT_CSS = """
    #
    # """

    class ProjectModified(Message):
        """Message sent when project is modified."""
        def __init__(self, project_data: dict) -> None:
            self.project_data = project_data
            super().__init__()

    def on_mount(self) -> None:
        load_dynamic_css(self, "screens_settings_project_modify.tcss")

    def compose(self) -> ComposeResult:
        # Get current project information from app_state
        project_id = self.app.app_state.get("project_id", 0)
        user_id = self.app.app_state.get("user_id", -1)

        self.app.log(f"ModifyProjectForm.compose() called: project_id={project_id}, user_id={user_id}")

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

        yield Static("Modify Project", classes="form-title")

        # Show current project name as header
        if project_info:
            current_name = project_info.get("project_name", "Unknown Project")
            yield Static(f"Currently Editing: {current_name}", classes="current-project-header")
        else:
            yield Static("No Project Loaded", classes="current-project-header")

        # Pre-fill form fields with current values
        current_description = ""
        current_currency_main = ""
        current_currency_list = ""

        if project_info:
            current_description = project_info.get("description", "")
            current_currency_main = project_info.get("currency_main", "")

            # Parse currency_list (stored as JSON string)
            currency_list_raw = project_info.get("currency_list", "[]")
            try:
                if isinstance(currency_list_raw, str):
                    currency_list_parsed = json.loads(currency_list_raw)
                else:
                    currency_list_parsed = currency_list_raw
                current_currency_list = ", ".join(currency_list_parsed) if currency_list_parsed else ""
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                self.app.log(f"Error parsing currency_list: {e}")
                current_currency_list = ""

        with ScrollableContainer(id="form-content"):
            with Vertical(id="form-project-area"):
                yield Static("Project Name *", classes="form-label")
                yield Input(
                    placeholder="Enter project name",
                    id="project-name",
                    max_length=24,
                    value=project_info.get("project_name", "") if project_info else ""
                )

                yield Static("Description (128 characters)", classes="form-label")
                yield TextArea(
                    id="project-description",
                    text=current_description,
                )

            with Horizontal(id="form-currency-section"):
                with Vertical(id="form-currency-section-main"):
                    yield Static("Main Currency *", classes="form-label")
                    yield Input(placeholder="e.g., USD",
                                id="currency-main",
                                max_length=3,
                                value=current_currency_main)
                with Vertical(id="form-currency-section-additional"):
                    yield Static("Additional Currencies (comma-separated)", classes="form-label")
                    yield Input(placeholder="e.g., USD, EUR, JPY",
                                id="currency-list",
                                value=current_currency_list)

            with Vertical(id="form-user-section"):
                # Fetch and display users for this project
                project_users = []
                if project_id and project_id > 0:
                    try:
                        dbh = self.app._config["dbh"]
                        project_users = dbh.op_project_get_users(project_id)
                        self.app.log(f"Found {len(project_users)} users for project {project_id}")
                    except Exception as e:
                        self.app.log(f"Error fetching project users: {e}")

                # with Vertical(id="users-list-container"):
                # Header with label and Add Users button
                with Horizontal(classes="users-header"):
                    yield Static("Project Users", classes="form-label")
                    yield Button("Add Users", id="add-users-button", classes="add-users-button")

                if project_users:
                    for user in project_users:
                        username = user.get('username', 'Unknown')
                        user_id_val = user.get('user_id', 0)
                        first_name = user.get('first_name', '')
                        last_name = user.get('last_name', '')
                        permission = user.get('project_perm_model', '000000')
                        is_primary = user.get('project_primary', False)

                        # Format display name
                        display_name = f"{username} "
                        if first_name or last_name:
                            display_name += f"  | ({first_name} {last_name})".strip()

                        # Add primary indicator
                        if is_primary:
                            display_name = f"⭐ {display_name} [PRIMARY]"
                        else:
                            display_name = f"   {display_name}"
                        # Add human-readable permission level
                        readable_perms = translate_permissions(permission)
                        display_name += f" - {readable_perms}"

                        # Create horizontal container for user info + button
                        with Horizontal(classes="user-row"):
                            yield Static(display_name, classes="user-item")
                            yield Button(
                                "🔧",
                                id=f"edit-perm-{user_id_val}",
                                classes="edit-permission-button"
                            )

                else:
                    yield Static("No users found for this project", classes="user-item-empty")

        with Grid(id="project-buttons"):
            yield Button("Update", id="project-update-button")
            yield Button("Cancel", id="project-cancel-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "project-cancel-button":
            self.app.notify("Project modification cancelled", severity="info")
        elif event.button.id == "project-update-button":
            self.update_project()
        elif event.button.id == "add-users-button":
            self._show_add_user_dialog()
        elif event.button.id and event.button.id.startswith("edit-perm-"):
            # Extract user_id from button ID
            user_id = int(event.button.id.replace("edit-perm-", ""))
            self._show_permission_dialog(user_id)

    def update_project(self) -> None:
        """Validate and update the project."""
        project_id = self.app.app_state.get("project_id", 0)
        user_id = self.app.app_state.get("user_id", -1)

        if not project_id or user_id <= 0:
            self.app.notify("No project loaded or user not logged in", severity="error")
            return

        name = self.query_one("#project-name", Input).value.strip()
        description = self.query_one("#project-description", TextArea).text.strip()
        currency_main = self.query_one("#currency-main", Input).value.strip().upper()
        currency_list_str = self.query_one("#currency-list", Input).value.strip()

        if not name:
            self.app.notify("Project name is required", severity="error")
            return

        if not currency_main or len(currency_main) != 3:
            self.app.notify("Valid 3-letter currency code required", severity="error")
            return

        currency_list = []
        if currency_list_str:
            currency_list = [c.strip().upper() for c in currency_list_str.split(",") if c.strip()]

        project_data = {
            "project_id": project_id,
            "name": name,
            "description": description if description else None,
            "currency_main": currency_main,
            "currency_list": currency_list,
        }

        # Update in database
        try:
            dbh = self.app._config["dbh"]
            dbh.op_project_update(project_data)
            self.app.notify("Project updated successfully!", severity="information")
            self.post_message(self.ProjectModified(project_data))
        except ValueError as e:
            self.app.notify(f"Update failed: {str(e)}", severity="error")
        except Exception as e:
            self.app.notify(f"Error updating project: {str(e)}", severity="error")

    def _show_permission_dialog(self, user_id: int) -> None:
        """Show permission edit dialog for a user."""
        project_id = self.app.app_state.get("project_id", 0)

        # Get current user permissions
        try:
            dbh = self.app._config["dbh"]
            project_users = dbh.op_project_get_users(project_id)
            user = next((u for u in project_users if u['user_id'] == user_id), None)

            if not user:
                self.app.notify("User not found", severity="error")
                return

            current_permissions = user.get('project_perm_model', '000000')
            username = user.get('username', 'Unknown')
            is_primary = user.get('project_primary', False)
            # Show the dialog
            dialog = UserPermissionsDialog(
                user_id=user_id,
                username=username,
                project_id=project_id,
                current_permissions=current_permissions,
                is_primary=is_primary
            )

            self.app.push_screen(dialog, self._handle_permission_result)

        except Exception as e:
            self.app.notify(f"Error loading user permissions: {str(e)}", severity="error")

    def _handle_permission_result(self, result) -> None:
        """Handle the result from the permission dialog."""
        if result:
            # Refresh the form to show updated permissions
            self.app.notify("Permissions updated successfully", severity="information")
            # Could refresh the user list here if needed

    def _show_add_user_dialog(self) -> None:
        """Show add user dialog with available users."""
        project_id = self.app.app_state.get("project_id", 0)

        try:
            dbh = self.app._config["dbh"]

            # Get all users in the system
            dbh.load()
            query = f"""
                SELECT user_id, username, first_name, last_name, email
                FROM p{dbh._db_salt}_users
                WHERE activated = 1
                ORDER BY username
            """
            all_users = dbh.execute_query(query)
            dbh.close()

            # Get users already in the project
            project_users = dbh.op_project_get_users(project_id)
            project_user_ids = {user['user_id'] for user in project_users}

            # Filter to only users NOT in the project
            available_users = [
                {
                    'user_id': row[0],
                    'username': row[1],
                    'first_name': row[2],
                    'last_name': row[3],
                    'email': row[4]
                }
                for row in all_users
                if row[0] not in project_user_ids
            ]

            if not available_users:
                self.app.notify("All users are already in this project", severity="info")
                return

            # Show the dialog
            dialog = UserAddDialog(
                project_id=project_id,
                available_users=available_users
            )

            self.app.push_screen(dialog, self._handle_add_user_result)

        except Exception as e:
            self.app.notify(f"Error loading available users: {str(e)}", severity="error")
            self.app.log(f"Error in _show_add_user_dialog: {e}")

    def _handle_add_user_result(self, result) -> None:
        """Handle the result from the add user dialog."""
        if result:
            # User was added, show success and could refresh the list
            self.app.notify(f"User added to project successfully", severity="information")


# ============================================================================
# UserPermissionsDialog Widget
# ============================================================================

class UserPermissionsDialog(ModalScreen):
    """Modal dialog for editing user permissions.

    Displays checkboxes for 6 permission levels:
    - R (Read): View expenses and project dashboard
    - C (Create): Add new expenses
    - U (Update): Edit existing expenses
    - D (Delete): Remove expenses
    - P (Project): Edit project details
    - M (Manage): Manage other users
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        user_id: int,
        username: str,
        project_id: int,
        current_permissions: str = "000000",
        is_primary: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.username = username
        self.project_id = project_id
        self.current_permissions = current_permissions
        self.is_primary = is_primary

    def compose(self) -> ComposeResult:
        """Build the permission dialog."""
        with ScrollableContainer(id="permission-dialog"):

            yield Static("Permissions", classes="dialog-title")
            yield Static(f"User: {self.username}", classes="dialog-user")

            with Vertical(id="permission-list"):
                # Parse current permissions (6-character string like "110000")
                perms = list(self.current_permissions.ljust(6, '0'))

                # Permission definitions
                permissions = [
                    ("R", "Read", "View expenses and project dashboard"),
                    ("C", "Create", "Add new expenses"),
                    ("U", "Update", "Edit existing expenses"),
                    ("D", "Delete", "Remove expenses"),
                    ("P", "Project", "Edit project details (Name, Description)"),
                    ("M", "Manage", "Manage other users (Add/Remove/Change Permissions)")
                ]

                for idx, (code, title, description) in enumerate(permissions):
                    is_checked = perms[idx] == '1'

                    with Vertical(classes="permission-row"):
                        yield Checkbox(
                            f"{code} ({title})",
                            value=is_checked,
                            id=f"perm-{idx}",
                            classes="permission-checkbox"
                        )
                    yield Static(description, classes="permission-description")

            yield Static("Set Primary Project", classes="dialog-title")
            with Horizontal(id="primary-switch-row"):
                if self.is_primary:
                    _text = "This is your primary project already"
                    _disb = True
                else:
                    _text = "Set as your primary project (⭐)\n(Only one primary project allowed)"
                    _disb = False
                yield Static(_text, classes="primary-description")

                yield Switch(id="primary-switch",
                             value=self.is_primary,
                             classes="primary-switch",
                             disabled=_disb)  # Disable switch if already primary


            with Horizontal(id="dialog-buttons"):
                yield Button("OK", id="dialog-ok", variant="success")
                yield Button("Cancel", id="dialog-cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the dialog."""
        if event.button.id == "dialog-ok":
            self._save_permissions()
        elif event.button.id == "dialog-cancel":
            self.dismiss(False)

    def action_cancel(self) -> None:
        """Action to cancel and close the dialog (triggered by ESC key)."""
        self.dismiss(False)

    def _save_permissions(self) -> None:
        """Save the updated permissions to the database."""
        # Collect checkbox values
        permission_string = ""
        for idx in range(6):
            try:
                checkbox = self.query_one(f"#perm-{idx}", Checkbox)
                permission_string += "1" if checkbox.value else "0"
            except:
                permission_string += "0"

        # Check primary switch
        try:
            primary_switch = self.query_one("#primary-switch", Switch)
            is_primary = primary_switch.value
        except:
            is_primary = self.is_primary  # fallback to original value if switch not found

        # Update in database
        try:
            dbh = self.app._config["dbh"]

            # Update the project_perm_model in user_project_map table
            dbh.load()
            query = f"""
                UPDATE p{dbh._db_salt}_user_project_map
                SET project_perm_model = ?
                WHERE user_id = ? AND project_id = ?
            """
            dbh.execute_query(query, [permission_string, self.user_id, self.project_id])
            dbh.close()

            self.app.log(f"Updated permissions for user {self.user_id}: {permission_string}")

            dbh.op_project_set_primary(project_id=self.project_id, user_id=self.user_id)

            self.dismiss(True)

        except Exception as e:
            self.app.notify(f"Failed to save permissions: {str(e)}", severity="error")
            self.app.log(f"Error saving permissions: {e}")
            self.dismiss(False)


# ============================================================================
# UserAddDialog Widget
# ============================================================================

class UserAddDialog(ModalScreen):
    """Modal dialog for adding users to a project.

    Displays a list of all users not currently in the project.
    Users can select multiple users to add at once.
    New users are added with Read-only permissions ("100000") by default.
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        project_id: int,
        available_users: list[dict],
        **kwargs
    ):
        super().__init__(**kwargs)
        self.project_id = project_id
        self.available_users = available_users
        self.selected_user_ids = set()

    def compose(self) -> ComposeResult:
        """Build the add user dialog."""
        with ScrollableContainer(id="add-user-dialog"):
            yield Static("Add Users to Project", classes="dialog-title")
            yield Static(
                f"{len(self.available_users)} user(s) available",
                classes="dialog-subtitle"
            )

            with ScrollableContainer(id="available-users-list"):
                if self.available_users:
                    for user in self.available_users:
                        user_id = user['user_id']
                        username = user['username']
                        first_name = user.get('first_name', '')
                        last_name = user.get('last_name', '')
                        email = user.get('email', '')

                        # Format display name
                        display_name = username
                        if first_name or last_name:
                            display_name += f" ({first_name} {last_name})".strip()
                        if email:
                            display_name += f" - {email}"

                        yield Checkbox(
                            display_name,
                            value=False,
                            id=f"user-{user_id}",
                            classes="user-checkbox"
                        )
                else:
                    yield Static("No available users", classes="empty-message")

                with Horizontal(id="dialog-buttons"):
                    yield Button("Add Selected", id="dialog-add", variant="success")
                    yield Button("Cancel", id="dialog-cancel", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the dialog."""
        if event.button.id == "dialog-add":
            self._add_selected_users()
        elif event.button.id == "dialog-cancel":
            self.dismiss(False)

    def action_cancel(self) -> None:
        """Action to cancel and close the dialog (triggered by ESC key)."""
        self.dismiss(False)

    def _add_selected_users(self) -> None:
        """Add selected users to the project with Read-only permissions."""
        # Collect selected checkboxes
        selected_users = []
        for user in self.available_users:
            user_id = user['user_id']
            try:
                checkbox = self.query_one(f"#user-{user_id}", Checkbox)
                if checkbox.value:
                    selected_users.append(user)
            except:
                pass

        if not selected_users:
            self.app.notify("No users selected", severity="warning")
            return

        # Add users to project with Read-only permissions ("100000")
        try:
            dbh = self.app._config["dbh"]
            dbh.load()

            added_count = 0
            for user in selected_users:
                user_id = user['user_id']

                # Check if user already exists (safety check)
                check_query = f"""
                    SELECT id FROM p{dbh._db_salt}_user_project_map
                    WHERE user_id = ? AND project_id = ?
                """
                existing = dbh.execute_query(check_query, [user_id, self.project_id])

                if existing:
                    self.app.log(f"User {user_id} already in project {self.project_id}, skipping")
                    continue

                # Insert user with Read-only permissions
                insert_query = f"""
                    INSERT INTO p{dbh._db_salt}_user_project_map
                    (user_id, project_id, project_perm_model, project_primary)
                    VALUES (?, ?, ?, ?)
                """
                dbh.execute_query(insert_query, [user_id, self.project_id, "100000", 0])
                added_count += 1
                self.app.log(f"Added user {user_id} to project {self.project_id} with Read permissions")

            dbh.close()

            if added_count > 0:
                self.app.notify(
                    f"Successfully added {added_count} user(s) to project",
                    severity="information"
                )
                self.dismiss(True)
            else:
                self.app.notify("No new users were added", severity="info")
                self.dismiss(False)

        except Exception as e:
            self.app.notify(f"Failed to add users: {str(e)}", severity="error")
            self.app.log(f"Error adding users: {e}")
            self.dismiss(False)


