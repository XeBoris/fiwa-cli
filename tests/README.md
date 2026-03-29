# FiWa CLI Tests

This directory contains all tests for the FiWa CLI application.

## Running Tests

### Quick Start

```bash
# Install test dependencies
make test-install

# Run all tests
make test

# Run with coverage
make test-coverage
```

### Direct pytest Commands

```bash
# Run all tests
PYTHONPATH=src pytest

# Run specific test file
PYTHONPATH=src pytest tests/test_basic.py

# Run specific test function
PYTHONPATH=src pytest tests/test_basic.py::test_pytest_works

# Run with verbose output
PYTHONPATH=src pytest -v

# Run with coverage
PYTHONPATH=src pytest --cov=src/fiwa_cli --cov-report=html

# Run and stop at first failure
PYTHONPATH=src pytest -x

# Run only failed tests from last run
PYTHONPATH=src pytest --lf
```

## Test Structure

```
tests/
├── __init__.py              # Makes tests a package
├── conftest.py              # Shared fixtures and configuration
├── test_basic.py            # Basic sanity tests
├── test_main.py             # Main application tests
├── test_compute_time.py     # Time computation tests
├── test_functions/          # Function module tests (future)
├── test_components/         # Component tests (future)
└── test_screens/            # Screen tests (future)
```

## Available Fixtures

Fixtures are defined in `conftest.py` and available to all tests:

### temp_dir
Provides a temporary directory for file operations:
```python
def test_file_operations(temp_dir):
    test_file = temp_dir / "test.db"
    test_file.write_text("test data")
    assert test_file.exists()
```

### temp_db_path
Provides a temporary database path:
```python
def test_database(temp_db_path):
    from fiwa_cli.functions.handler_sqllite import SQLLiteHandler
    dbh = SQLLiteHandler(db_path=str(temp_db_path))
    # Use dbh for testing
```

### sample_config
Provides sample configuration dictionary:
```python
def test_config(sample_config):
    assert sample_config["style"]["theme"] == "textual-light"
```

### mock_app_state
Provides mock app_state dictionary:
```python
def test_app_state(mock_app_state):
    assert mock_app_state["user_name"] == "TestUser"
    assert mock_app_state["is_logged_in"] == True
```

### sample_user_data
Provides sample user data for testing:
```python
def test_user(sample_user_data):
    assert sample_user_data["username"] == "testuser"
```

### sample_project_data
Provides sample project data:
```python
def test_project(sample_project_data):
    assert sample_project_data["project_name"] == "Test Project"
```

### sample_item_data
Provides sample item/transaction data:
```python
def test_item(sample_item_data):
    assert sample_item_data["name"] == "Test Item"
```

## Writing Tests

### Test File Naming

- Files must start with `test_`
- Example: `test_my_module.py`

### Test Function Naming

- Functions must start with `test_`
- Example: `def test_my_function():`

### Test Class Naming

- Classes must start with `Test`
- Example: `class TestMyClass:`

### Example Test

```python
"""Tests for my module."""

import pytest
from fiwa_cli.functions.my_module import my_function


def test_my_function():
    """Test my_function with valid input."""
    result = my_function("test")
    assert result == "expected_value"


def test_my_function_with_fixture(temp_dir):
    """Test my_function using a fixture."""
    # Use temp_dir fixture
    test_file = temp_dir / "test.txt"
    result = my_function(test_file)
    assert result is not None


@pytest.mark.parametrize("input,expected", [
    ("a", "A"),
    ("b", "B"),
    ("c", "C"),
])
def test_my_function_parametrized(input, expected):
    """Test with multiple inputs."""
    result = my_function(input)
    assert result == expected


class TestMyClass:
    """Test suite for MyClass."""
    
    def test_initialization(self):
        """Test class initialization."""
        obj = MyClass()
        assert obj is not None
    
    def test_method(self):
        """Test a specific method."""
        obj = MyClass()
        result = obj.my_method()
        assert result == "expected"
```

## Testing Textual Components

Testing Textual applications requires special setup. Use the Textual testing utilities:

```python
"""Tests for Textual components."""

import pytest
from textual.pilot import Pilot


async def test_app_basics():
    """Test basic app functionality."""
    from fiwa_cli.main import MyApp
    
    app = MyApp()
    async with app.run_test() as pilot:
        # App is running in test mode
        assert app.title == "FiWa - Financial Tracker"


async def test_widget_interaction():
    """Test widget interaction."""
    from fiwa_cli.main import MyApp
    
    app = MyApp()
    async with app.run_test() as pilot:
        # Simulate user interactions
        await pilot.press("m")  # Press M key
        # Assert menu opened
```

## Coverage Reports

After running `make test-coverage`, view the coverage report:

```bash
# Open HTML report in browser
firefox htmlcov/index.html

# Or view terminal output
PYTHONPATH=src pytest --cov=src/fiwa_cli --cov-report=term
```

## Continuous Integration

For CI/CD pipelines, use:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: PYTHONPATH=src pytest --cov=src/fiwa_cli
```

## Troubleshooting

### ModuleNotFoundError

If you see `ModuleNotFoundError: No module named 'fiwa_cli'`:
- Ensure PYTHONPATH=src is set
- Check pytest.ini has `pythonpath = src`
- Verify imports use `from fiwa_cli.*` not `from functions.*`

### Pytest Not Found

If you see `No module named pytest`:
```bash
make test-install
# or
pip install pytest pytest-asyncio pytest-cov
```

### Import Errors in Tests

All imports must use the package name:
- ✅ `from fiwa_cli.functions.loader import load_yaml_config`
- ✅ `from fiwa_cli.main import MyApp`
- ✅ `from fiwa_cli.components import FiwaHeader`
- ❌ `from functions.loader import ...`
- ❌ `from main import MyApp`

### Tests Not Discovered

Ensure:
- Test files start with `test_`
- Test functions start with `test_`
- Test files are in `tests/` directory
- `__init__.py` exists in `tests/`

## Best Practices

1. **One test per behavior**: Each test should verify one specific behavior
2. **Use fixtures**: Reuse common setup with fixtures in conftest.py
3. **Descriptive names**: Test names should describe what they test
4. **Arrange-Act-Assert**: Structure tests in three phases
5. **Mock external dependencies**: Use pytest-mock for external calls
6. **Test edge cases**: Include boundary conditions and error cases
7. **Keep tests fast**: Use in-memory databases, mock I/O
8. **Independent tests**: Tests should not depend on each other

## Next Steps

To expand test coverage, create:

```bash
# Function tests
mkdir -p tests/test_functions
touch tests/test_functions/__init__.py
touch tests/test_functions/test_loader.py
touch tests/test_functions/test_logout_util.py

# Component tests
mkdir -p tests/test_components
touch tests/test_components/__init__.py
touch tests/test_components/test_header.py

# Screen tests
mkdir -p tests/test_screens
touch tests/test_screens/__init__.py
touch tests/test_screens/test_base.py
```

Then add tests for each module!
