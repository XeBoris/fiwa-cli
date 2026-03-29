"""FiWa CLI - Financial Workflow Application.

A comprehensive financial tracking and workflow management application
built with Textual for terminal-based interfaces.
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("fiwa-cli")
except PackageNotFoundError:
    # Package is not installed, use fallback during development
    __version__ = "0.1.0.dev"

__author__ = "Boris Bauermeister"

# Don't import main components here to avoid circular import issues
# when running with `python -m fiwa_cli.main`
# Users should import directly: from fiwa_cli.main import MyApp, main

__all__ = ["__version__", "__author__"]
