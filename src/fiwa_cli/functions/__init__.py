"""Business logic and utility functions for FiWa CLI.

This package contains all core business logic, database handlers, utilities,
and helper functions used throughout the FiWa application. Functions are
organized by purpose and responsibility.

Available Modules:
    - **handler_sqllite**: SQLite database operations and queries
    - **handler_api**: API communication handlers (future)
    - **loader**: Configuration, CSS, and resource loading
    - **logout_util**: Shared logout functionality
    - **project_composer**: Project-specific logic and label composition
    - **db_faker**: Database seeding and test data generation
    - **faker_superhero_project**: Sample project creation

Key Responsibilities:
    - Database operations (CRUD)
    - Configuration management
    - Resource loading (CSS, YAML)
    - Authentication logic
    - Project-specific business rules
    - Data validation and transformation
    - Test data generation

Design Principles:
    - Single responsibility per module
    - Database handler abstraction
    - Reusable utility functions
    - Consistent error handling
    - Comprehensive logging

Example:
    Using database handler::

        >>> from fiwa_cli.functions.handler_sqllite import SQLLiteHandler
        >>> dbh = SQLLiteHandler(db_path="/path/to/db")
        >>> users = dbh.op_user_get_all()

    Loading configuration::

        >>> from fiwa_cli.functions.loader import load_yaml_config
        >>> config = load_yaml_config("/path/to/config.yml")

See Also:
    database: Database schema documentation
    main: Main application using these functions
"""

# from .handler_api import HandlerApi
# from .handler_sqlite import SQLLiteHandler

__all__ = []
