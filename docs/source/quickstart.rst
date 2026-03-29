Quickstart Guide
================

Get started with FiWa CLI in minutes!

Installation
------------

Install from source::

    $ cd /path/to/fiwa-cli
    $ make install

Or install in development mode::

    $ make install-dev

Initialization
--------------

Create a new FiWa data directory::

    $ fiwa init --path /home/user/fiwa-data

This creates:

* SQLite database with schema
* Default configuration files
* Log directory
* Sample data (optional)

First Run
---------

Start FiWa with a specific user::

    $ fiwa run --path /home/user/fiwa-data --user batman
    Enter password for user batman: ****

Or start without user (login via UI)::

    $ fiwa run --path /home/user/fiwa-data

Keyboard Shortcuts
------------------

Once running, use these shortcuts:

* **Q** or **Ctrl+C**: Quit application
* **M**: Open menu
* **S**: Open settings
* **E**: Open expenses/inputs
* **R**: Open reports
* **P**: Select project
* **D**: Toggle dark/light theme

Basic Workflow
--------------

1. **Create a Project**

   * Press **S** to open Settings
   * Click "Create Project"
   * Enter project name and currency
   * Select project style (e.g., "ExpenseTracker")

2. **Add an Expense**

   * Press **E** to open Expenses
   * Click "Add New Expense"
   * Fill in details (name, price, date)
   * Select labels/categories
   * Press Save

3. **View Reports**

   * Press **R** to open Reports
   * Select time period (week/month)
   * View expense summaries
   * Check repayment status

4. **Manage Settings**

   * Press **S** to open Settings
   * Manage projects, users, and labels
   * Modify project settings
   * Set default labels

Development Mode
----------------

Run without installing::

    $ make dev-run ARGS='run --path /test/path --user batman'

This is useful during development when you're making frequent code changes.

View Logs
---------

Monitor application activity::

    $ tail -f /home/user/fiwa-data/fiwa.log

See :doc:`logging` for detailed logging documentation.

Next Steps
----------

* Read the :doc:`installation` guide for detailed setup
* Check the :doc:`logging` documentation for monitoring
* Explore the :doc:`api/modules` for API reference
* See :doc:`development` for contributing guidelines

Common Tasks
------------

Switch Projects
~~~~~~~~~~~~~~~

* Press **P** to open project selector
* Select desired project from list
* Or use the project dropdown in the header

Add Users to Project
~~~~~~~~~~~~~~~~~~~~

* Press **S** for Settings
* Click "Modify Project"
* Click "Add Users" button
* Select users and assign permissions

Set Default Labels
~~~~~~~~~~~~~~~~~~

* Press **S** for Settings
* Click "Manage Labels"
* Click the star icon to set defaults
* One default per label category per user

Share Expenses
~~~~~~~~~~~~~~

* Press **E** for Expenses
* Click "Add New Expense"
* In "Bought For" section, adjust percentages
* System automatically handles liability accounts

Troubleshooting
---------------

Can't Login
~~~~~~~~~~~

1. Verify user exists in database
2. Check password is correct
3. Check database file permissions
4. View logs: ``tail /path/to/data/fiwa.log``

Project Not Loading
~~~~~~~~~~~~~~~~~~~

1. Verify project exists in database
2. Check user has project permissions
3. Try selecting project manually (Press **P**)
4. Check project_store is valid JSON

Performance Issues
~~~~~~~~~~~~~~~~~~

1. Check database size: ``ls -lh /path/to/data/*.db``
2. Check log file size: ``ls -lh /path/to/data/fiwa.log``
3. Clear old logs if needed
4. Vacuum database if very large

See Also
--------

* :doc:`installation`: Detailed installation guide
* :doc:`api/main`: Main application API reference
* :doc:`logging`: Logging system documentation
