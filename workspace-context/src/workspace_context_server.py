"""Workspace Context MCP Server - Intelligent file recommendations and context prediction.

Provides proactive context management by analyzing workspace state, access patterns,
and file dependencies to recommend relevant files.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server import Server
from mcp.types import TextContent, Tool

from shared.workspace_state import get_workspace_state

from .context_analyzer import ContextAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class WorkspaceContextServer:
    """MCP server providing intelligent context recommendations."""

    def __init__(self):
        self.server = Server("workspace-context-server")
        self.workspace_state = get_workspace_state()
        self.analyzer = ContextAnalyzer(self.workspace_state)

        self._register_handlers()

    def _register_handlers(self):
        """Register MCP tool handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="get_context_recommendations",
                    description="Get intelligent file recommendations based on current work context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "number",
                                "description": "Maximum recommendations (default: 10)",
                                "default": 10,
                            },
                            "include_dependencies": {
                                "type": "boolean",
                                "description": "Include dependency-based recommendations (default: true)",
                                "default": True,
                            },
                            "include_patterns": {
                                "type": "boolean",
                                "description": "Include pattern-based recommendations (default: true)",
                                "default": True,
                            },
                        },
                    },
                ),
                Tool(
                    name="get_related_files",
                    description="Find files related to a specific file by imports, dependencies, or co-access patterns",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to file"},
                            "relationship_type": {
                                "type": "string",
                                "enum": ["imports", "imported_by", "co_accessed", "all"],
                                "description": "Type of relationship to find (default: all)",
                                "default": "all",
                            },
                        },
                        "required": ["file_path"],
                    },
                ),
                Tool(
                    name="get_access_patterns",
                    description="Analyze file access patterns to understand usage trends",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="build_dependency_map",
                    description="Build a dependency map for Python files in the workspace",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "root_path": {
                                "type": "string",
                                "description": "Root directory to scan (default: current directory)",
                            }
                        },
                    },
                ),
                Tool(
                    name="predict_next_files",
                    description="Predict likely next files to access based on current context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "current_file": {
                                "type": "string",
                                "description": "Current file being worked on (optional)",
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum predictions (default: 5)",
                                "default": 5,
                            },
                        },
                    },
                ),
                Tool(
                    name="get_context_summary",
                    description="Get high-level summary of current workspace context",
                    inputSchema={"type": "object", "properties": {}},
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name == "get_context_recommendations":
                    return await self._handle_get_recommendations(arguments)
                elif name == "get_related_files":
                    return await self._handle_get_related_files(arguments)
                elif name == "get_access_patterns":
                    return await self._handle_get_access_patterns(arguments)
                elif name == "build_dependency_map":
                    return await self._handle_build_dependency_map(arguments)
                elif name == "predict_next_files":
                    return await self._handle_predict_next_files(arguments)
                elif name == "get_context_summary":
                    return await self._handle_get_context_summary(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}", exc_info=True)
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _handle_get_recommendations(self, arguments: dict) -> list[TextContent]:
        """Handle get_context_recommendations tool."""
        limit = arguments.get("limit", 10)
        include_dependencies = arguments.get("include_dependencies", True)
        include_patterns = arguments.get("include_patterns", True)

        recommendations = self.analyzer.get_recommendations(
            limit=limit,
            include_dependencies=include_dependencies,
            include_patterns=include_patterns,
        )

        if not recommendations:
            return [
                TextContent(
                    type="text",
                    text="No recommendations available. Start working with files to build context.",
                )
            ]

        output = f"🎯 Context Recommendations ({len(recommendations)} files):\n\n"

        for idx, rec in enumerate(recommendations, 1):
            score_bar = "█" * int(rec["score"] * 10)
            output += f"{idx}. {rec['file']}\n"
            output += f"   Score: {score_bar} ({rec['score']:.2f})\n"
            output += f"   Reasons: {', '.join(rec['reasons'])}\n\n"

        return [TextContent(type="text", text=output)]

    async def _handle_get_related_files(self, arguments: dict) -> list[TextContent]:
        """Handle get_related_files tool."""
        file_path = arguments.get("file_path")
        relationship_type = arguments.get("relationship_type", "all")

        if not file_path:
            return [TextContent(type="text", text="Error: file_path is required")]

        related_files = self.analyzer.get_related_files(
            file_path=file_path, relationship_type=relationship_type
        )

        if not related_files:
            return [TextContent(type="text", text=f"No related files found for {file_path}")]

        output = f"🔗 Related Files for {file_path}:\n\n"

        # Group by relationship type
        by_type = {}
        for rel in related_files:
            rel_type = rel["relationship"]
            if rel_type not in by_type:
                by_type[rel_type] = []
            by_type[rel_type].append(rel)

        for rel_type, files in by_type.items():
            output += f"\n{rel_type.upper().replace('_', ' ')}:\n"
            for rel in files:
                strength_bar = "●" * int(rel["strength"] * 5)
                output += f"  {strength_bar} {rel['file']}\n"

        return [TextContent(type="text", text=output)]

    async def _handle_get_access_patterns(self, arguments: dict) -> list[TextContent]:
        """Handle get_access_patterns tool."""
        patterns = self.analyzer.get_access_patterns()

        output = "📊 File Access Patterns:\n\n"
        output += f"Total unique files: {patterns['total_files']}\n"
        output += f"Avg accesses per file: {patterns['average_session_files']:.1f}\n\n"

        if patterns["most_accessed"]:
            output += "Most Accessed Files:\n"
            for item in patterns["most_accessed"]:
                output += f"  [{item['count']}×] {item['file']}\n"
            output += "\n"

        if patterns["access_by_hour"]:
            output += "Access by Hour:\n"
            max_count = max(patterns["access_by_hour"].values())
            for hour in sorted(patterns["access_by_hour"].keys()):
                count = patterns["access_by_hour"][hour]
                bar = "█" * int((count / max_count) * 20)
                output += f"  {hour:02d}:00 {bar} ({count})\n"

        return [TextContent(type="text", text=output)]

    async def _handle_build_dependency_map(self, arguments: dict) -> list[TextContent]:
        """Handle build_dependency_map tool."""
        root_path_str = arguments.get("root_path")
        root_path = Path(root_path_str) if root_path_str else None

        dependency_map = self.analyzer.build_dependency_map(root_path=root_path)

        if not dependency_map:
            return [
                TextContent(
                    type="text", text="No Python files with dependencies found in workspace"
                )
            ]

        output = f"📦 Dependency Map ({len(dependency_map)} files):\n\n"

        # Sort by number of dependencies
        sorted_files = sorted(dependency_map.items(), key=lambda x: len(x[1]), reverse=True)

        for file_path, deps in sorted_files[:20]:  # Show top 20
            output += f"{file_path}\n"
            output += f"  Imports {len(deps)} module(s):\n"
            for dep in deps[:5]:  # Show first 5 dependencies
                output += f"    - {dep}\n"
            if len(deps) > 5:
                output += f"    ... and {len(deps) - 5} more\n"
            output += "\n"

        if len(dependency_map) > 20:
            output += f"... and {len(dependency_map) - 20} more files\n"

        return [TextContent(type="text", text=output)]

    async def _handle_predict_next_files(self, arguments: dict) -> list[TextContent]:
        """Handle predict_next_files tool."""
        current_file = arguments.get("current_file")
        limit = arguments.get("limit", 5)

        predictions = self.analyzer.predict_next_files(current_file=current_file, limit=limit)

        if not predictions:
            return [
                TextContent(
                    type="text",
                    text="No predictions available. Build context by accessing more files.",
                )
            ]

        output = "🔮 Predicted Next Files:\n\n"

        for idx, pred in enumerate(predictions, 1):
            confidence_bar = "█" * int(pred["confidence"] * 10)
            output += f"{idx}. {pred['file']}\n"
            output += f"   Confidence: {confidence_bar} ({pred['confidence']:.0%})\n"
            output += f"   Reason: {pred['reason']}\n\n"

        return [TextContent(type="text", text=output)]

    async def _handle_get_context_summary(self, arguments: dict) -> list[TextContent]:
        """Handle get_context_summary tool."""
        summary = self.analyzer.get_context_summary()

        output = "📋 Workspace Context Summary:\n\n"
        output += f"Focus Files: {summary['focus_files_count']}\n"
        output += f"Active Tasks: {summary['active_tasks_count']}\n"
        output += f"Recent Queries: {summary['recent_queries_count']}\n"
        output += f"Recommendations Available: {summary['recommendations_available']}\n\n"

        if summary["primary_file_types"]:
            output += "Primary File Types:\n"
            for ext, count in summary["primary_file_types"].items():
                ext_display = ext if ext else "(no extension)"
                output += f"  {ext_display}: {count}\n"
            output += "\n"

        if summary["server_usage"]:
            output += "Server Usage:\n"
            for server, count in summary["server_usage"].items():
                output += f"  {server}: {count} queries\n"
            output += "\n"

        if summary["current_focus"]:
            output += "Current Focus (Top 5):\n"
            for file_info in summary["current_focus"]:
                output += f"  - {file_info['path']}\n"
                output += f"    ({file_info.get('reason', 'unknown')})\n"

        return [TextContent(type="text", text=output)]

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Workspace Context MCP Server...")

        # Run server
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


async def main():
    """Main entry point."""
    server = WorkspaceContextServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
