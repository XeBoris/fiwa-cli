"""Database handler factory for FiWa CLI.

This module provides a factory pattern for creating database handlers.
It abstracts the database backend selection, allowing the application
to work with different backends (SQLite, API) without changing code.

The handler factory:
    - Provides unified interface for database operations
    - Supports multiple backends (SQLite, API)
    - Allows runtime backend selection
    - Simplifies testing with mock handlers

Supported Backends:
    - **sqlite**: Local SQLite database (implemented)
    - **api**: Remote API backend (future implementation)

Classes:
    Handler: Factory class for creating database handlers

Example:
    Creating SQLite handler::

        >>> from fiwa_cli.functions.handler import Handler
        >>> handler = Handler(method="sqlite")
        >>> dbh = handler.load()
        >>> # Returns SQLLiteHandler instance

    Future API handler::

        >>> handler = Handler(method="api")
        >>> dbh = handler.load()
        >>> # Returns HandlerApi instance

See Also:
    handler_sqllite.SQLLiteHandler: SQLite database implementation
    handler_api.HandlerApi: API backend implementation (future)
"""

from fiwa_cli.functions.handler_api import HandlerApi
from fiwa_cli.functions.handler_sqllite import SQLLiteHandler


class Handler:
    """Factory class for creating database backend handlers.

    This factory pattern allows runtime selection of the database backend
    (SQLite or API) without changing application code. The factory returns
    the appropriate handler instance based on the specified method.

    Attributes:
        _method (str): Backend type ("sqlite" or "api")

    Supported Methods:
        - "sqlite": Returns SQLLiteHandler for local database
        - "api": Returns HandlerApi for remote API (future)

    Example:
        SQLite backend::

            >>> handler = Handler(method="sqlite")
            >>> dbh = handler.load()
            >>> # dbh is SQLLiteHandler instance
            >>> users = dbh.op_user_get_all()

        API backend (future)::

            >>> handler = Handler(method="api")
            >>> dbh = handler.load()
            >>> # dbh is HandlerApi instance
            >>> users = dbh.op_user_get_all()

    Note:
        The factory ensures both handler types implement the same
        interface (op_* methods), allowing seamless backend switching.
    """

    def __init__(self, method):
        """Initialize the handler factory with backend method.

        Args:
            method (str): Backend type - "sqlite" or "api"

        Example:
            >>> handler = Handler(method="sqlite")
        """
        self._method = method

    def load(self):
        """Load and return the appropriate database handler instance.

        Returns:
            SQLLiteHandler or HandlerApi: Database handler instance

        Raises:
            NotImplementedError: If method is not "sqlite" or "api"

        Example:
            >>> handler = Handler(method="sqlite")
            >>> dbh = handler.load()
            >>> # Use dbh for database operations
        """
        if self._method == "api":
            return HandlerApi(self)
        elif self._method == "sqlite":
            return SQLLiteHandler(self)
        else:
            raise NotImplementedError(f"Handler method '{self._method}' is not implemented.")
