"""Example usage of LoginScreen - can be deleted later."""

# Example 1: Show login form when user is not logged in
# from screens.base import LoginScreen
#
# def handle_login_result(result):
#     if result and result.get("success"):
#         print(f"User logged in: {result.get('username')}")
#         # Refresh app state, load user data, etc.
#
# # In your app or screen:
# self.push_screen(LoginScreen(is_logged_in=False), handle_login_result)


# Example 2: Show logout screen when user is logged in
# from screens.base import LoginScreen
#
# def handle_logout_result(result):
#     if result and result.get("action") == "logout":
#         print("User logged out")
#         # Clear app state, redirect to login, etc.
#
# # In your app or screen:
# current_username = self.app._store.get("user", "Unknown")
# self.push_screen(LoginScreen(is_logged_in=True, username=current_username), handle_logout_result)


# Example 3: Add to main menu in FiwaHeader or menu.py
# In components/header.py or screens/menu.py:
#
# def action_show_login(self):
#     """Show login/logout screen based on current state."""
#     from screens.base import LoginScreen
#
#     # Check if user is logged in
#     is_logged_in = self.app._store.get("user") is not None
#     username = self.app._store.get("user", "")
#
#     def handle_auth_result(result):
#         if result:
#             if result.get("action") == "logout":
#                 # Clear user session
#                 self.app._store["user"] = None
#                 self.app._store["user_id"] = None
#                 self.notify("Logged out successfully")
#             elif result.get("success"):
#                 # Refresh user data after login
#                 self.notify(f"Logged in as {result.get('username')}")
#
#     self.push_screen(LoginScreen(is_logged_in=is_logged_in, username=username), handle_auth_result)
