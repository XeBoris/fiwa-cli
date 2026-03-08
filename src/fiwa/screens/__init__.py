"""Screens package for FiWa application."""
from fiwa.screens.menu import MenuScreen
from fiwa.screens.project_selector import ProjectSelectorScreen
from fiwa.screens.dashboard import DashboardScreen
from fiwa.screens.inputs import InputsScreen
from fiwa.screens.reports import ReportsScreen
from fiwa.screens.settings import SettingsScreen

__all__ = [
    "MenuScreen",
    "ProjectSelectorScreen",
    "CalendarScreen",
    "DashboardScreen",
    "InputsScreen",
    "ReportsScreen",
    "SettingsScreen",
]
