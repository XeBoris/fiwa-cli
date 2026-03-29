Installation
============

This guide covers installing FiWa CLI on your system.

Requirements
------------

* Python 3.10 or higher
* pip package manager
* Terminal emulator with Unicode support
* ~50 MB disk space for application and logs

Python Dependencies
~~~~~~~~~~~~~~~~~~~

Core dependencies (installed automatically):

* textual >= 0.40.0
* bcrypt (for password hashing)
* pyyaml (for configuration)

Optional dependencies:

* sphinx (for building documentation)
* pytest (for running tests)

Install from Source
-------------------

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

For development work (editable install)::

    $ git clone https://github.com/yourusername/fiwa-cli.git
    $ cd fiwa-cli
    $ make install-dev

This installs the package in editable mode, so code changes take effect immediately.

Production Installation
~~~~~~~~~~~~~~~~~~~~~~~

For normal usage::

    $ git clone https://github.com/yourusername/fiwa-cli.git
    $ cd fiwa-cli
    $ make install

Or using pip directly::

    $ pip install .

Install from PyPI
-----------------

(Coming soon)::

    $ pip install fiwa-cli

Verify Installation
-------------------

Check that FiWa is installed correctly::

    $ fiwa --help

    # Or
    $ python -m fiwa_cli.main --help

You should see the help message with available commands.

Initialize Data Directory
-------------------------

Create a new FiWa data directory::

    $ fiwa init --path /home/user/fiwa-data

This creates:

* ``fiwa.db``: SQLite database with schema
* ``config.yml``: Configuration file
* ``fiwa.log``: Application log file (empty initially)

Directory Structure::

    fiwa-data/
    ├── fiwa.db         # Main database
    ├── config.yml      # Configuration
    └── fiwa.log        # Application logs

Configure Data Path
-------------------

You can set a default data path in environment variable::

    $ export FIWA_DATA_PATH="/home/user/fiwa-data"
    $ fiwa run --user batman  # Uses $FIWA_DATA_PATH

Or always specify it explicitly::

    $ fiwa run --path /home/user/fiwa-data --user batman

Uninstallation
--------------

Remove the package::

    $ make uninstall

    # Or
    $ pip uninstall fiwa-cli

Your data directory and logs are NOT removed during uninstallation.
To remove data::

    $ rm -rf /home/user/fiwa-data

Upgrading
---------

Development Mode
~~~~~~~~~~~~~~~~

If installed with ``make install-dev``, just pull latest code::

    $ git pull
    # Changes take effect immediately

Production Mode
~~~~~~~~~~~~~~~

Reinstall the package::

    $ git pull
    $ make reinstall

Or::

    $ pip install --upgrade fiwa-cli

Troubleshooting
---------------

Command Not Found
~~~~~~~~~~~~~~~~~

If ``fiwa`` command is not found:

1. Check PATH includes Python scripts directory::

    $ echo $PATH
    $ which fiwa

2. Add Python scripts to PATH (bash)::

    $ echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    $ source ~/.bashrc

3. Or use full Python module path::

    $ python -m fiwa_cli.main run --path /data --user batman

Permission Errors
~~~~~~~~~~~~~~~~~

If you get permission errors during installation:

1. Use user installation::

    $ pip install --user .

2. Or use virtual environment (recommended)::

    $ python -m venv venv
    $ source venv/bin/activate
    $ make install

Database Initialization Failed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If ``fiwa init`` fails:

1. Check directory permissions::

    $ ls -ld /path/to/data

2. Ensure directory is writable::

    $ chmod u+w /path/to/data

3. Check disk space::

    $ df -h /path/to/data

Virtual Environment Setup
--------------------------

Recommended for development::

    $ python -m venv fiwa-env
    $ source fiwa-env/bin/activate  # Linux/Mac
    $ fiwa-env\\Scripts\\activate     # Windows

    $ pip install -e .  # Editable install
    $ fiwa run --path ./data --user batman

Next Steps
----------

* See :doc:`quickstart` for getting started
* Read :doc:`logging` to understand the logging system
* Check :doc:`api/modules` for API documentation

