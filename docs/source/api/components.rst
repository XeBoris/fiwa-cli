Components
==========

Reusable UI components and widgets used throughout the FiWa CLI application.

Overview
--------

Components are self-contained widgets that can be reused across multiple
screens. They encapsulate both functionality and styling, and communicate
via Textual's message system.

Common Usage Pattern
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fiwa_cli.components.calendar_picker import CalendarWidget

    class MyScreen(Screen):
        def show_calendar(self):
            # Push calendar and wait for selection
            selected_date = await self.app.push_screen_wait(
                CalendarWidget(initial_date=datetime.now())
            )
            if selected_date:
                self.app.file_log.info(f"Date selected: {selected_date}")

Calendar Picker
---------------

Interactive calendar widget for date selection with month/year navigation.

.. automodule:: fiwa_cli.components.calendar_picker
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Features:
    - Month/year navigation with ◀ ▶ buttons
    - "Today" quick navigation
    - Configurable week start (Monday/Sunday)
    - Customizable positioning and margins
    - Dismissible by clicking outside or pressing Escape

Header
------

Main application header with branding, navigation, and status display.

.. automodule:: fiwa_cli.components.header
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

The FiwaHeader is a persistent component at the top of all screens:

Key Features:
    - FiWa branding/logo display
    - Menu button (☰) for navigation
    - Calendar button for date selection
    - Real-time clock display
    - Reactive properties (auto-updates on state changes)
    - Docked to top (always visible)
    - Themed accent background

Reactive Attributes:
    - **user**: Current username (updates on login/logout)
    - **projects**: List of project names
    - **project_id**: Active project ID
    - **project_ids**: All project IDs

Buttons:
    - **☰ Menu**: Opens navigation menu (keyboard: M)
    - **Calendar**: Opens date picker modal

Layout::

    ┌────────────────────────────────────────────────────┐
    │ FiWa  [☰ Menu] [Calendar]       Mar 29 2026 14:32 │
    └────────────────────────────────────────────────────┘

Time Display
------------

Auto-updating real-time clock widget.

.. automodule:: fiwa_cli.components.time_display
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Simple time display widget that updates every second:

Key Features:
    - Shows current date and time
    - Updates automatically every 1 second
    - Human-readable format: "Mar 29 2026 14:32:45"
    - Lightweight and efficient
    - Used in FiwaHeader

Display Format:
    "%b %d %Y %H:%M:%S"
        - Abbreviated month name
        - Day of month
        - 4-digit year
        - 24-hour time with seconds

Example::

    >>> from fiwa_cli.components.time_display import TimeDisplay
    >>> yield TimeDisplay()
    >>> # Displays: "Mar 29 2026 14:32:45"
    >>> # Auto-updates every second

Item Input Form
---------------

Comprehensive expense/transaction input form with validation and confirmation.

.. automodule:: fiwa_cli.components.item_input_form
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

The ItemInputForm is the core component for all expense data entry:

Key Features:
    - **Dual mode**: Create new or edit existing transactions
    - **Cost sharing**: Split expenses between users with percentages
    - **Label selection**: Dynamic tabbed interface for categories
    - **Default labels**: Auto-assignment if not manually selected
    - **Exchange rates**: Manual or automatic currency conversion
    - **Validation**: Comprehensive input checking and sanitization
    - **Confirmation**: Preview modal before database commit
    - **Security**: Input sanitization to prevent injection

Form Modes:
    **Create Mode** (edit_mode=False):
        - Empty form with default values
        - Current user as buyer/recipient
        - Today's date as default
        - New UUID generated
        - Posts ItemCreated message on save

    **Edit Mode** (edit_mode=True):
        - Pre-filled with existing expense data
        - Preserves item_id and item_uuid
        - Shows "Edit" in title
        - Updates database on save

Form Sections:
    1. **Basic Info**: Name, price, currency, date
    2. **User Assignment**: Bought by, bought for (with sharing)
    3. **Exchange Rate**: Rate and date (optional)
    4. **Labels**: Tabbed selection interface
    5. **Notes**: Free text field

Label Selection:
    Tabs dynamically created based on project style:
        - **Count**: Transaction counting
        - **Transaction**: Type (fixed/variable/daily/revenue)
        - **Account**: Bank/payment method
        - **Main**: Primary category
        - **Secondary**: Additional tags (multi-select)

    Each tab shows radio buttons for that label group.
    User-owned labels shown with colored background.

Cost Sharing:
    - Add multiple "Bought For" users
    - Set percentage for each user (sliders or input)
    - Validation ensures total equals 100%
    - Shared portions use liability accounts
    - Each user sees their share in their view

Validation:
    **Required Fields**:
        - Name (max 100 chars)
        - Price (positive number)
        - Currency (exactly 3 letters)
        - Date (valid date)

    **Optional Fields**:
        - Exchange rate (positive if provided)
        - Labels (defaults used if not selected)
        - Notes (free text)

    **Sharing Validation**:
        - Percentages must total 100%
        - Shows error modal if invalid
        - Prevents database write until corrected

Confirmation Flow:
    1. User fills form and clicks Save
    2. Form validates all inputs
    3. ItemConfirmationModal opens
    4. Preview shows all details and labels
    5. User reviews and clicks Confirm
    6. Database operation executes
    7. Success notification shown
    8. Form closes

Example::

    # Create new expense
    form = ItemInputForm(edit_mode=False)
    result = await self.app.push_screen_wait(form)

    # Edit existing
    item_data = {'item_id': 42, 'name': 'Groceries', ...}
    form = ItemInputForm(edit_mode=True, item_data=item_data)
    result = await self.app.push_screen_wait(form)

Related Modals:
    - **ItemConfirmationModal**: Preview and confirm before save
    - **DeleteConfirmationModal**: Confirm expense deletion
    - **LabelModalScreen**: Tabbed label selection interface

Week Month Picker
-----------------

Period navigation widget for selecting weeks or months.

.. automodule:: fiwa_cli.components.week_month_picker
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

The WeekMonthWidget provides period selection for filtering expenses:

Key Features:
    - **Mode switching**: Toggle between week and month view
    - **Dropdown selection**: Choose specific week/month
    - **Navigation buttons**: Previous (◀) and Next (▶)
    - **Year display**: Shows current year
    - **Period events**: Bubbles PeriodChanged message
    - **Reset button**: Quick return to current period

Display Modes:
    **Week Mode**:
        - Shows ISO week numbers (1-52/53)
        - Dropdown: "Week 1", "Week 2", ..., "Week 52"
        - Navigation respects year boundaries
        - Updates: current_year, current_week

    **Month Mode**:
        - Shows month names
        - Dropdown: "January", "February", ..., "December"
        - Navigation wraps at year boundaries
        - Updates: current_year, current_month

Layout::

    ┌──────────────────────────┐
    │    Week ▼                │  ← Dropdown (week/month)
    │  ◀  2026 Week 13  ▶      │  ← Navigation
    │   [Reset to Current]     │  ← Reset button
    └──────────────────────────┘

Integration:
    Used in:
        - InputsScreen sidebar (filters Edit view)
        - ReportsScreen sidebar (filters all reports)

    When period changes:
        - Widget posts PeriodChanged message
        - Parent screen updates app_state
        - Data views refresh with new period filter

PeriodChanged Message:
    Attributes:
        - period_type: "week" or "month"
        - year: Selected year
        - week: Week number (if week mode)
        - month: Month number (if month mode)

Example::

    # Add to sidebar
    yield WeekMonthWidget(id="period-picker")

    # Handle period changes
    def on_week_month_widget_period_changed(self, message):
        year = message.year
        if message.period_type == "week":
            week = message.week
            # Filter by week
        else:
            month = message.month
            # Filter by month

All Components
--------------

Complete list of available components:

.. autosummary::
   :toctree: generated/

   fiwa_cli.components.calendar_picker
   fiwa_cli.components.calendar_picker
   fiwa_cli.components.header
   fiwa_cli.components.time_display
   fiwa_cli.components.item_input_form
   fiwa_cli.components.week_month_picker

Component Usage Patterns
-------------------------

Using Header Component
~~~~~~~~~~~~~~~~~~~~~~

Every screen should include FiwaHeader for consistent navigation::

    from fiwa_cli.components import FiwaHeader

    class MyScreen(Screen):
        def compose(self) -> ComposeResult:
            yield FiwaHeader(
                user=self.app.app_state["user_name"],
                projects=self.app.app_state["project_names"],
                project_id=self.app.app_state["project_id"],
                project_ids=self.app.app_state["project_ids"]
            )
            # ... rest of screen content

Updating header reactively::

    header = self.query_one(FiwaHeader)
    header.user = "batman"  # Triggers automatic refresh
    header.project_id = 2   # Updates display

Using Time Display
~~~~~~~~~~~~~~~~~~

Add real-time clock to any layout::

    from fiwa_cli.components.time_display import TimeDisplay

    def compose(self):
        yield TimeDisplay()
        # Automatically updates every second

Using Calendar Picker
~~~~~~~~~~~~~~~~~~~~~

Get date selection from user::

    from fiwa_cli.components.calendar_picker import CalendarWidget

    async def select_date(self):
        calendar = CalendarWidget(
            initial_date=datetime.now(),
            week_starts_monday=True,
            margin=(3, 0, 0, 15)
        )
        selected = await self.app.push_screen_wait(calendar)
        if selected:
            self.app.notify(f"Selected: {selected.strftime('%Y-%m-%d')}")

Callback method::

    def show_calendar(self):
        self.app.push_screen(
            CalendarWidget(),
            callback=self._handle_date
        )

    def _handle_date(self, date):
        if date:
            print(f"User selected: {date}")

Using Week/Month Picker
~~~~~~~~~~~~~~~~~~~~~~~~

Add period selector to sidebar::

    from fiwa_cli.components.week_month_picker import WeekMonthWidget

    def compose(self):
        with Sidebar():
            yield WeekMonthWidget(id="period-picker")

Handle period changes::

    def on_week_month_widget_period_changed(self, message):
        if message.period_type == "week":
            self.filter_by_week(message.year, message.week)
        else:
            self.filter_by_month(message.year, message.month)

Using Item Input Form
~~~~~~~~~~~~~~~~~~~~~

Create new expense::

    from fiwa_cli.components.item_input_form import ItemInputForm

    async def add_expense(self):
        form = ItemInputForm(edit_mode=False)
        result = await self.app.push_screen_wait(form)
        # result is None if canceled

Edit existing expense::

    async def edit_expense(self, item_id):
        # Fetch item data from database
        dbh = self.app._config.get("dbh")
        item = dbh.op_item_get(item_id)

        # Open form in edit mode
        form = ItemInputForm(edit_mode=True, item_data=item)
        result = await self.app.push_screen_wait(form)

Callback method::

    def add_expense(self):
        form = ItemInputForm(edit_mode=False)
        self.app.push_screen(form, callback=self._handle_created)

    def _handle_created(self, result):
        if result:
            self.refresh_expense_list()

Best Practices
--------------

Component Composition
~~~~~~~~~~~~~~~~~~~~~

* Always include FiwaHeader for consistent navigation
* Use TimeDisplay in headers or status bars
* Position components logically (header top, content center)
* Group related components in containers
* Use ScrollableContainer for long content

State Management
~~~~~~~~~~~~~~~~

* Update reactive properties to trigger auto-refresh
* Don't call refresh() manually on reactive widgets
* Use app_state for global state
* Use component attributes for local state
* Clear state when component is removed

Message Handling
~~~~~~~~~~~~~~~~

* Listen for component messages (PeriodChanged, ItemCreated)
* Handle messages at appropriate level (parent screen)
* Don't block in message handlers
* Post messages for significant events
* Use Message.bubble for upward propagation

CSS and Styling
~~~~~~~~~~~~~~~~

* Use theme variables ($accent, $surface, $text)
* Define component-specific CSS in separate .tcss files
* Load CSS in on_mount() with load_dynamic_css()
* Use classes for reusable styles
* Use IDs for unique element styling

Performance
~~~~~~~~~~~

* Lazy load large components when needed
* Use set_interval() for auto-updates (TimeDisplay)
* Avoid re-rendering entire component on small changes
* Use reactive properties for targeted updates
* Clean up timers and watchers on unmount

Common Workflows
----------------

Adding Expense with Labels
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. User clicks "New" in inputs
2. ItemInputForm opens
3. User fills basic info (name, price, date)
4. User clicks "Select Labels" button
5. LabelModalScreen opens with tabs
6. User navigates to "Main Labels" tab
7. User selects "Groceries"
8. Modal closes, label shown in form
9. User clicks Save
10. ItemConfirmationModal shows preview
11. User clicks Confirm
12. Expense saved to database

Filtering by Period
~~~~~~~~~~~~~~~~~~~

1. User in Inputs screen (Edit view)
2. WeekMonthWidget in sidebar
3. User changes from "Week" to "Month"
4. User selects "March 2026"
5. Widget posts PeriodChanged message
6. InputsScreen updates app_state
7. EditExpenseView refreshes tables
8. Only March expenses shown

Sharing Expense Cost
~~~~~~~~~~~~~~~~~~~~

1. User creates expense in ItemInputForm
2. User fills name: "Dinner", price: 100
3. User scrolls to "Bought For" section
4. User sees self at 100%
5. User clicks "Add User" (or adjusts percentage)
6. User adds "Superman" at 50%
7. Adjusts self to 50%
8. Total shows 100% (valid)
9. User saves
10. System validates percentages
11. Confirmation shows split details
12. Each user sees their 50% share

Troubleshooting
---------------

Calendar Not Showing
~~~~~~~~~~~~~~~~~~~~

* Check if another modal is open (only one modal at a time)
* Verify calendar_picker.tcss is loaded
* Check margin/align settings
* Review logs for CSS loading errors

Week/Month Picker Not Updating
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Ensure parent listens for PeriodChanged message
* Check handler method name matches message class
* Verify app_state is being updated
* Check if data refresh is called after state update

Labels Not Showing in Form
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Verify project has labels created
* Check ProjectComposer for project_style
* Ensure label cache is loaded (op_label_get_all)
* Review label_status (must be active=2)
* Check label owner permissions

Cost Sharing Validation Fails
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* "Percentages must total 100%"
  - Check all user percentages
  - Ensure no rounding errors
  - Remove users with 0%
  - Recalculate totals

Form Won't Save
~~~~~~~~~~~~~~~

* Check required fields filled (name, price, currency, date)
* Verify price is positive number
* Ensure currency is exactly 3 letters
* Check date format is valid
* Review validation error messages

See Also
--------

* :doc:`screens`: Screen implementations
* :doc:`../development`: Development guide
* :doc:`../logging`: Logging documentation

