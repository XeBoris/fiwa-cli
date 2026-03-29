"""Basic tests to verify pytest setup."""

import pytest


def test_pytest_works():
    """Verify pytest is working."""
    assert True


def test_basic_math():
    """Test basic arithmetic."""
    assert 1 + 1 == 2
    assert 2 * 3 == 6


def test_string_operations():
    """Test string operations."""
    test_str = "FiWa CLI"
    assert test_str.startswith("FiWa")
    assert test_str.endswith("CLI")
    assert len(test_str) == 8


@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (5, 5, 10),
    (10, -5, 5),
])
def test_addition_parametrized(a, b, expected):
    """Test addition with multiple inputs."""
    assert a + b == expected


def test_with_fixture(temp_dir):
    """Test using temp_dir fixture from conftest.py."""
    assert temp_dir.exists()
    assert temp_dir.is_dir()


def test_sample_config(sample_config):
    """Test using sample_config fixture from conftest.py."""
    assert "configuration" in sample_config
    assert "style" in sample_config
    assert sample_config["style"]["theme"] == "textual-light"
