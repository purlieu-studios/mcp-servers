"""Task Generator MCP Server - AI-powered project planning and task breakdown."""

import asyncio
import json
import logging
from typing import Any, Dict

from mcp.server import Server
from mcp.types import Tool, TextContent

from .task_generator import TaskGenerator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskGeneratorServer:
    """MCP server providing task generation and project planning tools."""

    def __init__(self):
        self.server = Server("task-generator-server")
        self.generator = TaskGenerator()

        self._register_handlers()

    def _register_handlers(self):
        """Register MCP tool handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="generate_task_plan",
                    description="Generate structured task breakdown from project description. Returns detailed plan with LOC estimates, dependencies, and commit splits.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "Project or feature description"
                            },
                            "template": {
                                "type": "string",
                                "enum": ["mcp_server", "api_integration", "database", "testing", "custom"],
                                "description": "Template to use for generation (default: custom)",
                                "default": "custom"
                            },
                            "max_loc_per_commit": {
                                "type": "number",
                                "description": "Maximum lines of code per commit (default: 500)",
                                "default": 500
                            },
                            "include_tests": {
                                "type": "boolean",
                                "description": "Include test tasks (default: true)",
                                "default": True
                            },
                            "include_docs": {
                                "type": "boolean",
                                "description": "Include documentation tasks (default: true)",
                                "default": True
                            }
                        },
                        "required": ["description"]
                    }
                ),
                Tool(
                    name="refine_task_plan",
                    description="Refine an existing task plan by removing, splitting, or adjusting tasks",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "original_plan": {
                                "type": "object",
                                "description": "Original task plan to refine"
                            },
                            "remove_task_types": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Task types to remove (e.g., ['documentation', 'tests'])"
                            },
                            "split_task_id": {
                                "type": "number",
                                "description": "Task ID to split into multiple parts"
                            },
                            "split_count": {
                                "type": "number",
                                "description": "Number of parts to split task into (default: 2)",
                                "default": 2
                            }
                        },
                        "required": ["original_plan"]
                    }
                ),
                Tool(
                    name="estimate_complexity",
                    description="Estimate project complexity, LOC, and development time from description",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string",
                                "description": "Project description to analyze"
                            }
                        },
                        "required": ["description"]
                    }
                ),
                Tool(
                    name="list_templates",
                    description="List all available task generation templates with descriptions",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name == "generate_task_plan":
                    return await self._handle_generate_task_plan(arguments)
                elif name == "refine_task_plan":
                    return await self._handle_refine_task_plan(arguments)
                elif name == "estimate_complexity":
                    return await self._handle_estimate_complexity(arguments)
                elif name == "list_templates":
                    return await self._handle_list_templates(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}", exc_info=True)
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _handle_generate_task_plan(self, arguments: dict) -> list[TextContent]:
        """Handle generate_task_plan tool."""
        description = arguments.get('description')
        template = arguments.get('template', 'custom')

        constraints = {
            'max_loc_per_commit': arguments.get('max_loc_per_commit', 500),
            'include_tests': arguments.get('include_tests', True),
            'include_docs': arguments.get('include_docs', True)
        }

        plan = self.generator.generate_task_plan(
            description=description,
            template=template,
            constraints=constraints
        )

        output = self._format_task_plan(plan)
        return [TextContent(type="text", text=output)]

    async def _handle_refine_task_plan(self, arguments: dict) -> list[TextContent]:
        """Handle refine_task_plan tool."""
        original_plan = arguments.get('original_plan')

        adjustments = {}
        if 'remove_task_types' in arguments:
            adjustments['remove_task_types'] = arguments['remove_task_types']
        if 'split_task_id' in arguments:
            adjustments['split_task_id'] = arguments['split_task_id']
            adjustments['split_count'] = arguments.get('split_count', 2)

        refined_plan = self.generator.refine_task_plan(original_plan, adjustments)

        output = "## Refined Task Plan\n\n"
        output += self._format_task_plan(refined_plan)
        return [TextContent(type="text", text=output)]

    async def _handle_estimate_complexity(self, arguments: dict) -> list[TextContent]:
        """Handle estimate_complexity tool."""
        description = arguments.get('description')

        estimates = self.generator.estimate_complexity(description)

        output = f"## Complexity Estimate\n\n"
        output += f"**Project**: {description[:100]}...\n\n"
        output += f"**Estimated LOC**: {estimates['estimated_loc']}\n"
        output += f"**Estimated Time**: ~{estimates['estimated_hours']} hours\n"
        output += f"**Feature Count**: {estimates['feature_count']}\n"
        output += f"**Complexity Level**: {estimates['complexity_level'].upper()}\n\n"

        output += "**Complexity Indicators**:\n"
        for indicator, present in estimates['complexity_indicators'].items():
            status = "✓" if present else "✗"
            output += f"  {status} {indicator.replace('_', ' ').title()}\n"

        return [TextContent(type="text", text=output)]

    async def _handle_list_templates(self, arguments: dict) -> list[TextContent]:
        """Handle list_templates tool."""
        templates = self.generator.list_available_templates()

        output = "## Available Task Templates\n\n"
        for template in templates:
            output += f"**{template['name']}**\n"
            output += f"  {template['description']}\n\n"

        return [TextContent(type="text", text=output)]

    def _format_task_plan(self, plan: Dict[str, Any]) -> str:
        """Format task plan for display."""
        output = f"# Task Plan: {plan['project']}\n\n"
        output += f"**Template**: {plan['template']}\n"
        output += f"**Total Estimated LOC**: {plan['total_estimated_loc']}\n"
        output += f"**Commits Needed**: {plan['commits_needed']} (max {plan['max_loc_per_commit']} LOC each)\n"
        output += f"**Task Count**: {plan['task_count']}\n\n"

        output += "## Tasks\n\n"
        for task in plan['tasks']:
            output += f"### Task {task['id']}: {task['title']}\n"
            output += f"**Description**: {task['description']}\n"
            output += f"**Estimated LOC**: {task['estimated_loc']}\n"

            if task.get('dependencies'):
                deps = ', '.join(str(d) for d in task['dependencies'])
                output += f"**Dependencies**: Tasks {deps}\n"

            if task.get('files_to_create'):
                output += f"**Files**: {', '.join(task['files_to_create'])}\n"

            output += f"**Type**: {task.get('type', 'unknown')}\n\n"

        return output

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Task Generator MCP Server...")

        # Run server
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point."""
    server = TaskGeneratorServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
