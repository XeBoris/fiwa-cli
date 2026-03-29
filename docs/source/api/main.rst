Main Application
================

Core application logic and entry point for FiWa CLI.

Module Overview
---------------

The ``fiwa_cli.main`` module provides the main Textual application class
and command-line entry point. It manages:

* Application lifecycle and initialization
* Reactive state management (``app_state``)
* Custom file logging with rotation
* Keyboard shortcuts and navigation
* Theme management
* Screen composition

.. automodule:: fiwa_cli.main
   :members:
   :undoc-members:
   :show-inheritance:

Application Class
-----------------

The MyApp class is the core of the FiWa CLI application.

.. autoclass:: fiwa_cli.main.MyApp
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Reactive State
~~~~~~~~~~~~~~

The ``app_state`` reactive dictionary is the central state store:

.. code-block:: python

    app_state = {
        "user_name": "batman",
        "user_id": 1,
        "is_logged_in": True,
        "project_id": 42,
        "project_name": "Bat Cave Expenses",
        "project_style": "ExpenseTracker",
        "project_store": {"month_start": 15},
        # ... more fields
    }

Any screen or widget can access and modify this state:

.. code-block:: python

    # Read state
    user = self.app.app_state["user_name"]

    # Update state (triggers UI updates)
    self.app.app_state["project_id"] = new_project_id

Custom File Logging
~~~~~~~~~~~~~~~~~~~

Access the file logger from anywhere:

.. code-block:: python

    # From App
    self.file_log.info("Application started")

    # From Screen/Widget
    self.app.file_log.info("User action logged")
    self.app.file_log.error("Operation failed")

Keyboard Shortcuts
~~~~~~~~~~~~~~~~~~

Application-wide keyboard shortcuts:

* **Q** or **Ctrl+C**: Quit (with logout)
* **D**: Toggle dark/light theme
* **M**: Open menu
* **S**: Open settings
* **E**: Open expenses
* **R**: Open reports
* **P**: Select project

Entry Point Function
---------------------

.. autofunction:: fiwa_cli.main.main

Command-line Interface
~~~~~~~~~~~~~~~~~~~~~~

The ``main()`` function supports two modes:

**Initialize new data directory**::

    $ fiwa init --path /home/user/fiwa-data

**Run the application**::

    $ fiwa run --path /home/user/fiwa-data --user batman

Methods Reference
-----------------

Lifecycle Methods
~~~~~~~~~~~~~~~~~

.. automethod:: fiwa_cli.main.MyApp.on_mount
.. automethod:: fiwa_cli.main.MyApp.compose

State Management
~~~~~~~~~~~~~~~~

.. automethod:: fiwa_cli.main.MyApp.watch_app_state
.. automethod:: fiwa_cli.main.MyApp.update_session_display
.. automethod:: fiwa_cli.main.MyApp.update_main_body

Logging Setup
~~~~~~~~~~~~~

.. automethod:: fiwa_cli.main.MyApp._setup_file_logging

Action Handlers
~~~~~~~~~~~~~~~

.. automethod:: fiwa_cli.main.MyApp.action_quit_app
.. automethod:: fiwa_cli.main.MyApp.action_toggle_dark
.. automethod:: fiwa_cli.main.MyApp.action_open_menu
.. automethod:: fiwa_cli.main.MyApp.action_open_settings
.. automethod:: fiwa_cli.main.MyApp.action_open_expenses
.. automethod:: fiwa_cli.main.MyApp.action_open_reports
.. automethod:: fiwa_cli.main.MyApp.action_select_project

See Also
--------

* :doc:`../logging`: Detailed logging documentation
* :doc:`../quickstart`: Getting started guide
* :doc:`screens`: Screen implementations
* :doc:`components`: Reusable UI components

