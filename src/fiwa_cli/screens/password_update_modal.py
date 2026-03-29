"""Password update modal for FiWa CLI.

This module provides a secure interface for users to change their passwords.
It implements a three-field password update system with validation and
verification of the current password before allowing changes.

The password update process:
    - Requires current password for verification
    - Enforces minimum password length (6 characters)
    - Requires new password confirmation to prevent typos
    - Uses bcrypt for secure password hashing
    - Validates against database before updating

Security Features:
    - Current password verification via bcrypt hash comparison
    - New password confirmation (must enter twice)
    - Password strength validation (minimum 6 characters)
    - Masked input fields (password=True) - characters hidden
    - No plain text password storage or transmission
    - Database-level password hashing

Key Features:
    - Modal dialog centered on screen
    - Three password input fields (current, new, confirm)
    - Clear visual feedback with icons
    - Validation before database update
    - Success/error notifications
    - Escape key to cancel
    - Returns boolean result (True=success, False=canceled/failed)

Classes:
    PasswordUpdateModal: Modal screen for password updates

Example:
    Opening the modal (in async context)::

        >>> from fiwa_cli.screens.password_update_modal import PasswordUpdateModal
        >>> modal = PasswordUpdateModal(user_id=1, username="batman")
        >>> async def update_password():
        >>>     result = await self.app.push_screen_wait(modal)
        >>>     if result:
        >>>         self.notify("Password updated!")

    From settings screen::

        >>> # User in ModifyUserForm
        >>> # User clicks "Update Password" button
        >>> # PasswordUpdateModal opens
        >>> # User enters:
        >>> #   Current Password: ********
        >>> #   New Password: ************
        >>> #   Confirm: ************
        >>> # User clicks "✓ Update Password"
        >>> # System verifies current password
        >>> # System hashes new password
        >>> # Database updated
        >>> # Modal closes with True
        >>> # Success notification shown

Validation Rules:
    1. Current password must not be empty
    2. New password must not be empty
    3. Confirm password must not be empty
    4. New password must match confirm password
    5. New password must be at least 6 characters
    6. Current password must match database hash

Error Messages:
    - "Current password is required"
    - "New password is required"
    - "Please confirm your new password"
    - "New passwords do not match!"
    - "New password must be at least 6 characters long"
    - "Current password is incorrect"
    - "Database connection not available"

See Also:
    settings_user_modify: User modification screen that opens this modal
    functions.handler_sqllite.op_user_update_password: Database operation
"""
from textual.screen import ModalScreen
from textual.widgets import Static, Button, Input
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult


class PasswordUpdateModal(ModalScreen):
    """Modal screen for secure password updates.

    This modal provides a secure three-field interface for changing user
    passwords. It verifies the current password before allowing updates
    and enforces password strength requirements.

    The modal implements a complete password update workflow:
        1. User enters current password (for verification)
        2. User enters new password
        3. User confirms new password (must match)
        4. System validates all inputs
        5. System verifies current password against database
        6. System hashes new password with bcrypt
        7. System updates database
        8. Modal dismisses with success result

    Attributes:
        user_id (int): Database ID of the user updating password
        username (str): Username displayed in modal title

    BINDINGS:
        - Escape: Cancel and close without updating (action_cancel)

    Modal Layout:
        - Title: "Update Password for: {username}"
        - Info message
        - Current Password input (masked)
        - New Password input (masked)
        - Confirm New Password input (masked)
        - Update Password button (success variant)
        - Cancel button (default variant)

    Input Fields:
        All input fields use password=True for security:
            - Characters displayed as bullets (•••)
            - No clipboard copy of masked text
            - Protected from shoulder surfing

    Validation Process:
        1. **Empty field check**: All three fields required
        2. **Match check**: New password must equal confirm password
        3. **Strength check**: Minimum 6 characters
        4. **Verification check**: Current password must match database hash

    Security Implementation:
        - Current password verified via bcrypt.checkpw()
        - New password hashed via bcrypt.hashpw()
        - No plain text passwords logged or stored
        - Hash comparison prevents timing attacks
        - Minimum password length enforced

    Return Value:
        The modal returns via dismiss():
            - True: Password updated successfully
            - False: Canceled or verification failed

    Example:
        Basic usage (async context)::

            >>> async def handle_password_update(self):
            >>>     modal = PasswordUpdateModal(user_id=1, username="batman")
            >>>     result = await self.app.push_screen_wait(modal)
            >>>     if result:
            >>>         self.app.file_log.info("Password updated successfully")
            >>>     else:
            >>>         self.app.file_log.info("Password update canceled")

        Complete workflow::

            >>> # User clicks "Update Password" button
            >>> # Modal opens centered on screen
            >>> # Title shows: "Update Password for: batman"
            >>> # User enters current password: "oldpass123"
            >>> # User enters new password: "newpass456"
            >>> # User confirms: "newpass456"
            >>> # User clicks "✓ Update Password"
            >>> # _update_password() validates inputs
            >>> # All validations pass
            >>> # System calls op_user_update_password()
            >>> # Verifies old password matches hash in database
            >>> # Hashes new password with bcrypt
            >>> # Updates database: users table, password_hash column
            >>> # Returns True
            >>> # Modal shows: "✓ Password updated successfully for batman!"
            >>> # Modal dismisses with True

        Validation failure::

            >>> # User enters current: "wrongpass"
            >>> # User enters new: "short"
            >>> # User enters confirm: "short"
            >>> # User clicks Update
            >>> # Validation fails: "New password must be at least 6 characters"
            >>> # Modal stays open
            >>> # User corrects: new="longpassword123", confirm="longpassword123"
            >>> # User clicks Update
            >>> # Validation passes
            >>> # Database verification fails: "Current password is incorrect"
            >>> # Modal stays open

        Canceling::

            >>> # User opens modal
            >>> # User presses Escape (or clicks Cancel)
            >>> # action_cancel() fires
            >>> # Modal dismisses with False
            >>> # No database changes

    CSS Styling:
        The modal includes inline CSS for:
            - Centered alignment
            - 60-character width
            - Auto height
            - Themed colors ($surface, $primary, $text)
            - Thick primary border
            - Proper spacing and margins

    Error Handling:
        - Empty fields: Shows specific error for each field
        - Password mismatch: Clear error message
        - Too short: Shows minimum length requirement
        - Wrong current password: Indicates verification failure
        - Database errors: Logs exception, shows user-friendly message

    Note:
        The modal uses password=True on all Input fields to mask
        characters with bullets. This is essential for security,
        especially in shared environments or during screen recordings.

        The current password verification prevents unauthorized password
        changes even if someone gains access to an unlocked session.

        Password hashing is handled by the database handler
        (op_user_update_password) which uses bcrypt with appropriate
        salt rounds for security.

    See Also:
        settings_user_modify.ModifyUserForm: Opens this modal
        functions.handler_sqllite.op_user_update_password: Database operation
        bcrypt: Password hashing library (imported in handler)
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
    ]

    def __init__(self, user_id: int, username: str, *args, **kwargs):
        """Initialize the password update modal.

        Args:
            user_id: Database ID of the user whose password will be updated
            username: Username to display in the modal title
            *args: Additional positional arguments for ModalScreen
            **kwargs: Additional keyword arguments for ModalScreen

        Example:
            >>> modal = PasswordUpdateModal(user_id=1, username="batman")
            >>> self.app.push_screen(modal)
        """
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
        """Compose the password update modal interface.

        Creates a centered vertical container with three password input
        fields and action buttons. All password fields are masked for
        security.

        Yields:
            Static: Modal title with username
            Static: Instructional message
            Static: "Current Password *" label
            Input: Current password field (masked)
            Static: "New Password *" label
            Input: New password field (masked)
            Static: "Confirm New Password *" label
            Input: Confirm password field (masked)
            Horizontal: Button row with Update and Cancel buttons

        Form Fields:
            All fields are required (marked with *):
                1. Current Password: For verification
                2. New Password: Desired new password
                3. Confirm New Password: Must match new password

        Visual Design:
            - Centered modal overlay
            - 60 character width
            - Auto height based on content
            - Themed colors and borders
            - Icon-enhanced buttons (✓ and ✗)

        Example:
            Modal appearance::

                ╔══════════════════════════════════════════════════╗
                ║   Update Password for: batman                    ║
                ║   Enter your current password and new password   ║
                ║                                                  ║
                ║   Current Password *                             ║
                ║   [••••••••••••••]                               ║
                ║                                                  ║
                ║   New Password *                                 ║
                ║   [••••••••••••••]                               ║
                ║                                                  ║
                ║   Confirm New Password *                         ║
                ║   [••••••••••••••]                               ║
                ║                                                  ║
                ║        [✓ Update Password]  [✗ Cancel]           ║
                ╚══════════════════════════════════════════════════╝
        """
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
        """Handle button press events in the modal.

        Routes button clicks to appropriate handlers for password update
        or cancellation.

        Args:
            event: Button.Pressed event containing the clicked button

        Handles:
            - ok-button: Validates inputs and updates password
            - cancel-button: Dismisses modal without changes

        Side Effects:
            - Calls _update_password() if Update clicked
            - Dismisses with False if Cancel clicked

        Example:
            User clicks Update::

                >>> # User clicks "✓ Update Password"
                >>> # on_button_pressed fires with ok-button
                >>> # _update_password() called
                >>> # Validation and update process begins
        """
        if event.button.id == "ok-button":
            self._update_password()
        elif event.button.id == "cancel-button":
            self.dismiss(False)

    def action_cancel(self) -> None:
        """Handle escape key press to cancel password update.

        Dismisses the modal without making any changes. This provides
        a quick exit for users who opened the modal by mistake or
        changed their mind.

        Bound to:
            - Escape key

        Side Effects:
            - Dismisses modal with False (update canceled)
            - No database changes
            - No notifications shown

        Example:
            >>> # User opens password modal
            >>> # User presses Escape
            >>> # action_cancel() fires
            >>> # Modal closes immediately
            >>> # Password unchanged in database
        """
        self.dismiss(False)

    def _update_password(self) -> None:
        """Validate inputs and update the user's password in the database.

        Performs comprehensive validation of all password fields, verifies
        the current password against the database, and updates with the
        new password if all checks pass.

        Validation Steps:
            1. Check current password not empty
            2. Check new password not empty
            3. Check confirm password not empty
            4. Verify new == confirm passwords
            5. Verify new password >= 6 characters
            6. Verify database connection available
            7. Verify current password matches database hash
            8. Update password in database

        Side Effects:
            - Queries database to verify current password
            - Updates database with new password hash
            - Shows error notifications for validation failures
            - Shows success notification on successful update
            - Dismisses modal with True on success
            - Stays open on validation failure (allows retry)
            - Logs all errors for debugging

        Database Operation:
            Calls op_user_update_password(user_id, old_password, new_password):
                - Retrieves user's current password hash
                - Verifies old_password with bcrypt.checkpw()
                - Hashes new_password with bcrypt.hashpw()
                - Updates users table with new hash
                - Returns True on success, False if verification failed

        Error Handling:
            Each validation failure shows specific error message:
                - Missing fields: Shows which field is empty
                - Mismatch: "New passwords do not match!"
                - Too short: "Must be at least 6 characters long"
                - Wrong current: "Current password is incorrect"
                - Database error: "Database connection not available"
                - Exception: Shows error message and logs details

        Example:
            Successful update::

                >>> # User enters:
                >>> #   Current: "oldpass123"
                >>> #   New: "newpass456"
                >>> #   Confirm: "newpass456"
                >>> # _update_password() called
                >>> # Validations: ✓ All pass
                >>> # Database query: SELECT password_hash WHERE user_id=1
                >>> # bcrypt.checkpw("oldpass123", hash) → True
                >>> # bcrypt.hashpw("newpass456") → new_hash
                >>> # UPDATE users SET password_hash=new_hash WHERE user_id=1
                >>> # Notification: "✓ Password updated successfully for batman!"
                >>> # dismiss(True)

            Validation failure - passwords don't match::

                >>> # User enters:
                >>> #   Current: "oldpass123"
                >>> #   New: "newpass456"
                >>> #   Confirm: "newpass789"  # DIFFERENT!
                >>> # _update_password() called
                >>> # Validation fails at step 4
                >>> # Notification: "New passwords do not match!"
                >>> # Modal stays open (return early)
                >>> # User can correct and try again

            Verification failure - wrong current password::

                >>> # User enters:
                >>> #   Current: "wrongpass"
                >>> #   New: "newpass456"
                >>> #   Confirm: "newpass456"
                >>> # _update_password() called
                >>> # All validations pass
                >>> # Database verification:
                >>> # bcrypt.checkpw("wrongpass", hash) → False
                >>> # op_user_update_password() returns False
                >>> # Notification: "Current password is incorrect"
                >>> # Modal stays open

        Note:
            The modal stays open on validation failures, allowing users
            to correct their inputs and retry without having to reopen
            the modal and start over.

            On successful update, the modal dismisses with True, which
            can be used by the parent screen to show confirmation or
            trigger additional actions.

            All password validation happens client-side before database
            access, except for the current password verification which
            requires database comparison.

        See Also:
            functions.handler_sqllite.op_user_update_password: Database operation
            bcrypt.checkpw: Password verification (in handler)
            bcrypt.hashpw: Password hashing (in handler)
        """
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
