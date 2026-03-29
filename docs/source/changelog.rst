Changelog
=========

All notable changes to FiWa CLI will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[Unreleased]
------------

Added
~~~~~

* Custom file logging with rotation (10 MB, 5 backups)
* ``self.app.file_log`` accessible from all screens and widgets
* Comprehensive docstrings for main.py
* Sphinx documentation structure
* Month start day configuration in project settings
* User-specific liability account assignment
* Week navigation across year boundaries
* Project store loading on login and project switch

Changed
~~~~~~~

* Improved week navigation logic for ISO calendar boundaries
* Simplified logging setup (no interference with Textual's logging)
* Project reload after settings changes (no re-login required)

Fixed
~~~~~

* Week navigation from 2026/W01 to 2025/W52 now works correctly
* Project store not loading when logging in without --user flag
* RuntimeWarning about circular imports in __init__.py
* "test" notification from menu.py (replaced with log message)

[0.1.0] - 2026-03-29
--------------------

Initial release.

Added
~~~~~

* Basic application structure with Textual
* User authentication and session management
* Multi-project support
* Expense tracking and management
* Calendar widget for date selection
* Settings screens for projects, users, and labels
* Report generation
* SQLite database backend
* TCSS styling system
* Keyboard shortcuts for navigation
* Dark/light theme support

