"""
Example showing how to use the custom file_log from calendar_picker.py
or any other screen/widget.
"""

# In your calendar_picker.py or any other screen/widget, use it like this:

class CalendarWidget(ModalScreen):
    def on_mount(self):
        # Log to file (NOT to Textual's devtools)
        self.app.file_log.info("CalendarWidget mounted")
        self.app.file_log.debug("Initializing calendar grid")

    def _refresh_calendar(self):
        # Log calendar operations
        self.app.file_log.info(f"Refreshing calendar to: {self.current_year}-{self.current_month}")

    def on_button_pressed(self, event):
        # Log user interactions
        if event.button.id == "prev-month":
            self.app.file_log.info("User clicked previous month button")
        elif event.button.id == "next-month":
            self.app.file_log.info("User clicked next month button")

    def _select_date(self, date_str):
        # Log selections
        self.app.file_log.info(f"User selected date: {date_str}")
        self.app.file_log.debug(f"Full date info: {date_str}")

# Available log levels:
# self.app.file_log.debug("Detailed debug information")
# self.app.file_log.info("General information")
# self.app.file_log.warning("Warning message")
# self.app.file_log.error("Error message")
# self.app.file_log.critical("Critical error")
