"""Screens package for FiWa application."""
from screens.menu import MenuScreen
from screens.project_selector import ProjectSelectorScreen
from screens.calendar_screen import CalendarScreen
from screens.dashboard import DashboardScreen
from screens.inputs import InputsScreen
from screens.reports import ReportsScreen
from screens.settings import SettingsScreen

__all__ = [
    "MenuScreen",
    "ProjectSelectorScreen",
    "CalendarScreen",
    "DashboardScreen",
    "InputsScreen",
    "ReportsScreen",
    "SettingsScreen",
]
