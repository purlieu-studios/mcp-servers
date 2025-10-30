"""Tests for task generator module."""

import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.task_generator import TaskGenerator

pytestmark = pytest.mark.unit


class TestTaskGenerator:
    """Test TaskGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create TaskGenerator instance."""
        return TaskGenerator()

    def test_initialization(self, generator):
        """Test generator initialization."""
        assert generator.default_max_loc == 500
        assert generator.default_include_tests is True
        assert generator.default_include_docs is True

    def test_generate_task_plan_with_mcp_template(self, generator):
        """Test generating task plan with MCP server template."""
        plan = generator.generate_task_plan(
            description="Build a git operations server with commit analysis and branch recommendations",
            template="mcp_server",
        )

        assert "project" in plan
        assert "tasks" in plan
        assert plan["template"] == "mcp_server"
        assert len(plan["tasks"]) > 0
        assert plan["total_estimated_loc"] > 0

    def test_generate_task_plan_custom(self, generator):
        """Test generating custom task plan."""
        plan = generator.generate_task_plan(
            description="Create a monitoring system with real-time alerts", template="custom"
        )

        assert plan["template"] == "custom"
        assert len(plan["tasks"]) >= 2
        # Should have core logic task
        assert any(task["type"] == "core_logic" for task in plan["tasks"])

    def test_generate_task_plan_without_tests(self, generator):
        """Test generating plan without tests."""
        plan = generator.generate_task_plan(
            description="Build a simple utility",
            template="custom",
            constraints={"include_tests": False},
        )

        # Should not have test tasks
        assert not any(task.get("type") == "tests" for task in plan["tasks"])

    def test_generate_task_plan_without_docs(self, generator):
        """Test generating plan without documentation."""
        plan = generator.generate_task_plan(
            description="Build a tool", template="custom", constraints={"include_docs": False}
        )

        # Should not have documentation tasks
        assert not any(task.get("type") == "documentation" for task in plan["tasks"])

    def test_estimate_complexity_simple(self, generator):
        """Test complexity estimation for simple project."""
        estimates = generator.estimate_complexity("Create a simple parser for JSON files")

        assert "feature_count" in estimates
        assert "estimated_loc" in estimates
        assert "estimated_hours" in estimates
        assert "complexity_level" in estimates
        assert estimates["complexity_level"] in ["low", "medium", "high"]

    def test_estimate_complexity_complex(self, generator):
        """Test complexity estimation for complex project."""
        estimates = generator.estimate_complexity(
            "Build async real-time database with cache monitoring and API integration"
        )

        assert estimates["feature_count"] >= 1  # At least 1 feature detected
        assert estimates["complexity_indicators"]["async"] is True
        assert estimates["complexity_indicators"]["database"] is True
        assert estimates["complexity_indicators"]["api"] is True
        assert estimates["complexity_indicators"]["caching"] is True
        assert estimates["complexity_level"] in ["medium", "high"]

    def test_refine_task_plan_remove_docs(self, generator):
        """Test refining plan by removing documentation."""
        original = generator.generate_task_plan("Build a tool", template="custom")

        refined = generator.refine_task_plan(original, {"remove_task_types": ["documentation"]})

        # Documentation tasks should be removed
        assert not any(t.get("type") == "documentation" for t in refined["tasks"])
        assert len(refined["tasks"]) < len(original["tasks"])

    def test_refine_task_plan_split_task(self, generator):
        """Test splitting a task into multiple parts."""
        original = generator.generate_task_plan("Build a system", template="custom")

        # Split task 1 into 2 parts
        refined = generator.refine_task_plan(original, {"split_task_id": 1, "split_count": 2})

        # Should have more tasks
        assert len(refined["tasks"]) == len(original["tasks"]) + 1

    def test_list_available_templates(self, generator):
        """Test listing templates."""
        templates = generator.list_available_templates()

        assert len(templates) > 0
        assert all("name" in t and "description" in t for t in templates)
        template_names = [t["name"] for t in templates]
        assert "mcp_server" in template_names

    def test_extract_project_name(self, generator):
        """Test project name extraction."""
        name1 = generator._extract_project_name("build a git operations server")
        assert "git" in name1 or "operations" in name1

        name2 = generator._extract_project_name("create API integration")
        assert "api" in name2.lower()

    def test_detect_db_type(self, generator):
        """Test database type detection."""
        assert generator._detect_db_type("use PostgreSQL database") == "postgres"
        assert generator._detect_db_type("MongoDB for storage") == "mongodb"
        assert generator._detect_db_type("no database mentioned") == "sqlite"

    def test_commits_calculation(self, generator):
        """Test commit calculation."""
        plan = generator.generate_task_plan(
            "Large project with many features",
            template="custom",
            constraints={"max_loc_per_commit": 200},
        )

        # Should calculate correct number of commits
        expected_commits = (plan["total_estimated_loc"] + 199) // 200
        assert plan["commits_needed"] == expected_commits

    def test_task_dependencies(self, generator):
        """Test that tasks have proper dependencies."""
        plan = generator.generate_task_plan("Build a server", template="mcp_server")

        # First task should have no dependencies
        assert plan["tasks"][0].get("dependencies", []) == []

        # Later tasks should depend on earlier ones
        for task in plan["tasks"][1:]:
            if "dependencies" in task:
                # Dependencies should reference earlier task IDs
                assert all(dep < task["id"] for dep in task["dependencies"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
