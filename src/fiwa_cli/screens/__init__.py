"""Screens package for FiWa application."""

from fiwa_cli.screens.menu import MenuScreen
from fiwa_cli.screens.project_selector import ProjectSelectorScreen
from fiwa_cli.screens.dashboard import DashboardScreen
from fiwa_cli.screens.inputs import InputsScreen
from fiwa_cli.screens.reports import ReportsScreen
from fiwa_cli.screens.settings import SettingsScreen

__all__ = [
    "MenuScreen",
    "ProjectSelectorScreen",
    "CalendarScreen",
    "DashboardScreen",
    "InputsScreen",
    "ReportsScreen",
    "SettingsScreen",
]
