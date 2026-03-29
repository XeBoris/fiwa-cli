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

import fiwa_cli.functions.faker_superhero_project as shp

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
        print(f"Running in local mode with path: {os_home_dir} - prod")
        print(sqlite_path)
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
        configyml["_abs_path"] = abs_path
        return configyml

    elif opp_model == "api":
        print("Running in API mode - API client setup not implemented yet.")
        # Here you would set up your API client and store it in the config
        # For example:
        # api_client = APIClient(base_url=config["configuration"]["path"])
        # config["api_client"] = api_client
        return config

    elif opp_model == "local" and dev_config.get("stage", None) == "superheros":
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

        # This one creates the whole superhero project from scratch:
        # handle with care!
        sph_user_ids = shp.generate_superhero_data(dbh)

        shp.generate_superhero_projects(dbh, users=sph_user_ids)

        shp.generate_superhero_labels(dbh, users=sph_user_ids)
        #
        start_date = "2024-01-01"
        shp.generate_personal_supplies_data(dbh, users=sph_user_ids, start_date_str=start_date)

        shp.generate_groceries_data(dbh, users=sph_user_ids, start_date_str=start_date)

        shp.generate_books_data(dbh, users=sph_user_ids, start_date_str=start_date)
        #
        shp.generate_income_data(dbh, users=sph_user_ids, start_date_str=start_date)
        #
        # shp.generate_savings_data(dbh, users=sph_user_ids)

        # if user + password are provided, let's log in the user:
        if "user" in config and "password" in config:
            dbh.op_user_login(username=config.get("user"),
                              password=config.get("password"))

        configyml["_data_directory"] = os_home_dir
        configyml["dbh"] = dbh
        configyml["_abs_path"] = abs_path
        return configyml
    elif opp_model == "local" and dev_config.get("stage", None) == "stage2":
        print(f"[Stage2] Running in local mode with path: {os_home_dir}")
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

        # This one creates the whole superhero project from scratch:
        # handle with care!
        sph_user_ids = shp.generate_superhero_data(dbh)
        print(sph_user_ids)
        # Create some projects:
        project_dict = {
            "name": "Bat Cave Expenses",
            "description": "A common project of super heros",
            "currency_main": "USD",
            "currency_list": ["SEK", "EUR", "GBP"],
            "project_style": "ExpenseTracker",
            "project_staged": False,
            "project_activated": True,
            "project_store": {"month_start": 25}
        }
        p0_id = dbh.op_project_create(project_dict=project_dict,
                                      user_id=sph_user_ids["batman"])

        dbh.op_project_stage(project_id=p0_id,
                             users=[ {"user_id": sph_user_ids["batman"],
                                      "user_name": "batman"} ]
                             )

        # exit()
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








