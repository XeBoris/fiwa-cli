Logging
=======

FiWa CLI includes a comprehensive logging system with automatic file rotation.

Overview
--------

The application uses a custom file logger (``self.app.file_log``) that:

* Writes to ``{data_path}/fiwa.log``
* Automatically rotates at 10 MB
* Keeps 5 backup files (fiwa.log.1, fiwa.log.2, etc.)
* Uses UTF-8 encoding
* Includes timestamps and log levels

Log Format
----------

Each log entry follows this format::

    2026-03-29 14:30:45 - INFO     - User logged in: batman
    2026-03-29 14:30:46 - WARNING  - Database query slow: 2.3s
    2026-03-29 14:30:47 - ERROR    - Failed to save expense

Format components:

* **Timestamp**: YYYY-MM-DD HH:MM:SS
* **Log Level**: DEBUG, INFO, WARNING, ERROR, CRITICAL (8 chars padded)
* **Message**: Your log message

Usage
-----

From the Main Application
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class MyApp(App):
        def on_mount(self):
            self.file_log.info("Application started")
            self.file_log.debug(f"Config: {self._config}")

From Any Screen
~~~~~~~~~~~~~~~

.. code-block:: python

    class SettingsScreen(Screen):
        def on_mount(self):
            self.app.file_log.info("Settings screen opened")

        def save_settings(self):
            self.app.file_log.info("Saving settings...")
            # ... save logic ...
            self.app.file_log.info("Settings saved successfully")

From Any Widget
~~~~~~~~~~~~~~~

.. code-block:: python

    class CalendarWidget(ModalScreen):
        def _change_month(self, delta):
            self.app.file_log.info(f"Calendar navigated to: {self.display_date}")

        def _select_date(self, date):
            self.app.file_log.info(f"User selected date: {date}")

Log Levels
----------

Use appropriate log levels for different message types:

debug()
~~~~~~~

Detailed debugging information. Use for development and troubleshooting::

    self.app.file_log.debug(f"Variables: x={x}, y={y}, state={state}")
    self.app.file_log.debug("Entering complex calculation loop")

info()
~~~~~~

General informational messages. Use for normal operations::

    self.app.file_log.info("User logged in: batman")
    self.app.file_log.info("Project created: Bat Cave Expenses")
    self.app.file_log.info("Report generated for March 2026")

warning()
~~~~~~~~~

Warning messages for unusual but recoverable situations::

    self.app.file_log.warning("Database query took 2.5 seconds")
    self.app.file_log.warning("User has no projects assigned")
    self.app.file_log.warning("Cache miss for project labels")

error()
~~~~~~~

Error messages for failures that prevent specific operations::

    self.app.file_log.error("Failed to save expense to database")
    self.app.file_log.error(f"Invalid currency code: {currency}")
    self.app.file_log.error("Database connection lost")

critical()
~~~~~~~~~~

Critical errors that may cause application failure::

    self.app.file_log.critical("Database file corrupted")
    self.app.file_log.critical("Cannot create log directory")

Viewing Logs
------------

Real-time Monitoring
~~~~~~~~~~~~~~~~~~~~

View logs as they're written::

    $ tail -f /path/to/data/fiwa.log

View Last 100 Lines
~~~~~~~~~~~~~~~~~~~

See recent activity::

    $ tail -n 100 /path/to/data/fiwa.log

View Entire Log
~~~~~~~~~~~~~~~

See all logged events::

    $ cat /path/to/data/fiwa.log
    $ less /path/to/data/fiwa.log

Search Logs
~~~~~~~~~~~

Find specific events::

    $ grep "ERROR" /path/to/data/fiwa.log
    $ grep "User logged in" /path/to/data/fiwa.log
    $ grep "2026-03-29" /path/to/data/fiwa.log

Log Rotation
------------

Automatic Rotation
~~~~~~~~~~~~~~~~~~

Logs automatically rotate when ``fiwa.log`` reaches 10 MB:

* **fiwa.log** → **fiwa.log.1** (current becomes backup 1)
* **fiwa.log.1** → **fiwa.log.2** (backup 1 becomes backup 2)
* ... and so on up to **fiwa.log.5**

The oldest log (fiwa.log.5) is deleted when a new rotation occurs.

Total Log Storage
~~~~~~~~~~~~~~~~~

Maximum disk space used: **50 MB** (10 MB × 5 files)

Manual Log Management
~~~~~~~~~~~~~~~~~~~~~

Archive old logs::

    $ cd /path/to/data
    $ tar -czf fiwa-logs-$(date +%Y%m%d).tar.gz fiwa.log*
    $ rm fiwa.log.*  # Keep only fiwa.log

Clear all logs::

    $ rm /path/to/data/fiwa.log*

Best Practices
--------------

1. **Log at appropriate levels**: Don't use ERROR for warnings
2. **Include context**: Add user IDs, project names, timestamps
3. **Be descriptive**: "User login failed: invalid password" not just "Login failed"
4. **Don't log sensitive data**: Avoid logging passwords or tokens
5. **Use structured messages**: Include enough info to debug issues

Example Logging Pattern
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def create_project(self, name, user_id):
        self.app.file_log.info(f"Creating project: '{name}' for user {user_id}")

        try:
            project_id = self.dbh.op_project_create(name, user_id)
            self.app.file_log.info(f"Project created successfully: ID={project_id}")
            return project_id
        except ValueError as e:
            self.app.file_log.error(f"Validation error creating project '{name}': {e}")
            raise
        except Exception as e:
            self.app.file_log.critical(f"Unexpected error creating project '{name}': {e}")
            raise

Troubleshooting
---------------

Log File Not Created
~~~~~~~~~~~~~~~~~~~~

1. Check data directory exists: ``ls -la /path/to/data``
2. Check permissions: ``ls -ld /path/to/data``
3. Check console output for error messages

No Logs Appearing
~~~~~~~~~~~~~~~~~

1. Verify logging is configured: Look for "✓ Custom file logging configured" message
2. Check if using correct logger: Use ``self.app.file_log.info()`` not ``self.log()``
3. Verify file exists: ``ls -lh /path/to/data/fiwa.log``

Performance Considerations
--------------------------

* File logging is asynchronous and has minimal performance impact
* Log rotation happens automatically without blocking the application
* Debug-level logging may impact performance in production - use INFO level
* The 10 MB file size ensures good performance even with extensive logging

See Also
--------

* :py:class:`fiwa_cli.main.MyApp`: Main application class with file_log setup
* :py:meth:`fiwa_cli.main.MyApp._setup_file_logging`: Logging configuration method
* `Python logging module <https://docs.python.org/3/library/logging.html>`_
* `RotatingFileHandler <https://docs.python.org/3/library/logging.handlers.html#rotatingfilehandler>`_
