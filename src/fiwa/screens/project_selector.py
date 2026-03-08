"""Project selector screen."""
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Static, OptionList
from textual.widgets.option_list import Option
from textual.app import ComposeResult

from fiwa.functions.loader import load_dynamic_css

class ProjectSelectorScreen(ModalScreen):
    """Screen to select a project from available projects."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    # DEFAULT_CSS = """
    #
    # """
    def on_mount(self) -> None:
        """Load CSS when screen is mounted."""
        try:
            load_dynamic_css(self, "screens_project_selection.tcss")
        except Exception as e:
            self.app.log(f"Could not load CSS for ProjectSelectorScreen: {e}")

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Select a Project", id="project-title")
            # Get projects from app store
            project_names = self.app.app_state.get("project_names", ["No Projects"])
            project_ids = self.app.app_state.get("project_ids", [0])
            current_project_id = self.app.app_state.get("project_id", 0)

            # Create options for each project
            options = []
            for idx, (proj_id, proj_name) in enumerate(zip(project_ids, project_names)):
                # Mark current project with arrow
                prompt = f"► {proj_name}" if proj_id == current_project_id else f"  {proj_name}"
                options.append(Option(prompt, id=f"project-{proj_id}"))

            yield OptionList(*options)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle project selection."""
        # Extract project ID from option id (format: "project-1", "project-2", etc.)
        option_id = event.option.id
        if option_id and option_id.startswith("project-"):
            selected_project_id = int(option_id.split("-")[1])

            # Update the app's store with the new primary project ID
            self.app.app_state["project_id"] = selected_project_id

            # Find the project name for notification
            project_ids = self.app.app_state.get("project_ids", [])
            project_names = self.app.app_state.get("project_names", [])

            project_name = "Unknown Project"
            if selected_project_id in project_ids:
                idx = project_ids.index(selected_project_id)
                project_name = project_names[idx]

            # Load currency information for the selected project
            self._load_project_currency(selected_project_id)

            # Explicitly update the header to reflect the new project BEFORE dismissing
            self._refresh_header()

            # Notify and dismiss
            self.app.notify(f"Switched to project: {project_name}")
            self.dismiss()
        else:
            # If no valid selection, just dismiss
            self.dismiss()

    def _load_project_currency(self, project_id: int) -> None:
        """Load currency information for the selected project into app_state."""
        try:
            dbh = self.app._config.get("dbh")
            if not dbh:
                return

            # Get project info
            user_id = self.app.app_state.get("user_id", -1)
            project_info_list = dbh.op_project_get_info(user_id)

            # Find the selected project
            project = next((p for p in project_info_list if p["project_id"] == project_id), None)

            if project:
                import json
                currency_main = project.get("currency_main", "USD")
                currency_list_str = project.get("currency_list", "[]")
                try:
                    currency_list = json.loads(currency_list_str) if currency_list_str else []
                except:
                    currency_list = []

                self.app.app_state["current_project_currency_main"] = currency_main
                self.app.app_state["current_project_currency_list"] = currency_list
                self.app.log(f"Loaded currencies for project {project_id}: {currency_main}, {currency_list}")
        except Exception as e:
            self.app.log(f"Error loading project currency: {e}")

    def _refresh_header(self) -> None:
        """Refresh the header to display the updated project."""
        try:
            from components.header import FiwaHeader
            header = self.app.query_one(FiwaHeader)
            header.project_id = self.app.app_state["project_id"]
            header.project_ids = self.app.app_state["project_ids"]
            header.projects = self.app.app_state["project_names"]
            header.refresh()
        except Exception as e:
            # Header might not be available yet or other error
            self.app.log(f"Could not refresh header: {e}")

    def action_cancel(self) -> None:
        """Handle escape key press - dismiss modal without selecting a project."""
        self.dismiss()

