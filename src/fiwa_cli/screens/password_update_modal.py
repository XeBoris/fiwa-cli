"""Password update modal screen."""
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Input
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult


class PasswordUpdateModal(ModalScreen):
    """Modal screen for updating user password.

    Allows users to change their password by entering:
    - Old password (for verification)
    - New password (to set)

    Returns True if password was updated successfully, False otherwise.
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, user_id: int, username: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = user_id
        self.username = username

    CSS = """
    PasswordUpdateModal {
        align: center middle;
    }
    
    PasswordUpdateModal > Vertical {
        width: 60;
        height: auto;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    
    .modal-title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    
    .form-label {
        margin-top: 1;
        color: $text;
    }
    
    .password-input {
        width: 100%;
        margin-bottom: 1;
    }
    
    .info-message {
        color: $text-muted;
        text-style: italic;
        margin-bottom: 1;
    }
    
    .button-row {
        width: 100%;
        height: auto;
        margin-top: 1;
        align: center middle;
    }
    
    .button-row Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(f"Update Password for: {self.username}", classes="modal-title")
            yield Static("Enter your current password and new password", classes="info-message")

            # Old password
            yield Static("Current Password *", classes="form-label")
            yield Input(
                placeholder="Enter current password",
                password=True,
                id="old-password-input",
                classes="password-input"
            )

            # New password
            yield Static("New Password *", classes="form-label")
            yield Input(
                placeholder="Enter new password",
                password=True,
                id="new-password-input",
                classes="password-input"
            )

            # Confirm new password
            yield Static("Confirm New Password *", classes="form-label")
            yield Input(
                placeholder="Re-enter new password",
                password=True,
                id="confirm-password-input",
                classes="password-input"
            )

            with Horizontal(classes="button-row"):
                yield Button("✓ Update Password", id="ok-button", variant="success")
                yield Button("✗ Cancel", id="cancel-button", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the modal."""
        if event.button.id == "ok-button":
            self._update_password()
        elif event.button.id == "cancel-button":
            self.dismiss(False)

    def action_cancel(self) -> None:
        """Handle escape key press."""
        self.dismiss(False)

    def _update_password(self) -> None:
        """Validate and update the password."""
        try:
            # Get input values
            old_password = self.query_one("#old-password-input", Input).value
            new_password = self.query_one("#new-password-input", Input).value
            confirm_password = self.query_one("#confirm-password-input", Input).value

            # Validate inputs
            if not old_password:
                self.app.notify("Current password is required", severity="error")
                return

            if not new_password:
                self.app.notify("New password is required", severity="error")
                return

            if not confirm_password:
                self.app.notify("Please confirm your new password", severity="error")
                return

            # Check if new passwords match
            if new_password != confirm_password:
                self.app.notify("New passwords do not match!", severity="error")
                return

            # Validate password strength (minimum 6 characters)
            if len(new_password) < 6:
                self.app.notify("New password must be at least 6 characters long", severity="error")
                return

            # Get database handler
            dbh = self.app._config.get("dbh")
            if not dbh:
                self.app.notify("Database connection not available", severity="error")
                return

            # Verify old password and update
            success = dbh.op_user_update_password(
                user_id=self.user_id,
                old_password=old_password,
                new_password=new_password
            )

            if success:
                self.app.notify(f"✓ Password updated successfully for {self.username}!", severity="success")
                self.dismiss(True)
            else:
                self.app.notify("Current password is incorrect", severity="error")

        except Exception as e:
            self.app.notify(f"Error updating password: {str(e)}", severity="error")
            self.app.log(f"Error in _update_password: {e}")
