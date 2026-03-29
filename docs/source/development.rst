Development Guide
=================

Contributing to FiWa CLI development.

Development Setup
-----------------

Clone and Install
~~~~~~~~~~~~~~~~~

::

    $ git clone https://github.com/yourusername/fiwa-cli.git
    $ cd fiwa-cli
    $ make install-dev

This installs the package in editable mode.

Project Structure
-----------------

::

    fiwa-cli/
    ├── src/
    │   └── fiwa_cli/
    │       ├── main.py              # Main application
    │       ├── components/          # Reusable UI components
    │       │   ├── calendar_picker.py
    │       │   ├── header.py
    │       │   └── ...
    │       ├── screens/             # Application screens
    │       │   ├── base.py
    │       │   ├── settings.py
    │       │   ├── inputs.py
    │       │   ├── reports.py
    │       │   └── ...
    │       ├── functions/           # Business logic
    │       │   ├── handler_sqllite.py
    │       │   ├── loader.py
    │       │   └── ...
    │       ├── database/            # Database schemas
    │       │   └── schema.sql
    │       └── css/                 # TCSS stylesheets
    │           └── handsome/
    │               ├── main.tcss
    │               ├── screens_*.tcss
    │               └── components_*.tcss
    ├── docs/                        # Sphinx documentation
    ├── tests/                       # Test suite
    ├── Makefile                     # Build automation
    └── pyproject.toml              # Package configuration

Development Workflow
--------------------

1. Make Code Changes
~~~~~~~~~~~~~~~~~~~~

Edit files in ``src/fiwa_cli/``

2. Run Without Installing
~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    $ make dev-run ARGS='run --path ./testdata --user batman'

3. Test Changes
~~~~~~~~~~~~~~~

::

    $ make test  # Run test suite (when available)

4. Build Documentation
~~~~~~~~~~~~~~~~~~~~~~

::

    $ make docs-build
    $ make docs-view

5. Commit Changes
~~~~~~~~~~~~~~~~~

::

    $ git add .
    $ git commit -m "Add feature X"
    $ git push

Code Style Guidelines
---------------------

Docstrings
~~~~~~~~~~

Use Google-style docstrings::

    def my_function(arg1: str, arg2: int) -> bool:
        """Short description of function.

        Longer description providing more detail about what
        the function does and how it works.

        Args:
            arg1: Description of arg1
            arg2: Description of arg2

        Returns:
            Description of return value

        Raises:
            ValueError: Description of when this is raised

        Example:
            >>> my_function("test", 42)
            True
        """

Type Hints
~~~~~~~~~~

Always include type hints::

    from typing import Dict, List, Optional, Any

    def process_data(
        items: List[Dict[str, Any]],
        user_id: int
    ) -> Optional[int]:
        ...

Imports
~~~~~~~

Organize imports::

    # Standard library
    import os
    import sys
    from pathlib import Path

    # Third-party
    from textual.app import App
    from textual.widgets import Button

    # Local
    from fiwa_cli.functions.handler_sqllite import SQLLiteHandler
    from fiwa_cli.components.header import FiwaHeader

Adding New Features
-------------------

New Screen
~~~~~~~~~~

1. Create file in ``src/fiwa_cli/screens/my_screen.py``
2. Create TCSS file in ``src/fiwa_cli/css/handsome/screens_my_screen.tcss``
3. Import and use in main.py or other screens

Template::

    from textual.screen import Screen
    from textual.app import ComposeResult
    from fiwa_cli.functions.loader import load_dynamic_css

    class MyScreen(Screen):
        """My new screen.

        Detailed description here.
        """

        def on_mount(self) -> None:
            """Load CSS when mounted."""
            load_dynamic_css(self, "screens_my_screen.tcss")
            self.app.file_log.info("MyScreen mounted")

        def compose(self) -> ComposeResult:
            """Compose the screen layout."""
            # ...

New Widget
~~~~~~~~~~

1. Create file in ``src/fiwa_cli/components/my_widget.py``
2. Create TCSS file if needed
3. Import and use in screens

Template::

    from textual.widget import Widget
    from textual.app import ComposeResult

    class MyWidget(Widget):
        """My new widget.

        Detailed description here.
        """

        def compose(self) -> ComposeResult:
            """Compose widget layout."""
            # ...

Database Changes
~~~~~~~~~~~~~~~~

1. Modify ``src/fiwa_cli/database/schema.sql``
2. Add migration logic in ``handler_sqllite.py``
3. Update relevant operations (op_*)
4. Test with sample data

TCSS Styling
~~~~~~~~~~~~

Follow the handsome theme conventions::

    MyWidget {
        layout: vertical;
        width: 100%;
        height: auto;
    }

    MyWidget .my-class {
        background: $surface;
        border: solid $accent;
        padding: 1;
    }

Testing
-------

Run Tests
~~~~~~~~~

::

    $ make test

Add New Tests
~~~~~~~~~~~~~

Create tests in ``tests/test_my_feature.py``::

    import pytest
    from fiwa_cli.main import MyApp

    def test_my_feature():
        """Test my new feature."""
        app = MyApp(config={})
        # ... test logic ...
        assert result == expected

Debugging
---------

Console Logging
~~~~~~~~~~~~~~~

Use Textual's devtools::

    $ textual console

    # In another terminal:
    $ textual run --dev src/fiwa_cli/main.py

File Logging
~~~~~~~~~~~~

Add debug logs::

    self.app.file_log.debug(f"Variable state: {my_var}")
    self.app.file_log.info(f"Entering function: {func_name}")

View logs::

    $ tail -f /path/to/data/fiwa.log

Python Debugger
~~~~~~~~~~~~~~~

Add breakpoint::

    import pdb; pdb.set_trace()

    # Or
    breakpoint()

Building Documentation
----------------------

Install Dependencies
~~~~~~~~~~~~~~~~~~~~

::

    $ make docs-install

Generate API Docs
~~~~~~~~~~~~~~~~~

::

    $ make docs-build

This automatically:

1. Runs ``sphinx-apidoc`` to extract docstrings
2. Builds HTML documentation
3. Places output in ``docs/build/html/``

View Documentation
~~~~~~~~~~~~~~~~~~

::

    $ make docs-view  # Opens in browser

    # Or serve locally:
    $ make docs-serve  # http://localhost:8000

Update Documentation
~~~~~~~~~~~~~~~~~~~~

::

    $ make docs-rebuild  # Clean and rebuild

Release Process
---------------

1. Update Version
~~~~~~~~~~~~~~~~~

In ``src/fiwa_cli/__init__.py``::

    __version__ = "0.2.0"

2. Update Changelog
~~~~~~~~~~~~~~~~~~~

Add changes to ``CHANGELOG.md``

3. Build Package
~~~~~~~~~~~~~~~~

::

    $ make clean
    $ make build

4. Tag Release
~~~~~~~~~~~~~~

::

    $ git tag -a v0.2.0 -m "Release version 0.2.0"
    $ git push origin v0.2.0

5. Publish (when ready)
~~~~~~~~~~~~~~~~~~~~~~~

::

    $ python -m twine upload dist/*

Coding Standards
----------------

* Follow PEP 8 style guide
* Maximum line length: 100 characters
* Use type hints for all functions
* Write docstrings for all public APIs
* Add logging for important operations
* Handle exceptions gracefully
* Test new features before committing

Useful Make Commands
--------------------

::

    make install-dev   # Install for development
    make clean         # Remove build artifacts
    make build         # Build wheel package
    make dev-run       # Run without installing
    make docs-build    # Build documentation
    make docs-view     # View documentation
    make reinstall-dev # Clean reinstall in dev mode

Getting Help
------------

* Check existing issues on GitHub
* Review documentation at docs/
* Ask questions in discussions
* Submit bug reports with logs attached

See Also
--------

* :doc:`quickstart`: Getting started guide
* :doc:`api/modules`: Complete API reference
* :doc:`logging`: Logging system details
