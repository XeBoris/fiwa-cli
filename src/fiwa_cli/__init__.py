"""FiWa CLI - Financial Workflow Application.

A comprehensive financial tracking and workflow management application
built with Textual for terminal-based interfaces.
"""

__version__ = "0.1.0"
__author__ = "Boris Bauermeister"

# Import main components for easy access
from fiwa_cli.main import MyApp, main

__all__ = ["MyApp", "main", "__version__", "__author__"]
