"""EF Core Analysis MCP Server - DbContext and Entity Framework Core analysis."""

import logging
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .analyzers.dbcontext_analyzer import DbContextAnalyzer
from .analyzers.entity_analyzer import EntityAnalyzer
from .analyzers.migration_analyzer import MigrationAnalyzer
from .analyzers.linq_analyzer import LinqAnalyzer
from .analyzers.index_recommender import IndexRecommender

logger = logging.getLogger(__name__)

# Initialize server
server = Server("efcore-analysis-server")

# Initialize analyzers
dbcontext_analyzer = DbContextAnalyzer()
entity_analyzer = EntityAnalyzer()
migration_analyzer = MigrationAnalyzer()
linq_analyzer = LinqAnalyzer()
index_recommender = IndexRecommender()


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available EF Core analysis tools."""
    return [
        types.Tool(
            name="analyze_dbcontext",
            description="Analyze DbContext class to extract DbSet properties, configuration, and connection info",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the DbContext file (.cs)"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="analyze_entity",
            description="Analyze entity class to extract properties, relationships, and EF Core configurations",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the entity class file (.cs)"
                    },
                    "entity_name": {
                        "type": "string",
                        "description": "Optional: specific entity class name to analyze"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="generate_migration",
            description="Generate EF Core migration code based on entity model changes",
            inputSchema={
                "type": "object",
                "properties": {
                    "old_model_path": {
                        "type": "string",
                        "description": "Path to the old entity model file"
                    },
                    "new_model_path": {
                        "type": "string",
                        "description": "Path to the new entity model file"
                    },
                    "migration_name": {
                        "type": "string",
                        "description": "Name for the migration (e.g., AddUserEmailIndex)"
                    }
                },
                "required": ["old_model_path", "new_model_path", "migration_name"]
            }
        ),
        types.Tool(
            name="analyze_linq",
            description="Analyze LINQ queries for optimization opportunities and potential issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file containing LINQ queries"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="suggest_indexes",
            description="Suggest database indexes based on LINQ queries and entity usage patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory to analyze"
                    },
                    "dbcontext_name": {
                        "type": "string",
                        "description": "Optional: specific DbContext to analyze"
                    }
                },
                "required": ["project_path"]
            }
        ),
        types.Tool(
            name="validate_model",
            description="Validate entity models for common EF Core configuration issues",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the entity model file or DbContext"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="find_relationships",
            description="Map relationships between entities (one-to-many, many-to-many, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory"
                    }
                },
                "required": ["project_path"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool calls for EF Core analysis."""
    try:
        if name == "analyze_dbcontext":
            result = await handle_analyze_dbcontext(arguments)
        elif name == "analyze_entity":
            result = await handle_analyze_entity(arguments)
        elif name == "generate_migration":
            result = await handle_generate_migration(arguments)
        elif name == "analyze_linq":
            result = await handle_analyze_linq(arguments)
        elif name == "suggest_indexes":
            result = await handle_suggest_indexes(arguments)
        elif name == "validate_model":
            result = await handle_validate_model(arguments)
        elif name == "find_relationships":
            result = await handle_find_relationships(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(type="text", text=str(result))]

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def handle_analyze_dbcontext(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze DbContext class."""
    file_path = Path(arguments["file_path"])

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    analysis = await dbcontext_analyzer.analyze(file_path)

    return {
        "file_path": str(file_path),
        "dbcontext": analysis
    }


async def handle_analyze_entity(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze entity class."""
    file_path = Path(arguments["file_path"])
    entity_name = arguments.get("entity_name")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    entities = await entity_analyzer.analyze(file_path, entity_name)

    return {
        "file_path": str(file_path),
        "entities": entities
    }


async def handle_generate_migration(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Generate migration code."""
    old_path = Path(arguments["old_model_path"])
    new_path = Path(arguments["new_model_path"])
    migration_name = arguments["migration_name"]

    if not old_path.exists() or not new_path.exists():
        raise FileNotFoundError("Model files not found")

    migration_code = await migration_analyzer.generate_migration(
        old_path,
        new_path,
        migration_name
    )

    return {
        "migration_name": migration_name,
        "migration_code": migration_code
    }


async def handle_analyze_linq(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze LINQ queries."""
    file_path = Path(arguments["file_path"])

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    analysis = await linq_analyzer.analyze(file_path)

    return {
        "file_path": str(file_path),
        "linq_analysis": analysis
    }


async def handle_suggest_indexes(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Suggest database indexes."""
    project_path = Path(arguments["project_path"])
    dbcontext_name = arguments.get("dbcontext_name")

    if not project_path.exists():
        raise FileNotFoundError(f"Project path not found: {project_path}")

    suggestions = await index_recommender.analyze(
        project_path,
        dbcontext_name=dbcontext_name
    )

    return {
        "project_path": str(project_path),
        "index_suggestions": suggestions
    }


async def handle_validate_model(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Validate entity model."""
    file_path = Path(arguments["file_path"])

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    validation_results = await entity_analyzer.validate(file_path)

    return {
        "file_path": str(file_path),
        "validation": validation_results
    }


async def handle_find_relationships(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Find entity relationships."""
    project_path = Path(arguments["project_path"])

    if not project_path.exists():
        raise FileNotFoundError(f"Project path not found: {project_path}")

    relationships = await entity_analyzer.find_relationships(project_path)

    return {
        "project_path": str(project_path),
        "relationships": relationships
    }


async def main():
    """Run the EF Core Analysis MCP server."""
    logger.info("Starting EF Core Analysis MCP Server...")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
