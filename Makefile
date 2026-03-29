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
	@echo "make dev-run      - Run the app in development mode (without installing)"
	@echo "make reinstall    - Uninstall and reinstall the package"
	@echo "make reinstall-dev - Uninstall and reinstall in editable mode"
	@echo ""
	@echo "Running in Development Mode:"
	@echo "============================"
	@echo "Usage: make dev-run ARGS='<command> <options>'"
	@echo ""
	@echo "Examples:"
	@echo "  make dev-run ARGS='run --path /test/to/path --user batman'"
	@echo "  make dev-run ARGS='init --path /test/to/path'"
	@echo "  make dev-run                    # Shows help"
	@echo ""
	@echo "Available commands:"
	@echo "  run   - Run FiWa application"
	@echo "  init  - Initialize new FiWa database"
	@echo ""
	@echo "Common options for 'run' command:"
	@echo "  --path <path>   - Path to FiWa data directory (required)"
	@echo "  --user <name>   - Username to login as (required)"
	@echo ""
	@echo "Development workflow:"
	@echo "  1. make install-dev    # Install in editable mode"
	@echo "  2. make changes to code"
	@echo "  3. make dev-run ARGS='run --path /path/to/data --user username'"
	@echo ""
	@echo "Alternative without installation:"
	@echo "  make dev-run ARGS='run --path /path/to/data --user username'"
	@echo ""
	@echo "Documentation Commands:"
	@echo "======================="
	@echo "make docs-install - Install Sphinx and documentation dependencies"
	@echo "make docs-init    - Initialize Sphinx documentation structure"
	@echo "make docs-build   - Build HTML documentation"
	@echo "make docs-view    - Open documentation in browser"
	@echo "make docs-serve   - Serve documentation on http://localhost:8000"
	@echo "make docs-clean   - Remove documentation build files"
	@echo "make docs-rebuild - Clean and rebuild documentation"


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
# Usage: make dev-run ARGS="run --path /path/to/data --user username"
dev-run:
	@echo "Running FiWa CLI in development mode..."
	@if [ -z "$(ARGS)" ]; then \
		echo "Usage: make dev-run ARGS='run --path /path/to/data --user username'"; \
		PYTHONPATH=src python -m fiwa_cli.main --help; \
	else \
		PYTHONPATH=src python -m fiwa_cli.main $(ARGS); \
	fi

# Reinstall (useful when switching between dev and prod)
reinstall: uninstall install

# Reinstall in dev mode
reinstall-dev: uninstall install-dev





docs-install:
	@echo "Installing documentation dependencies..."
	pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints
	@echo "Documentation dependencies installed!"

docs-init:
	@echo "Initializing Sphinx documentation..."
	@if [ ! -d "docs" ]; then \
		mkdir -p docs; \
		cd docs && sphinx-quickstart -q -p "FiWa CLI" -a "Your Name" -v "0.1.0" --sep --ext-autodoc --ext-viewcode; \
		echo "Sphinx initialized in docs/"; \
	else \
		echo "docs/ directory already exists. Skipping initialization."; \
	fi

docs-apidoc:
	@echo "Generating API documentation..."
	sphinx-apidoc -f -o docs/source/api src/fiwa_cli
	@echo "API documentation generated!"

docs-build: docs-apidoc
	@echo "Building HTML documentation..."
	cd docs && make html
	@echo "Documentation built successfully!"
	@echo "Open docs/build/html/index.html in your browser."

docs-view:
	@echo "Opening documentation in browser..."
	@if command -v xdg-open > /dev/null; then \
		xdg-open docs/build/html/index.html; \
	elif command -v firefox > /dev/null; then \
		firefox docs/build/html/index.html; \
	elif command -v google-chrome > /dev/null; then \
		google-chrome docs/build/html/index.html; \
	else \
		echo "Please open docs/build/html/index.html manually"; \
	fi

docs-clean:
	@echo "Cleaning documentation build files..."
	@if [ -d "docs/build" ]; then \
		rm -rf docs/build; \
		echo "Documentation build files removed!"; \
	else \
		echo "No documentation build files to clean."; \
	fi

docs-serve:
	@echo "Starting local documentation server..."
	@cd docs/build/html && python -m http.server 8000

docs-rebuild: docs-clean docs-build
