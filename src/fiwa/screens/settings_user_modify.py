# settings_user_modify.py
from textual.widgets import Static, Button, Input, Select
from textual.containers import Vertical, Horizontal, Grid, ScrollableContainer
from textual.app import ComposeResult
from textual.message import Message
from datetime import datetime

from fiwa.functions.loader import load_dynamic_css


class ModifyUserForm(Vertical):
    """Widget for modifying user information.

    Behavior depends on the logged-in user's scope:
    - admin:* scope: Can see and modify all users
    - user:* scope: Can only see and modify their own information

    Restrictions:
    - unique_identifier: Cannot be changed (immutable)
    - max_projects: Only admin users can modify this field
    """

    class UserModified(Message):
        """Message sent when user is modified."""
        def __init__(self, user_data: dict) -> None:
            self.user_data = user_data
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_admin = False
        self._current_user_id = -1
        self._selected_user_id = None
        self._all_users = []

    def on_mount(self) -> None:
        load_dynamic_css(self, "screens_settings_user_modify.tcss")

        # For regular users, load their own data immediately after mount
        if not self._is_admin and self._current_user_id > 0:
            self._load_user_form(self._current_user_id)

    def compose(self) -> ComposeResult:
        # Get current user info and store in instance variables
        self._current_user_id = self.app.app_state.get("user_id", -1)
        user_scope = self.app.app_state.get("user_scope", "user:write")

        # Check if user is admin (scope starts with "admin:")
        self._is_admin = user_scope.startswith("admin:")

        # For regular users, set selected_user_id immediately
        if not self._is_admin:
            self._selected_user_id = self._current_user_id

        self.app.log(f"ModifyUserForm: user_id={self._current_user_id}, scope={user_scope}, is_admin={self._is_admin}")

        yield Static("Modify User", classes="form-title")

        # User selection (only for admins)
        if self._is_admin:
            # Admin can see all users
            yield Static("Select User to Modify", classes="form-label")
            yield Static("As an admin, you can modify any user account", classes="info-message")

            # Get all users from database
            try:
                dbh = self.app._config["dbh"]
                dbh.load()
                query = f"""
                    SELECT user_id, username, first_name, last_name, email
                    FROM p{dbh._db_salt}_users
                    WHERE activated = 1
                    ORDER BY username
                """
                result = dbh.execute_query(query)
                dbh.close()

                self._all_users = [
                    {
                        'user_id': row[0],
                        'username': row[1],
                        'first_name': row[2],
                        'last_name': row[3],
                        'email': row[4]
                    }
                    for row in result
                ]

                # Create options for Select widget
                options = [
                    (f"{user['username']} ({user['first_name']} {user['last_name']})", str(user['user_id']))
                    for user in self._all_users
                ]

                yield Select(
                    options=options,
                    prompt="Choose a user...",
                    id="user-select",
                    allow_blank=False
                )

            except Exception as e:
                self.app.notify(f"Error loading users: {str(e)}", severity="error")
                self.app.log(f"Error loading users: {e}")
                yield Static(f"Error loading users: {str(e)}", classes="error-message")
        else:
            # Regular user can only see their own info
            yield Static("Your User Information", classes="form-label")
            yield Static("You can modify your own account details", classes="info-message")

        with ScrollableContainer(id="form-content"):
            with Vertical(id="form-user-area"):
                # User form fields will be populated after mounting
                # For admin: show placeholder until user selects from dropdown
                # For regular user: will load via on_mount
                yield Static("Please select a user from the dropdown above" if self._is_admin else "Loading your user information...",
                           id="placeholder-message",
                           classes="placeholder-message")

        with Grid(id="action-buttons"):
            yield Button("Update User", id="user-update-button")
            yield Button("Reset", id="user-reset-button")
            yield Button("Cancel", id="user-cancel-button")

    def _create_user_form_fields(self, user_id: int) -> list:
        """Create form fields for the selected user."""
        fields = []

        try:
            dbh = self.app._config["dbh"]
            dbh.load()
            query = f"""
                SELECT user_id, first_name, last_name, username, birthday, email,
                       password_hash, created_at, activated, is_superuser, scope,
                       max_projects, unique_identifier
                FROM p{dbh._db_salt}_users
                WHERE user_id = ?
            """
            result = dbh.execute_query(query, [user_id])
            dbh.close()

            if not result:
                fields.append(Static("User not found", classes="error-message"))
                return fields

            user_data = result[0]

            # First Name
            fields.append(Static("First Name *", classes="form-label"))
            fields.append(Input(
                value=user_data[1] or "",
                id="user-first-name",
                placeholder="Enter first name"
            ))

            # Last Name
            fields.append(Static("Last Name *", classes="form-label"))
            fields.append(Input(
                value=user_data[2] or "",
                id="user-last-name",
                placeholder="Enter last name"
            ))

            # Username
            fields.append(Static("Username *", classes="form-label"))
            fields.append(Input(
                value=user_data[3] or "",
                id="user-username",
                placeholder="Enter username"
            ))

            # Email
            fields.append(Static("Email *", classes="form-label"))
            fields.append(Input(
                value=user_data[5] or "",
                id="user-email",
                placeholder="Enter email address"
            ))

            # Birthday (optional)
            fields.append(Static("Birthday (YYYY-MM-DD)", classes="form-label"))
            fields.append(Input(
                value=user_data[4] or "",
                id="user-birthday",
                placeholder="YYYY-MM-DD"
            ))

            # Scope
            fields.append(Static("Scope *", classes="form-label"))
            fields.append(Input(
                value=user_data[10] or "user:write",
                id="user-scope",
                placeholder="user:write, admin:full, etc."
            ))

            # Max Projects (only editable by admin)
            if self._is_admin:
                fields.append(Static("Maximum Projects * (Admin Only)", classes="form-label"))
                fields.append(Input(
                    value=str(user_data[11] or 3),
                    id="user-max-projects",
                    placeholder="Number of allowed projects"
                ))
            else:
                fields.append(Static(f"Maximum Projects: {user_data[11]} (Contact admin to change)",
                                   classes="info-label"))

            # Unique Identifier (read-only)
            fields.append(Static("Unique Identifier (Cannot be changed)", classes="form-label"))
            fields.append(Static(
                user_data[12] or "N/A",
                id="user-unique-identifier-display",
                classes="readonly-field"
            ))

            # Is Superuser (admin only)
            if self._is_admin:
                fields.append(Static(f"Superuser Status: {'Yes' if user_data[9] else 'No'}",
                                   classes="info-label"))

            # Activated status (admin only)
            if self._is_admin:
                fields.append(Static(f"Account Status: {'Active' if user_data[8] else 'Inactive'}",
                                   classes="info-label"))

            # Created at
            fields.append(Static(f"Account Created: {user_data[7] or 'Unknown'}",
                               classes="info-label"))

        except Exception as e:
            self.app.notify(f"Error loading user data: {str(e)}", severity="error")
            self.app.log(f"Error loading user data: {e}")
            fields.append(Static(f"Error: {str(e)}", classes="error-message"))

        return fields

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle user selection change (admin only)."""
        if event.select.id == "user-select" and self._is_admin:
            try:
                selected_user_id = int(event.value)
                self._selected_user_id = selected_user_id
                self._load_user_form(selected_user_id)
                self.app.log(f"Selected user ID: {selected_user_id}")
            except (ValueError, TypeError) as e:
                self.app.notify(f"Invalid user selection: {str(e)}", severity="error")

    def _load_user_form(self, user_id: int) -> None:
        """Load and display the user form for the selected user."""
        try:
            # Get the form area
            form_area = self.query_one("#form-user-area", Vertical)

            # Check if form already has widgets (reload case)
            existing_widgets = list(form_area.query("Input, Static"))

            if existing_widgets and any(w.id and w.id.startswith("user-") for w in existing_widgets):
                # Form already loaded - update existing widget values instead of recreating
                self._update_form_values(user_id)
            else:
                # First load - create and mount widgets
                # Remove any placeholders
                for child in list(form_area.children):
                    child.remove()

                # Create all form fields
                fields = self._create_user_form_fields(user_id)

                # Mount all fields at once
                if fields:
                    form_area.mount(*fields)

        except Exception as e:
            self.app.notify(f"Error loading user form: {str(e)}", severity="error")
            self.app.log(f"Error in _load_user_form: {e}")

    def _update_form_values(self, user_id: int) -> None:
        """Update existing form widget values without recreating them."""
        try:
            dbh = self.app._config["dbh"]
            dbh.load()
            query = f"""
                SELECT user_id, first_name, last_name, username, birthday, email,
                       password_hash, created_at, activated, is_superuser, scope,
                       max_projects, unique_identifier
                FROM p{dbh._db_salt}_users
                WHERE user_id = ?
            """
            result = dbh.execute_query(query, [user_id])
            dbh.close()

            if not result:
                self.app.notify("User not found", severity="error")
                return

            user_data = result[0]

            # Update Input widgets
            try:
                self.query_one("#user-first-name", Input).value = user_data[1] or ""
            except:
                pass

            try:
                self.query_one("#user-last-name", Input).value = user_data[2] or ""
            except:
                pass

            try:
                self.query_one("#user-username", Input).value = user_data[3] or ""
            except:
                pass

            try:
                self.query_one("#user-email", Input).value = user_data[5] or ""
            except:
                pass

            try:
                self.query_one("#user-birthday", Input).value = user_data[4] or ""
            except:
                pass

            try:
                self.query_one("#user-scope", Input).value = user_data[10] or "user:write"
            except:
                pass

            # Update max_projects if it exists (admin only)
            if self._is_admin:
                try:
                    self.query_one("#user-max-projects", Input).value = str(user_data[11] or 3)
                except:
                    pass

            self.app.log(f"Updated form values for user {user_id}")

        except Exception as e:
            self.app.notify(f"Error updating form values: {str(e)}", severity="error")
            self.app.log(f"Error in _update_form_values: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "user-cancel-button":
            self.app.notify("User modification cancelled", severity="info")
        elif event.button.id == "user-reset-button":
            self._reset_form()
        elif event.button.id == "user-update-button":
            self._update_user()

    def _reset_form(self) -> None:
        """Reset the form to original values."""
        if self._selected_user_id:
            self._load_user_form(self._selected_user_id)
            self.app.notify("Form reset to original values", severity="info")
        else:
            self.app.notify("No user selected", severity="warning")

    def _update_user(self) -> None:
        """Validate and update the user."""
        if not self._selected_user_id:
            self.app.notify("No user selected", severity="error")
            return

        try:
            # Get form values
            first_name = self.query_one("#user-first-name", Input).value.strip()
            last_name = self.query_one("#user-last-name", Input).value.strip()
            username = self.query_one("#user-username", Input).value.strip()
            email = self.query_one("#user-email", Input).value.strip()
            birthday = self.query_one("#user-birthday", Input).value.strip()
            scope = self.query_one("#user-scope", Input).value.strip()

            # Validate required fields
            if not first_name:
                self.app.notify("First name is required", severity="error")
                return
            if not last_name:
                self.app.notify("Last name is required", severity="error")
                return
            if not username:
                self.app.notify("Username is required", severity="error")
                return
            if not email:
                self.app.notify("Email is required", severity="error")
                return
            if not scope:
                self.app.notify("Scope is required", severity="error")
                return

            # Validate email format (basic)
            if "@" not in email or "." not in email:
                self.app.notify("Invalid email format", severity="error")
                return

            # Build update dict
            update_data = {
                'first_name': first_name,
                'last_name': last_name,
                'username': username,
                'email': email,
                'scope': scope
            }

            # Add birthday if provided
            if birthday:
                # Validate date format
                try:
                    datetime.strptime(birthday, "%Y-%m-%d")
                    update_data['birthday'] = birthday
                except ValueError:
                    self.app.notify("Invalid birthday format. Use YYYY-MM-DD", severity="error")
                    return

            # Max projects (admin only)
            if self._is_admin:
                try:
                    max_projects_input = self.query_one("#user-max-projects", Input)
                    max_projects = int(max_projects_input.value.strip())
                    if max_projects < 1:
                        self.app.notify("Max projects must be at least 1", severity="error")
                        return
                    update_data['max_projects'] = max_projects
                except ValueError:
                    self.app.notify("Max projects must be a valid number", severity="error")
                    return
                except Exception:
                    # Field doesn't exist (non-admin user)
                    pass

            # Update database
            dbh = self.app._config["dbh"]
            dbh.load()

            # Build dynamic UPDATE query
            set_clauses = []
            params = []
            for key, value in update_data.items():
                set_clauses.append(f"{key} = ?")
                params.append(value)

            params.append(self._selected_user_id)

            query = f"""
                UPDATE p{dbh._db_salt}_users
                SET {', '.join(set_clauses)}
                WHERE user_id = ?
            """

            dbh.execute_query(query, params)
            dbh.close()

            self.app.notify(f"User '{username}' updated successfully!", severity="information")
            self.app.log(f"Updated user {self._selected_user_id}: {update_data}")

            # Post message
            self.post_message(self.UserModified(update_data))

            # Reload form to show updated values
            self._load_user_form(self._selected_user_id)

        except Exception as e:
            self.app.notify(f"Error updating user: {str(e)}", severity="error")
            self.app.log(f"Error in _update_user: {e}")
