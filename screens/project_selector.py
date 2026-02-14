"""Project selector screen."""
from textual.screen import ModalScreen
from textual.containers import Vertical
from textual.widgets import Static, OptionList
from textual.widgets.option_list import Option
from textual.app import ComposeResult

class ProjectSelectorScreen(ModalScreen):
    """Screen to select a project from available projects."""

    DEFAULT_CSS = """
    ProjectSelectorScreen {
        align: center middle;
    }

    ProjectSelectorScreen > Vertical {
        width: 50;
        height: auto;
        max-height: 30;
        background: $surface;
        border: solid $accent;
        padding: 1;
    }

    ProjectSelectorScreen #project-title {
        text-style: bold;
        padding: 0 0 1 0;
        text-align: center;
    }

    ProjectSelectorScreen OptionList {
        height: auto;
        max-height: 20;
    }
    """

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

            # Explicitly update the header to reflect the new project BEFORE dismissing
            self._refresh_header()

            # Notify and dismiss
            self.app.notify(f"Switched to project: {project_name}")
            self.dismiss()
        else:
            # If no valid selection, just dismiss
            self.dismiss()

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
