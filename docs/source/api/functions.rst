Functions Module
================

Business logic, utilities, and database operations for FiWa CLI.

Overview
--------

.. automodule:: fiwa_cli.functions
   :members:
   :undoc-members:
   :show-inheritance:

The functions package contains all core business logic and utilities:

* **Database operations**: SQLite CRUD operations
* **Configuration management**: YAML config loading
* **Resource loading**: CSS and asset loading
* **Authentication**: Login/logout logic
* **Project composition**: Type-specific project logic
* **Data generation**: Test data and faker utilities

Module Organization
-------------------

Functions are organized by responsibility:

* **handler_sqllite.py**: Database operations (100+ op_* methods)
* **loader.py**: Configuration, CSS, and setup utilities
* **logout_util.py**: Shared logout functionality
* **project_composer.py**: Project-type-specific logic
* **db_faker.py**: Test data generation
* **faker_superhero_project.py**: Sample project creation
* **handler_api.py**: Future API handler (not implemented)
* **handler.py**: Handler factory/selector

Loader Module
-------------

.. automodule:: fiwa_cli.functions.loader
   :members:
   :undoc-members:
   :show-inheritance:

Configuration, resource, and initialization utilities.

Key Functions:
    **load_dynamic_css(widget, css_filename)**:
        - Loads theme-specific CSS for widgets
        - Called from widget.on_mount()
        - Resolves path based on app_state css_form
        - Gracefully handles missing files

    **handle_args()**:
        - Parses command-line arguments
        - Returns (mode, config) tuple
        - Supports 'init' and 'run' modes
        - Handles --path, --user, --password args

    **get_abs_path()**:
        - Returns package installation directory
        - Used for finding CSS and config files
        - Works in both dev and installed modes

    **load_yaml_config(config_path)**:
        - Parses YAML configuration files
        - Returns config dictionary
        - Handles parsing errors gracefully

    **identify_os(os_folder)**:
        - Detects operating system
        - Returns (os_type, config_dir)
        - Determines config file locations

    **prep_fiwa(mode, config)**:
        - Initializes FiWa data directory
        - Creates config files
        - Sets up directory structure
        - Used in 'init' mode

    **setup_fiwa(abs_path, config)**:
        - Sets up application for 'run' mode
        - Loads configuration
        - Initializes database
        - Creates sample data if needed
        - Returns complete config dict

Example::

    # Application initialization
    from fiwa_cli.functions.loader import handle_args, setup_fiwa, get_abs_path

    mode, config = handle_args()
    abs_path = get_abs_path()

    if mode == "run":
        full_config = setup_fiwa(abs_path=abs_path, config=config)

Logout Utility
--------------

.. automodule:: fiwa_cli.functions.logout_util
   :members:
   :undoc-members:
   :show-inheritance:

Centralized logout functionality shared across the application.

Key Functions:
    **perform_logout(app)**:
        - Clears user session in database
        - Resets app_state to defaults
        - Preserves app-level config (abs_path, css_form, css_theme)
        - Returns to main screen
        - Returns True on success

    **return_to_main_screen(app)**:
        - Pops all screens except base screen
        - Cleans up screen stack
        - Called after logout completes

Usage::

    from fiwa_cli.functions.logout_util import perform_logout

    # From menu, settings, or anywhere
    success = perform_logout(self.app)
    if success:
        # User logged out

Benefits:
    - Single source of truth for logout logic
    - Consistent behavior across app
    - No code duplication
    - Easier testing and maintenance

Time Computation Utilities
---------------------------

.. automodule:: fiwa_cli.functions.compute_time
   :members:
   :undoc-members:
   :show-inheritance:

Date, week, month, and holiday calculations with internationalization.

The TimeClass provides comprehensive date calculations with support for
multiple countries and languages using the Babel library for localization.

Features:
    - Day calculations with localized names
    - ISO week numbers and boundaries
    - Custom month periods (for accounting)
    - Year boundaries
    - Holiday detection with translations
    - Multi-language support

Example::

    from fiwa_cli.functions.compute_time import TimeClass
    import datetime

    # German locale
    tc = TimeClass(day=datetime.date(2024, 12, 25), country_code="DE")
    result = tc.get_day()

    print(result['day_name'])      # 'Mittwoch'
    print(result['month_name'])    # 'Dezember'
    print(result['holiday_name'])  # 'Weihnachten'

Custom Periods::

    # Financial period: 15th to 14th
    tc = TimeClass()
    period = tc.cmp_month_by_number(2026, 3, month_start_day=15)
    # Returns: 2026-03-15 to 2026-04-14

Project Composer
----------------

.. automodule:: fiwa_cli.functions.project_composer
   :members:
   :undoc-members:
   :show-inheritance:

Project-type-specific business logic and label composition.

Key Classes:
    **ProjectComposer** (Abstract):
        - Base class for all project types
        - Defines composer interface
        - Factory method for instantiation
        - COMPOSERS registry

    **ProjectExpenseTracker**:
        - Expense tracking project implementation
        - Label types: Count, Transaction, Account, Main, Secondary
        - Transaction types: Fixed, Variable, Daily, Revenue
        - Account types: Checking, Savings, Credit, Cash, Liability
        - Tag parsing and formatting

    **ProjectVacation**:
        - Vacation planning project (future)
        - Travel-specific categories

Factory Pattern::

    from fiwa_cli.functions.project_composer import ProjectComposer

    # Create composer for project type
    pc = ProjectComposer.create(
        compose_type="ExpenseTracker",
        dbh=database_handler,
        project_id=1,
        users=project_users
    )

    # Use composer methods
    pc.build()  # Create labels
    label_map = pc.get_label_map()  # Get type mappings

    # Parse tag strings
    tag_dict = pc.parse_tag_string("1_2_5_8_[12,15]")
    tag_string = pc.format_tag_string(tag_dict)

Label Structure (ExpenseTracker):
    **Type 0 - Count**:
        - Balance tracking labels

    **Type 1 - Transaction**:
        - Sub 0: Fixed (recurring expenses)
        - Sub 1: Variable (irregular expenses)
        - Sub 2: Daily (frequent small purchases)
        - Sub 3: Revenue (income)

    **Type 2 - Account**:
        - Sub 0: Liability (shared costs)
        - Sub 1: Checking
        - Sub 2: Savings
        - Sub 3: Credit
        - Sub 4: Cash

    **Type 3 - Main**:
        - Primary categories (Groceries, Rent, Travel, etc.)

    **Type 4 - Secondary**:
        - Additional tags for fine-grained categorization

Tag String Format:
    Compact database storage format::

        "count_transaction_account_main_[sec1,sec2,...]"

        Example: "1_2_5_8_[12,15,18]"
        Means:
            - Count label ID: 1
            - Transaction label ID: 2
            - Account label ID: 5
            - Main label ID: 8
            - Secondary label IDs: [12, 15, 18]

Database Handler
----------------

.. automodule:: fiwa_cli.functions.handler_sqllite
   :members:
   :undoc-members:
   :show-inheritance:

SQLite database operations and query management.

**Note**: Due to the large size of this module (100+ methods), only
key operations are highlighted here. See the module source for complete
documentation of all op_* methods.

Key Operation Categories:
    **User Operations**:
        - op_user_create(user_dict)
        - op_user_login(username, password)
        - op_user_logout(session_uuid)
        - op_user_get_info(user_id)
        - op_user_get_all()
        - op_user_update(user_id, user_dict)
        - op_user_update_password(user_id, old_pwd, new_pwd)

    **Project Operations**:
        - op_project_create(project_dict, user_id)
        - op_project_update(project_dict)
        - op_project_get_info(user_id)
        - op_project_get_users(project_id)
        - op_project_set_primary(project_id, user_id)
        - op_project_stage(project_id, user_id)

    **Item/Transaction Operations**:
        - op_item_create(item_dict)
        - op_item_update(item_id, item_dict)
        - op_item_get(item_id)
        - op_item_get_by_user(user_id, project_id, start, end)
        - op_item_delete(item_id)

    **Label Operations**:
        - op_label_create(label_dict)
        - op_label_update(label_id, label_dict)
        - op_label_get_all(project_id, use_cache)
        - op_label_get_by_name(name, project_id)
        - op_label_delete(label_id)
        - op_label_set_default(label_id, user_id, label_type)

    **Session Operations**:
        - op_get_user_sessions()
        - op_create_session(user_id)

    **Permission Operations**:
        - op_user_project_permission_update(user_id, project_id, perm)

Database Handler Pattern::

    from fiwa_cli.functions.handler_sqllite import SQLLiteHandler

    # Initialize handler
    dbh = SQLLiteHandler(db_path="/path/to/fiwa.db")

    # User operations
    user_id = dbh.op_user_create(user_data)
    session = dbh.op_user_login("batman", "password")

    # Project operations
    project_id = dbh.op_project_create(project_data, user_id)
    projects = dbh.op_project_get_info(user_id)

    # Item operations
    item_id = dbh.op_item_create(item_data)
    items = dbh.op_item_get_by_user(user_id, project_id, start, end)

    # Label operations
    label_id = dbh.op_label_create(label_data)
    labels = dbh.op_label_get_all(project_id)

Caching:
    The handler implements label caching:
        - op_label_get_all(use_cache=True): Uses cached labels
        - op_label_get_all(force_refresh=True): Clears and reloads cache
        - Cache key: project_id
        - Cache cleared on project switch

Database Handler
----------------

.. automodule:: fiwa_cli.functions.handler_sqllite
   :members:
   :undoc-members:
   :show-inheritance:

SQLite database operations and query management.

The SQLLiteHandler class implements all database operations for FiWa CLI
with 100+ op_* methods following a consistent naming convention.

Architecture:
    **Connection Management**:
        - SQLite3 connection pooling
        - Prepared statements for security
        - Table name prefixing (_db_salt)

    **Security**:
        - SHA-256 password hashing with salt
        - Parameterized queries (no SQL injection)
        - Session UUID tracking

    **Performance**:
        - Label caching by project_id
        - Efficient query patterns
        - Indexed lookups

Operation Categories (100+ methods):
    **User Operations** (15+ methods):
        - op_user_create(user_dict): Create new user
        - op_user_login(username, password): Authenticate
        - op_user_logout(session_uuid): End session
        - op_user_get_info(user_id): Get user details
        - op_user_get_all(): List all users
        - op_user_update(user_id, user_dict): Update user
        - op_user_update_password(...): Change password
        - op_total_number_of_users(): Count users

    **Project Operations** (12+ methods):
        - op_project_create(project_dict, user_id): Create project
        - op_project_update(project_dict): Update project
        - op_project_get_info(user_id): Get user's projects
        - op_project_get_users(project_id): List project members
        - op_project_set_primary(project_id, user_id): Set primary
        - op_project_stage(project_id, user_id): Setup defaults
        - op_project_add_user(project_id, user_id, perm, primary): Add member

    **Item/Transaction Operations** (10+ methods):
        - op_item_create(item_dict): Create expense/income
        - op_item_update(item_id, item_dict): Update transaction
        - op_item_get(item_id): Get single item
        - op_item_get_by_user(user_id, project_id, start, end): Query items
        - op_item_delete(item_id): Remove transaction

    **Label Operations** (10+ methods):
        - op_label_create(label_dict): Create label/category
        - op_label_update(label_id, label_dict): Update label
        - op_label_get_all(project_id, use_cache, force_refresh): Get all
        - op_label_get_by_name(name, project_id): Find by name
        - op_label_delete(label_id): Remove label
        - op_label_set_default(label_id, user_id, label_type): Set default

    **Session Operations** (5+ methods):
        - op_get_user_sessions(): Get session info
        - op_create_session(user_id): Create new session

    **Permission Operations** (5+ methods):
        - op_user_project_permission_update(user_id, project_id, perm)

Database Schema:
    Tables (prefixed with p{salt}_):
        - **users**: User accounts with hashed passwords
        - **sessions**: Active user sessions
        - **projects**: Project definitions with currency and style
        - **user_project_map**: User-project relationships with permissions
        - **items**: Transactions (expenses/income)
        - **labels**: Categories and tags with ownership

Label Caching:
    Performance optimization for frequently accessed labels::

        # First call: Queries database
        labels = dbh.op_label_get_all(project_id=1, use_cache=True)

        # Subsequent calls: Uses cache (fast)
        labels = dbh.op_label_get_all(project_id=1, use_cache=True)

        # After changes: Force refresh
        labels = dbh.op_label_get_all(project_id=1, force_refresh=True)

    Cache Strategy:
        - Key: project_id
        - Invalidation: On project switch or force_refresh=True
        - Benefits: 10-100x faster for repeated label queries

Security Features:
    **Password Hashing**:
        - Algorithm: SHA-256
        - Salt: Configurable (_pw_salt)
        - Default: "fiwa_default_salt_2026"
        - No plain text storage

    **SQL Injection Prevention**:
        - All queries use parameterized statements
        - User inputs never concatenated into SQL
        - Prepared statements for all operations

    **Session Management**:
        - UUID-based session identifiers
        - is_logged_in flag
        - Session expiration tracking

Handler Factory
---------------

.. automodule:: fiwa_cli.functions.handler
   :members:
   :undoc-members:
   :show-inheritance:

Factory pattern for database backend selection.

Purpose:
    - Abstracts database backend choice
    - Provides unified interface
    - Enables runtime backend switching
    - Simplifies testing

Supported Backends:
    - **sqlite**: SQLLiteHandler (current implementation)
    - **api**: HandlerApi (future - remote backend)

Usage::

    from fiwa_cli.functions.handler import Handler

    # Create SQLite handler
    handler = Handler(method="sqlite")
    dbh = handler.load()

    # Use unified interface
    users = dbh.op_user_get_all()

Handler API (Future)
--------------------

.. automodule:: fiwa_cli.functions.handler_api
   :members:
   :undoc-members:
   :show-inheritance:

API backend for remote FiWa server (placeholder).

**Status**: Not yet implemented - skeleton only.

Planned Features:
    - RESTful API communication
    - Bearer token authentication
    - Same op_* interface as SQLLiteHandler
    - Connection pooling
    - Retry logic
    - Response caching

Future Architecture::

    class HandlerApi:
        def __init__(self, base_url, api_key):
            self.base_url = base_url
            self.bearer_token = None

        def authenticate(self, username, password):
            # POST /api/v1/login
            # Receive bearer token
            pass

        def op_user_get_all(self):
            # GET /api/v1/users
            # Headers: Authorization: Bearer {token}
            # Returns: List of users
            pass

Test Data Generation
--------------------

db_faker Module
~~~~~~~~~~~~~~~

.. automodule:: fiwa_cli.functions.db_faker
   :members:
   :undoc-members:
   :show-inheritance:

Utilities for generating realistic test data.

The db_faker module provides functions to populate the database with
random but plausible data using the Faker library. It generates users,
projects, labels, and transactions with realistic distributions.

Key Functions:
    **faker_users(dbh, num_users=10)**:
        - Creates random user profiles
        - First user is superuser
        - Generates names, emails, birthdays
        - Simple passwords for testing (u0, u1, etc.)

    **faker_user_login(user, password, dbh)**:
        - Tests authentication
        - Prints session info
        - Useful for verification

    **faker_projects(dbh)**:
        - Creates one project per user
        - Additional projects for user 1 and 2
        - Sets up shared projects (user 2 and 3 join user 1's projects)
        - Random currencies and settings

    **faker_labels(dbh, project_ids)**:
        - Creates label structures
        - Random label types and statuses
        - Associates with specified projects

    **faker_items(dbh, project_ids, items_per_project)**:
        - Generates transactions
        - Realistic prices and dates
        - Random bought_by/bought_for assignments
        - Grocery-focused items

Data Patterns:
    The faker uses realistic statistical distributions:
        - **Poisson distribution**: For expense frequency (shopping trips)
        - **Clipped normal**: For expense amounts (average ± variance)
        - **Random dates**: Spread across date ranges
        - **Realistic vendors**: Actual store names

Example::

    from fiwa_cli.functions.db_faker import *
    from fiwa_cli.functions.handler_sqllite import SQLLiteHandler

    dbh = SQLLiteHandler(db_path="./test.db")

    # Generate test environment
    faker_users(dbh, num_users=5)
    project_ids = faker_projects(dbh)
    faker_labels(dbh, project_ids)
    faker_items(dbh, project_ids, items_per_project=50)

    # Test login
    faker_user_login("user0", "u0", dbh)

faker_superhero_project Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: fiwa_cli.functions.faker_superhero_project
   :members:
   :undoc-members:
   :show-inheritance:

Sample project creation with superhero users (Batman and Superman).

The superhero project provides a complete, ready-to-use test environment
with realistic transaction history spanning several months. It's ideal
for demonstrations, screenshots, and testing all FiWa features.

Features:
    - **4 Users**: Admin, Superman, Batman, Spiderman
    - **1 Shared Project**: Batman and Superman expense tracking
    - **Complete Labels**: All ExpenseTracker label types
    - **Transaction History**: Nov 2024 to present
    - **Realistic Patterns**: Income, expenses, savings
    - **Cost Sharing**: Some expenses split between users

Key Functions:
    **generate_superhero_data(dbh)**:
        - Creates 4 superhero users
        - Returns user ID mapping

    **generate_superhero_project(dbh, users)**:
        - Creates shared project
        - Generates all labels
        - Populates transaction history
        - Returns project_id

    **create_groceries(dbh, project_id, user_id, bought_by_id, start_date)**:
        - Generates grocery expenses
        - 1-8 shopping trips per week
        - Average $100/week
        - Real store names (Walmart, Kroger, etc.)

    **create_personal_supplies(dbh, ...)**:
        - Personal care and household items
        - Less frequent than groceries
        - Average $50/week

    **create_books(dbh, ...)**:
        - Book purchases
        - Infrequent (lower Poisson λ)
        - Various vendors

    **generate_income_data(dbh, project_id, user_id)**:
        - Monthly income streams
        - Batman: Wayne Enterprises (25th), Inheritance (26th)
        - Superman: Daily Planet (26th)

    **generate_savings_data(dbh, project_id, user_id)**:
        - Monthly savings on 27th
        - After income received
        - Responsible financial behavior

Transaction Timeline:
    All data generated from Nov 1, 2024 to present:
        - **Daily**: Groceries (1-8x per week)
        - **Weekly**: Personal supplies (1-3x per week)
        - **Monthly**: Income (25th-26th), Savings (27th)
        - **Occasional**: Books (variable)

Example::

    from fiwa_cli.functions.faker_superhero_project import *

    dbh = SQLLiteHandler(db_path="./demo.db")

    # Complete setup
    users = generate_superhero_data(dbh)
    project_id = generate_superhero_project(dbh, users)

    # Now database has:
    # - 4 users ready to login
    # - 1 shared project
    # - Months of transaction history
    # - Realistic expense patterns

Credentials:
    After generation, login with:
        - admin / admin123 (administrator)
        - batman / abc (regular user)
        - superman / abc (regular user)
        - spiderman / abc (regular user)

Common Workflows
----------------

Loading Configuration
~~~~~~~~~~~~~~~~~~~~~

From command line::

    # User runs: fiwa run --path /data/fiwa

    # In main.py:
    from fiwa_cli.functions.loader import handle_args, setup_fiwa

    mode, config = handle_args()
    # mode = "run"
    # config = {"path": "/data/fiwa", ...}

    full_config = setup_fiwa(abs_path=abs_path, config=config)
    # Returns complete config with dbh, paths, etc.

Loading CSS for Widget
~~~~~~~~~~~~~~~~~~~~~~

From widget's on_mount()::

    from fiwa_cli.functions.loader import load_dynamic_css

    class MyWidget(Widget):
        def on_mount(self):
            load_dynamic_css(self, "components_my_widget.tcss")
            # Loads: css/handsome/components_my_widget.tcss

Performing Logout
~~~~~~~~~~~~~~~~~

From any screen or component::

    from fiwa_cli.functions.logout_util import perform_logout

    def logout_user(self):
        success = perform_logout(self.app)
        if success:
            # User logged out, back at main screen
            pass

Using Project Composer
~~~~~~~~~~~~~~~~~~~~~~

Get project-specific labels::

    from fiwa_cli.functions.project_composer import ProjectComposer

    # Get composer for current project
    project_style = app.app_state["project_style"]
    pc = ProjectComposer.create(
        compose_type=project_style,
        dbh=dbh,
        project_id=project_id,
        users=[]
    )

    # Get label type map
    label_map = pc.get_label_map()
    # Returns: {0: "Balance", 1: "Transaction", ...}

    # Parse tag string from database
    tag_dict = pc.parse_tag_string("1_2_5_8_[12,15]")
    # Returns: {'count': 1, 'transaction': 2, ...}

Handler Architecture
--------------------

Handler Factory
~~~~~~~~~~~~~~~

.. automodule:: fiwa_cli.functions.handler
   :members:
   :undoc-members:
   :show-inheritance:

Factory pattern for database backend selection.

The Handler class provides a factory for creating database backend handlers,
abstracting the choice between local SQLite and remote API backends.

Purpose:
    - **Abstraction**: Hide backend implementation details
    - **Flexibility**: Runtime backend selection
    - **Consistency**: Unified op_* interface
    - **Testing**: Easy mocking and testing

Factory Pattern::

    from fiwa_cli.functions.handler import Handler

    # Create SQLite handler
    handler = Handler(method="sqlite")
    dbh = handler.load()
    # Returns: SQLLiteHandler instance

    # Future: Create API handler
    handler = Handler(method="api")
    dbh = handler.load()
    # Returns: HandlerApi instance

    # Both have same interface
    users = dbh.op_user_get_all()

Benefits:
    - Single point of backend selection
    - No conditional logic in application code
    - Easy to add new backends
    - Consistent error handling

Handler API (Future Implementation)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: fiwa_cli.functions.handler_api
   :members:
   :undoc-members:
   :show-inheritance:

API backend for remote FiWa server communication.

**Implementation Status**: ⚠️ Placeholder only - not production ready.

The HandlerApi will provide remote backend communication for multi-user
deployments where a centralized database is needed.

Planned Architecture:
    **Authentication**:
        - Bearer token-based authentication
        - Token refresh mechanism
        - Secure credential storage

    **Communication**:
        - RESTful API over HTTPS
        - JSON request/response format
        - Connection pooling
        - Retry logic with exponential backoff

    **Endpoints**:
        - POST /api/v1/login: Authentication
        - GET /api/v1/users: List users
        - POST /api/v1/users: Create user
        - GET /api/v1/projects: List projects
        - POST /api/v1/items: Create transaction
        - (All op_* methods mapped to endpoints)

    **Caching**:
        - Response caching for GET requests
        - Cache invalidation on mutations
        - Offline mode support (future)

Future Usage::

    from fiwa_cli.functions.handler import Handler

    # Configure API backend
    handler = Handler(method="api")
    handler.configure(
        base_url="https://api.fiwa.com",
        api_version="v1"
    )

    # Load handler
    dbh = handler.load()

    # Authenticate
    session = dbh.op_user_login("batman", "password")
    # POST https://api.fiwa.com/api/v1/login

    # Use same interface as SQLite
    projects = dbh.op_project_get_info(user_id=1)
    # GET https://api.fiwa.com/api/v1/projects?user_id=1

Current Implementation:
    Basic HTTP method wrappers only:
        - get(*args, **kwargs): HTTP GET
        - post(*args, **kwargs): HTTP POST
        - put(*args, **kwargs): HTTP PUT
        - delete(*args, **kwargs): HTTP DELETE

Database Handler
~~~~~~~~~~~~~~~~~~~

Creating a user::

    from fiwa_cli.functions.handler_sqllite import SQLLiteHandler

    dbh = SQLLiteHandler(db_path="/data/fiwa.db")

    user_data = {
        "first_name": "Bruce",
        "last_name": "Wayne",
        "username": "batman",
        "email": "bruce@wayneenterprises.com",
        "password": "darkknight123",
        "scope": "user:write"
    }

    user_id = dbh.op_user_create(user_data)

Creating a project::

    project_data = {
        "project_name": "Bat Cave Expenses",
        "description": "Personal expense tracking",
        "currency_main": "USD",
        "currency_list": json.dumps(["EUR", "GBP"]),
        "project_store": json.dumps({"month_start": 1})
    }

    project_id = dbh.op_project_create(project_data, user_id=1)

Creating an expense::

    item_data = {
        "item_uuid": str(uuid.uuid4()),
        "name": "Groceries",
        "price": 85.00,
        "currency": "USD",
        "price_final": 85.00,
        "currency_final": "USD",
        "bought_date": datetime.now(),
        "bought_by_id": 1,
        "bought_for_id": 1,
        "added_by_id": 1,
        "project_id": 1,
        "tags": "1_2_5_8_[]"
    }

    item_id = dbh.op_item_create(item_data)

Querying expenses::

    # Get all expenses for a user in date range
    items = dbh.op_item_get_by_user(
        user_id=1,
        project_id=1,
        start_date=datetime(2026, 3, 1),
        end_date=datetime(2026, 3, 31)
    )

    for item in items:
        print(f"{item['name']}: {item['price']} {item['currency']}")

Label operations::

    # Get all labels for a project
    labels = dbh.op_label_get_all(project_id=1, use_cache=True)

    # Create a new label
    label_data = {
        "name": "Groceries",
        "description": "Food and household items",
        "label_type": 3,  # Main category
        "label_sub_type": -1,  # Default
        "label_status": 2,  # Active
        "label_owner": 1,  # User ID or -1 for common
        "label_default": False
    }

    label_id = dbh.op_label_create(label_data)

Best Practices
--------------

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~

* Use handle_args() for CLI argument parsing
* Use load_yaml_config() for YAML files
* Store paths in app_state for easy access
* Preserve app-level config across logout
* Validate config before use

Resource Loading
~~~~~~~~~~~~~~~~

* Use load_dynamic_css() in widget on_mount()
* Check app_state is available before loading
* Handle missing CSS files gracefully
* Log all loading operations
* Use theme-specific paths (css/{theme}/)

Database Operations
~~~~~~~~~~~~~~~~~~~

* Always use op_* methods, never raw SQL in screens
* Check return values (None indicates failure)
* Use transactions for multi-step operations
* Handle database errors gracefully
* Log all database operations

Project Composition
~~~~~~~~~~~~~~~~~~~

* Use ProjectComposer.create() factory method
* Don't instantiate concrete composers directly
* Cache label_map for performance
* Use parse/format methods for tag strings
* Validate compose_type before creating

Logout Implementation
~~~~~~~~~~~~~~~~~~~~~

* Use perform_logout() from logout_util
* Don't duplicate logout logic
* Preserve app-level configuration
* Always return to main screen after logout
* Show clear success/error notifications

Troubleshooting
---------------

Configuration Not Loading
~~~~~~~~~~~~~~~~~~~~~~~~~

* Check config.yml exists in expected path
* Verify YAML syntax is valid
* Review logs for parsing errors
* Ensure file permissions allow reading

CSS Not Loading
~~~~~~~~~~~~~~~

* Verify app_state["abs_path"] is set
* Check app_state["css_form"] is correct
* Ensure .tcss file exists in css/{theme}/ directory
* Review logs for file not found errors
* Check file permissions

Database Connection Fails
~~~~~~~~~~~~~~~~~~~~~~~~~~

* Verify db_path exists and is writable
* Check database file permissions
* Ensure SQLite3 is available
* Review schema.sql matches database version
* Check logs for SQL errors

Logout Not Working
~~~~~~~~~~~~~~~~~~

* Verify session_uuid in app_state
* Check database handler is available
* Ensure op_user_logout() returns True
* Review logs for errors
* Check if app_state is being reset

Project Composer Errors
~~~~~~~~~~~~~~~~~~~~~~~

* "Invalid compose type" - Check project_style in database
* "Abstract class" - Use .create() factory, not direct instantiation
* Missing labels - Ensure compose_labels() was called
* Tag parsing fails - Verify tag string format

See Also
--------

* :doc:`database`: Database schema documentation
* :doc:`main`: Main application
* :doc:`screens`: Screen implementations
* :doc:`components`: UI components
