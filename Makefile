.PHONY: help test test-server coverage lint format format-check install install-server clean pre-commit-install pre-commit-run

# Define servers
SERVERS := code-analysis efcore-analysis rag task-generator workspace-context session-memory

help:
	@echo "MCP Servers - Development Commands"
	@echo ""
	@echo "Testing:"
	@echo "  make test                Run all tests across all servers"
	@echo "  make test-server SERVER=rag  Run tests for specific server"
	@echo "  make coverage            Generate coverage reports for all servers"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint                Run ruff linter on all servers"
	@echo "  make format              Auto-format all Python code with ruff"
	@echo "  make format-check        Check formatting without making changes"
	@echo "  make pre-commit-install  Install pre-commit hooks"
	@echo "  make pre-commit-run      Run pre-commit on all files"
	@echo ""
	@echo "Setup:"
	@echo "  make install             Install dependencies for all servers"
	@echo "  make install-server SERVER=rag  Install dependencies for specific server"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean               Remove cache files, coverage reports, etc."
	@echo ""
	@echo "Available servers: $(SERVERS)"

test:
	@echo "Running tests for all servers..."
	@for server in $(SERVERS); do \
		echo "\n=== Testing $$server ==="; \
		cd $$server && python -m pytest tests/ -v || exit 1; \
		cd ..; \
	done
	@echo "\n✅ All tests passed!"

test-server:
ifndef SERVER
	$(error SERVER is not set. Usage: make test-server SERVER=rag)
endif
	@echo "Running tests for $(SERVER)..."
	@cd $(SERVER) && python -m pytest tests/ -v

coverage:
	@echo "Generating coverage reports for all servers..."
	@for server in $(SERVERS); do \
		echo "\n=== Coverage for $$server ==="; \
		cd $$server && python -m pytest tests/ --cov=src --cov-report=term --cov-report=html || exit 1; \
		cd ..; \
	done
	@echo "\n✅ Coverage reports generated!"
	@echo "View HTML reports in each server's htmlcov/ directory"

lint:
	@echo "Running ruff linter on all servers..."
	@ruff check .
	@echo "✅ Linting complete!"

format:
	@echo "Formatting all Python code..."
	@ruff format .
	@ruff check --fix .
	@echo "✅ Formatting complete!"

format-check:
	@echo "Checking code formatting..."
	@ruff format --check .
	@ruff check .

pre-commit-install:
	@echo "Installing pre-commit hooks..."
	@pip install pre-commit
	@pre-commit install
	@echo "✅ Pre-commit hooks installed!"
	@echo "Run 'make pre-commit-run' to test on all files"

pre-commit-run:
	@echo "Running pre-commit on all files..."
	@pre-commit run --all-files

install:
	@echo "Installing dependencies for all servers..."
	@for server in $(SERVERS); do \
		echo "\n=== Installing $$server ==="; \
		cd $$server; \
		if [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then \
			pip install -e .; \
		elif [ -f "requirements.txt" ]; then \
			pip install -r requirements.txt; \
		fi; \
		cd ..; \
	done
	@echo "\n=== Installing test dependencies ===";
	@pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-xdist
	@echo "\n✅ All dependencies installed!"

install-server:
ifndef SERVER
	$(error SERVER is not set. Usage: make install-server SERVER=rag)
endif
	@echo "Installing dependencies for $(SERVER)..."
	@cd $(SERVER) && \
		if [ -f "setup.py" ] || [ -f "pyproject.toml" ]; then \
			pip install -e .; \
		elif [ -f "requirements.txt" ]; then \
			pip install -r requirements.txt; \
		fi
	@echo "✅ $(SERVER) dependencies installed!"

clean:
	@echo "Cleaning cache files and build artifacts..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name ".coverage" -delete 2>/dev/null || true
	@find . -type f -name "coverage.xml" -delete 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"
