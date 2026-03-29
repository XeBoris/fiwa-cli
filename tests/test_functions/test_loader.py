"""Tests for loader.py functions."""

import pytest
import os
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from fiwa_cli.functions.loader import (
    load_dynamic_css,
    load_yaml_config,
    get_abs_path,
    identify_os
)


class TestLoadYamlConfig:
    """Test suite for load_yaml_config function."""
    
    def test_load_valid_yaml(self, temp_dir):
        """Test loading a valid YAML file."""
        config_path = temp_dir / "config.yml"
        config_data = {
            "configuration": {"host": "terminal"},
            "style": {"theme": "dark"}
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        result = load_yaml_config(str(config_path))
        
        assert result == config_data
        assert result["configuration"]["host"] == "terminal"
        assert result["style"]["theme"] == "dark"
    
    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        result = load_yaml_config("/nonexistent/path/config.yml")
        assert result == {}
    
    def test_load_empty_yaml(self, temp_dir):
        """Test loading an empty YAML file."""
        config_path = temp_dir / "empty.yml"
        config_path.write_text("")
        
        result = load_yaml_config(str(config_path))
        assert result == {}
    
    def test_load_complex_yaml(self, temp_dir):
        """Test loading complex nested YAML structure."""
        config_path = temp_dir / "complex.yml"
        config_data = {
            "configuration": {
                "host": "terminal",
                "model": "local",
                "path": "/data/fiwa"
            },
            "development": {
                "debug_mode": True,
                "stage": "prod"
            },
            "style": {
                "form": "handsome",
                "theme": "textual-light"
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        result = load_yaml_config(str(config_path))
        
        assert result["configuration"]["model"] == "local"
        assert result["development"]["debug_mode"] is True
        assert result["style"]["form"] == "handsome"


class TestIdentifyOs:
    """Test suite for identify_os function."""
    
    @patch('platform.system')
    def test_linux_detection(self, mock_platform):
        """Test Linux OS detection."""
        mock_platform.return_value = "Linux"
        
        os_name, config_dir = identify_os("fiwa-cli")
        
        assert os_name == "linux"
        assert "fiwa-cli" in config_dir or ".config" in config_dir
    
    @patch('platform.system')
    def test_windows_detection(self, mock_platform):
        """Test Windows OS detection."""
        mock_platform.return_value = "Windows"
        
        os_name, config_dir = identify_os("fiwa-cli")
        
        assert os_name == "windows"
        assert "fiwa-cli" in config_dir
    
    @patch('platform.system')
    def test_macos_detection(self, mock_platform):
        """Test macOS (Darwin) detection."""
        mock_platform.return_value = "Darwin"
        
        os_name, config_dir = identify_os("fiwa-cli")
        
        assert os_name == "darwin"
        assert "fiwa-cli" in config_dir
    
    @patch('platform.system')
    def test_unknown_os(self, mock_platform):
        """Test unknown OS detection."""
        mock_platform.return_value = "FreeBSD"
        
        result, path = identify_os("fiwa-cli")

        # identify_os returns only "unknown" string for unknown OS
        assert result == "unknown"


class TestGetAbsPath:
    """Test suite for get_abs_path function."""
    
    def test_get_abs_path_returns_string(self):
        """Test that get_abs_path returns a string."""
        result = get_abs_path()
        assert isinstance(result, str)
    
    def test_get_abs_path_is_absolute(self):
        """Test that returned path is absolute."""
        result = get_abs_path()
        assert os.path.isabs(result)
    
    def test_get_abs_path_points_to_package(self):
        """Test that path points to fiwa_cli package directory."""
        result = get_abs_path()
        # Should end with src/fiwa_cli/ or similar
        assert "fiwa_cli" in result or result.endswith("src")


class TestLoadDynamicCss:
    """Test suite for load_dynamic_css function."""
    
    def test_load_css_missing_app_state(self):
        """Test CSS loading when app_state is not available."""
        mock_widget = Mock()
        mock_widget.app.app_state = {}
        
        # Should handle gracefully without crashing
        load_dynamic_css(mock_widget, "test.tcss")
        
        # Verify it tried to log the issue
        mock_widget.app.log.assert_called()
    
    def test_load_css_file_not_found(self, temp_dir):
        """Test CSS loading when file doesn't exist."""
        mock_widget = Mock()
        mock_widget.app.app_state = {
            "css_form": "handsome",
            "abs_path": str(temp_dir)
        }
        
        # Should handle gracefully
        load_dynamic_css(mock_widget, "nonexistent.tcss")
        
        # Should log that file was not found
        assert mock_widget.app.log.called
    
    def test_load_css_success(self, temp_dir):
        """Test successful CSS loading."""
        # Create CSS directory structure
        css_dir = temp_dir / "css" / "handsome"
        css_dir.mkdir(parents=True)
        
        # Create CSS file
        css_file = css_dir / "test.tcss"
        css_content = "Widget { background: blue; }"
        css_file.write_text(css_content)
        
        # Setup mock widget
        mock_widget = Mock()
        mock_widget.app.app_state = {
            "css_form": "handsome",
            "abs_path": str(temp_dir)
        }
        mock_widget.app.stylesheet.add_source = Mock()
        
        # Load CSS
        load_dynamic_css(mock_widget, "test.tcss")
        
        # Verify CSS was added to stylesheet
        mock_widget.app.stylesheet.add_source.assert_called_once()
        call_args = mock_widget.app.stylesheet.add_source.call_args
        assert css_content in call_args[0][0]
        
        # Verify refresh was called
        mock_widget.refresh.assert_called_once_with(layout=True)
        
        # Verify success was logged
        mock_widget.app.log.assert_called()


class TestConfigIntegration:
    """Integration tests for config loading workflow."""
    
    def test_complete_config_structure(self, sample_config):
        """Test that sample_config has all required keys."""
        # Top-level keys
        assert "configuration" in sample_config
        assert "development" in sample_config
        assert "style" in sample_config
        assert "_data_directory" in sample_config
        assert "_abs_path" in sample_config
        assert "dbh" in sample_config
        
        # Configuration keys
        assert "host" in sample_config["configuration"]
        assert "model" in sample_config["configuration"]
        assert "path" in sample_config["configuration"]
        
        # Development keys
        assert "debug_mode" in sample_config["development"]
        assert "stage" in sample_config["development"]
        
        # Style keys
        assert "form" in sample_config["style"]
        assert "theme" in sample_config["style"]
    
    def test_config_values(self, sample_config):
        """Test that config values are sensible."""
        assert sample_config["configuration"]["host"] in ["terminal", "web"]
        assert sample_config["configuration"]["model"] in ["local", "api"]
        assert sample_config["style"]["form"] == "handsome"
        assert sample_config["style"]["theme"] in ["textual-light", "textual-dark"]
        assert isinstance(sample_config["development"]["debug_mode"], bool)
