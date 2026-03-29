"""Settings screen - configure application settings."""
from textual.screen import ModalScreen, Screen
from textual.containers import Vertical, Horizontal, ScrollableContainer, Container
from textual.widgets import Static, Button
from textual.app import ComposeResult
from fiwa_cli.components import FiwaHeader


from fiwa_cli.functions.loader import load_dynamic_css

# from .settings_project_new import CreateProjectModal
from .settings_project_new import CreateProjectForm
from .settings_project_modify import ModifyProjectForm
from .settings_user_new import CreateUserForm
from .settings_user_modify import ModifyUserForm
from .settings_label_page import LabelManagementForm
from .settings_label_new import CreateLabelForm

from .base import ReactiveScreen


class SettingsScreen(ReactiveScreen):
    """Settings screen - configure application settings."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize with current login state to avoid initial rebuild
        self._last_login_state = self.app.app_state.get("is_logged_in", False)
        self._mounted = False

    def compose(self) -> ComposeResult:

        yield FiwaHeader(
            user=self.app.app_state["user_name"],
            projects=self.app.app_state["project_names"],
            project_id=self.app.app_state["project_id"],
            project_ids=self.app.app_state["project_ids"]
        )
        #yield Static("Settings", id="settings-title")
        #yield Static(str(self.app.app_state["is_logged_in"]), id="login-status")
        # Add create project button
        with Container(id="container-body"):
            with ScrollableContainer(id="container-sidebar"):
                if self.app.app_state["is_logged_in"] is True:
                    yield Static("Project Management", classes="menu-section")
                    yield Button("+ Create Project",
                                 id="create-project-button",
                                 classes="sidebar-menu-button",
                                 variant="default")
                    yield Button("= Modify Project",
                                 id="modify-project-button",
                                 classes="sidebar-menu-button",
                                 variant="default")

                    yield Static("Label Management", classes="menu-section")
                    yield Button("+ Create Label",
                                 id="create-label-button",
                                 classes="sidebar-menu-button",
                                 variant="default")
                    yield Button("= Manage Labels",
                                 id="manage-labels-button",
                                 classes="sidebar-menu-button",
                                 variant="default")

                    yield Static("User Management", classes="menu-section")
                    yield Button("+ Create User",
                                 id="create-user-button",
                                 classes="sidebar-menu-button",
                                 variant="default")
                    yield Button("= Modify User",
                                 id="modify-user-button",
                                 classes="sidebar-menu-button",
                                 variant="default")
                    yield Button("Back", id="menu-back-button",
                                 classes="sidebar-menu-button",
                                 variant="primary",
                                 flat=True)
                else:
                    yield Static("Please login to access settings", classes="menu-section")

                    # Always show Back button
                    yield Button("Back", id="menu-back-button",
                                 variant="primary")

            # Right content area
            with ScrollableContainer(id="settings-content-area"):
                yield Static("Select an option from the menu", id="content-display")
                m = """
 ____       _   _   _                 
/ ___|  ___| |_| |_(_)_ __   __ _ ___ 
\___ \ / _ \ __| __| | '_ \ / _` / __|
 ___) |  __/ |_| |_| | | | | (_| \__ \\
|____/ \___|\__|\__|_|_| |_|\__, |___/
                            |___/"""
                yield Static(m)

        # yield Button("Back", id="back-button", variant="primary")

    def on_mount(self) -> None:
        """Called when screen is mounted. Set up watchers."""
        super().on_mount()

        load_dynamic_css(self, css_filename="screens_settings.tcss")

        self._mounted = True
        self.app.log("SettingsScreen mounted")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "menu-back-button":
            self._return_to_main_screen()

        elif event.button.id == "create-project-button":
            # show a notification:
            # self.app.push_screen(CreateProjectForm(), self.handle_new_project)
            self.show_create_project_form()
        elif event.button.id == "modify-project-button":
            self.show_modify_project_form()
        elif event.button.id == "create-user-button":
            # self.show_content("Create User", "User creation interface coming soon...")
            self.show_create_user_form()
        elif event.button.id == "modify-user-button":
            self.show_modify_user_form()
        elif event.button.id == "currency-settings-button":
            self.show_content("Currency Settings", "Currency configuration interface coming soon...")
        elif event.button.id == "create-label-button":
            self.show_create_label_form()
        elif event.button.id == "manage-labels-button":
            self.show_label_management_form()
        elif event.button.id == "api-config-button":
            self.show_content("API Configuration", "API configuration interface coming soon...")
        elif event.button.id == "confirmation-ok-button":
            # Clear confirmation and show default message
            self.show_content("Settings", "Select an option from the menu")


    def show_content(self, title: str, message: str) -> None:
        """Update the content area with new information."""
        content_area = self.query_one("#settings-content-area", ScrollableContainer)
        content_area.remove_children()
        content_area.mount(Static(f"[bold]{title}[/bold]\n\n{message}",
                                  # id="content-display"
                                  )
                           )

    def show_create_project_form(self) -> None:
        """Show the create project form in the content area."""
        content_area = self.query_one("#settings-content-area", ScrollableContainer)
        content_area.remove_children()
        form = CreateProjectForm()
        form.on_mount()
        content_area.mount(form)

    def show_modify_project_form(self) -> None:
        """Show the modify project form in the content area."""
        content_area = self.query_one("#settings-content-area", ScrollableContainer)
        content_area.remove_children()

        form = ModifyProjectForm()
        form.on_mount()
        content_area.mount(form)

    def show_create_user_form(self) -> None:
        """Show the create user form in the content area."""
        content_area = self.query_one("#settings-content-area", ScrollableContainer)
        content_area.remove_children()
        form = CreateUserForm()
        form.on_mount()
        content_area.mount(form)

    def show_modify_user_form(self) -> None:
        """Show the modify user form in the content area."""
        content_area = self.query_one("#settings-content-area", ScrollableContainer)
        content_area.remove_children()

        form = ModifyUserForm()
        form.on_mount()
        content_area.mount(form)

    def show_label_management_form(self) -> None:
        """Show the label management form in the content area."""
        content_area = self.query_one("#settings-content-area", ScrollableContainer)
        content_area.remove_children()
        form = LabelManagementForm()
        form.on_mount()
        content_area.mount(form)

    def show_create_label_form(self) -> None:
        """Show the create label form in the content area."""
        content_area = self.query_one("#settings-content-area", ScrollableContainer)
        content_area.remove_children()
        form = CreateLabelForm()
        form.on_mount()
        content_area.mount(form)

    def on_create_project_form_project_created(self, message: CreateProjectForm.ProjectCreated) -> None:
        """
        Handle the ProjectCreated message from CreateProjectForm.
        Creates the project in the database and updates app_state.
        """
        from fiwa_cli.functions.project_composer import ProjectComposer

        try:
            dbh = self.app._config["dbh"]
            user_id = self.app.app_state.get("user_id", -1)

            if user_id <= 0:
                self.notify("Error: No user logged in", severity="error")
                return

            # extract the project style from the message: we need it
            # to finish the project build phase and set up the minimum required structure
            # of the project.
            project_style = message.project_data.get("project_style", "ExpenseTracker")

            # Create project in database
            project_id = dbh.op_project_create(message.project_data, user_id)

            if not project_id:
                self.notify("Failed to create project", severity="error")
                return

            # Fetch updated project list for the user
            project_info = dbh.op_project_get_info(user_id)

            # Finish project setup based on style:
            compose_users =[
                {"user_id": user_id,
                 "username": self.app.app_state.get("user_name", "Unknown")}
            ]

            pc = ProjectComposer.create(compose_type=project_style,
                                        dbh=dbh,
                                        project_id=project_id,
                                        users=compose_users)

            pc.build()            # prepare the project
            pc.compose_accounts() # prepare the default accounts

            # Extract project data for app_state
            project_names = []
            project_ids = []
            primary_project_id = 0
            primary_project_style = "default"
            primary_project_name = "No Project"
            primary_project_store = {}

            if project_info and len(project_info) > 0:
                for project in project_info:
                    project_ids.append(project["project_id"])
                    project_names.append(project["project_name"])
                    if project.get("project_primary", False):
                        primary_project_id = project["project_id"]
                        primary_project_style = project.get("project_style", "default")
                        primary_project_name = project.get("project_name", "No Project")
                        primary_project_store = project.get("project_store", {})

                # If no primary project, use the newly created one
                if primary_project_id == 0:
                    primary_project_id = project_id
                    # Find the newly created project details
                    new_project = next((p for p in project_info if p["project_id"] == project_id), None)
                    if new_project:
                        primary_project_style = new_project.get("project_style", "default")
                        primary_project_name = new_project.get("project_name", "No Project")
                        primary_project_store = new_project.get("project_store", {})

            # Update app_state with new project information
            self.app.app_state = {
                **self.app.app_state,
                "project_names": project_names,
                "project_ids": project_ids,
                "project_id": primary_project_id,
                "project_style": primary_project_style,
                "project_name": primary_project_name,
                "project_store": primary_project_store,
            }

            self.notify(
                f"Project '{message.project_data['name']}' created successfully! "
                f"You can now select it from the project menu.",
                severity="information"
            )

            # Show success message
            self.show_content(
                "Project Created",
                f"Successfully created: {message.project_data['name']}\n\n"
                f"Project ID: {project_id}\n"
                f"You can now switch to this project using the project selector."
            )

        except ValueError as e:
            self.notify(f"Failed to create project: {str(e)}", severity="error")
        except Exception as e:
            self.notify(f"Error creating project: {str(e)}", severity="error")

    def on_modify_project_form_project_modified(self, message: ModifyProjectForm.ProjectModified) -> None:
        """Handle the ProjectModified message from ModifyProjectForm."""
        self.notify(f"Project '{message.project_data['name']}' updated!", severity="information")

        # Update the app_state with the new project name if it changed
        project_ids = self.app.app_state.get("project_ids", [])
        project_names = self.app.app_state.get("project_names", [])
        current_project_id = self.app.app_state.get("project_id", 0)

        if current_project_id in project_ids:
            idx = project_ids.index(current_project_id)
            project_names[idx] = message.project_data['name']
            self.app.app_state["project_names"] = project_names

        # Show confirmation with OK button
        self.show_project_update_confirmation(message.project_data)

    def show_project_update_confirmation(self, project_data: dict) -> None:
        """Show confirmation message after project update."""
        content_area = self.query_one("#settings-content-area", ScrollableContainer)
        content_area.remove_children()

        # Mount the container first, then add children
        confirmation_widget = Vertical()
        content_area.mount(confirmation_widget)

        # Now mount children to the attached container
        confirmation_widget.mount(Static(f"[bold green]✓ Project Updated Successfully[/bold green]\n", classes="success-message"))
        confirmation_widget.mount(Static(f"Project Name: {project_data['name']}", classes="detail"))
        confirmation_widget.mount(Static(f"Description: {project_data.get('description', 'N/A')}", classes="detail"))
        confirmation_widget.mount(Static(f"Main Currency: {project_data.get('currency_main', 'N/A')}", classes="detail"))
        confirmation_widget.mount(Static(f"Currency List: {', '.join(project_data.get('currency_list', []))}", classes="detail"))
        confirmation_widget.mount(Static("\n"))
        confirmation_widget.mount(Button("OK", id="confirmation-ok-button", variant="success"))

    def on_create_user_form_user_created(self, message: CreateUserForm.UserCreated) -> None:
        """Handle the UserCreated message from CreateUserForm."""
        self.notify(f"User '{message.user_data['username']}' created!", severity="information")
        self.show_content("User Created", f"Successfully created: {message.user_data['username']}")

    def on_label_management_form_labels_modified(self, message: LabelManagementForm.LabelsModified) -> None:
        """Handle the LabelsModified message from LabelManagementForm."""
        summary = message.changes_summary
        self.notify(
            f"Label changes saved: {summary['new_labels']} new, {summary['modified_labels']} modified",
            severity="information"
        )
        # Reload the form to show updated data
        self.show_label_management_form()

    def on_label_management_form_new_label_requested(self, message: LabelManagementForm.NewLabelRequested) -> None:
        """Handle the NewLabelRequested message from LabelManagementForm."""
        # Switch to the CreateLabelForm
        self.show_create_label_form()

    def on_create_label_form_label_created(self, message: CreateLabelForm.LabelCreated) -> None:
        """Handle the LabelCreated message from CreateLabelForm."""
        self.notify(f"Label '{message.label_data['name']}' created!", severity="information")
        # Show the label management form to see all labels including the new one
        self.show_label_management_form()

    def update_displays(self) -> None:
        """Update displays when app_state changes."""
        try:
            session_widget = self.query_one("#login-status", Static)
            session_widget.update(f"{self.app.app_state['is_logged_in']}")
        except Exception as e:
            self.app.log(f"Error updating login status: {e}")

        try:
            # Update header if needed
            header = self.query_one(FiwaHeader)
            header.user = self.app.app_state["user_name"]
            header.projects = self.app.app_state["project_names"]
            header.project_id = self.app.app_state["project_id"]
            header.project_ids = self.app.app_state["project_ids"]
        except Exception as e:
            self.app.log(f"Error updating header: {e}")

        # Only rebuild sidebar if screen is mounted AND login state has changed
        if not self._mounted:
            self.app.log("Screen not yet mounted, skipping sidebar rebuild")
            return

        current_login_state = self.app.app_state.get("is_logged_in", False)
        if self._last_login_state != current_login_state:
            self.app.log(f"Login state changed from {self._last_login_state} to {current_login_state}")
            self._last_login_state = current_login_state
            try:
                self._rebuild_sidebar()
            except Exception as e:
                self.app.log(f"Error rebuilding sidebar: {e}")
        else:
            self.app.log(f"Login state unchanged ({current_login_state}), not rebuilding sidebar")

    def _rebuild_sidebar(self) -> None:
        """Rebuild the sidebar menu based on login state."""
        try:
            sidebar = self.query_one("#settings-sidebar", ScrollableContainer)
        except Exception as e:
            self.app.log(f"Could not find sidebar: {e}")
            return

        # Log current state
        is_logged_in = self.app.app_state.get("is_logged_in", False)
        self.app.log(f"Rebuilding sidebar with is_logged_in={is_logged_in}")

        # Remove all children
        sidebar.remove_children()

        # Rebuild sidebar based on login state
        if is_logged_in is True:
            self.app.log("Mounting logged-in menu items")
            sidebar.mount(Static("Project Management", classes="menu-section"))
            sidebar.mount(Button("+ Create Project", id="create-project-button",
                         variant="default"))
            sidebar.mount(Button("= Modify Project", id="modify-project-button",
                         variant="default"))

            sidebar.mount(Static("Label Management", classes="menu-section"))
            sidebar.mount(Button("+ Create Label", id="create-label-button",
                         variant="default"))
            sidebar.mount(Button("= Manage Labels", id="manage-labels-button",
                         variant="default"))

            sidebar.mount(Static("User Management", classes="menu-section"))
            sidebar.mount(Button("+ Create User", id="create-user-button",
                         variant="default"))
            sidebar.mount(Button("= Modify User", id="modify-user-button",
                         variant="default"))
        else:
            self.app.log("Mounting logged-out message")
            sidebar.mount(Static("Please login to access settings", classes="menu-section"))

        # Always show Back button at the bottom
        sidebar.mount(Button("Back", id="menu-back-button", variant="primary"))

        # Force refresh the sidebar
        sidebar.refresh()
        self.app.log(f"Sidebar rebuilt with {len(sidebar.children)} children")

    def _return_to_main_screen(self) -> None:
        """Pop all screens to return to the main screen."""
        try:
            # Pop all screens except the main screen
            while len(self.app.screen_stack) > 1:
                self.app.pop_screen()
        except Exception as e:
            self.app.log(f"Error returning to main screen: {e}")
