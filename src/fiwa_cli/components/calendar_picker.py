from textual.widgets import Static, Button
from textual.containers import Container, Grid, Vertical, Horizontal
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.message import Message
from textual import events

import os
from datetime import datetime, timedelta



class CalendarWidget(ModalScreen):
    """Interactive calendar modal for date selection in terminal user interfaces.

    A fully-featured calendar widget that displays a month view with navigation controls,
    allowing users to select dates through mouse clicks or keyboard navigation. The widget
    appears as a modal overlay and supports customizable positioning and styling.

    Features:
        - Month/year navigation with previous/next buttons
        - "Today" button to quickly jump to current date
        - Highlights today's date with special styling
        - Grays out dates from adjacent months
        - Keyboard support (Escape to close)
        - Click outside to dismiss without selection
        - Configurable week start day (Monday or Sunday)
        - Customizable positioning and margins

    Attributes:
        WEEK_STARTS_MONDAY (bool): Class-level default for week start day.
            True = Monday (default), False = Sunday.
        BINDINGS (list): Keyboard bindings. Currently supports Escape to dismiss.
        current_date (datetime): The date used for initial display.
        today (datetime): Today's date (for highlighting).
        selected_date (datetime | None): The date selected by user (set on selection).
        display_date (datetime): The currently displayed month (always day=1).

    Args:
        initial_date (datetime, optional): Date to display initially.
            Defaults to today if None.
        align (str, optional): Widget alignment on screen.
            Format: "horizontal vertical" (e.g., "center middle", "left top").
            Defaults to "center middle".
        margin (int | tuple[int, ...] | None, optional): Margin around the calendar container.
            Can be a single int (all sides), tuple of 2 (vertical, horizontal),
            or tuple of 4 (top, right, bottom, left). Defaults to None.
        week_starts_monday (bool, optional): Whether week starts on Monday (True)
            or Sunday (False). Defaults to True.
        *args: Additional positional arguments passed to ModalScreen.
        **kwargs: Additional keyword arguments passed to ModalScreen.

    Returns:
        datetime | None: When dismissed, returns the selected datetime object,
            or None if dismissed without selection (Escape or click outside).

    Example:
        Basic usage with default settings:

        >>> # Show calendar and wait for user selection
        >>> selected = await self.app.push_screen_wait(CalendarWidget())
        >>> if selected:
        >>>     self.log(f"User selected: {selected.strftime('%Y-%m-%d')}")
        >>> else:
        >>>     self.log("Calendar dismissed without selection")

        With custom initial date:

        >>> # Show calendar for December 2024
        >>> from datetime import datetime
        >>> selected = await self.app.push_screen_wait(
        >>>     CalendarWidget(initial_date=datetime(2024, 12, 25))
        >>> )

        With custom positioning:

        >>> # Position in top-left with margin
        >>> selected = await self.app.push_screen_wait(
        >>>     CalendarWidget(
        >>>         align="left top",
        >>>         margin=(2, 4),  # top/bottom=2, left/right=4
        >>>         week_starts_monday=False  # Start week on Sunday
        >>>     )
        >>> )

    Note:
        - The calendar always displays exactly 6 rows × 7 columns (42 days total)
        - Dates from previous/next months are shown in grayed-out style
        - Clicking outside the calendar dismisses it without selection
        - Pressing Escape also dismisses without selection
        - The widget requires a CSS file at css/{theme}/components_calendar.tcss

    CSS Classes:
        - calendar-nav-grid: Navigation button container
        - nav-button: Previous/next month buttons (◀ ▶)
        - today-button: "Today" button in navigation
        - calendar-title: Month/year display
        - weekday-header: Weekday labels row
        - weekday-label: Individual weekday labels
        - calendar-grid: Main calendar grid container
        - calendar-week-row: Each week row (Horizontal container)
        - day-button: Individual day buttons
        - day-today: Today's date (added to day-button)
        - day-other-month: Days from adjacent months (added to day-button)
    """

    # Configuration: True = week starts on Monday, False = week starts on Sunday
    WEEK_STARTS_MONDAY = True

    BINDINGS = [
        ("escape", "dismiss_calendar", "Close"),
    ]

    @property
    def CSS_PATH(self):
        """Dynamically load CSS path based on the theme stored in app_state. Needs
        @property to work with Textual's CSS loading system. Otherwise, "self", does not
        yet exist at class level when CSS is being loaded, and we cannot access app_state to
        determine the theme.
        CSS file structure:
        fiwa-cli/
          ├── components/
          │   └── calendar_display.py (this file)
          └── css/
              └── handsome/
                  └── components_calendar.tcss
        """
        css_form = self.app.app_state.get("css_form", "handsome")
        abs_path = self.app.app_state["abs_path"]

        # Absolute path: /path/to/fiwa-cli/css/handsome/components_calendar.tcss
        css_file = os.path.join(abs_path, "css", css_form, "components_calendar_picker.tcss")

        return css_file

    class DateSelected(Message):
        """Message sent when a date is selected in the calendar.

        This message is posted when the user clicks on a day button, containing
        the selected date information.

        Attributes:
            selected_date (datetime): The date that was selected by the user.

        Note:
            Currently not used in the implementation as the calendar dismisses
            directly with the selected date. Kept for potential future use
            if event-based notification is needed instead of modal dismissal.
        """
        def __init__(self, selected_date: datetime) -> None:
            self.selected_date = selected_date
            super().__init__()

    def __init__(self,
                 initial_date: datetime = None,
                 align: str = "center middle",
                 margin: int | tuple[int, ...] | None = None,
                 week_starts_monday: bool = True,
                 *args, **kwargs):
        """Initialize the calendar widget with optional configuration.

        Sets up the calendar with the specified initial date and appearance options.
        The calendar will display the month of the initial_date, or today's month
        if no date is provided.

        Args:
            initial_date (datetime, optional): The date to display when calendar opens.
                The calendar will show the month containing this date. If None,
                displays the current month. Defaults to None (today).
            align (str, optional): Screen alignment for the calendar modal.
                Format: "horizontal vertical" where:
                - horizontal: "left", "center", or "right"
                - vertical: "top", "middle", or "bottom"
                Examples: "center middle", "left top", "right bottom"
                Defaults to "center middle".
            margin (int | tuple[int, ...] | None, optional): Margin spacing around
                the calendar container in terminal cells. Can be:
                - int: Same margin on all sides (e.g., 2)
                - tuple of 2: (vertical, horizontal) (e.g., (2, 4))
                - tuple of 4: (top, right, bottom, left) (e.g., (1, 2, 3, 4))
                - None: No margin (calendar uses CSS defaults)
                Defaults to None.
            week_starts_monday (bool, optional): Determines the first day of the week.
                True = week starts on Monday (Mo, Tu, We, Th, Fr, Sa, Su)
                False = week starts on Sunday (Su, Mo, Tu, We, Th, Fr, Sa)
                Defaults to True.
            *args: Additional positional arguments passed to parent ModalScreen.
            **kwargs: Additional keyword arguments passed to parent ModalScreen.
                Can include 'id' and 'classes' for widget identification.

        Attributes Set:
            current_date (datetime): Set to initial_date or today
            today (datetime): Always set to the current date/time
            selected_date (None): Initially None, set when user selects a date
            display_date (datetime): Set to first day of initial_date's month
            _align (str): Stored alignment preference
            _margin (int | tuple | None): Stored margin preference
            WEEK_STARTS_MONDAY (bool): Instance-level week start setting

        Example:
            >>> # Default calendar (today's month, centered)
            >>> calendar = CalendarWidget()

            >>> # Show December 2024, top-left positioned
            >>> calendar = CalendarWidget(
            >>>     initial_date=datetime(2024, 12, 1),
            >>>     align="left top",
            >>>     margin=(3, 5)
            >>> )

            >>> # Sunday-first calendar with custom ID
            >>> calendar = CalendarWidget(
            >>>     week_starts_monday=False,
            >>>     id="event-calendar"
            >>> )
        """
        super().__init__(*args, **kwargs)
        self.current_date = initial_date if initial_date else datetime.now()
        self.today = datetime.now()
        self.selected_date = None

        # Set to first day of current month for display
        self.display_date = self.current_date.replace(day=1)

        self._align = align
        self._margin = margin
        self.WEEK_STARTS_MONDAY = week_starts_monday

    def compose(self) -> ComposeResult:
        """Build the calendar widget's visual structure.

        Creates the complete widget hierarchy including:
        - Navigation controls (previous month, today, next month buttons)
        - Month/year title display
        - Weekday header row
        - 6×7 grid of day buttons

        The structure follows this hierarchy:
        Container
          ├── Grid (navigation buttons)
          │   ├── Button (◀ previous)
          │   ├── Button (Today)
          │   └── Button (▶ next)
          └── Vertical
              ├── Static (month/year title)
              ├── Horizontal (weekday labels)
              │   └── Static × 7 (Mon-Sun or Sun-Sat)
              └── Vertical (calendar grid)
                  └── Horizontal × 6 (week rows)
                      └── Button × 7 (day buttons)

        Returns:
            ComposeResult: Iterator of widgets that make up the calendar interface.

        Note:
            This method is called automatically by Textual during widget mounting.
            It uses context managers (with statements) to establish parent-child
            relationships between widgets. The day buttons are generated via
            _generate_calendar_rows() and _generate_calendar_days().
        """
        with Container():
            with Grid(classes="calendar-nav-grid"):
                yield Button("◀", id="prev-month", classes="nav-button")
                yield Button("Today", id="today-button", classes="today-button")
                yield Button("▶", id="next-month", classes="nav-button")

            with Vertical():
                # Navigation header with prev/next month and today button
                # Using Grid layout for navigation: < Today >


                # Month/Year display
                month_year = self.display_date.strftime("%B %Y")
                yield Static(month_year, id="month-year-display", classes="calendar-title")

                # Weekday headers row
                with Horizontal(classes="weekday-header"):
                    if self.WEEK_STARTS_MONDAY:
                        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                    else:
                        weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

                    for day in weekdays:
                        yield Static(day, classes="weekday-label")

                # Calendar grid using Vertical container with Horizontal rows
                with Vertical(classes="calendar-grid", id="calendar-grid"):
                    yield from self._generate_calendar_rows()

    def on_mount(self) -> None:
        """Adjust container position and styling after the widget is mounted.

        This lifecycle hook is called automatically after the widget is added to
        the screen. It applies custom positioning, sizing, and margin settings
        to the calendar container.

        Actions performed:
            1. Query and get the Container widget
            2. Center the container on screen
            3. Set container dimensions (35 columns × 15 rows)
            4. Apply custom margin if provided during initialization

        Note:
            This method runs after compose() and before the widget is displayed.
            The container styles set here can override CSS defaults.

        Side Effects:
            Modifies the Container widget's styles:
            - align: Set to ("center", "middle")
            - width: Set to 35 terminal columns
            - height: Set to 15 terminal rows
            - margin: Set to self._margin if provided
        """
        # Log to custom file logger (self.app.file_log)
        try:
            self.app.file_log.info(f"CalendarWidget mounted - displaying {self.display_date.strftime('%B %Y')}")
        except:
            pass  # Logging is not critical

        # Get the container widget
        container = self.query_one(Container)

        # Center the container on screen
        container.styles.align = ("center", "middle")

        container.styles.width = 35
        container.styles.height = 15
        container.styles.margin = self._margin  # Add top margin to move it down from the top edge

    def _generate_calendar_rows(self):
        """Generate 6 week rows for the calendar grid, each containing 7 day buttons.

        Creates the calendar grid structure by organizing 42 day buttons into
        6 Horizontal row containers. This method is called during compose()
        for initial rendering and during _refresh_calendar() when the month changes.

        The layout structure:
        - 6 Horizontal containers (one per week row)
        - Each Horizontal contains 7 Button widgets (one per day)
        - Total: 42 day buttons filling a 7×6 grid

        Implementation:
            1. Gets all 42 day buttons from _generate_calendar_days()
            2. Splits them into 6 groups of 7 buttons each
            3. Creates a Horizontal container for each group
            4. Yields each Horizontal with its 7 buttons as children

        Yields:
            Horizontal: Week row containers, each containing 7 day buttons.
                Each Horizontal has the class "calendar-week-row".

        Note:
            This method uses explicit widget creation (Horizontal(*buttons))
            rather than context managers to support dynamic refresh operations.
            Context managers only work during the initial compose() phase.

        See Also:
            _generate_calendar_days(): Creates the 42 individual day buttons
            _refresh_calendar(): Uses this method to rebuild the calendar grid
        """
        # Get all 42 day buttons
        all_days = list(self._generate_calendar_days())

        # Split into 6 rows of 7 days each
        for week in range(6):
            start_idx = week * 7
            end_idx = start_idx + 7
            week_buttons = all_days[start_idx:end_idx]

            # Create Horizontal container with buttons as children
            week_row = Horizontal(*week_buttons, classes="calendar-week-row")
            yield week_row

    def _generate_calendar_days(self):
        """Generate all 42 day buttons for the calendar grid display.

        Creates buttons for a complete 6×7 calendar grid, including:
        - Days from the previous month (to fill the first week)
        - All days of the current month
        - Days from the next month (to fill the last week)

        The calendar always displays exactly 42 buttons (6 rows × 7 columns)
        to maintain consistent layout regardless of how many days are in the
        current month or which day of the week the month starts on.

        Day Button Styling:
            - Previous month days: Classes "day-button day-other-month" (grayed out)
            - Current month days: Class "day-button"
            - Today's date: Classes "day-button day-today" (highlighted)
            - Next month days: Classes "day-button day-other-month" (grayed out)

        Algorithm:
            1. Calculate first day of the current month
            2. Determine weekday offset based on WEEK_STARTS_MONDAY setting
            3. Generate buttons for previous month days (to fill start of first week)
            4. Generate buttons for all days in current month
            5. Check if current day is today and apply special styling
            6. Generate buttons for next month days (to fill remainder of grid to 42)

        Yields:
            Button: Day buttons with appropriate labels, IDs, and CSS classes.
                Each button has:
                - Label: Day number (1-31)
                - ID: "day-YYYY-MM-DD" format for date identification
                - Classes: Styling classes based on day type
                - compact=True, flat=True: Compact button styling

        Example:
            For March 2026 (starts on Sunday with WEEK_STARTS_MONDAY=True):
            Week 1: [23, 24, 25, 26, 27, 28, 1]  ← 6 from Feb, 1 from Mar
            Week 2: [2, 3, 4, 5, 6, 7, 8]       ← All March
            Week 3: [9, 10, 11, 12, 13, 14, 15] ← All March
            Week 4: [16, 17, 18, 19, 20, 21, 22]← All March
            Week 5: [23, 24, 25, 26, 27, 28, 29]← All March
            Week 6: [30, 31, 1, 2, 3, 4, 5]     ← 2 from Mar, 5 from Apr

        Note:
            - Button IDs use ISO date format (YYYY-MM-DD) for reliable parsing
            - The compact and flat button options create a minimal visual style
            - Days from other months are still clickable and selectable

        See Also:
            _generate_calendar_rows(): Organizes these buttons into week rows
            on_button_pressed(): Handles button clicks and date selection
        """
        year = self.display_date.year
        month = self.display_date.month

        # Get first day of the month
        first_day = self.display_date

        # Determine the weekday of the first day
        if self.WEEK_STARTS_MONDAY:
            first_weekday = first_day.weekday()  # 0=Monday, 6=Sunday
        else:
            first_weekday = (first_day.weekday() + 1) % 7  # 0=Sunday, 6=Saturday

        # Get number of days in current month
        if month == 12:
            next_month_first = first_day.replace(year=year+1, month=1, day=1)
        else:
            next_month_first = first_day.replace(month=month+1, day=1)
        last_day = next_month_first - timedelta(days=1)
        days_in_month = last_day.day

        # Get previous month date for calculations
        prev_month_last = first_day - timedelta(days=1)
        prev_month_days = prev_month_last.day
        prev_year = prev_month_last.year
        prev_month = prev_month_last.month

        # Calculate how many days from previous month to show
        days_from_prev = first_weekday

        # PART 1: Add days from previous month (grayed out)
        for i in range(days_from_prev):
            day_num = prev_month_days - days_from_prev + i + 1
            date = datetime(prev_year, prev_month, day_num)
            yield Button(
                str(day_num),
                id=f"day-{date.strftime('%Y-%m-%d')}",
                classes="day-button day-other-month",
                compact=True,
                flat=True
            )

        # PART 2: Add days of current month
        for day in range(1, days_in_month + 1):
            date = first_day.replace(day=day)
            classes = "day-button"

            # Highlight today
            if (date.year == self.today.year and
                date.month == self.today.month and
                date.day == self.today.day):
                classes += " day-today"

            yield Button(
                str(day),
                id=f"day-{date.strftime('%Y-%m-%d')}",
                classes=classes,
                compact=True,
                flat=True
            )

        # PART 3: Fill remaining cells with next month days (grayed out)
        total_shown = days_from_prev + days_in_month
        remaining = 42 - total_shown  # Always show exactly 42 cells (7×6 grid)

        next_year = next_month_first.year
        next_month = next_month_first.month

        for day in range(1, remaining + 1):
            date = datetime(next_year, next_month, day)
            yield Button(
                str(day),
                id=f"day-{date.strftime('%Y-%m-%d')}",
                classes="day-button day-other-month",
                compact=True,
                flat=True
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle all button press events in the calendar widget.

        This event handler is called whenever any button in the calendar is clicked.
        It determines which button was pressed by checking the button's ID and
        routes to the appropriate handler method.

        Button Routing:
            - "prev-month": Calls _change_month(-1) to go to previous month
            - "next-month": Calls _change_month(1) to go to next month
            - "today-button": Calls _jump_to_today() to show current month
            - "day-*": Calls _select_date() to select the clicked date

        Args:
            event (Button.Pressed): The button press event containing information
                about which button was clicked. Access the button via event.button
                and its ID via event.button.id.

        Example:
            User clicks "▶" button:
            → event.button.id == "next-month"
            → Calls _change_month(1)
            → Display advances to next month

            User clicks day "15":
            → event.button.id == "day-2026-03-15"
            → Calls _select_date("day-2026-03-15")
            → Calendar closes and returns datetime(2026, 3, 15)

        Note:
            This method uses Textual's event system. It's automatically called
            by the framework when buttons are pressed - you don't call it directly.

        See Also:
            _change_month(): Handles month navigation
            _jump_to_today(): Handles "Today" button
            _select_date(): Handles day selection and dismissal
        """
        if event.button.id == "prev-month":
            self._change_month(-1)
        elif event.button.id == "next-month":
            self._change_month(1)
        elif event.button.id == "today-button":
            self._jump_to_today()
        elif event.button.id and event.button.id.startswith("day-"):
            self._select_date(event.button.id)

    def on_click(self, event: events.Click) -> None:
        """Dismiss the calendar modal when clicking outside the container.

        Implements the common modal behavior where clicking on the semi-transparent
        overlay (outside the actual calendar) closes the modal without selecting
        a date. This provides an intuitive way for users to cancel the calendar.

        The handler checks if the click event occurred directly on the ModalScreen
        widget itself (the overlay background) rather than on any child widgets
        like the container, buttons, or labels.

        Args:
            event (events.Click): The click event containing information about
                where the click occurred and which widget received it.

        Behavior:
            - If click is on ModalScreen itself: Dismiss with None (no selection)
            - If click is on any child widget: Event ignored, normal handling proceeds

        Example:
            User clicks on calendar day button:
            → event.widget is the Button
            → event.widget is self == False
            → Method does nothing, button handler runs instead

            User clicks on dark overlay outside calendar:
            → event.widget is the ModalScreen (self)
            → event.widget is self == True
            → Calls self.dismiss(None)
            → Calendar closes without returning a date

        Note:
            This creates user-friendly modal dismissal behavior where users can
            click outside the dialog to close it, which is a common UX pattern.
            The calendar returns None when dismissed this way, allowing the caller
            to distinguish between cancellation and actual date selection.

        See Also:
            action_dismiss_calendar(): Alternative dismissal via Escape key
            _select_date(): Dismissal with a selected date
        """
        # Check if the click was on the ModalScreen itself (not on a child widget)
        if event.widget is self:
            # Close without returning a date
            self.dismiss(None)

    def action_dismiss_calendar(self) -> None:
        """Dismiss the calendar modal without selecting a date (Escape key handler).

        This action method is bound to the Escape key via the BINDINGS class variable.
        When the user presses Escape, this method is called automatically by Textual's
        action system, closing the calendar and returning None.

        This provides a standard keyboard-based way to cancel the calendar operation,
        following common UI conventions where Escape closes dialogs without action.

        Binding:
            Defined in BINDINGS as: ("escape", "dismiss_calendar", "Close")
            - Key: Escape
            - Action: dismiss_calendar
            - Description: "Close" (shown in footer if enabled)

        Behavior:
            Calls self.dismiss(None) to close the modal and return None to the caller.

        Example:
            User presses Escape while calendar is open:
            → Textual's action system calls action_dismiss_calendar()
            → self.dismiss(None) is called
            → await push_screen_wait(CalendarWidget()) returns None
            → Caller knows user cancelled without selecting a date

        Note:
            Action methods in Textual are automatically discovered by the framework
            if they start with "action_" and match a binding. You typically don't
            call this method directly - the framework calls it when Escape is pressed.

        See Also:
            on_click(): Alternative dismissal by clicking outside
            _select_date(): Dismissal with a selected date
            BINDINGS: Class variable defining keyboard shortcuts
        """
        self.dismiss(None)

    def _change_month(self, delta: int) -> None:
        """Navigate to a different month by applying a month offset.

        Updates the displayed month by adding or subtracting months from the
        current display_date. Handles year transitions automatically (e.g.,
        December → January increases year, January → December decreases year).

        After updating the date, triggers a calendar refresh to display the
        new month's days.

        Args:
            delta (int): Number of months to move. Positive values move forward,
                negative values move backward.
                - +1: Next month (e.g., March → April)
                - -1: Previous month (e.g., March → February)
                - +12: One year forward
                - -12: One year backward

        Year Handling:
            - If new month > 12: Wrap to January and increment year
            - If new month < 1: Wrap to December and decrement year
            - Ensures month always stays in valid range [1-12]

        Example:
            Starting at March 2026:
            >>> self._change_month(-1)  # → February 2026
            >>> self._change_month(1)   # → April 2026
            >>> self._change_month(10)  # → January 2027 (Mar + 10 = month 13 → Jan +1 year)
            >>> self._change_month(-3)  # → December 2025 (Mar - 3 = month 0 → Dec -1 year)

        Side Effects:
            - Updates self.display_date to first day of new month
            - Calls _refresh_calendar() to rebuild the day grid
            - Logs refresh operation to console

        Note:
            This method is called by on_button_pressed() when the user clicks
            the previous (◀) or next (▶) month navigation buttons.

        See Also:
            _refresh_calendar(): Rebuilds the calendar display
            _jump_to_today(): Alternative navigation to current month
        """
        current_month = self.display_date.month
        current_year = self.display_date.year

        new_month = current_month + delta
        new_year = current_year

        if new_month > 12:
            new_month = 1
            new_year += 1
        elif new_month < 1:
            new_month = 12
            new_year -= 1

        self.display_date = self.display_date.replace(year=new_year, month=new_month, day=1)
        self._refresh_calendar()

    def _jump_to_today(self) -> None:
        """Navigate to the current month and highlight today's date.

        Immediately switches the calendar display to show the current month,
        regardless of what month was previously displayed. This provides a
        quick way for users to return to today's date from any month.

        The method updates the display_date to the first day of the current
        month (from self.today), then refreshes the calendar grid. Today's
        date will be automatically highlighted with the "day-today" CSS class
        during the refresh.

        Behavior:
            1. Set display_date to first day of current month
            2. Call _refresh_calendar() to rebuild the day grid
            3. Today's date receives special highlighting automatically

        Example:
            User navigates to December 2024, then clicks "Today":
            → Current date is March 1, 2026
            → display_date set to March 1, 2026
            → Calendar rebuilds showing March 2026
            → Day "1" appears with day-today styling

        Optional Enhancement (Currently Commented):
            The method could auto-select today's date and dismiss the calendar:
            # self._select_date(f"day-{self.today.strftime('%Y-%m-%d')}")
            This would be useful for "quick select today" functionality.

        Note:
            This method is triggered when the user clicks the "Today" button
            in the navigation area. The button is defined in compose() with
            id="today-button" and handled by on_button_pressed().

        See Also:
            _change_month(): Alternative navigation method (month by month)
            _refresh_calendar(): Rebuilds the calendar after date change
            on_button_pressed(): Routes "Today" button clicks to this method
        """
        self.display_date = self.today.replace(day=1)
        self._refresh_calendar()
        # Optionally auto-select today
        # self._select_date(f"day-{self.today.strftime('%Y-%m-%d')}")

    def _select_date(self, button_id: str) -> None:
        """Process date selection and dismiss the calendar with the chosen date.

        Extracts the date from the clicked button's ID, converts it to a datetime
        object, and closes the calendar modal, returning the selected date to the
        caller. This completes the date selection workflow.

        Args:
            button_id (str): The ID of the clicked day button in the format
                "day-YYYY-MM-DD" (e.g., "day-2026-03-15", "day-2026-12-25").
                The date portion uses ISO 8601 format for reliable parsing.

        Process:
            1. Remove "day-" prefix from button ID
            2. Parse remaining string as ISO date (YYYY-MM-DD)
            3. Create datetime object from parsed date
            4. Call self.dismiss() with the datetime object
            5. Calendar closes and returns datetime to caller

        Example:
            User clicks day "15" in March 2026:
            → Button has id="day-2026-03-15"
            → _select_date("day-2026-03-15") is called
            → date_str = "2026-03-15"
            → selected_date = datetime(2026, 3, 15, 0, 0, 0)
            → self.dismiss(selected_date)
            → Caller receives datetime(2026, 3, 15)

        Return Value (via dismiss):
            When used with push_screen_wait():
            >>> selected = await self.app.push_screen_wait(CalendarWidget())
            >>> # selected is datetime(2026, 3, 15) or None

        Note:
            - This method works for dates from any month (current, previous, or next)
            - The datetime object has time set to 00:00:00 (midnight)
            - If parsing fails, strptime will raise ValueError (not currently caught)
            - The modal is dismissed immediately after date extraction

        Raises:
            ValueError: If button_id doesn't contain a valid date in YYYY-MM-DD format

        See Also:
            on_button_pressed(): Routes day button clicks to this method
            _generate_calendar_days(): Creates buttons with the expected ID format
            dismiss(): ModalScreen method that closes the modal and returns a value
        """
        # Extract date from button ID (format: "day-YYYY-MM-DD")
        date_str = button_id.replace("day-", "")
        selected_date = datetime.strptime(date_str, "%Y-%m-%d")

        # Return the selected date and close the calendar
        self.dismiss(selected_date)

    def _refresh_calendar(self) -> None:
        """Rebuild the calendar display to show a different month.

        Completely regenerates the calendar grid when the displayed month changes,
        updating both the month/year title and all 42 day buttons to reflect the
        new month. This method is called after month navigation (_change_month)
        or jumping to today (_jump_to_today).

        The refresh process:
            1. Format new month/year string (e.g., "March 2026")
            2. Update the title Static widget with new text
            3. Query the calendar grid container
            4. Remove all existing week rows and day buttons
            5. Generate 6 new week rows with 42 new day buttons
            6. Mount the new rows into the container
            7. Log detailed progress information for debugging

        Logging:
            The method logs detailed information at each step:
            - "Refreshing calendar to: March 2026"
            - "✓ Updated month display to: March 2026"
            - "✓ Removed 6 old rows"
            - "✓ Generated 6 new rows"
            - "✓ First row has 7 buttons"
            - "✓ Mounted 6 rows successfully"
            - Or error messages with full tracebacks if something fails

        Technical Details:
            - Uses query_one() to find specific widgets by ID
            - Calls remove_children() to clear the old grid
            - Converts generator to list for proper widget mounting
            - Uses mount(*widgets) to add new rows (not mount_all!)
            - Explicit widget creation required (no context managers)

        Error Handling:
            - Catches exceptions during title update
            - Catches exceptions during grid refresh
            - Logs errors with full Python traceback for debugging
            - Continues operation even if parts fail

        Example:
            User clicks next month (◀) from March → April:
            → _change_month(1) updates display_date to April 1
            → _change_month(1) calls _refresh_calendar()
            → Title updates: "March 2026" → "April 2026"
            → Grid clears: Removes March's 42 buttons
            → Grid rebuilds: Creates April's 42 buttons
            → Calendar now shows April 2026

        Note:
            This method uses explicit widget creation (Horizontal(*buttons))
            because context managers (with Horizontal():) only work during the
            initial compose() phase. Dynamic updates require explicit creation.

        Side Effects:
            - Updates month-year-display Static widget text
            - Removes all children from calendar-grid container
            - Mounts 6 new Horizontal rows with 7 buttons each
            - Writes multiple log entries to app.log()

        See Also:
            _generate_calendar_rows(): Creates the new week row widgets
            _generate_calendar_days(): Creates the 42 day buttons
            _change_month(): Calls this after month navigation
            _jump_to_today(): Calls this after jumping to current month
        """
        self.app.log(f"Refreshing calendar to: {self.display_date.strftime('%B %Y')}")

        # Update month/year display
        month_year = self.display_date.strftime("%B %Y")
        try:
            month_display = self.query_one("#month-year-display", Static)
            month_display.update(month_year)
            self.app.log(f"✓ Updated month display to: {month_year}")
            self.app.file_log.info(f"Updated month display to: {month_year}")
        except Exception as e:
            self.app.log(f"✗ Error updating month display: {e}")

        # Regenerate calendar grid using Vertical container with Horizontal rows
        try:
            calendar_container = self.query_one("#calendar-grid", Vertical)

            # Remove existing children
            old_count = len(calendar_container.children)
            calendar_container.remove_children()
            self.app.log(f"✓ Removed {old_count} old rows")

            # Mount new calendar rows - convert generator to list for mount()
            new_rows = list(self._generate_calendar_rows())
            self.app.log(f"✓ Generated {len(new_rows)} new rows")

            # Count buttons in first row to verify
            if new_rows:
                first_row_buttons = len(new_rows[0].children)
                self.app.log(f"✓ First row has {first_row_buttons} buttons")

            calendar_container.mount(*new_rows)
            self.app.log(f"✓ Mounted {len(new_rows)} rows successfully")

        except Exception as e:
            self.app.log(f"✗ Error refreshing calendar: {e}")
            import traceback
            self.app.log(traceback.format_exc())
