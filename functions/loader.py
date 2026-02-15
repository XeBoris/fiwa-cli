from typing import Dict, Any
import os
import yaml
import time

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

def setup_fiwa(abs_path:str = "", config: Dict[str, Any] = {}) -> None:
    """
    Set up the FiWa application with the given configuration.

    Args:
        config (Dict[str, Any]): Configuration dictionary for FiWa.
    """
    # Here you can add any setup logic needed before starting the app
    # For example, you could initialize logging, set environment variables, etc.
    print("FiWa configuration loaded:")

    opp_mode = config.get("configuration", {}).get("host", "terminal")
    opp_path = config.get("configuration", {}).get("path", "<local>")
    opp_model = config.get("configuration", {}).get("model", "terminal")

    dev_config = config.get("development", None)

    if opp_model == "local" and dev_config is None:
        # assume that we run 100% locally with all data stored in local files
        # therefore, we use a local path for data storage and a sqlite database.
        print(f"Running in local mode with path: {opp_path}")

        from functions.handler import Handler

        os_home_dir = ""
        os_folder = "fiwa-cli"  # No leading dot for Windows

        os_system, os_home_dir = identify_os(os_folder=os_folder)

        # Create directory if it doesn't exist
        os.makedirs(os_home_dir, exist_ok=True)

        print(f"Data directory: {os_home_dir}")

        # check if a sqlite file "data.sqlite" exists in the data directory, if not create it and initialize the database
        sqlite_path = os.path.join(os_home_dir, "data.sqlite")

        h = Handler(method="sqlite")
        dbh = h.load()
        dbh.set_path(sqlite_path)
        dbh.initialize_database(schema_path=os.path.join(abs_path, "database", "schema.sql"))

        # write config dictionary to a yaml file in the data directory for later use
        config_path = os.path.join(os_home_dir, "config.yml")
        with open(config_path, "w", encoding="utf-8") as handle:
            yaml.safe_dump(config, handle)

        # Store in config for later use
        config["data_directory"] = os_home_dir
        config["dbh"] = dbh
        return config

    elif opp_model == "api" and dev_config is None:
        # assume that you run this app with a remote API.
        pass

    elif dev_config is not None:

        # assume that you run this app in development mode with a local API server.
        print("dev")

        os_folder = "fiwa-cli-dev"  # No leading dot for Windows
        os_system, os_home_dir = identify_os(os_folder=os_folder)

        print(f"Data directory: {os_home_dir}")

        # Create directory if it doesn't exist. Delete previous content for clean dev environment:
        import shutil
        if os.path.exists(os_home_dir):
            shutil.rmtree(os_home_dir)
        os.makedirs(os_home_dir, exist_ok=True)

        # check if a sqlite file "data.sqlite" exists in the data directory, if not create it and initialize the database
        sqlite_path = os.path.join(os_home_dir, "data.sqlite")

        # write config dictionary to a yaml file in the data directory for later use
        dev_config_path = os.path.join(os_home_dir, "dev_config.yml")
        with open(dev_config_path, "w", encoding="utf-8") as handle:
            yaml.safe_dump(dev_config, handle)

        # we setup the local database handler
        from functions.handler import Handler
        h = Handler(method="sqlite")
        dbh = h.load()
        dbh.set_path(sqlite_path)
        dbh.initialize_database(schema_path=os.path.join(abs_path, "database", "schema.sql"))

        from .db_faker import faker_users, faker_user_login, faker_projects, faker_labels

        faker_users(dbh=dbh, num_users=5)


        faker_user_login("user1", "u1", dbh=dbh)

        project_ids = faker_projects(dbh=dbh)

        faker_labels(dbh=dbh, project_ids=project_ids)

        r = dbh.op_get_user_sessions()
        print(r)

        time.sleep(0.5)
        # Store in config for later use
        config["data_directory"] = os_home_dir
        config["dbh"] = dbh
        return config