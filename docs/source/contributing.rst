Contributing
============

Thank you for considering contributing to FiWa CLI!

How to Contribute
-----------------

Reporting Bugs
~~~~~~~~~~~~~~

Submit bug reports with:

* Clear description of the issue
* Steps to reproduce
* Expected vs actual behavior
* FiWa version and Python version
* Relevant log excerpts from ``fiwa.log``

Example bug report::

    **Bug**: Calendar navigation jumps incorrectly

    **Steps**:
    1. Open calendar widget
    2. Navigate from 2026/W01 backwards
    3. Should show 2025/W52, but shows 2025/W01

    **Environment**:
    - FiWa CLI: 0.1.0
    - Python: 3.12
    - OS: Linux

    **Logs**:
    2026-03-29 14:30:45 - ERROR - Calendar navigation error

Suggesting Features
~~~~~~~~~~~~~~~~~~~

Feature requests should include:

* Clear use case description
* Expected behavior
* Potential implementation approach (optional)

Submitting Pull Requests
~~~~~~~~~~~~~~~~~~~~~~~~~

1. Fork the repository
2. Create a feature branch: ``git checkout -b feature/my-feature``
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Commit with clear messages
7. Push to your fork
8. Submit a pull request

Development Guidelines
----------------------

Code Style
~~~~~~~~~~

* Follow PEP 8
* Use type hints
* Maximum line length: 100 characters
* Use meaningful variable names

Documentation
~~~~~~~~~~~~~

* Add docstrings to all public functions/classes
* Use Google-style docstring format
* Include examples in docstrings
* Update relevant .rst files

Logging
~~~~~~~

Add appropriate logging::

    def my_function(self):
        self.app.file_log.info("Starting my_function")
        try:
            # ... operation ...
            self.app.file_log.info("Operation successful")
        except Exception as e:
            self.app.file_log.error(f"Operation failed: {e}")
            raise

Testing
~~~~~~~

* Add tests for new features
* Ensure existing tests pass
* Test with different Python versions

Commit Messages
~~~~~~~~~~~~~~~

Use clear, descriptive commit messages::

    # Good
    Fix week navigation across year boundaries
    Add month_start configuration to project settings

    # Bad
    Fix bug
    Update code

TCSS Styling
~~~~~~~~~~~~

* Keep styles organized by component
* Use consistent naming conventions
* Document special styling decisions

Pull Request Checklist
----------------------

Before submitting a pull request:

- [ ] Code follows project style guidelines
- [ ] Docstrings added/updated
- [ ] Type hints included
- [ ] Logging added for important operations
- [ ] Tests added (if applicable)
- [ ] Documentation updated
- [ ] Changelog.rst updated
- [ ] No breaking changes (or documented if necessary)
- [ ] Tested manually

Code Review Process
-------------------

1. Maintainer reviews code
2. Automated checks run (if configured)
3. Feedback provided
4. Changes requested (if needed)
5. Approval and merge

Areas for Contribution
----------------------

High Priority
~~~~~~~~~~~~~

* Test coverage improvements
* Performance optimizations
* Documentation improvements
* Bug fixes

Medium Priority
~~~~~~~~~~~~~~~

* New report types
* Additional project styles/composers
* UI/UX improvements
* Accessibility enhancements

Low Priority
~~~~~~~~~~~~

* Web mode implementation
* Additional themes
* Export/import features
* Advanced analytics

Getting Help
------------

* Read existing documentation
* Check closed issues for similar problems
* Ask in discussions
* Contact maintainers

License
-------

By contributing, you agree that your contributions will be licensed
under the same license as the project (see LICENSE file).

Code of Conduct
---------------

Be respectful, constructive, and collaborative.

See Also
--------

* :doc:`development`: Development setup guide
* :doc:`api/modules`: API documentation
