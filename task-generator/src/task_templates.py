"""Task templates for common development patterns."""

from typing import Any


class TaskTemplate:
    """Base class for task templates."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def generate_tasks(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate task breakdown based on template.

        Args:
            context: Project context (description, constraints, etc.)

        Returns:
            List of task dictionaries
        """
        raise NotImplementedError


class MCPServerTemplate(TaskTemplate):
    """Template for building MCP servers."""

    def __init__(self):
        super().__init__(
            name="mcp_server",
            description="Build a new MCP server with core logic, tools, tests, and docs",
        )

    def generate_tasks(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate MCP server tasks."""
        description = context.get("description", "")
        include_tests = context.get("constraints", {}).get("include_tests", True)
        include_docs = context.get("constraints", {}).get("include_docs", True)
        server_name = context.get("server_name", "new-server")

        # Extract features/tools from description (simplified)
        estimated_tools = self._estimate_tool_count(description)

        tasks = []
        task_id = 1

        # Task 1: Core logic module
        tasks.append(
            {
                "id": task_id,
                "title": f"Create core {server_name} logic",
                "description": f"Implement core analysis/processing logic for {server_name}",
                "estimated_loc": 300,
                "dependencies": [],
                "files_to_create": [
                    f"{server_name}/src/__init__.py",
                    f'{server_name}/src/{server_name.replace("-", "_")}_core.py',
                ],
                "type": "core_logic",
            }
        )
        task_id += 1

        # Task 2: MCP server with tools
        tasks.append(
            {
                "id": task_id,
                "title": f"Build MCP server with {estimated_tools} tools",
                "description": f"Create MCP server exposing {estimated_tools} tools for {server_name}",
                "estimated_loc": 200 + (estimated_tools * 30),
                "dependencies": [1],
                "files_to_create": [f'{server_name}/src/{server_name.replace("-", "_")}_server.py'],
                "type": "mcp_server",
            }
        )
        task_id += 1

        # Task 3: Tests
        if include_tests:
            tasks.append(
                {
                    "id": task_id,
                    "title": "Write comprehensive test suite",
                    "description": f"Create unit tests for {server_name} core and integration tests",
                    "estimated_loc": 250,
                    "dependencies": [1, 2],
                    "files_to_create": [
                        f'{server_name}/tests/test_{server_name.replace("-", "_")}_core.py',
                        f"{server_name}/tests/test_integration.py",
                    ],
                    "type": "tests",
                }
            )
            task_id += 1

        # Task 4: Documentation
        if include_docs:
            tasks.append(
                {
                    "id": task_id,
                    "title": "Create documentation",
                    "description": "Write README with features, usage, and examples",
                    "estimated_loc": 150,
                    "dependencies": [2],
                    "files_to_create": [
                        f"{server_name}/README.md",
                        f"{server_name}/requirements.txt",
                    ],
                    "type": "documentation",
                }
            )
            task_id += 1

        return tasks

    def _estimate_tool_count(self, description: str) -> int:
        """Estimate number of MCP tools based on description."""
        # Simple heuristic: count action words and features mentioned
        keywords = ["analyze", "generate", "get", "search", "find", "create", "update", "delete"]
        count = sum(1 for keyword in keywords if keyword in description.lower())
        return max(3, min(count, 8))  # Between 3-8 tools


class APIIntegrationTemplate(TaskTemplate):
    """Template for API integration projects."""

    def __init__(self):
        super().__init__(
            name="api_integration",
            description="Integrate with external API - client, models, error handling",
        )

    def generate_tasks(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate API integration tasks."""
        api_name = context.get("api_name", "external-api")
        include_tests = context.get("constraints", {}).get("include_tests", True)

        tasks = []

        # Task 1: API client
        tasks.append(
            {
                "id": 1,
                "title": f"Create {api_name} API client",
                "description": "HTTP client with authentication and request handling",
                "estimated_loc": 200,
                "dependencies": [],
                "files_to_create": [f"src/{api_name}_client.py"],
                "type": "api_client",
            }
        )

        # Task 2: Data models
        tasks.append(
            {
                "id": 2,
                "title": "Define data models",
                "description": "Request/response models with validation",
                "estimated_loc": 150,
                "dependencies": [],
                "files_to_create": [f"src/{api_name}_models.py"],
                "type": "models",
            }
        )

        # Task 3: Error handling
        tasks.append(
            {
                "id": 3,
                "title": "Implement error handling",
                "description": "Retry logic, rate limiting, custom exceptions",
                "estimated_loc": 100,
                "dependencies": [1],
                "files_to_create": [f"src/{api_name}_errors.py"],
                "type": "error_handling",
            }
        )

        # Task 4: Tests
        if include_tests:
            tasks.append(
                {
                    "id": 4,
                    "title": "Write integration tests",
                    "description": "Mock API responses, test error cases",
                    "estimated_loc": 200,
                    "dependencies": [1, 2, 3],
                    "files_to_create": [f"tests/test_{api_name}_client.py"],
                    "type": "tests",
                }
            )

        return tasks


class DatabaseTemplate(TaskTemplate):
    """Template for database/storage projects."""

    def __init__(self):
        super().__init__(
            name="database", description="Database schema, migrations, and data access layer"
        )

    def generate_tasks(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate database tasks."""
        db_type = context.get("db_type", "sqlite")
        include_tests = context.get("constraints", {}).get("include_tests", True)

        tasks = []

        # Task 1: Schema definition
        tasks.append(
            {
                "id": 1,
                "title": f"Define {db_type} schema",
                "description": "Table definitions, indexes, relationships",
                "estimated_loc": 150,
                "dependencies": [],
                "files_to_create": ["src/schema.py"],
                "type": "schema",
            }
        )

        # Task 2: Data access layer
        tasks.append(
            {
                "id": 2,
                "title": "Create data access layer",
                "description": "CRUD operations, queries, transactions",
                "estimated_loc": 250,
                "dependencies": [1],
                "files_to_create": ["src/db_access.py"],
                "type": "data_access",
            }
        )

        # Task 3: Migrations
        tasks.append(
            {
                "id": 3,
                "title": "Implement migration system",
                "description": "Version control for schema changes",
                "estimated_loc": 100,
                "dependencies": [1],
                "files_to_create": ["src/migrations.py"],
                "type": "migrations",
            }
        )

        # Task 4: Tests
        if include_tests:
            tasks.append(
                {
                    "id": 4,
                    "title": "Write database tests",
                    "description": "Test queries, transactions, migrations",
                    "estimated_loc": 200,
                    "dependencies": [1, 2, 3],
                    "files_to_create": ["tests/test_db_access.py"],
                    "type": "tests",
                }
            )

        return tasks


class TestingInfrastructureTemplate(TaskTemplate):
    """Template for testing infrastructure."""

    def __init__(self):
        super().__init__(
            name="testing", description="Testing framework, fixtures, and CI integration"
        )

    def generate_tasks(self, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate testing infrastructure tasks."""
        return [
            {
                "id": 1,
                "title": "Set up pytest configuration",
                "description": "Configure pytest with plugins, coverage, markers",
                "estimated_loc": 50,
                "dependencies": [],
                "files_to_create": ["pytest.ini", "conftest.py"],
                "type": "configuration",
            },
            {
                "id": 2,
                "title": "Create test fixtures",
                "description": "Reusable fixtures for common test scenarios",
                "estimated_loc": 150,
                "dependencies": [1],
                "files_to_create": ["tests/fixtures.py"],
                "type": "fixtures",
            },
            {
                "id": 3,
                "title": "Add CI/CD integration",
                "description": "GitHub Actions workflow for automated testing",
                "estimated_loc": 100,
                "dependencies": [1],
                "files_to_create": [".github/workflows/test.yml"],
                "type": "ci_cd",
            },
        ]


# Template registry
TEMPLATES: dict[str, TaskTemplate] = {
    "mcp_server": MCPServerTemplate(),
    "api_integration": APIIntegrationTemplate(),
    "database": DatabaseTemplate(),
    "testing": TestingInfrastructureTemplate(),
}


def get_template(name: str) -> TaskTemplate:
    """Get template by name.

    Args:
        name: Template name

    Returns:
        TaskTemplate instance

    Raises:
        KeyError: If template not found
    """
    return TEMPLATES[name]


def list_templates() -> list[dict[str, str]]:
    """List all available templates.

    Returns:
        List of template info dicts
    """
    return [
        {"name": name, "description": template.description} for name, template in TEMPLATES.items()
    ]
