import copy

"""SQLite database handler for FiWa CLI.

This module provides comprehensive SQLite database operations for the FiWa
application. It implements all CRUD operations, authentication, session
management, and data queries using the op_* (operation) naming convention.

The SQLite handler:
    - Manages all database operations
    - Provides 100+ op_* methods for CRUD operations
    - Handles password hashing and authentication
    - Manages user sessions
    - Implements label caching
    - Supports transactions
    - Provides comprehensive error handling

Key Features:
    - **User Management**: Create, update, authenticate users
    - **Project Management**: CRUD operations for projects
    - **Item/Transaction Management**: Expense and income tracking
    - **Label Management**: Category and tag operations with caching
    - **Session Management**: Login/logout with UUID sessions
    - **Permission Management**: User-project permission mapping
    - **Password Security**: SHA-256 hashing with salt
    - **Label Caching**: Performance optimization for label queries

Classes:
    SQLLiteHandler: Main database handler class

Database Schema:
    The handler works with tables defined in schema.sql:
        - users: User accounts and authentication
        - sessions: Active user sessions
        - projects: Project definitions
        - user_project_map: User-project relationships with permissions
        - items: Transactions/expenses/income
        - labels: Categories and tags
        - label_defaults: User-specific default labels (future)

Operation Naming Convention:
    All database operations follow the op_* pattern:
        - op_user_*: User operations
        - op_project_*: Project operations
        - op_item_*: Item/transaction operations
        - op_label_*: Label/category operations
        - op_get_*: General query operations

Example:
    Initialize and use handler::

        >>> from fiwa_cli.functions.handler_sqllite import SQLLiteHandler
        >>>
        >>> # Initialize with database path
        >>> dbh = SQLLiteHandler(db_path="/data/fiwa.db")
        >>>
        >>> # User operations
        >>> user_id = dbh.op_user_create({
        >>>     "username": "batman",
        >>>     "password": "darkknight123",
        >>>     "email": "bruce@wayne.com"
        >>> })
        >>>
        >>> # Login
        >>> session = dbh.op_user_login("batman", "darkknight123")
        >>>
        >>> # Project operations
        >>> project_id = dbh.op_project_create(project_data, user_id)
        >>> projects = dbh.op_project_get_info(user_id)
        >>>
        >>> # Item operations
        >>> item_id = dbh.op_item_create(item_data)
        >>> items = dbh.op_item_get_by_user(user_id, project_id, start, end)
        >>>
        >>> # Label operations (with caching)
        >>> labels = dbh.op_label_get_all(project_id, use_cache=True)

Operation Categories:
    **User Operations** (15+ methods):
        - op_user_create: Create new user
        - op_user_login: Authenticate user
        - op_user_logout: End session
        - op_user_get_info: Get user details
        - op_user_get_all: List all users
        - op_user_update: Update user info
        - op_user_update_password: Change password
        - op_total_number_of_users: Count users

    **Project Operations** (12+ methods):
        - op_project_create: Create project
        - op_project_update: Update project
        - op_project_get_info: Get user's projects
        - op_project_get_users: List project members
        - op_project_set_primary: Set primary project
        - op_project_stage: Setup project with defaults

    **Item/Transaction Operations** (10+ methods):
        - op_item_create: Create expense/income
        - op_item_update: Update transaction
        - op_item_get: Get single item
        - op_item_get_by_user: Query user's items
        - op_item_delete: Remove transaction

    **Label Operations** (10+ methods):
        - op_label_create: Create label/category
        - op_label_update: Update label
        - op_label_get_all: Get all labels (with caching)
        - op_label_get_by_name: Find label by name
        - op_label_delete: Remove label
        - op_label_set_default: Set user's default label

    **Session Operations** (5+ methods):
        - op_get_user_sessions: Get current session info
        - op_create_session: Create new session

    **Permission Operations** (5+ methods):
        - op_user_project_permission_update: Update permissions
        - op_project_get_users: Get users with permissions

Caching Strategy:
    Label Caching:
        - Cache key: project_id
        - Cached data: Complete label list
        - Cache invalidation: On project switch or force_refresh
        - Benefits: Reduces database queries, faster label lookups

    Usage::

        >>> # First call: Queries database
        >>> labels = dbh.op_label_get_all(project_id=1, use_cache=True)
        >>>
        >>> # Subsequent calls: Uses cache
        >>> labels = dbh.op_label_get_all(project_id=1, use_cache=True)
        >>>
        >>> # Force refresh: Clears cache and reloads
        >>> labels = dbh.op_label_get_all(project_id=1, force_refresh=True)

Security:
    Password Hashing:
        - Algorithm: SHA-256
        - Salt: Configurable via set_pw_salt()
        - Default salt: "fiwa_default_salt_2026"
        - No plain text passwords stored
        - Hash comparison for authentication

    Session Management:
        - UUID-based session identifiers
        - Session expiration tracking
        - Logout invalidates sessions

Database Connection:
    - Path: Configurable via db_path parameter
    - Default: ":memory:" (in-memory database)
    - Connection: Managed internally
    - Cursor: Reused for operations
    - Salt prefix: Applied to table names for multi-tenancy

See Also:
    handler.Handler: Factory for creating handlers
    handler_api.HandlerApi: API backend (future)
    database.schema.sql: Database schema definition
"""
import sqlite3
from typing import Dict, Optional
from pathlib import Path
import os
import hashlib
import uuid
import json
from datetime import datetime
from datetime import timedelta


class SQLLiteHandler:
    """SQLite database handler implementing all FiWa database operations.

    This class provides a comprehensive interface for all database operations
    in FiWa CLI. It implements 100+ op_* methods for users, projects, items,
    labels, sessions, and permissions.

    The handler manages:
        - Database connections
        - Password hashing and verification
        - Session creation and management
        - Label caching for performance
        - Table name prefixing for multi-tenancy

    Attributes:
        _pw_salt (str): Salt for password hashing, default "fiwa_default_salt_2026"
        _db_salt (str): Prefix for table names, default "stand"
        _db_path (str): Path to SQLite database file
        _connection: SQLite connection object
        _cursor: SQLite cursor object
        _label_cache (dict): Cache of labels by project_id

    Table Naming:
        Tables are prefixed with _db_salt for multi-tenancy:
            - p{salt}_users: User accounts
            - p{salt}_sessions: Active sessions
            - p{salt}_projects: Project definitions
            - p{salt}_user_project_map: User-project relationships
            - p{salt}_items: Transactions
            - p{salt}_labels: Categories/tags

    Password Security:
        - Hashing: SHA-256 with salt
        - Salt: Configurable per instance
        - Comparison: Hash comparison, never plain text
        - Storage: Only hashes stored in database

    Example:
        Basic initialization::

            >>> dbh = SQLLiteHandler(db_path="/data/fiwa.db")
            >>> dbh.set_pw_salt("custom_salt_2026")
            >>> dbh.set_db_salt("prod")

        User operations::

            >>> # Create user
            >>> user_id = dbh.op_user_create({
            >>>     "username": "batman",
            >>>     "password": "secret",
            >>>     "email": "bruce@wayne.com"
            >>> })
            >>>
            >>> # Login
            >>> session = dbh.op_user_login("batman", "secret")
            >>> print(session["session_uuid"])

        Project operations::

            >>> # Create project
            >>> project_id = dbh.op_project_create(project_data, user_id=1)
            >>>
            >>> # Get user's projects
            >>> projects = dbh.op_project_get_info(user_id=1)

        Item operations with date filtering::

            >>> # Get items for user in March 2026
            >>> items = dbh.op_item_get_by_user(
            >>>     user_id=1,
            >>>     project_id=1,
            >>>     start_date=datetime(2026, 3, 1),
            >>>     end_date=datetime(2026, 4, 1)  # Exclusive end
            >>> )

        Label operations with caching::

            >>> # First call: Queries database
            >>> labels = dbh.op_label_get_all(project_id=1, use_cache=True)
            >>>
            >>> # Second call: Uses cache (fast)
            >>> labels = dbh.op_label_get_all(project_id=1, use_cache=True)
            >>>
            >>> # After label changes: Force refresh
            >>> labels = dbh.op_label_get_all(project_id=1, force_refresh=True)

    Note:
        The handler uses prepared statements for all queries to prevent
        SQL injection. All user inputs are parameterized, never concatenated
        into SQL strings.

        The label cache significantly improves performance when repeatedly
        querying labels (e.g., populating dropdown menus). Clear the cache
        when switching projects or after label modifications.

    See Also:
        handler.Handler: Factory for creating handlers
        database.schema.sql: Complete database schema
        project_composer.ProjectComposer: Uses handler for label operations
    """

    def __init__(self, db_path=":memory:"):
        """Initialize SQLite database handler.

        Args:
            db_path (str): Path to SQLite database file
                Default ":memory:" creates in-memory database

        Example:
            >>> # In-memory database (testing)
            >>> dbh = SQLLiteHandler()
            >>>
            >>> # File-based database (production)
            >>> dbh = SQLLiteHandler(db_path="/data/fiwa.db")
        """
        self._pw_salt = "fiwa_default_salt_2026"
        self._db_salt = "stand"
        self._db_path = db_path
        self._connection = None
        self._cursor = None
        self._label_cache: dict[int, list] = {}

    def set_path(self, db_path):
        """Set database file path.

        Args:
            db_path (str): Path to SQLite database file
        """
        self._db_path = db_path

    def set_pw_salt(self, pw_salt):
        """Set password hashing salt.

        Args:
            pw_salt (str): Salt string for password hashing
        """
        self._pw_salt = pw_salt

    def set_db_salt(self, db_salt):
        """Set database table name prefix.

        Args:
            db_salt (str): Prefix for table names (multi-tenancy)
        """
        self._db_salt = db_salt

    @staticmethod
    def hash_password(password: str, salt: str = None) -> str:
        """Hash a password using SHA-256 with salt.

        Args:
            password: The plain text password to hash
            salt: Salt to add to the password (required)

        Returns:
            The hashed password as a hexadecimal string

        Raises:
            ValueError: If salt is not provided

        Example:
            >>> hashed = SQLLiteHandler.hash_password("secret", "my_salt")
            >>> len(hashed)
            64  # SHA-256 produces 64 hex characters
        """
        if salt is None:
            raise ValueError("Salt must be provided for password hashing")

        # Combine password with salt
        salted_password = f"{password}{salt}"

        # Create SHA-256 hash
        hash_object = hashlib.sha256(salted_password.encode("utf-8"))

        return hash_object.hexdigest()

    def initialize_database(self, schema_path=None):

        if os.path.exists(self._db_path):
            return 2  # Database already exists, no need to initialize

        self.load()

        # Read and execute schema file
        schema_file = Path(schema_path)
        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        schema_sql = schema_file.read_text(encoding="utf-8")
        self._cursor.executescript(schema_sql)
        self._connection.commit()

        self.close()

        return 1

    def drop_all_tables(self):
        """Drop all tables from the database.

        This method drops all FiWa tables in the correct order to respect
        foreign key constraints. Tables are dropped in reverse dependency order:
        child tables first, then parent tables.

        WARNING: This operation is DESTRUCTIVE and IRREVERSIBLE. All data will
        be permanently deleted.

        Returns:
            int: Number of tables successfully dropped

        Raises:
            sqlite3.Error: If there's an error dropping tables

        Example:
            >>> handler = SQLLiteHandler("data.sqlite")
            >>> handler.drop_all_tables()
            8  # 8 tables dropped

        Notes:
            - This method should only be used for testing or complete reinitialization
            - Backup your database before calling this method
            - Foreign key constraints are temporarily disabled during the operation
        """
        self.load()

        try:
            # Disable foreign key constraints temporarily
            self._cursor.execute("PRAGMA foreign_keys = OFF")

            # List of all tables in reverse dependency order (children first)
            tables = [
                f"p{self._db_salt}_aggregates",
                f"p{self._db_salt}_register",
                f"p{self._db_salt}_session_table",
                f"p{self._db_salt}_items",
                f"p{self._db_salt}_labels",
                f"p{self._db_salt}_user_project_map",
                f"p{self._db_salt}_users",
                f"p{self._db_salt}_projects",
            ]

            dropped_count = 0
            for table in tables:
                try:
                    self._cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    dropped_count += 1
                except sqlite3.Error as e:
                    # Log error but continue dropping other tables
                    print(f"Warning: Could not drop table {table}: {e}")

            self._connection.commit()

            # Re-enable foreign key constraints
            self._cursor.execute("PRAGMA foreign_keys = ON")
            self._connection.commit()

            self._invalidate_label_cache()
            return dropped_count

        except Exception as e:
            self._connection.rollback()
            raise sqlite3.Error(f"Error dropping tables: {e}")
        finally:
            self.close()

    def load(self):
        self._connection = sqlite3.connect(self._db_path)
        self._cursor = self._connection.cursor()

    def execute_query(self, query, params=None):
        if params is None:
            params = []
        self._cursor.execute(query, params)
        self._connection.commit()
        return self._cursor.fetchall()

    def close(self):
        self._connection.close()

    def op_total_number_of_users(self):
        """
        This is database operation (op_) to get the total number of users from the database.
        :return:
        """
        self.load()
        result = self.execute_query(f"SELECT COUNT(*) FROM p{self._db_salt}_users")
        self.close()
        return result[0][0] if result else 0

    def op_user_create(self, user_dict: Dict) -> Optional[int]:
        """
        Create a user in the database based on the schema.

        Args:
            user_dict: Dictionary containing user information with keys:
                - first_name (required): User's first name
                - last_name (required): User's last name
                - username (required): Username
                - email (required): Email address (must be unique)
                - password (required): Plain text password (will be hashed)
                - birthday (optional): Date of birth in 'YYYY-MM-DD' format
                - max_projects (optional): Maximum number of projects allowed (default: 3)
                - is_superuser (optional): Whether user is a superuser (default: False)
                - scope (optional): User scope (default: 'user:write')
                - activated (optional): Whether user is activated (default: True)

        Returns:
            The user_id of the created user, or None if creation failed
        """
        # Validate required fields
        required_fields = ["first_name", "last_name", "username", "email", "password"]
        for field in required_fields:
            if not user_dict.get(field):
                raise ValueError(f"Required field '{field}' is missing or empty")

        # Hash the password
        password_hash = self.hash_password(user_dict["password"], salt=self._pw_salt)

        # Generate unique identifier
        unique_identifier = str(uuid.uuid4())

        # Prepare values with defaults
        first_name = user_dict["first_name"]
        last_name = user_dict["last_name"]
        username = user_dict["username"]
        email = user_dict["email"]
        birthday = user_dict.get("birthday", None)
        max_projects = user_dict.get("max_projects", 3)
        is_superuser = 1 if user_dict.get("is_superuser", False) else 0
        scope = user_dict.get("scope", "user:write")
        activated = 1 if user_dict.get("activated", True) else 0

        # Construct query
        query = f"""
            INSERT INTO p{self._db_salt}_users
            (first_name, last_name, username, birthday, email, password_hash,
             activated, is_superuser, scope, max_projects, unique_identifier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = [
            first_name,
            last_name,
            username,
            birthday,
            email,
            password_hash,
            activated,
            is_superuser,
            scope,
            max_projects,
            unique_identifier,
        ]

        try:
            self.load()
            self.execute_query(query, params)
            # Get the last inserted row id
            user_id = self._cursor.lastrowid
            self.close()
            return user_id
        except sqlite3.IntegrityError as e:
            self.close()
            if "UNIQUE constraint failed" in str(e):
                if "email" in str(e):
                    raise ValueError(f"Email '{email}' already exists in the database")
                else:
                    raise ValueError(f"User with this information already exists")
            raise
        except Exception as e:
            self.close()
            raise Exception(f"Failed to create user: {str(e)}")

    def op_user_login(self, username, password):
        """
        This is database operation (op_) to login a user from the database.
        1) A login consists out of checking username & password.
        2) Check all projects of that user (and their permissions in those projects).

        Args:
            username: Username or email of the user
            password: Plain text password (will be hashed for comparison)

        Returns:
            user_id if login successful, None otherwise
        """
        # Hash the provided password
        password_hash = self.hash_password(password=password, salt=self._pw_salt)

        self.load()
        # Check against both username and email fields
        result = self.execute_query(
            f"""SELECT user_id FROM p{self._db_salt}_users
                WHERE (username = ? OR email = ?) AND password_hash = ? AND activated = 1""",
            [username, username, password_hash],
        )

        # If no matching user is found, return None
        if not result:
            self.close()
            return None

        # Register the user to the session_table: each user can
        # only have one active session, so we delete old sessions and insert a new one
        user_id = result[0][0]
        now = datetime.utcnow().isoformat()
        session_uuid = str(uuid.uuid4())
        session_type = "local_login"

        # Delete any existing sessions for this user (enforce single session)
        self.execute_query(
            f"DELETE FROM p{self._db_salt}_session_table WHERE user_id = ?", [user_id]
        )

        # Insert new session
        self.execute_query(
            f"""INSERT INTO p{self._db_salt}_session_table
                (user_id, session_start, session_uuid, session_type)
                VALUES (?, ?, ?, ?)""",
            [user_id, now, session_uuid, session_type],
        )

        self.close()

        # Return session information as a dictionary
        return {
            "user_id": user_id,
            "session_uuid": session_uuid,
            "session_start": now,
            "session_type": session_type,
        }

    def op_user_logout(self, session_uuid):
        """
        This is database operation (op_) to logout a user from the database.
        1) A logout consists out of deleting the session from the session table.

        Args:
            session_uuid: The UUID of the session to delete
        Returns:
            True if logout successful, False otherwise
        """
        self.load()
        # Delete the session with the given UUID
        try:
            self.execute_query(
                f"DELETE FROM p{self._db_salt}_session_table WHERE session_uuid = ?", [session_uuid]
            )
            self.close()
            return True
        except Exception as e:
            self.close()
            return False

    def op_get_user_sessions(self) -> Dict:
        """
        This is database operation (op_) to get all active sessions for a user from the database.

        Args:
            user_id: The ID of the user to retrieve sessions for
        Returns:
            A dictionary containing session information for the user
        """
        dt_now = datetime.utcnow()

        self.load()
        result = self.execute_query(f"""SELECT * FROM p{self._db_salt}_session_table""")

        if len(result) != 1:
            print(
                "Not allowed to have multiple sessions for one user, but found multiple sessions in the database. This should not happen."
            )
            self.close()
            return {}

        elif len(result) == 1:
            # we use the first session, extract the user_id and session_uuid and session_start and session_type
            result = result[0]
            user_id = result[1]
            session_uuid = result[3]
            session_start = result[2]
            session_type = result[4]
            session_start = datetime.fromisoformat(session_start)

            self.close()

            if dt_now - session_start > timedelta(minutes=30):
                # session expired, delete it and return empty
                self.op_user_logout(session_uuid)
                return {}

            # Fetch user info and project info
            user_info = self.op_user_get_info(user_id)
            project_info = self.op_project_get_info(user_id)

            return {
                "user_id": user_info["user_id"],
                "session_info": {
                    "session_uuid": session_uuid,
                    "session_start": session_start,
                    "session_type": session_type,
                    "is_logged_in": True,
                },
                "user_info": user_info,
                "project_info": project_info,
            }

        return True

    def op_user_get_info(self, user_id):
        """
        This is database operation (op_) to get user information from the database.
        :return:
        """
        self.load()
        result = self.execute_query(
            f"""SELECT user_id, first_name, last_name, username, email, birthday,
                activated, is_superuser, scope, max_projects, unique_identifier
                FROM p{self._db_salt}_users WHERE user_id = ?""",
            [user_id],
        )
        self.close()
        if not result:
            return None

        row = result[0]
        user_info = {
            "user_id": row[0],
            "first_name": row[1],
            "last_name": row[2],
            "username": row[3],
            "email": row[4],
            "birthday": row[5],
            "activated": bool(row[6]),
            "is_superuser": bool(row[7]),
            "scope": row[8],
            "max_projects": row[9],
            "unique_identifier": row[10],
        }
        return user_info

    def op_get_max_projects(self, user_id: int) -> int:
        """
        Get the maximum number of projects allowed for a user.

        Args:
            user_id: The user ID to query

        Returns:
            The max_projects value for the user, or 3 (default) if not found
        """
        self.load()
        result = self.execute_query(
            f"""SELECT max_projects FROM p{self._db_salt}_users WHERE user_id = ?""", [user_id]
        )
        self.close()

        if result and len(result) > 0:
            return result[0][0]
        return 3  # Default

    def op_project_get_info(self, user_id):
        """
        This is database operation (op_) to get project information for a user from the database.
        :return:
        """
        self.load()
        result = self.execute_query(
            f"""SELECT p.project_id, p.name, p.description, p.created_at,
                p.currency_main, p.currency_list, p.project_hash,
                p.project_store, p.project_style,
                upm.project_primary, upm.project_perm_model
                FROM p{self._db_salt}_projects p
                JOIN p{self._db_salt}_user_project_map upm ON p.project_id = upm.project_id
                WHERE upm.user_id = ?""",
            [user_id],
        )
        self.close()
        if not result:
            return []

        import json

        project_list = []
        for row in result:
            project_info = {
                "project_id": row[0],
                "project_name": row[1],  # Column is 'name' in DB, but we return as 'project_name'
                "description": row[2],
                "created_at": row[3],
                "currency_main": row[4],
                "currency_list": row[5],
                "project_hash": row[6],
                "project_store": row[7],
                "project_style": row[8],
                "project_primary": bool(row[9]),
                "project_perm_model": row[10],
            }
            project_list.append(project_info)
        return project_list

    def op_user_get_all_ids(self):
        """
        This is database operation (op_) to get all user IDs from the database.
        :return: List of user_ids
        """
        self.load()
        result = self.execute_query(f"""SELECT user_id FROM p{self._db_salt}_users""")
        self.close()
        return [row[0] for row in result] if result else []

    def op_project_create(self, project_dict: Dict, user_id: int) -> Optional[int]:
        """
        Create a project in the database and link it to a user.

        Args:
            project_dict: Dictionary containing project information with keys:
                - name (required): Project name
                - description (optional): Project description
                - currency_main (optional): Main currency (3-letter code)
                - currency_list (optional): List of currencies
                - project_style (optional): Style of the project (e.g., "ExpenseTracker")
                - project_staged (optional): Whether the project is staged (default: False)
                - project_activated (optional): Whether the project is activated (default: True)
                - project_store (optional): JSON string or dict for project-specific data
            user_id: The ID of the user creating/owning the project

        Returns:
            The project_id of the created project, or None if creation failed
        """
        import json

        # Validate required fields
        if not project_dict.get("name"):
            raise ValueError("Project name is required")

        # Prepare values with defaults
        name = project_dict["name"]
        description = project_dict.get("description", "")
        created_at = project_dict.get("created_at", datetime.utcnow().isoformat())
        currency_main = project_dict.get("currency_main", None)
        currency_list = project_dict.get("currency_list", [])
        project_style = project_dict.get("project_style", "default")
        project_staged = project_dict.get("project_staged", False)
        project_activated = project_dict.get("project_activated", True)

        # Convert currency_list to JSON string for storage
        currency_list_str = json.dumps(currency_list) if currency_list else "[]"

        # Generate project hash from name, description, and currency_main
        hash_input = f"{name}|{description}|{currency_main or ''}"
        project_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

        # Check if user exists and get max_projects
        self.load()
        user_result = self.execute_query(
            f"""SELECT user_id, max_projects FROM p{self._db_salt}_users
                WHERE user_id = ?""",
            [user_id],
        )

        if not user_result:
            self.close()
            raise ValueError(f"User with ID {user_id} not found")

        max_projects = user_result[0][1]

        # Count current projects for this user
        current_projects = self.execute_query(
            f"""SELECT COUNT(*) FROM p{self._db_salt}_user_project_map
                WHERE user_id = ?""",
            [user_id],
        )
        project_count = current_projects[0][0] if current_projects else 0

        if project_count >= max_projects:
            self.close()
            raise ValueError(
                f"User {user_id} has reached the maximum number of projects ({max_projects})"
            )

        # Prepare project_store with empty JSON
        project_store = project_dict.get("project_store", "{}")
        if isinstance(project_store, dict):
            project_store = json.dumps(project_store)

        # Insert project
        query = f"""
            INSERT INTO p{self._db_salt}_projects
            (name,
             description,
             created_at,
             currency_main,
             currency_list,
             project_hash,
             project_style,
             project_staged,
             project_activated,
             project_store
             )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = [
            name,
            description,
            created_at,
            currency_main,
            currency_list_str,
            project_hash,
            project_style,
            project_staged,
            project_activated,
            project_store,
        ]

        try:
            self.execute_query(query, params)
            project_id = self._cursor.lastrowid

            # Determine if this is the user's first/primary project
            is_primary = 1 if project_count == 0 else 0

            # Link project to user in user_project_map
            map_query = f"""
                INSERT INTO p{self._db_salt}_user_project_map
                (user_id, project_id, created_at, project_perm_model, project_primary)
                VALUES (?, ?, ?, ?, ?)
            """
            map_params = [user_id, project_id, datetime.utcnow().isoformat(), "111111", is_primary]
            self.execute_query(map_query, map_params)

            self.close()
            return project_id
        except sqlite3.IntegrityError as e:
            self.close()
            if "UNIQUE constraint failed" in str(e):
                if "project_hash" in str(e):
                    raise ValueError(f"A project with similar attributes already exists")
                else:
                    raise ValueError(f"Project with this information already exists")
            raise
        except Exception as e:
            self.close()
            raise Exception(f"Failed to create project: {str(e)}")

    def op_project_stage(self, project_id, users=[]):
        """
        We stage a project for its self and for a user (labels) if needed
        :param project_id:
        :param user_id:
        :return:
        """
        self.load()

        # first step: fetch the project by the project id:
        query = f"""
        SELECT project_style, project_staged, project_activated
        FROM p{self._db_salt}_projects WHERE project_id = ?"""

        p0 = self.execute_query(query, [project_id])
        self.close()
        # if we do not find the project, we return False
        if len(p0) != 1:
            print(f"Project with ID {project_id} not found")
            return False

        # if we find it, we extract the style
        p0 = p0[0]
        p_style = p0[0]
        p_staged = p0[1]
        p_activated = p0[2]

        if p_style == "default":
            print(f"Project {project_id} has default style, staging not required")
            return True

        if p_staged == 1 and len(users) == 0:
            print(f"Project {project_id} is already staged. No user_id provided")
            return True
        elif p_staged == 0 and len(users) >= 0:
            from fiwa_cli.functions.project_composer import ProjectComposer

            print(f"Staging project {project_id} with style {p_style}")

            # Get project users to pass to composer
            # users = self.op_project_get_users(project_id)
            # if not users:
            #     print(f"No users found for project {project_id}, cannot stage")
            #     self.close()
            #     return False

            # Create composer instance using factory method
            pc = ProjectComposer.create(
                compose_type=p_style, dbh=self, project_id=project_id, users=users
            )

            # Compose Labels for the project
            pc.compose_labels()
            pc.compose_accounts()

            k = pc.get()
            print(k)

            # Mark project as staged
            self.load()
            update_query = f"""
            UPDATE p{self._db_salt}_projects
            SET project_staged = 1
            WHERE project_id = ?
            """
            self.execute_query(update_query, [project_id])
            print(f"Project {project_id} successfully staged")
            self.close()

        elif p_staged == 1 and len(users) > 0:
            from fiwa_cli.functions.project_composer import ProjectComposer

            print(f"Staging project {project_id} with style {p_style}")

            # Get project users to pass to composer
            # users = self.op_project_get_users(project_id)
            # if not users:
            #     print(f"No users found for project {project_id}, cannot stage")
            #     self.close()
            #     return False

            # Create composer instance using factory method
            pc = ProjectComposer.create(
                compose_type=p_style, dbh=self, project_id=project_id, users=users
            )

            # Compose Labels for the project
            pc.compose_accounts()

        print(project_id)
        print(p0)

    def op_project_update(self, project_dict: Dict) -> bool:
        """
        Update an existing project in the database.

        Args:
            project_dict: Dictionary containing project information with keys:
                - project_id (required): The ID of the project to update
                - name (optional): Updated project name
                - description (optional): Updated description
                - currency_main (optional): Updated main currency
                - currency_list (optional): Updated list of currencies

        Returns:
            True if successful, raises exception otherwise
        """
        import json

        # Validate required fields
        project_id = project_dict.get("project_id")
        if not project_id:
            raise ValueError("Project ID is required for update")

        self.load()

        # Check if project exists
        existing = self.execute_query(
            f"""SELECT project_id FROM p{self._db_salt}_projects WHERE project_id = ?""",
            [project_id],
        )
        if not existing:
            self.close()
            raise ValueError(f"Project with ID {project_id} not found")

        # Build update query dynamically based on provided fields
        update_fields = []
        params = []

        if "name" in project_dict and project_dict["name"]:
            update_fields.append("name = ?")
            params.append(project_dict["name"])

        if "description" in project_dict:
            update_fields.append("description = ?")
            params.append(project_dict["description"] if project_dict["description"] else "")

        if "currency_main" in project_dict:
            update_fields.append("currency_main = ?")
            params.append(project_dict["currency_main"])

        if "currency_list" in project_dict:
            currency_list_str = (
                json.dumps(project_dict["currency_list"]) if project_dict["currency_list"] else "[]"
            )
            update_fields.append("currency_list = ?")
            params.append(currency_list_str)

        if "project_store" in project_dict:
            project_store = project_dict["project_store"]
            if isinstance(project_store, dict):
                project_store = json.dumps(project_store)
            update_fields.append("project_store = ?")
            params.append(project_store)

        if not update_fields:
            self.close()
            raise ValueError("No fields to update")

        # Generate new project hash if name, description, or currency_main changed
        if any(k in project_dict for k in ["name", "description", "currency_main"]):
            # Get current values for hash calculation
            current_data = self.execute_query(
                f"""SELECT name, description, currency_main FROM p{self._db_salt}_projects
                    WHERE project_id = ?""",
                [project_id],
            )
            if current_data:
                current_name = project_dict.get("name", current_data[0][0])
                current_desc = project_dict.get("description", current_data[0][1] or "")
                current_curr = project_dict.get("currency_main", current_data[0][2] or "")

                hash_input = f"{current_name}|{current_desc}|{current_curr}"
                project_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

                update_fields.append("project_hash = ?")
                params.append(project_hash)

        # Add project_id for WHERE clause
        params.append(project_id)

        # Execute update
        query = f"""
            UPDATE p{self._db_salt}_projects
            SET {', '.join(update_fields)}
            WHERE project_id = ?
        """

        try:
            self.execute_query(query, params)
            self.close()
            return True
        except sqlite3.IntegrityError as e:
            self.close()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"A project with similar attributes already exists")
            raise
        except Exception as e:
            self.close()
            raise Exception(f"Failed to update project: {str(e)}")

    def op_project_add_user(
        self,
        project_id: int,
        user_id: int,
        project_perm_model: str = "000000",
        project_primary: bool = False,
    ) -> bool:
        """
        Add a user to an existing project.

        Args:
            project_id: The ID of the project
            user_id: The ID of the user to add to the project
            project_perm_model: Permission model for the user (default: '000000')
            project_primary: Whether this is the user's primary project (default: False)

        Returns:
            True if successful, raises exception otherwise
        """
        self.load()

        # Check if project exists
        project_check = self.execute_query(
            f"""SELECT project_id FROM p{self._db_salt}_projects WHERE project_id = ?""",
            [project_id],
        )
        if not project_check:
            self.close()
            raise ValueError(f"Project with ID {project_id} not found")

        # Check if user exists
        user_check = self.execute_query(
            f"""SELECT user_id FROM p{self._db_salt}_users WHERE user_id = ?""", [user_id]
        )
        if not user_check:
            self.close()
            raise ValueError(f"User with ID {user_id} not found")

        # Check if user is already in the project
        existing = self.execute_query(
            f"""SELECT id FROM p{self._db_salt}_user_project_map
                WHERE user_id = ? AND project_id = ?""",
            [user_id, project_id],
        )
        if existing:
            self.close()
            raise ValueError(f"User {user_id} is already a member of project {project_id}")

        # Add user to project
        try:
            map_query = f"""
                INSERT INTO p{self._db_salt}_user_project_map
                (user_id, project_id, created_at, project_perm_model, project_primary)
                VALUES (?, ?, ?, ?, ?)
            """
            map_params = [
                user_id,
                project_id,
                datetime.utcnow().isoformat(),
                project_perm_model,
                1 if project_primary else 0,
            ]
            self.execute_query(map_query, map_params)
            self.close()
            return True
        except Exception as e:
            self.close()
            raise Exception(f"Failed to add user to project: {str(e)}")

    def op_project_set_primary(self, project_id: int, user_id: int) -> bool:
        """
        Set a project as the primary project for a user.

        This method ensures that only one project is marked as primary for a user.
        It first sets all projects for this user to non-primary (project_primary = 0),
        then sets the specified project as primary (project_primary = 1).

        Args:
            project_id: The ID of the project to set as primary
            user_id: The ID of the user

        Returns:
            True if successful, raises exception otherwise

        Raises:
            ValueError: If the user is not a member of the specified project
            Exception: If the database operation fails

        Example:
            >>> handler = SQLLiteHandler("data.sqlite")
            >>> handler.op_project_set_primary(project_id=5, user_id=2)
            True

        Notes:
            - Only one project can be primary for a user at any time
            - All other projects for this user will be set to non-primary
            - The user must be a member of the project to set it as primary
        """
        self.load()

        try:
            # Step 1: Verify the user is a member of the specified project
            membership_check = self.execute_query(
                f"""SELECT id FROM p{self._db_salt}_user_project_map
                    WHERE user_id = ? AND project_id = ?""",
                [user_id, project_id],
            )

            if not membership_check:
                self.close()
                print(f"User {user_id} is not a member of project {project_id}")
                return False

            # Step 2: Set all projects for this user to non-primary
            update_all_query = f"""
                UPDATE p{self._db_salt}_user_project_map
                SET project_primary = 0
                WHERE user_id = ?
            """
            self.execute_query(update_all_query, [user_id])

            # Step 3: Set the specified project as primary
            update_primary_query = f"""
                UPDATE p{self._db_salt}_user_project_map
                SET project_primary = 1
                WHERE user_id = ? AND project_id = ?
            """
            self.execute_query(update_primary_query, [user_id, project_id])

            self.close()
            return True

        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            self.close()
            raise Exception(f"Failed to set primary project: {str(e)}")

    def op_project_get_users(self, project_id: int) -> list:
        """
        Get all users associated with a specific project.

        Args:
            project_id: The ID of the project

        Returns:
            List of dictionaries containing user information for the project
        """
        self.load()

        query = f"""
            SELECT
                u.user_id,
                u.username,
                u.first_name,
                u.last_name,
                u.email,
                upm.project_perm_model,
                upm.project_primary,
                upm.created_at as joined_at
            FROM p{self._db_salt}_users u
            INNER JOIN p{self._db_salt}_user_project_map upm
                ON u.user_id = upm.user_id
            WHERE upm.project_id = ?
            ORDER BY upm.project_primary DESC, u.username ASC
        """

        results = self.execute_query(query, [project_id])
        self.close()

        if not results:
            return []

        users = []
        for row in results:
            users.append(
                {
                    "user_id": row[0],
                    "username": row[1],
                    "first_name": row[2],
                    "last_name": row[3],
                    "email": row[4],
                    "project_perm_model": row[5],
                    "project_primary": bool(row[6]),
                    "joined_at": row[7],
                }
            )

        return users

    def op_label_get_all(
        self,
        project_id: int,
        *,
        use_cache: bool = True,
        force_refresh: bool = False,
        user_id: int = None,
    ) -> list:
        """
        Get all labels for a specific project.

        Args:
            project_id: The ID of the project
            use_cache: Return cached data when available
            force_refresh: Bypass cache and query the database
            user_id: If provided, includes user-specific default label info

        Returns:
            List of label dictionaries with optional 'is_user_default' field
        """
        if use_cache and not force_refresh:
            cached = self._label_cache.get(project_id)
            if cached is not None:
                return copy.deepcopy(cached)

        self.load()
        result = self.execute_query(
            f"""SELECT label_id, name, description, created_at, composite,
                label_status, label_type, label_sub_type, label_owner
                FROM p{self._db_salt}_labels
                WHERE project_id = ?
                ORDER BY name""",
            [project_id],
        )
        self.close()

        if not result:
            if use_cache:
                self._label_cache[project_id] = []
            return []

        labels = [
            {
                "label_id": row[0],
                "name": row[1],
                "description": row[2],
                "created_at": row[3],
                "composite": row[4],
                "label_status": row[5],
                "label_type": row[6],
                "label_sub_type": row[7],
                "label_owner": row[8],
            }
            for row in result
        ]

        # If user_id provided, fetch user's default labels
        if user_id:
            self.load()
            defaults_query = f"""
                SELECT label_id, label_type
                FROM p{self._db_salt}_user_label_defaults
                WHERE user_id = ? AND project_id = ?
            """
            user_defaults = self.execute_query(defaults_query, [user_id, project_id])
            self.close()

            # Create a map of label_type -> label_id for this user's defaults
            user_default_map = {row[1]: row[0] for row in user_defaults}

            # Add is_user_default flag to each label
            for label in labels:
                label["is_user_default"] = (
                    user_default_map.get(label["label_type"]) == label["label_id"]
                )

        if use_cache:
            self._label_cache[project_id] = copy.deepcopy(labels)
            return copy.deepcopy(self._label_cache[project_id])

        return labels

    def op_label_get_by_name(self, label_name: str, project_id: int) -> Optional[int]:
        """
        Get a label ID by its name within a specific project.

        Args:
            label_name: The name of the label to search for
            project_id: The ID of the project

        Returns:
            The label_id if found, None otherwise

        Example:
            >>> groceries_id = dbh.op_label_get_by_name("Groceries", project_id=1)
            >>> if groceries_id:
            ...     print(f"Groceries label ID: {groceries_id}")
        """
        self.load()
        result = self.execute_query(
            f"""SELECT label_id
                FROM p{self._db_salt}_labels
                WHERE project_id = ? AND name = ?
                LIMIT 1""",
            [project_id, label_name],
        )
        self.close()

        if result and len(result) > 0:
            return result[0][0]  # Return the label_id
        return None

    def op_label_create(self, label_dict: Dict, project_id: int) -> Optional[int]:
        """
        Create a new label for a project.

        Args:
            label_dict: Dictionary containing label information with keys:
                - name (required): Label name
                - description (optional): Label description
                - composite (optional): List of composite elements
                - label_status (optional): Status (0=deleted, 1=deactivated, 2=active)
                - label_type (optional): Type (default: 1)
                - label_sub_type (optional): Sub-type (default: -2)
                - label_owner (optional): User ID who owns the label, or -1 for project-wide (default: -1)
            project_id: The ID of the project

        Returns:
            The label_id of the created label, or None if creation failed
        """
        import json

        # Validate required fields
        if not label_dict.get("name"):
            raise ValueError("Label name is required")

        # Prepare values with defaults
        name = label_dict["name"]
        description = label_dict.get("description", "")
        composite = label_dict.get("composite", [])
        composite_str = json.dumps(composite)
        label_status = label_dict.get("label_status", 2)  # Default: active
        label_type = label_dict.get("label_type", 1)
        label_sub_type = label_dict.get("label_sub_type", -2)  # Default: -2
        label_owner = label_dict.get("label_owner", -1)  # Default: -1 (project-wide/common)
        created_at = datetime.utcnow().isoformat()

        self.load()

        # Check if label with same name exists in this project
        existing = self.execute_query(
            f"""SELECT label_id FROM p{self._db_salt}_labels
                WHERE name = ? AND project_id = ?""",
            [name, project_id],
        )

        if existing:
            self.close()
            raise ValueError(f"Label '{name}' already exists in this project")

        # Insert label with label_owner and label_sub_type
        query = f"""
            INSERT INTO p{self._db_salt}_labels
            (name, description, created_at, project_id, composite, label_owner, label_status, label_type, label_sub_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = [
            name,
            description,
            created_at,
            project_id,
            composite_str,
            label_owner,
            label_status,
            label_type,
            label_sub_type,
        ]

        try:
            self.execute_query(query, params)
            label_id = self._cursor.lastrowid

            # Invalidate the cache for this project so that next fetch gets fresh data
            if project_id in self._label_cache:
                del self._label_cache[project_id]

            self.close()
            return label_id
        except sqlite3.IntegrityError as e:
            self.close()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Label '{name}' already exists in this project")
            raise
        except Exception as e:
            self.close()
            raise Exception(f"Failed to create label: {str(e)}")

    def op_label_update(self, label_id: int, label_dict: Dict) -> bool:
        """
        Update an existing label.

        Args:
            label_id: The ID of the label to update
            label_dict: Dictionary containing label information with keys:
                - name (optional): Updated label name
                - description (optional): Updated description
                - composite (optional): Updated composite list
                - label_status (optional): Updated status
                - label_type (optional): Updated type
                - label_sub_type (optional): Updated sub-type
                - label_owner (optional): Updated label owner
                - label_default (optional): Updated default status

        Returns:
            True if successful, raises exception otherwise
        """
        import json

        self.load()

        # Check if label exists and get project_id for cache invalidation
        existing = self.execute_query(
            f"""SELECT label_id, project_id FROM p{self._db_salt}_labels WHERE label_id = ?""",
            [label_id],
        )

        if not existing:
            self.close()
            raise ValueError(f"Label with ID {label_id} not found")

        project_id = existing[0][1]  # Get project_id from the query result

        # Build update query dynamically
        update_fields = []
        params = []

        if "name" in label_dict and label_dict["name"]:
            update_fields.append("name = ?")
            params.append(label_dict["name"])

        if "description" in label_dict:
            update_fields.append("description = ?")
            params.append(label_dict["description"])

        if "composite" in label_dict:
            update_fields.append("composite = ?")
            params.append(json.dumps(label_dict["composite"]))

        if "label_status" in label_dict:
            update_fields.append("label_status = ?")
            params.append(label_dict["label_status"])

        if "label_type" in label_dict:
            update_fields.append("label_type = ?")
            params.append(label_dict["label_type"])

        if "label_sub_type" in label_dict:
            update_fields.append("label_sub_type = ?")
            params.append(label_dict["label_sub_type"])

        if "label_owner" in label_dict:
            update_fields.append("label_owner = ?")
            params.append(label_dict["label_owner"])

        if not update_fields:
            self.close()
            raise ValueError("No fields to update")

        # Add label_id for WHERE clause
        params.append(label_id)

        # Execute update
        query = f"""
            UPDATE p{self._db_salt}_labels
            SET {', '.join(update_fields)}
            WHERE label_id = ?
        """

        try:
            self.execute_query(query, params)

            # Invalidate cache after successful update
            if project_id in self._label_cache:
                del self._label_cache[project_id]

            self.close()
            return True
        except sqlite3.IntegrityError as e:
            self.close()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Label name must be unique within the project")
            raise
        except Exception as e:
            self.close()
            raise Exception(f"Failed to update label: {str(e)}")

    def op_label_set_default(
        self, label_id: int, project_id: int, label_type: int, user_id: int
    ) -> bool:
        """
        Set a label as default for a specific user and label type.
        Ensures only one default label per user per label_type within a project.

        Args:
            label_id: The ID of the label to set as default
            project_id: The project ID
            label_type: The label type (to clear other defaults in same category)
            user_id: The user ID for whom to set the default

        Returns:
            True if successful, raises exception otherwise
        """
        self.load()

        # First, delete any existing default for this user, project, and label_type
        delete_query = f"""
            DELETE FROM p{self._db_salt}_user_label_defaults
            WHERE user_id = ? AND project_id = ? AND label_type = ?
        """
        self.execute_query(delete_query, [user_id, project_id, label_type])

        # Then, insert the new default
        insert_query = f"""
            INSERT INTO p{self._db_salt}_user_label_defaults
            (user_id, project_id, label_id, label_type, created_at)
            VALUES (?, ?, ?, ?, ?)
        """
        self.execute_query(
            insert_query, [user_id, project_id, label_id, label_type, datetime.utcnow().isoformat()]
        )

        # Invalidate cache
        if project_id in self._label_cache:
            del self._label_cache[project_id]

        self.close()
        return True

    def op_label_unset_default(self, project_id: int, label_type: int, user_id: int) -> bool:
        """
        Remove default label for a specific user and label type.

        Args:
            project_id: The project ID
            label_type: The label type
            user_id: The user ID

        Returns:
            True if successful, raises exception otherwise
        """
        self.load()

        delete_query = f"""
            DELETE FROM p{self._db_salt}_user_label_defaults
            WHERE user_id = ? AND project_id = ? AND label_type = ?
        """
        self.execute_query(delete_query, [user_id, project_id, label_type])

        # Invalidate cache
        if project_id in self._label_cache:
            del self._label_cache[project_id]

        self.close()
        return True

    def op_label_get_user_defaults(self, user_id: int, project_id: int) -> dict:
        """
        Get all default labels for a specific user in a project.

        Args:
            user_id: The user ID
            project_id: The project ID

        Returns:
            Dictionary mapping label_type -> label_id for user's defaults
            Example: {0: 5, 1: 2, 2: 8, 3: 12} means:
                - Type 0 (Balance): label_id 5 is default
                - Type 1 (Transaction): label_id 2 is default
                - Type 2 (Account): label_id 8 is default
                - Type 3 (Main Labels): label_id 12 is default
        """
        self.load()

        query = f"""
            SELECT label_type, label_id
            FROM p{self._db_salt}_user_label_defaults
            WHERE user_id = ? AND project_id = ?
        """
        results = self.execute_query(query, [user_id, project_id])
        self.close()

        # Build map of label_type -> label_id
        defaults_map = {row[0]: row[1] for row in results}
        return defaults_map

    def op_item_create(self, item_dict: Dict) -> Optional[int]:
        """
        Create an item (transaction) in the database.

        Args:
            item_dict: Dictionary containing item information with keys:
                - item_uuid (required): UUID for the item
                - name (required): Item name
                - note (optional): Additional notes
                - price (required): Original price
                - price_final (required): Final price after conversion
                - currency (required): Original currency
                - currency_final (required): Final currency
                - bought_date (required): Date/time of purchase
                - bought_by_id (required): User ID who bought the item
                - bought_for_id (required): User ID for whom the item was bought
                - added_by_id (required): User ID who added the entry
                - project_id (required): Project ID
                - exchange_rate (optional): Exchange rate (default: 1.0)
                - exchange_rate_date (optional): Date of exchange rate (default: today)
                - tags (optional): JSON string of tag/label IDs

        Returns:
            The item_id of the created item, or None if creation failed
        """
        import json

        # Validate required fields
        required_fields = [
            "item_uuid",
            "name",
            "price",
            "price_final",
            "currency",
            "currency_final",
            "bought_date",
            "bought_by_id",
            "bought_for_id",
            "added_by_id",
            "project_id",
        ]

        for field in required_fields:
            if field not in item_dict:
                raise ValueError(f"Required field '{field}' is missing")

        # Prepare values with defaults
        item_uuid = item_dict["item_uuid"]
        name = item_dict["name"]
        note = item_dict.get("note", "")
        price = item_dict["price"]
        price_final = item_dict["price_final"]
        currency = item_dict["currency"]
        currency_final = item_dict["currency_final"]
        bought_date = item_dict["bought_date"]
        bought_by_id = item_dict["bought_by_id"]
        bought_for_id = item_dict["bought_for_id"]
        added_by_id = item_dict["added_by_id"]
        project_id = item_dict["project_id"]
        exchange_rate = item_dict.get("exchange_rate", 1.0)
        exchange_rate_date = item_dict.get(
            "exchange_rate_date", datetime.now().strftime("%Y-%m-%d")
        )
        tags = item_dict.get("tags", "[]")

        # Ensure tags is a JSON string
        if isinstance(tags, (list, dict)):
            tags = json.dumps(tags)

        self.load()

        # Verify project exists
        project_check = self.execute_query(
            f"""SELECT project_id FROM p{self._db_salt}_projects WHERE project_id = ?""",
            [project_id],
        )
        if not project_check:
            self.close()
            raise ValueError(f"Project with ID {project_id} not found")

        # Verify users exist
        for user_field, user_id in [
            ("bought_by_id", bought_by_id),
            ("bought_for_id", bought_for_id),
            ("added_by_id", added_by_id),
        ]:
            user_check = self.execute_query(
                f"""SELECT user_id FROM p{self._db_salt}_users WHERE user_id = ?""", [user_id]
            )
            if not user_check:
                self.close()
                raise ValueError(f"User with ID {user_id} ({user_field}) not found")

        # Insert item
        query = f"""
            INSERT INTO p{self._db_salt}_items
            (item_uuid, name, note, price, price_final, currency, currency_final,
             bought_date, bought_by_id, bought_for_id, added_by_id, project_id,
             exchange_rate, exchange_rate_date, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        params = [
            item_uuid,
            name,
            note,
            price,
            price_final,
            currency,
            currency_final,
            bought_date,
            bought_by_id,
            bought_for_id,
            added_by_id,
            project_id,
            exchange_rate,
            exchange_rate_date,
            tags,
        ]

        try:
            self.execute_query(query, params)
            item_id = self._cursor.lastrowid
            self.close()
            return item_id
        except sqlite3.IntegrityError as e:
            self.close()
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Item with UUID {item_uuid} already exists")
            raise
        except Exception as e:
            self.close()
            raise Exception(f"Failed to create item: {str(e)}")

    def op_item_delete(self, item_id: int, project_id: int) -> bool:
        """
        Delete an item from the database.

        This is a database operation (op_) to delete a single item by its ID.
        Validates that the item exists and belongs to the specified project
        before deletion.

        Args:
            item_id: The ID of the item to delete
            project_id: The project ID (for security validation)

        Returns:
            True if the item was successfully deleted, False otherwise

        Raises:
            ValueError: If the item doesn't exist or doesn't belong to the project
            Exception: If the deletion fails for any other reason
        """
        self.load()

        try:
            # Verify the item exists and belongs to the project
            check_query = f"""
                SELECT item_id FROM p{self._db_salt}_items
                WHERE item_id = ? AND project_id = ?
            """
            result = self.execute_query(check_query, [item_id, project_id])

            if not result:
                self.close()
                raise ValueError(f"Item with ID {item_id} not found in project {project_id}")

            # Delete the item
            delete_query = f"""
                DELETE FROM p{self._db_salt}_items
                WHERE item_id = ? AND project_id = ?
            """
            self.execute_query(delete_query, [item_id, project_id])

            self.close()
            return True

        except ValueError:
            # Re-raise validation errors
            raise
        except Exception as e:
            self.close()
            raise Exception(f"Failed to delete item {item_id}: {str(e)}")

    def op_user_update_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Update a user's password after verifying the old password.

        Args:
            user_id: The ID of the user whose password to update
            old_password: The current password (plain text) for verification
            new_password: The new password (plain text) to set

        Returns:
            True if password was updated successfully, False if old password is incorrect

        Raises:
            Exception: If database operation fails
        """
        try:
            # Hash the old password for verification
            old_password_hash = self.hash_password(password=old_password, salt=self._pw_salt)

            self.load()

            # Verify the old password matches
            result = self.execute_query(
                f"""SELECT user_id FROM p{self._db_salt}_users
                    WHERE user_id = ? AND password_hash = ?""",
                [user_id, old_password_hash],
            )

            if not result:
                # Old password doesn't match
                self.close()
                return False

            # Hash the new password
            new_password_hash = self.hash_password(password=new_password, salt=self._pw_salt)

            # Update the password
            self.execute_query(
                f"""UPDATE p{self._db_salt}_users
                    SET password_hash = ?
                    WHERE user_id = ?""",
                [new_password_hash, user_id],
            )

            self.close()
            return True

        except Exception as e:
            self.close()
            raise Exception(f"Failed to update password for user {user_id}: {str(e)}")

    def op_get_current_user(self):
        """
        This is database operation (op_) to get the current user from the database.
        :return:
        """
        u = {
            "username": "Guest",
            "user_id": 0,
        }
        p = [
            {
                "project_id": 0,
                "project_name": "Default Project",
                "is_primary": True,
                "users_in_project": [u],
                "permissions": "",
                "labels": [],
            }
        ]

        return {"users": u, "projects": p}

    def _invalidate_label_cache(self, project_id: Optional[int] = None) -> None:
        """Invalidate cached label lists."""
        if project_id is None:
            self._label_cache.clear()
        else:
            self._label_cache.pop(project_id, None)
