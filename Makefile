.PHONY: help install uninstall clean build dev test run

# Default target - show help
help:
	@echo "FiWa CLI - Makefile Commands"
	@echo "============================"
	@echo "make install      - Install the package in production mode"
	@echo "make install-dev  - Install the package in editable/development mode"
	@echo "make uninstall    - Uninstall the package"
	@echo "make clean        - Remove build artifacts and cache files"
	@echo "make build        - Build the wheel package"
	@echo "make dev          - Install in editable mode (alias for install-dev)"
	@echo "make test         - Run tests (if available)"
	@echo "make run          - Run the app in development mode (without installing)"
	@echo ""
	@echo "Development workflow:"
	@echo "  1. make install-dev    # Install in editable mode"
	@echo "  2. make changes to code"
	@echo "  3. fiwa run --path /path/to/data --user username"
	@echo ""
	@echo "Alternative: Use ./run_dev.sh for running without installation"

# Install the package in production mode
install: clean
	@echo "Building and installing fiwa-cli..."
	pip install .
	@echo "Installation complete! Run 'fiwa --help' to get started."

# Install the package in editable/development mode
install-dev: clean
	@echo "Installing fiwa-cli in editable mode..."
	pip install -e .
	@echo "Development installation complete!"
	@echo "Changes to the code will be reflected immediately."

# Alias for install-dev
dev: install-dev

# Uninstall the package
uninstall:
	@echo "Uninstalling fiwa-cli..."
	pip uninstall -y fiwa-cli
	@echo "Uninstall complete!"

# Remove build artifacts and cache files
clean:
	@echo "Cleaning build artifacts and cache files..."
	rm -rf build/
	rm -rf dist/
	rm -rf src/*.egg-info
	rm -rf src/**/*.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	@echo "Cleanup complete!"

# Build the wheel package (without installing)
build: clean
	@echo "Building wheel package..."
	python -m build --wheel
	@echo "Build complete! Package is in dist/"

# Run tests (placeholder - implement when tests are available)
test:
	@echo "Running tests..."
	@if [ -d "tests" ]; then \
		python -m pytest tests/ -v; \
	else \
		echo "No tests directory found. Create tests/ and add test files."; \
	fi

# Run the app in development mode without installing
run-dev:
    #export ARGS='run --path /home/koenig/fiwa-cli-stage1 --user batman'
	@echo "Running FiWa CLI in development mode..."
	@echo "Usage: make run ARGS='run --path /path/to/data --user username'"
	@if [ -z "$(ARGS)" ]; then \
		PYTHONPATH=src python -m fiwa_cli.main --help; \
	else \
		PYTHONPATH=src python -m fiwa_cli.main $(ARGS); \
	fi

# Reinstall (useful when switching between dev and prod)
reinstall: uninstall install

# Reinstall in dev mode
reinstall-dev: uninstall install-dev
