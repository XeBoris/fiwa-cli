from typing import Dict, Any, Optional, List
import os
import yaml
import time
import random
import uuid
import json
from datetime import datetime, timedelta
import numpy as np

from fiwa_cli.functions.handler import Handler


def generate_data(
    dbh,
    project_id: int,
    user_id: int,
    bought_for_id: int,
    names: list = [],
    labels: list = [],
    start_date_str: str = "2024-11-01",
    end_date: Optional[datetime] = None,
    currency: str = "USD",
    avg_weekly_spend: float = 100.0,
    max_weekly_spend: float = 150.0
) -> List[int]:
    """
    Generate realistic grocery shopping transaction data with Poisson-distributed shopping frequency.

    Creates shopping entries from a start date to today (or specified end date) with:
    - 1-8 shopping trips per week (Poisson distribution, mean ~3)
    - Average weekly spend of ~100 (with variance)
    - Individual trip amounts using clipped Poisson distribution (max 150)
    - Realistic grocery store names

    Args:
        dbh: Database handler instance with op_item_create method
        project_id (int): The project ID to associate items with
        user_id (int): User ID who bought and added the items
        bought_for_id (int): User ID for whom items were bought
        start_date_str (str): Start date in format "YYYY-MM-DD" (default: "2024-11-01")
        end_date (datetime, optional): End date for generation. Defaults to today.
        currency (str): Currency code (default: "USD")
        avg_weekly_spend (float): Average total spending per week (default: 100.0)
        max_weekly_spend (float): Maximum allowed weekly spend (default: 150.0)

    Returns:
        List[int]: List of created item IDs

    Example:
        >>> item_ids = generate_grocery_shopping_data(
        ...     dbh=database_handler,
        ...     project_id=1,
        ...     user_id=123,
        ...     bought_for_id=123,
        ...     start_date_str="2024-11-01"
        ... )
        >>> print(f"Created {len(item_ids)} grocery transactions")
    """

    # Grocery store names (mix of real chains from different regions)
    # grocery_stores =

    # Parse dates
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    if end_date is None:
        end_date = datetime.now()

    # Calculate number of weeks
    total_days = (end_date - start_date).days
    num_weeks = total_days / 7.0

    created_items = []
    current_date = start_date

    # Process week by week
    week_num = 0
    while current_date <= end_date:
        week_num += 1
        week_start = current_date
        week_end = min(current_date + timedelta(days=6), end_date)

        # Determine number of shopping trips this week (1-8, Poisson with mean 3)
        # Using Poisson lambda=2.5 gives good distribution between 1-8
        trips_this_week = min(8, max(1, int(np.random.poisson(2.5) + 1)))

        # Generate random shopping days within the week
        week_days_range = (week_end - week_start).days + 1
        shopping_days = sorted(random.sample(range(week_days_range), min(trips_this_week, week_days_range)))

        # Calculate target weekly spend with some variance (±20%)
        weekly_variance = random.uniform(0.8, 1.2)
        target_weekly_spend = min(avg_weekly_spend * weekly_variance, max_weekly_spend)

        # Distribute the weekly spend across trips (with random variation)
        trip_weights = [random.uniform(0.5, 1.5) for _ in range(trips_this_week)]
        total_weight = sum(trip_weights)
        trip_amounts = [target_weekly_spend * (w / total_weight) for w in trip_weights]

        # Create shopping transactions for this week
        for day_offset, trip_amount in zip(shopping_days, trip_amounts):
            shopping_date = week_start + timedelta(days=day_offset)

            # Add some time variation (morning to evening)
            shopping_hour = random.randint(8, 20)
            shopping_minute = random.randint(0, 59)
            shopping_datetime = shopping_date.replace(hour=shopping_hour, minute=shopping_minute)

            # Clip amount to max (simulating Poisson-like distribution with cap)
            # Add Poisson-like variance to the amount
            amount_variance = np.random.poisson(10) - 10  # Centers around 0
            final_amount = max(5.0, min(trip_amount + amount_variance, max_weekly_spend))
            final_amount = round(final_amount, 2)

            # Select random store
            store_name = random.choice(names)

            # Create item dictionary
            item_dict = {
                "item_uuid": str(uuid.uuid4()),
                "name": f"{store_name}",
                "note": f"Weekly shopping at {store_name}",
                "price": final_amount,
                "price_final": final_amount,
                "currency": currency,
                "currency_final": currency,
                "bought_date": shopping_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "bought_by_id": user_id,
                "bought_for_id": bought_for_id,
                "added_by_id": user_id,
                "project_id": project_id,
                "exchange_rate": 1.0,
                "exchange_rate_date": shopping_date.strftime("%Y-%m-%d"),
                "tags": json.dumps(labels)  # Empty tags for now, can be populated with label IDs
            }

            # Create item in database
            try:
                item_id = dbh.op_item_create(item_dict=item_dict)
                if item_id:
                    created_items.append(item_id)
            except Exception as e:
                print(f"Warning: Failed to create item for {shopping_date}: {e}")

        # Move to next week
        current_date = week_end + timedelta(days=1)

    print(f"Generated {len(created_items)} grocery shopping transactions")
    print(f"Period: {start_date_str} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Average trips per week: {len(created_items) / num_weeks:.1f}")

    return created_items


def load_dynamic_css(widget, css_filename: str) -> None:
    """Load external CSS file based on app theme configuration.

    Attempts to load a widget's CSS file from the theme directory
    specified in app_state. Falls back silently if CSS cannot be loaded.

    This function should be called from a widget's on_mount() method after
    the app is fully initialized and app_state is available.

    Args:
        widget: The Textual widget instance (must have self.app attribute)
        css_filename: Name of the CSS file (e.g., "components_week_month_picker.tcss")

    Example:
        >>> def on_mount(self):
        >>>     load_dynamic_css(self, "components_calendar_picker.tcss")
    """
    try:
        # Get theme and base path from app state
        css_form = widget.app.app_state.get("css_form", "handsome")
        abs_path = widget.app.app_state["abs_path"]

        # Build path to CSS file
        css_file = os.path.join(abs_path, "css", css_form, css_filename)

        # Check if file exists
        if not os.path.exists(css_file):
            widget.app.log(f"✗ CSS file not found: {css_file}")
            return

        # Read CSS content
        with open(css_file, "r") as f:
            css_content = f.read()

        # Add to app stylesheet and force refresh
        widget.app.stylesheet.add_source(css_content)
        widget.refresh(layout=True)

        widget.app.log(f"✓ Loaded CSS from: {css_file}")

    except (AttributeError, KeyError) as e:
        widget.app.log(f"✗ app_state not available: {e}")
        widget.app.notify("Error loading theme CSS. 'all_state' not available.", severity="error")
    except Exception as e:
        widget.app.log(f"✗ Failed to load CSS: {e}")
        widget.app.notify("Error loading theme CSS.", severity="error")





def handle_args()-> [str, Dict[str, Any]]:
    """Handle command-line arguments for FiWa CLI application.

    Parses command-line arguments using argparse with two main subcommands:
    'init' and 'run'. This function supports secure password input via getpass
    when running with user authentication.

    Subcommands:
        init: Initialize a new FiWa environment
            --path: Optional path to configuration directory (default: OS-specific)
            --operation-model: Operations model to use (default: "local")
                Options: "local", "api"

        run: Run the FiWa application
            --path: Optional path to configuration directory (default: OS-specific)
            --user: Optional username for authenticated session
                Note: Password will be prompted securely if user is provided

    Returns:
        tuple: A tuple containing:
            - mode (str): The selected mode ("init" or "run")
            - config (dict): Dictionary containing parsed arguments with keys:
                - config_path (str|None): Path to config directory
                - operation_model (str): Operation model (for init mode)
                - user (str|None): Username (for run mode)
                Note: 'mode' is removed from the config dict

    Examples:
        Initialize FiWa with default settings:
            $ python main.py init

        Initialize with custom path:
            $ python main.py init --path /path/to/config --operation-model local

        Run FiWa without authentication:
            $ python main.py run

        Run FiWa with user authentication (password will be prompted):
            $ python main.py run --user alice --path ~/my-fiwa
            Enter password for user alice: ********

    Raises:
        SystemExit: If required arguments are missing or invalid

    Security:
        Passwords are NEVER accepted as command-line arguments to prevent
        exposure in shell history or process lists. Use getpass in main()
        to prompt for passwords securely.
    """
    import argparse

    parser = argparse.ArgumentParser(description="FiWa CLI Application")
    subparsers = parser.add_subparsers(dest='mode',
                                       help='Available modes',
                                       required=True,
                                       description="Choose the mode to run FiWa in. 'init' will initialize a new FiWa environment.")

    init_parser = subparsers.add_parser('init', help='Initialize a new FiWa environment')
    init_parser.add_argument("--path",
                             type=str,
                             default=None,
                             dest="config_path",
                             help="Path to configuration YAML file")
    init_parser.add_argument("--operation-model", type=str,
                             default="local",
                             dest="operation_model",
                             help="Operations model to use")
    init_parser.add_argument("--stage", type=str,
                             default="prod",
                             dest="stage",
                             help="Stage to use (prod or dev)")


    # Subparser for 'run' command
    run_parser = subparsers.add_parser('run', help='Run the FiWa application')
    run_parser.add_argument('--path',
                            type=str,
                            default=None,
                            dest="config_path",
                            help='Path to configuration YAML file')
    run_parser.add_argument('--user',
                            type=str,
                            default=None,
                            dest="user",
                            help='Username for the session')

    args = parser.parse_args()

    _mode = args.mode
    _conf = dict(vars(args))
    del _conf["mode"]  # Remove mode from config as it's already stored in _mode variable
    return _mode, _conf

def get_abs_path():
    """
    Get the absolute path of the current script.
    Returns:
        str: The absolute path of the current script.
    """
    return os.path.dirname(os.path.abspath(__file__)).split("functions")[0]

def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load YAML configuration from disk.
    Args:
        config_path (str): Path to the YAML configuration file.
    Returns:
        Dict[str, Any]: The loaded configuration as a dictionary. Returns an empty dictionary if the file does not exist or is empty.
    """

    if not os.path.exists(config_path):
        return {}

    with open(config_path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def identify_os(os_folder:str="fiwa-cli") -> [str, str]:
    """
    Identify the operating system and return the home directory path for application data.

    Args:
        os_folder (str): The folder name to use for application data.
    Returns:
        str: The name of the operating system ('linux', 'windows', 'darwin', or 'unknown').
        str: The path to the home directory for the application data.
    """
    import platform
    os_system = platform.system().lower()
    if os_system not in  ["linux", "windows", "darwin"]:
        return "unknown"
    # detect home directory based on OS:

    if os_system == "linux":
        print("Running on Linux")
        os_home_dir = os.path.join(os.getenv("HOME", ""), ".config", os_folder)
    elif os_system == "windows":
        print("Running on Windows")
        # Use LOCALAPPDATA for local databases and application data
        os_home_dir = os.path.join(os.getenv("LOCALAPPDATA", ""), os_folder)
    elif os_system == "darwin":
        print("Running on macOS")
        # macOS uses ~/Library/Application Support/
        os_home_dir = os.path.join(
            os.getenv("HOME", ""),
            "Library",
            "Application Support",
            os_folder
        )
    else:
        print(f"Running on an unsupported OS: {os_system}. Using fallback.")
        os_home_dir = os.path.join(os.getenv("HOME", ""), f".{os_folder}")

    return os_system, os_home_dir

def prep_fiwa(mode: str = "", config: Dict[str, Any] = {}) -> None:
    """Prepare and initialize a new FiWa environment.

    This function sets up a fresh FiWa installation by creating the necessary
    directory structure, configuration files, and SQLite database. It should
    be called during the 'init' mode to bootstrap a new FiWa environment.

    The function performs the following operations:
    1. Determines the OS-specific data directory location
    2. Validates the configuration path if provided
    3. Creates the data directory structure
    4. Generates and saves a default config.yml file
    5. Initializes a new SQLite database with the schema
    6. Creates a default admin user for initial access

    Args:
        mode (str, optional): The initialization mode. Currently unused but
            reserved for future expansion. Defaults to "".
        config (Dict[str, Any], optional): Configuration dictionary that may contain:
            - config_path (str): Custom absolute path for data directory.
                If not provided, uses OS-specific default locations:
                - Linux: ~/.config/fiwa-cli/
                - Windows: %LOCALAPPDATA%/fiwa-cli/
                - macOS: ~/Library/Application Support/fiwa-cli/
            - operational_model (str): Operation model ("local" or "api").
                Defaults to "local".

    Returns:
        bool: True if initialization succeeds.

    Raises:
        ValueError: If config_path is provided but not an absolute path.
        SystemExit: If data directory already exists or cannot be created.

    Side Effects:
        - Creates OS-specific data directory
        - Creates config.yml file with default settings
        - Creates data.sqlite database with schema
        - Creates default admin user with credentials:
            username: "admin", password: "admin123"

    Examples:
        Initialize with default OS-specific location:
            >>> prep_fiwa(mode="init", config={})

        Initialize with custom path:
            >>> prep_fiwa(mode="init", config={"config_path": "/opt/fiwa-data"})

        Initialize with custom operation model:
            >>> prep_fiwa(mode="init", config={"operational_model": "api"})

    Notes:
        - This function will exit with code 1 if the data directory already exists
        - The default admin user should have their password changed after first login
        - The function creates a production-ready configuration by default
        - Database schema is loaded from the package's database/schema.sql file

    Security:
        The default admin credentials (admin/admin123) are created for initial
        setup only and should be changed immediately after first login.
    """

    os_home_dir = ""
    os_folder = "fiwa-cli"  # No leading dot for Windows

    os_system, os_home_dir = identify_os(os_folder=os_folder)

    if config.get("config_path", None) is not None:
        config_path = config["config_path"]
        #test if config_path is absolute, otherwise raise an error:
        if not os.path.isabs(config_path):
            raise ValueError(f"Config path must be absolute: {config_path}")
        else:
            os_home_dir = config_path

    # if path exists, we can assume that the project is setup.
    # we stop here:
    if os.path.exists(os_home_dir):
        print(f"Data directory already exists at: {os_home_dir}")
        exit(1)

    config = {
        "configuration": {
            "host": "terminal",
            "path": os_home_dir,
            "model": config.get("operational_model", "local")
        },
        "development": {
            "stage": config.get("stage", "prod"),
            "debug_mode": True
        },
        "style": {
            "theme": "textual-light",
            "form": "handsome"
        }
    }
    # create the data directory if it doesn't exist:
    try:
        os.makedirs(os_home_dir, exist_ok=True)
    except Exception as e:
        print(f"Error creating data directory: {e}")
        exit(1)

    # save the config to a yaml file in the data directory for later use:
    config_path = os.path.join(os_home_dir, "config.yml")
    with open(config_path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle)

    # receive the initial absolute schema path for the database initialization:
    _schema_path = os.path.dirname(os.path.abspath(__file__))
    _schema_path = _schema_path.split("functions")[0]
    _schema_path = os.path.join(_schema_path, "database", "schema.sql")

    sqlite_path = os.path.join(os_home_dir, "data.sqlite")

    if not os.path.exists(sqlite_path):
        # we setup the local database handler
        h = Handler(method="sqlite")
        dbh = h.load()
        dbh.set_path(sqlite_path)
        dbh.initialize_database(schema_path=_schema_path)

        user_dict = {"first_name": "Admin",
                     "last_name": "User",
                     "username": "admin",
                     "email": "admin@info.com",
                     "password": "admin123",
                     "is_superuser": True,
                     "scope": "admin:write",
                     "activated": True}
        dbh.op_user_create(user_dict=user_dict)
        return True
    else:
        print(f"SQLite database already exists at: {sqlite_path}")
        exit(1)



def setup_fiwa(abs_path:str = "", config: Dict[str, Any] = {}) -> None:
    """
    Set up the FiWa application with the given configuration.

    Args:
        config (Dict[str, Any]): Configuration dictionary for FiWa.
    """
    # Here you can add any setup logic needed before starting the app
    # For example, you could initialize logging, set environment variables, etc.
    print("FiWa configuration loaded:")

    os_home_dir = ""
    os_folder = "fiwa-cli"  # No leading dot for Windows

    os_system, os_home_dir = identify_os(os_folder=os_folder)
    print(os_system, os_home_dir)

    if config.get("config_path", None) is not None:
        config_path = config["config_path"]
        #test if config_path is absolute, otherwise raise an error:
        if not os.path.isabs(config_path):
            raise ValueError(f"Config path must be absolute: {config_path}")
        else:
            os_home_dir = config_path

    print(os_home_dir)
    # load according yaml file from location:
    configyml = load_yaml_config(os.path.join(os_home_dir, "config.yml"))
    sqlite_path = os.path.join(os_home_dir, "data.sqlite")
    print(configyml)

    # we need the operation model to decide how to setup:
    opp_model = configyml.get("configuration", {}).get("model", "terminal")

    dev_config = configyml.get("development", {})
    # opp_mode = config.get("configuration", {}).get("host", "terminal")
    # opp_path = config.get("configuration", {}).get("path", "<local>")
    # opp_model = config.get("configuration", {}).get("model", "terminal")

    if opp_model == "local" and dev_config.get("stage", None) == "prod":
        print(f"Running in local mode with path: {os_home_dir}")

        h = Handler(method="sqlite")
        dbh = h.load()
        dbh.set_path(sqlite_path)

        # if user + password are provided, let's log in the user:
        if "user" in config and "password" in config:
            dbh.op_user_login(username=config.get("user"),
                              password=config.get("password"))

        # Store in config for later use
        configyml["_data_directory"] = os_home_dir
        configyml["dbh"] = dbh
        return configyml

    elif opp_model == "api":
        print("Running in API mode - API client setup not implemented yet.")
        # Here you would set up your API client and store it in the config
        # For example:
        # api_client = APIClient(base_url=config["configuration"]["path"])
        # config["api_client"] = api_client
        return config

    elif opp_model == "local" and dev_config.get("stage", None) == "stage-1":
        print(f"Running in local mode with path: {os_home_dir}")
        print(f"Run in stage {dev_config.get('stage', None)} - initializing database with schema and default data")

        # delete previous database for clean dev environment:
        if os.path.exists(sqlite_path):
            os.remove(sqlite_path)

        h = Handler(method="sqlite")
        dbh = h.load()
        dbh.set_path(sqlite_path)

        _schema_path = os.path.dirname(os.path.abspath(__file__))
        _schema_path = _schema_path.split("functions")[0]
        _schema_path = os.path.join(_schema_path, "database", "schema.sql")

        dbh.initialize_database(schema_path=_schema_path)

        user_dict = {"first_name": "Admin",
                     "last_name": "User",
                     "username": "admin",
                     "email": "admin@info.com",
                     "password": "admin123",
                     "is_superuser": True,
                     "scope": "admin:write",
                     "activated": True}
        uid0 = dbh.op_user_create(user_dict=user_dict)

        user_dict = {"first_name": "Clark",
                     "last_name": "Kent",
                     "username": "superman",
                     "email": "superman@info.com",
                     "password": "abc",
                     "is_superuser": False,
                     "scope": "user:write",
                     "activated": True}
        uid0 = dbh.op_user_create(user_dict=user_dict)

        user_dict = {"first_name": "Bruce",
                     "last_name": "Wayne",
                     "username": "batman",
                     "email": "batman@info.com",
                     "password": "abc",
                     "is_superuser": False,
                     "scope": "user:write",
                     "activated": True}
        uid1 = dbh.op_user_create(user_dict=user_dict)

        user_dict = {"first_name": "Peter",
                     "last_name": "Parker",
                     "username": "Spiderman",
                     "email": "spiderman@info.com",
                     "password": "abc",
                     "is_superuser": False,
                     "scope": "user:write",
                     "activated": True}
        uid2 = dbh.op_user_create(user_dict=user_dict)

        # Create some projects:
        project_dict = {
            "name": "Bat Cave Expenses",
            "description": "A common project of super heros",
            "currency_main": "USD",
            "currency_list": ["SEK", "EUR", "GBP"],
            "project_store" : {"month_start": 25}
        }
        dbh.op_project_create(project_dict=project_dict,
                              user_id=uid1)

        project_dict = {
            "name": "Sweden Day Job",
            "description": "Being a friendly neighborhood spiderman is expensive",
            "currency_main": "SEK",
            "currency_list": ["USD", "EUR", "GBP"],
            "project_store": {"month_start": 1}

        }
        dbh.op_project_create(project_dict=project_dict,
                              user_id=uid2)


        # bruce adds clark to his project:
        p_info = dbh.op_project_get_info(user_id=uid1)
        p_info = [i for i in p_info if i["project_name"] == "Bat Cave Expenses"][0]

        dbh.op_project_add_user(project_id=p_info["project_id"],
                                user_id=uid0,
                                project_perm_model='111100',
                                project_primary=False)

        # peter adds bruce to his project:
        p_info = dbh.op_project_get_info(user_id=uid2)
        p_info = [i for i in p_info if i["project_name"] == "Sweden Day Job"][0]

        dbh.op_project_add_user(project_id=p_info["project_id"],
                                user_id=uid1,
                                project_perm_model='111100',
                                project_primary=False)

        # now we need labels for the bat cave project:
        p_info = dbh.op_project_get_info(user_id=uid1)
        p_info = [i for i in p_info if i["project_name"] == "Bat Cave Expenses"][0]

        # action labels
        action_labels = []
        i_label = {"name": "expenses", "description": "Expenses", "composite": None,
                   "label_status": 2, "label_type": 0}
        action_labels.append(i_label)
        i_label = {"name": "revenue", "description": "Revenue", "composite": None,
                   "label_status": 2, "label_type": 0}
        action_labels.append(i_label)
        i_label = {"name": "recurring", "description": "", "composite": None,
                   "label_status": 2, "label_type": 0}
        action_labels.append(i_label)
        i_label = {"name": "permanent", "description": "", "composite": None,
                   "label_status": 2, "label_type": 0}
        action_labels.append(i_label)
        i_label = {"name": "irregular", "description": "", "composite": None,
                   "label_status": 2, "label_type": 0}
        action_labels.append(i_label)

        account_labels = []
        i_label = {"name": "Liability", "description": "", "composite": None,
                   "label_status": 2, "label_type": 1}
        account_labels.append(i_label)
        i_label = {"name": "Income", "description": "", "composite": None,
                   "label_status": 2, "label_type": 1}
        account_labels.append(i_label)
        i_label = {"name": "Spending", "description": "", "composite": None,
                   "label_status": 2, "label_type": 1}
        account_labels.append(i_label)

        _labels = []
        i_label = {"name": "Groceries", "description": "", "composite": None,
                   "label_status": 2, "label_type": 2}
        _labels.append(i_label)
        i_label = {"name": "Concerts/Festivals", "description": "", "composite": None,
                   "label_status": 2, "label_type": 2}
        _labels.append(i_label)
        i_label = {"name": "Sports", "description": "", "composite": None,
                   "label_status": 2, "label_type": 2}
        _labels.append(i_label)
        i_label = {"name": "Personal Supplies", "description": "", "composite": None,
                   "label_status": 2, "label_type": 2}
        _labels.append(i_label)
        i_label = {"name": "Books", "description": "", "composite": None,
                   "label_status": 2, "label_type": 2}
        _labels.append(i_label)
        i_label = {"name": "eLearning", "description": "", "composite": None,
                   "label_status": 2, "label_type": 2}
        _labels.append(i_label)
        i_label = {"name": "Travel", "description": "", "composite": None,
                   "label_status": 2, "label_type": 2}
        _labels.append(i_label)
        i_label = {"name": "Gifts", "description": "", "composite": None,
                   "label_status": 2, "label_type": 2}
        _labels.append(i_label)

        for i_label in action_labels:
            dbh.op_label_create(label_dict=i_label, project_id=p_info["project_id"])

        for i_label in account_labels:
            dbh.op_label_create(label_dict=i_label, project_id=p_info["project_id"])

        for i_label in _labels:
            dbh.op_label_create(label_dict=i_label, project_id=p_info["project_id"])

        # Generate grocery shopping data with realistic patterns
        label_id_person = dbh.op_label_get_by_name("Personal Supplies", p_info["project_id"])
        label_id_expenses = dbh.op_label_get_by_name("expenses", p_info["project_id"])
        label_id_spending = dbh.op_label_get_by_name("Spending", p_info["project_id"])
        label_id_irregular = dbh.op_label_get_by_name("irregular", p_info["project_id"])
        grocery_store_names = [
            "Normal", "Haargummies", "Duschsachen", "Zahncreme", "Rasierklingen", "Deo", "Shampoo",
            "DM", "Rossmann", "Müller", "Boots", "CVS", "Walgreens", "Superdrug",
            "DVD"
        ]

        print(f"ID: ({label_id_person}), generating sample data...")
        item_ids = generate_data(
            dbh=dbh,
            project_id=p_info["project_id"],
            user_id=uid1,
            bought_for_id=uid1,
            names=grocery_store_names,
            labels=[label_id_person, label_id_expenses,
                    label_id_spending, label_id_irregular],
            start_date_str="2024-11-01",
            currency="USD",
            avg_weekly_spend=10.0,
            max_weekly_spend=15.0
        )
        print(f"ID: ({label_id_person}), generating sample data...")

        item_ids = generate_data(
            dbh=dbh,
            project_id=p_info["project_id"],
            user_id=uid1,
            bought_for_id=uid0,
            names=grocery_store_names,
            labels=[label_id_person, label_id_expenses,
                    label_id_spending, label_id_irregular],
            start_date_str="2024-11-01",
            currency="USD",
            avg_weekly_spend=2.0,
            max_weekly_spend=5.0
        )
        print(f"ID: ({label_id_person}), generating sample data...")

        item_ids = generate_data(
            dbh=dbh,
            project_id=p_info["project_id"],
            user_id=uid0,
            bought_for_id=uid0,
            names=grocery_store_names,
            labels=[label_id_person, label_id_expenses,
                    label_id_spending, label_id_irregular],
            start_date_str="2024-11-01",
            currency="USD",
            avg_weekly_spend=12.0,
            max_weekly_spend=17.0
        )
        print(f"ID: ({label_id_person}), generating sample data...")

        item_ids = generate_data(
            dbh=dbh,
            project_id=p_info["project_id"],
            user_id=uid0,
            bought_for_id=uid1,
            names=grocery_store_names,
            labels=[label_id_person, label_id_expenses,
                    label_id_spending, label_id_irregular],
            start_date_str="2024-11-01",
            currency="USD",
            avg_weekly_spend=1.0,
            max_weekly_spend=3.0
        )
        print(f"ID: ({label_id_person}), generating sample data...")

        # Generate grocery shopping data with realistic patterns
        label_id_groceries = dbh.op_label_get_by_name("Groceries", p_info["project_id"])
        label_id_expenses = dbh.op_label_get_by_name("expenses", p_info["project_id"])
        label_id_spending = dbh.op_label_get_by_name("Spending", p_info["project_id"])
        label_id_irregular = dbh.op_label_get_by_name("irregular", p_info["project_id"])
        grocery_store_names = [
            "Lidl", "Aldi", "Coop", "Netto", "Walmart", "Target", "Kroger",
            "Tesco", "Carrefour", "Whole Foods", "Trader Joe's", "Safeway",
            "ICA", "Rewe", "Edeka", "Albert Heijn", "Costco", "Sam's Club"
        ]
        print(f"Found 'Groceries' label (ID: {label_id_groceries}), generating sample data...")
        item_ids = generate_data(
            dbh=dbh,
            project_id=p_info["project_id"],
            user_id=uid1,
            bought_for_id=uid1,
            names=grocery_store_names,
            labels=[label_id_groceries, label_id_expenses,
                    label_id_spending, label_id_irregular],
            start_date_str="2024-11-01",
            currency="USD",
            avg_weekly_spend=100.0,
            max_weekly_spend=150.0
        )
        print(f"✓ Generated {len(item_ids)} grocery transactions for Batman")

        item_ids = generate_data(
            dbh=dbh,
            project_id=p_info["project_id"],
            user_id=uid1,
            bought_for_id=uid0,
            names=grocery_store_names,
            labels=[label_id_groceries, label_id_expenses,
                    label_id_spending, label_id_irregular],
            start_date_str="2024-11-01",
            currency="USD",
            avg_weekly_spend=10.0,
            max_weekly_spend=15.0
        )
        print(f"✓ Batman generated {len(item_ids)} grocery transactions for Clark")

        item_ids = generate_data(
            dbh=dbh,
            project_id=p_info["project_id"],
            user_id=uid0,
            bought_for_id=uid0,
            names=grocery_store_names,
            labels=[label_id_groceries, label_id_expenses,
                    label_id_spending, label_id_irregular],
            start_date_str="2024-11-01",
            currency="USD",
            avg_weekly_spend=80.0,
            max_weekly_spend=110.0
        )
        print(f"✓ Generated {len(item_ids)} grocery transactions for Batman")

        item_ids = generate_data(
            dbh=dbh,
            project_id=p_info["project_id"],
            user_id=uid0,
            bought_for_id=uid1,
            names=grocery_store_names,
            labels=[label_id_groceries, label_id_expenses,
                    label_id_spending, label_id_irregular],
            start_date_str="2024-11-01",
            currency="USD",
            avg_weekly_spend=5.0,
            max_weekly_spend=10.0
        )
        print(f"✓ Clark generated {len(item_ids)} grocery transactions for Batman")

        # if user + password are provided, let's log in the user:
        if "user" in config and "password" in config:
            dbh.op_user_login(username=config.get("user"),
                              password=config.get("password"))

        configyml["_data_directory"] = os_home_dir
        configyml["dbh"] = dbh
        configyml["_abs_path"] = abs_path
        return configyml

    elif opp_model == "local" and dev_config.get("stage", None) == "dev":
        print(f"Running in local mode with path: {os_home_dir}")

        #delete previous database for clean dev environment:
        if os.path.exists(sqlite_path):
            os.remove(sqlite_path)

        h = Handler(method="sqlite")
        dbh = h.load()
        dbh.set_path(sqlite_path)


        _schema_path = os.path.dirname(os.path.abspath(__file__))
        _schema_path = _schema_path.split("functions")[0]
        _schema_path = os.path.join(_schema_path, "database", "schema.sql")

        dbh.initialize_database(schema_path=_schema_path)

        from .db_faker import faker_users, faker_user_login, faker_projects, faker_labels, faker_items

        faker_users(dbh=dbh, num_users=5)
        #
        #
        faker_user_login("user0", "u0", dbh=dbh)

        project_ids = faker_projects(dbh=dbh)

        faker_labels(dbh=dbh, project_ids=project_ids)

        faker_items(dbh=dbh, project_ids=project_ids)

        r = dbh.op_get_user_sessions()
        print(r)

        time.sleep(0.5)
        # Store in config for later use
        configyml["_data_directory"] = os_home_dir
        configyml["dbh"] = dbh
        configyml["_abs_path"] = abs_path
        return configyml

    # def generate_fake_shopping_data(dbh, start_date, end_date, user_id, num_entries=10):
    #     """
    #     Generate fake grocery shopping data with realistic patterns.
    #
    #     Args:
    #         dbh: Database handler instance.
    #         start_date (datetime): The start date for the data generation.
    #         end_date (datetime): The end date for the data generation.
    #         user_id (str): The ID of the user for whom the data is generated.
    #         num_entries (int): The number of shopping entries to generate.
    #
    #     Returns:
    #         list: A list of dictionaries containing fake shopping data.
    #     """
    #     fake_data = []
    #     product_categories = ["Fruits", "Vegetables", "Dairy", "Meat", "Grains", "Snacks", "Beverages"]
    #     store_locations = ["Store A", "Store B", "Store C"]
    #
    #     for _ in range(num_entries):
    #         date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
    #         category = random.choice(product_categories)
    #         store = random.choice(store_locations)
    #         amount = round(random.uniform(5.0, 100.0), 2)  # Random amount between 5 and 100
    #         price = round(random.uniform(1.0, 20.0), 2)    # Random price between 1 and 20
    #
    #         entry = {
    #             "user_id": user_id,
    #             "date": date.strftime("%Y-%m-%d"),
    #             "category": category,
    #             "store": store,
    #             "amount": amount,
    #             "price": price
    #         }
    #         fake_data.append(entry)
    #
    #         # Insert into database
    #         dbh.op_shopping_create(shopping_dict=entry)
    #
    #     return fake_data

    # Generate fake shopping data for testing
    # start_date = datetime.strptime("2024-11-01", "%Y-%m-%d")
    # end_date = datetime.now()
    # user_id = "admin"  # Assuming admin user ID
    # generate_fake_shopping_data(dbh, start_date, end_date, user_id, num_entries=10)



