"""Reusable UI components for FiWa CLI.

This package contains all reusable widgets and components used throughout
the FiWa application. Components are self-contained, themeable, and follow
consistent design patterns.

Available Components:
    - **FiwaHeader**: Application header with branding and navigation
    - **TimeDisplay**: Auto-updating real-time clock
    - **CalendarWidget**: Interactive date picker modal
    - **WeekMonthWidget**: Week/month period selector with navigation
    - **ItemInputForm**: Comprehensive expense/transaction input form

Component Design Principles:
    - Self-contained: Each component manages its own state
    - Reusable: Can be used in multiple screens
    - Themeable: Uses CSS variables for consistent styling
    - Message-based: Communicate via Textual messages
    - Reactive: Auto-update when state changes

Quick Import:
    >>> from fiwa_cli.components import FiwaHeader, TimeDisplay
    >>>
    >>> yield FiwaHeader(user="batman", projects=["Project 1"])
    >>> yield TimeDisplay()

Example:
    Using multiple components::

        >>> from fiwa_cli.components import FiwaHeader, TimeDisplay
        >>> from fiwa_cli.components.calendar_picker import CalendarWidget
        >>> from fiwa_cli.components.week_month_picker import WeekMonthWidget
        >>>
        >>> def compose(self):
        >>>     yield FiwaHeader(...)
        >>>     yield WeekMonthWidget()
        >>>     # ... content ...

See Also:
    screens: Screen implementations using these components
    main: Main application
"""

from fiwa_cli.components.header import FiwaHeader
from fiwa_cli.components.time_display import TimeDisplay

__all__ = ["FiwaHeader", "TimeDisplay"]
