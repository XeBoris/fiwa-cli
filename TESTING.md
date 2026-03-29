# FiWa CLI Testing Guide

## Quick Reference: Fixed Issues

### Issue 1: `identify_os` Return Value ✅ FIXED

**Problem**: `identify_os()` returns different values based on OS:
- Known OS (Linux, Windows, Darwin): Returns tuple `(os_name, config_dir)`
- Unknown OS: Returns string `"unknown"`

**Fix**: Updated test to handle single return value:
```python
# Before (WRONG):
os_name, config_dir = identify_os("fiwa-cli")  # ValueError for unknown OS

# After (CORRECT):
result = identify_os("fiwa-cli")
assert result == "unknown"  # Works for unknown OS
```

### Issue 2: Missing `project_style` in Mock Config ✅ FIXED

**Problem**: `MyApp.__init__()` expects project_info to include:
- `project_style` (required)
- `project_store` (required)
- `currency_main` (required)
- `currency_list` (required)

**Fix**: Updated `mock_config` fixture in test_main.py:
```python
"project_info": [
    {
        "project_id": 1,
        "project_name": "Test Project Alpha",
        "project_primary": True,
        "project_style": "ExpenseTracker",  # ✅ Added
        "project_store": {"month_start": 1},  # ✅ Added
        "currency_main": "USD",  # ✅ Added
        "currency_list": json.dumps(["EUR", "GBP"])  # ✅ Added
    }
]
```

## Running Tests

### Install Test Dependencies

```bash
make test-install
```

This installs:
- pytest
- pytest-asyncio
- pytest-cov
- pytest-mock

### Run All Tests

```bash
make test
```

Expected output:
```
Running tests...
======================== test session starts =========================
collected 30+ items

tests/test_basic.py::test_pytest_works PASSED                  [  3%]
tests/test_basic.py::test_basic_math PASSED                    [  6%]
tests/test_functions/test_loader.py::TestLoadYamlConfig::test_load_valid_yaml PASSED  [ 10%]
...
======================== 30 passed in 2.50s ==========================
```

### Run Specific Tests

```bash
# Run single test file
PYTHONPATH=src pytest tests/test_functions/test_loader.py

# Run single test class
PYTHONPATH=src pytest tests/test_functions/test_loader.py::TestLoadYamlConfig

# Run single test function
PYTHONPATH=src pytest tests/test_functions/test_loader.py::TestLoadYamlConfig::test_load_valid_yaml

# Run with verbose output
PYTHONPATH=src pytest -v

# Run and show print statements
PYTHONPATH=src pytest -v -s
```

## Available Fixtures (from conftest.py)

All fixtures are available to all tests automatically:

### 1. `temp_dir`
Temporary directory that auto-cleans after test:
```python
def test_file_operations(temp_dir):
    test_file = temp_dir / "test.txt"
    test_file.write_text("data")
    assert test_file.exists()
    # Auto-deleted after test
```

### 2. `temp_db_path`
Path to temporary database file:
```python
def test_database(temp_db_path):
    dbh = SQLLiteHandler(db_path=str(temp_db_path))
    # Use real database
```

### 3. `mock_dbh` ✅ NEW
Mock database handler with pre-configured methods:
```python
def test_without_db(mock_dbh):
    # Customize mock behavior
    mock_dbh.op_user_get_all.return_value = [
        {"user_id": 1, "username": "batman"}
    ]
    
    # Use mock
    users = mock_dbh.op_user_get_all()
    assert len(users) == 1
```

Pre-configured mocks:
- `op_user_get_all()` → `[]`
- `op_user_get_info()` → `{}`
- `op_project_get_info()` → `[]`
- `op_label_get_all()` → `[]`
- `op_item_get_by_user()` → `[]`
- `op_user_login()` → `None`
- `op_user_logout()` → `True`
- `op_total_number_of_users()` → `0`

### 4. `real_dbh` ✅ NEW
Real SQLite handler with schema initialized:
```python
def test_user_crud(real_dbh, sample_user_data):
    # Create user in real database
    user_id = real_dbh.op_user_create(sample_user_data)
    assert user_id > 0
    
    # Query user
    user = real_dbh.op_user_get_info(user_id)
    assert user["username"] == "testuser"
```

Uses in-memory database (:memory:) for speed.

### 5. `sample_config` ✅ ENHANCED
Complete configuration matching loader.py structure:
```python
def test_config(sample_config):
    assert sample_config["dbh"] is not None  # Mock dbh
    assert sample_config["_abs_path"] == "/tmp/fiwa-cli"
    assert sample_config["configuration"]["model"] == "local"
    assert sample_config["style"]["theme"] == "textual-light"
```

Complete structure:
```python
{
    "configuration": {"host": "terminal", "model": "local", "path": "/tmp/fiwa-test"},
    "development": {"debug_mode": True, "stage": "test"},
    "style": {"form": "handsome", "theme": "textual-light"},
    "_data_directory": "/tmp/fiwa-test",
    "_abs_path": "/tmp/fiwa-cli",
    "dbh": mock_dbh  # Mock database handler
}
```

### 6. `mock_app_state`
Mock app_state with logged-in user:
```python
def test_screen(mock_app_state):
    assert mock_app_state["user_name"] == "TestUser"
    assert mock_app_state["is_logged_in"] == True
    assert mock_app_state["project_id"] == 1
```

### 7. `sample_user_data`
User creation data:
```python
def test_user_creation(real_dbh, sample_user_data):
    user_id = real_dbh.op_user_create(sample_user_data)
    assert user_id > 0
```

### 8. `sample_project_data`
Project creation data with all required fields:
```python
def test_project_creation(real_dbh, sample_project_data):
    project_id = real_dbh.op_project_create(sample_project_data, user_id=1)
    assert project_id > 0
```

Includes:
- `project_name`
- `description`
- `currency_main`
- `currency_list` (JSON string)
- `project_store` (JSON string with month_start)
- `project_style` ("ExpenseTracker")

### 9. `sample_item_data`
Transaction/expense data:
```python
def test_item_creation(real_dbh, sample_item_data):
    item_id = real_dbh.op_item_create(sample_item_data)
    assert item_id > 0
```

## Test Files Overview

### tests/test_basic.py (7 tests)
Sanity tests to verify pytest works:
- test_pytest_works
- test_basic_math
- test_string_operations
- test_addition_parametrized (3 parameterized cases)
- test_with_fixture (uses temp_dir)
- test_sample_config (uses sample_config)

### tests/test_functions/test_loader.py (18 tests)
Comprehensive loader.py function tests:

**TestLoadYamlConfig** (4 tests):
- Valid YAML loading
- Nonexistent file handling
- Empty file handling
- Complex nested YAML

**TestIdentifyOs** (4 tests):
- Linux detection
- Windows detection
- macOS detection
- Unknown OS detection ✅ FIXED

**TestGetAbsPath** (3 tests):
- Returns string
- Is absolute path
- Points to package

**TestLoadDynamicCss** (3 tests):
- Missing app_state handling
- File not found handling
- Successful CSS loading

**TestConfigIntegration** (2 tests):
- Complete config structure
- Config values validation

### tests/test_main.py (3 tests)
Main application tests:
- test_app_initialization ✅ FIXED
- test_app_compose_correctly
- test_app_bindings

### tests/test_compute_time.py (existing)
Time calculation tests (using unittest.TestCase)

## Common Test Patterns

### Testing with Mock Database

Fast tests without database:
```python
def test_my_function(mock_dbh):
    # Configure mock
    mock_dbh.op_user_get_all.return_value = [
        {"user_id": 1, "username": "batman"},
        {"user_id": 2, "username": "superman"}
    ]
    
    # Test your code
    result = my_function(mock_dbh)
    
    # Verify mock was called
    mock_dbh.op_user_get_all.assert_called_once()
    
    # Verify result
    assert len(result) == 2
```

### Testing with Real Database

Comprehensive tests with actual database:
```python
def test_database_operations(real_dbh, sample_user_data, sample_project_data):
    # Create user
    user_id = real_dbh.op_user_create(sample_user_data)
    assert user_id > 0
    
    # Create project
    project_id = real_dbh.op_project_create(sample_project_data, user_id)
    assert project_id > 0
    
    # Query data
    projects = real_dbh.op_project_get_info(user_id)
    assert len(projects) > 0
    assert projects[0]["project_name"] == "Test Project"
```

### Testing File Operations

```python
def test_file_creation(temp_dir):
    test_file = temp_dir / "test.yml"
    
    # Write data
    import yaml
    data = {"key": "value"}
    with open(test_file, 'w') as f:
        yaml.dump(data, f)
    
    # Read and verify
    assert test_file.exists()
    with open(test_file) as f:
        loaded = yaml.safe_load(f)
    assert loaded == data
```

### Parametrized Tests

Test multiple inputs efficiently:
```python
@pytest.mark.parametrize("os_type,expected_dir", [
    ("linux", ".config/fiwa-cli"),
    ("windows", "fiwa-cli"),
    ("darwin", "Library/Application Support/fiwa-cli"),
])
def test_os_paths(os_type, expected_dir):
    # Test with different OS types
    pass
```

### Mocking External Calls

```python
@patch('fiwa_cli.functions.loader.load_yaml_config')
def test_with_mock(mock_load_yaml):
    mock_load_yaml.return_value = {"key": "value"}
    
    # Call code that uses load_yaml_config
    result = my_function()
    
    # Verify mock was called
    mock_load_yaml.assert_called_once()
```

## Coverage Reports

Run tests with coverage:
```bash
make test-coverage
```

View HTML report:
```bash
firefox htmlcov/index.html
```

## Debugging Failed Tests

### Verbose Output
```bash
PYTHONPATH=src pytest -v -s
```

### Stop at First Failure
```bash
PYTHONPATH=src pytest -x
```

### Show Full Traceback
```bash
PYTHONPATH=src pytest --tb=long
```

### Run Last Failed Tests Only
```bash
PYTHONPATH=src pytest --lf
```

### Debug with pdb
```python
def test_something():
    import pdb; pdb.set_trace()  # Breakpoint
    result = my_function()
    assert result == expected
```

## Common Errors and Solutions

### ModuleNotFoundError: No module named 'fiwa_cli'

**Solution**: Ensure PYTHONPATH=src is set:
```bash
PYTHONPATH=src pytest
# or use make test (automatically sets PYTHONPATH)
make test
```

### KeyError in Mock Config

**Solution**: Check MyApp expects these keys in project_info:
- project_style ✅
- project_store ✅
- currency_main ✅
- currency_list ✅

Updated mock_config fixture includes all required fields.

### ValueError: too many values to unpack

**Solution**: Check function return value count:
- `identify_os()` returns 2 values for known OS
- `identify_os()` returns 1 value ("unknown") for unknown OS

Use appropriate unpacking for each case.

### Fixture Not Found

**Solution**: Ensure conftest.py is in tests/ directory:
```bash
ls tests/conftest.py  # Should exist
```

All fixtures in conftest.py are automatically available.

## Next Steps: Expand Test Coverage

### Create Component Tests

```bash
mkdir -p tests/test_components
touch tests/test_components/__init__.py

cat > tests/test_components/test_header.py << 'EOF'
"""Tests for FiwaHeader component."""
import pytest
from fiwa_cli.components import FiwaHeader

def test_header_creation():
    header = FiwaHeader(user="batman")
    assert header.user == "batman"

def test_header_reactive():
    header = FiwaHeader()
    header.user = "superman"
    assert header.user == "superman"
EOF
```

### Create Screen Tests

```bash
mkdir -p tests/test_screens
touch tests/test_screens/__init__.py

cat > tests/test_screens/test_base.py << 'EOF'
"""Tests for base screen classes."""
import pytest
from fiwa_cli.screens.base import ReactiveScreen

def test_reactive_screen_exists():
    assert ReactiveScreen is not None
EOF
```

### Create Database Tests

```bash
cat > tests/test_functions/test_handler_sqlite.py << 'EOF'
"""Tests for SQLLiteHandler."""
import pytest
from fiwa_cli.functions.handler_sqllite import SQLLiteHandler

def test_hash_password():
    hashed = SQLLiteHandler.hash_password("test123", "salt")
    assert len(hashed) == 64  # SHA-256 hex

def test_user_crud(real_dbh, sample_user_data):
    # Create
    user_id = real_dbh.op_user_create(sample_user_data)
    assert user_id > 0
    
    # Read
    user = real_dbh.op_user_get_info(user_id)
    assert user["username"] == sample_user_data["username"]
EOF
```

## Test Coverage Goals

Target coverage levels:
- **Critical modules** (handler_sqllite, loader): 80%+
- **Business logic** (project_composer): 70%+
- **Components**: 60%+
- **Screens**: 50%+ (harder to test UI)

Current coverage:
```bash
make test-coverage
# Check htmlcov/index.html for detailed breakdown
```

## CI/CD Integration

Add to `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run tests
        run: PYTHONPATH=src pytest --cov=src/fiwa_cli --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Summary

✅ **Fixed Issues**:
1. test_unknown_os: Now handles single return value
2. test_app_initialization: Mock config now includes all required fields

✅ **Enhanced Fixtures**:
- mock_dbh: Pre-configured mock database
- real_dbh: In-memory database with schema
- sample_config: Complete config structure
- All project fields included (project_style, project_store, currency_*)

✅ **Test Files**:
- tests/test_basic.py: 7 sanity tests
- tests/test_functions/test_loader.py: 18 comprehensive tests
- tests/test_main.py: 3 app tests (fixed)
- tests/test_compute_time.py: Time calculation tests

**Run `make test` to verify all tests pass!**
