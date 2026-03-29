"""Real-time clock widget for FiWa CLI.

This module provides a simple widget that displays the current date and
time, updating every second to show live time information.

The time display:
    - Shows current date and time in readable format
    - Updates automatically every second
    - Uses system clock for accuracy
    - Integrates seamlessly into headers and status bars

Key Features:
    - Auto-updating display (1-second interval)
    - Human-readable format: "Mar 29 2026 14:32:45"
    - No user interaction required
    - Lightweight and efficient

Components:
    TimeDisplay: Auto-updating time widget

Example:
    Adding time display to a layout::

        >>> from fiwa_cli.components.time_display import TimeDisplay
        >>> yield TimeDisplay()

    Used in header::

        >>> # FiwaHeader includes TimeDisplay
        >>> # Shows: "FiWa  [☰ Menu]  Mar 29 2026 14:32:45"
        >>> # Updates every second
        >>> # Shows: "FiWa  [☰ Menu]  Mar 29 2026 14:32:46"

See Also:
    components.header.FiwaHeader: Header component that uses TimeDisplay
"""

from datetime import datetime

from textual.widgets import Static


class TimeDisplay(Static):
    """Widget displaying current date and time with automatic updates.

    This widget shows the current system time in a human-readable format
    and automatically updates every second to stay current.

    The widget uses Textual's set_interval() to schedule updates,
    ensuring the displayed time is always accurate within one second.

    Display Format:
        "%b %d %Y %H:%M:%S"
        Example: "Mar 29 2026 14:32:45"

        Components:
            - %b: Abbreviated month name (Jan, Feb, Mar, etc.)
            - %d: Day of month (01-31)
            - %Y: 4-digit year (2026)
            - %H: Hour in 24-hour format (00-23)
            - %M: Minute (00-59)
            - %S: Second (00-59)

    Update Mechanism:
        1. on_mount() initializes display with current time
        2. set_interval(1, update_time) schedules updates
        3. update_time() called every 1 second
        4. Display refreshed with new time

    Performance:
        - Efficient: Only updates text content (no re-render)
        - Lightweight: Single string update per second
        - Non-blocking: Runs in Textual's event loop

    Example:
        Basic usage::

            >>> from fiwa_cli.components.time_display import TimeDisplay
            >>> time_widget = TimeDisplay()
            >>> yield time_widget
            >>> # Displays: "Mar 29 2026 14:32:45"
            >>> # Auto-updates every second

        In header context::

            >>> # FiwaHeader.compose() includes:
            >>> yield TimeDisplay()
            >>> # Header shows current time
            >>> # Time updates automatically
            >>> # User always sees accurate time

        Checking time format::

            >>> # Widget mounted at 14:32:45
            >>> # Shows: "Mar 29 2026 14:32:45"
            >>> # After 1 second: "Mar 29 2026 14:32:46"
            >>> # After 60 seconds: "Mar 29 2026 14:33:45"

    Note:
        The widget uses system time via datetime.now(), so accuracy
        depends on the system clock being properly configured.

        The interval is set to 1 second, which is appropriate for
        second-level precision. If you only need minute precision,
        you could use set_interval(60, ...) instead.

        The widget automatically cleans up the interval when removed
        from the app (handled by Textual).

    See Also:
        components.header.FiwaHeader: Uses this widget in header
        datetime.datetime.now: Python datetime function
        textual.widgets.Static: Parent widget class
    """

    def on_mount(self) -> None:
        """Initialize time display when widget is mounted.

        Sets the initial time and schedules automatic updates every second.

        Side Effects:
            - Calls update_time() to show initial time
            - Schedules update_time() to run every 1 second

        Note:
            This is called automatically by Textual after the widget is
            added to the app but before it's displayed.
        """
        self.update_time()
        self.set_interval(1, self.update_time)

    def update_time(self) -> None:
        """Update the display with the current system time.

        Fetches the current time from the system clock and updates
        the widget text to show the formatted time string.

        Side Effects:
            - Calls datetime.now() to get current time
            - Updates widget content via self.update()

        Format:
            "Mar 29 2026 14:32:45" (abbreviated month, day, year, time)

        Example:
            >>> # update_time() called
            >>> # datetime.now() returns: datetime(2026, 3, 29, 14, 32, 45)
            >>> # strftime formats: "Mar 29 2026 14:32:45"
            >>> # Widget displays: "Mar 29 2026 14:32:45"
        """
        self.update(datetime.now().strftime("%b %d %Y %H:%M:%S"))
