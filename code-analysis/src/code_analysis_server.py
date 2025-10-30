"""Code Analysis MCP Server - AST parsing and code quality analysis."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.workspace_state import get_workspace_state

from .analysis_cache import get_cache
from .analyzers.csharp_analyzer import CSharpAnalyzer
from .analyzers.javascript_analyzer import JavaScriptAnalyzer
from .analyzers.python_analyzer import PythonAnalyzer
from .code_smells import detect_code_smells
from .complexity import calculate_complexity
from .dependency_analyzer import DependencyAnalyzer

logger = logging.getLogger(__name__)

# Initialize server
server = Server("code-analysis-server")

# Initialize analyzers
analyzers = {
    ".py": PythonAnalyzer(),
    ".js": JavaScriptAnalyzer(),
    ".ts": JavaScriptAnalyzer(),
    ".jsx": JavaScriptAnalyzer(),
    ".tsx": JavaScriptAnalyzer(),
    ".cs": CSharpAnalyzer(),
}

dependency_analyzer = DependencyAnalyzer()

# Initialize cache and workspace state
cache = get_cache()
workspace_state = get_workspace_state()


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available code analysis tools."""
    return [
        types.Tool(
            name="parse_ast",
            description="Parse file and return AST representation with detailed structure analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file to parse",
                    },
                    "include_body": {
                        "type": "boolean",
                        "description": "Include function/method bodies in output (default: false)",
                    },
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="analyze_complexity",
            description="Calculate cyclomatic and cognitive complexity metrics for code",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file to analyze",
                    },
                    "function_name": {
                        "type": "string",
                        "description": "Optional: specific function/method to analyze",
                    },
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="find_code_smells",
            description="Detect code smells and quality issues (long methods, complexity, duplicated code)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file to analyze",
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "all"],
                        "description": "Minimum severity level (default: all)",
                    },
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="analyze_functions",
            description="Extract and analyze all functions/methods with signatures, parameters, and types",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file to analyze",
                    }
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="find_dependencies",
            description="Analyze import statements and map file dependencies",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file or directory to analyze",
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Recursively analyze all files in directory (default: false)",
                    },
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="analyze_classes",
            description="Analyze class definitions, methods, properties, and inheritance",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file to analyze",
                    }
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="get_cache_stats",
            description="Get analysis cache statistics (hit rate, size, entries)",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="clear_cache",
            description="Clear analysis cache entries (optionally older than N days)",
            inputSchema={
                "type": "object",
                "properties": {
                    "older_than_days": {
                        "type": "integer",
                        "description": "Clear only entries older than this many days (optional)",
                    }
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[types.TextContent]:
    """Handle tool calls for code analysis."""
    try:
        if name == "parse_ast":
            result = await handle_parse_ast(arguments)
        elif name == "analyze_complexity":
            result = await handle_analyze_complexity(arguments)
        elif name == "find_code_smells":
            result = await handle_find_code_smells(arguments)
        elif name == "analyze_functions":
            result = await handle_analyze_functions(arguments)
        elif name == "find_dependencies":
            result = await handle_find_dependencies(arguments)
        elif name == "analyze_classes":
            result = await handle_analyze_classes(arguments)
        elif name == "get_cache_stats":
            result = handle_get_cache_stats()
        elif name == "clear_cache":
            result = handle_clear_cache(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(type="text", text=str(result))]

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def handle_parse_ast(arguments: dict[str, Any]) -> dict[str, Any]:
    """Parse file and return AST."""
    file_path = Path(arguments["file_path"])
    include_body = arguments.get("include_body", False)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get analyzer based on file extension
    analyzer = analyzers.get(file_path.suffix)
    if not analyzer:
        raise ValueError(f"No analyzer available for {file_path.suffix} files")

    # Check cache first
    cache_key = f"ast_body_{include_body}"
    cached_result = cache.get(file_path, cache_key)
    if cached_result is not None:
        logger.info(f"[CACHE HIT] AST parse for {file_path.name}")
        cached_result["_cached"] = True
        return cached_result

    # Parse and return AST
    ast_data = await analyzer.parse_file(file_path, include_body=include_body)

    result = {
        "file_path": str(file_path),
        "language": analyzer.language,
        "ast": ast_data,
        "_cached": False,
    }

    # Store in cache
    cache.set(file_path, cache_key, result)
    logger.info(f"[CACHE MISS] Parsed AST for {file_path.name}")

    return result


async def handle_analyze_complexity(arguments: dict[str, Any]) -> dict[str, Any]:
    """Analyze code complexity."""
    file_path = Path(arguments["file_path"])
    function_name = arguments.get("function_name")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    analyzer = analyzers.get(file_path.suffix)
    if not analyzer:
        raise ValueError(f"No analyzer available for {file_path.suffix} files")

    # Check cache first
    cache_key = f"complexity_{function_name or 'all'}"
    cached_result = cache.get(file_path, cache_key)
    if cached_result is not None:
        logger.info(f"[CACHE HIT] Complexity analysis for {file_path.name}")
        cached_result["_cached"] = True
        return cached_result

    # Calculate complexity metrics
    complexity_data = await calculate_complexity(file_path, analyzer, function_name=function_name)

    result = {"file_path": str(file_path), "complexity": complexity_data, "_cached": False}

    # Store in cache
    cache.set(file_path, cache_key, result)
    logger.info(f"[CACHE MISS] Computed complexity for {file_path.name}")

    # Log to workspace
    try:
        workspace_state.add_focus_file(file_path=str(file_path), reason="complexity_analysis")
        workspace_state.add_query(
            server="code-analysis",
            tool="analyze_complexity",
            metadata={"file": str(file_path), "function": function_name},
        )
    except Exception as e:
        logger.error(f"Error updating workspace: {e}")

    return result


async def handle_find_code_smells(arguments: dict[str, Any]) -> dict[str, Any]:
    """Find code smells and quality issues."""
    file_path = Path(arguments["file_path"])
    severity = arguments.get("severity", "all")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    analyzer = analyzers.get(file_path.suffix)
    if not analyzer:
        raise ValueError(f"No analyzer available for {file_path.suffix} files")

    # Check cache first
    cache_key = f"smells_{severity}"
    cached_result = cache.get(file_path, cache_key)
    if cached_result is not None:
        logger.info(f"[CACHE HIT] Code smells analysis for {file_path.name}")
        cached_result["_cached"] = True
        return cached_result

    # Detect code smells
    smells = await detect_code_smells(file_path, analyzer, min_severity=severity)

    result = {
        "file_path": str(file_path),
        "code_smells": smells,
        "total_issues": len(smells),
        "_cached": False,
    }

    # Store in cache
    cache.set(file_path, cache_key, result)
    logger.info(f"[CACHE MISS] Computed code smells for {file_path.name}")

    return result


async def handle_analyze_functions(arguments: dict[str, Any]) -> dict[str, Any]:
    """Analyze functions and methods."""
    file_path = Path(arguments["file_path"])

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    analyzer = analyzers.get(file_path.suffix)
    if not analyzer:
        raise ValueError(f"No analyzer available for {file_path.suffix} files")

    # Check cache first
    cache_key = "functions"
    cached_result = cache.get(file_path, cache_key)
    if cached_result is not None:
        logger.info(f"[CACHE HIT] Function analysis for {file_path.name}")
        cached_result["_cached"] = True
        return cached_result

    # Extract function information
    functions = await analyzer.analyze_functions(file_path)

    result = {
        "file_path": str(file_path),
        "functions": functions,
        "function_count": len(functions),
        "_cached": False,
    }

    # Store in cache
    cache.set(file_path, cache_key, result)
    logger.info(f"[CACHE MISS] Analyzed functions for {file_path.name}")

    return result


async def handle_analyze_classes(arguments: dict[str, Any]) -> dict[str, Any]:
    """Analyze class definitions."""
    file_path = Path(arguments["file_path"])

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    analyzer = analyzers.get(file_path.suffix)
    if not analyzer:
        raise ValueError(f"No analyzer available for {file_path.suffix} files")

    # Check cache first
    cache_key = "classes"
    cached_result = cache.get(file_path, cache_key)
    if cached_result is not None:
        logger.info(f"[CACHE HIT] Class analysis for {file_path.name}")
        cached_result["_cached"] = True
        return cached_result

    # Extract class information
    classes = await analyzer.analyze_classes(file_path)

    result = {
        "file_path": str(file_path),
        "classes": classes,
        "class_count": len(classes),
        "_cached": False,
    }

    # Store in cache
    cache.set(file_path, cache_key, result)
    logger.info(f"[CACHE MISS] Analyzed classes for {file_path.name}")

    return result


async def handle_find_dependencies(arguments: dict[str, Any]) -> dict[str, Any]:
    """Analyze file dependencies."""
    file_path = Path(arguments["file_path"])
    recursive = arguments.get("recursive", False)

    if not file_path.exists():
        raise FileNotFoundError(f"Path not found: {file_path}")

    # Analyze dependencies
    dependencies = await dependency_analyzer.analyze(file_path, recursive=recursive)

    return {"path": str(file_path), "dependencies": dependencies}


def handle_get_cache_stats() -> dict[str, Any]:
    """Get cache statistics."""
    stats = cache.get_stats()
    logger.info(
        f"Cache stats: {stats['hit_rate_percent']}% hit rate, {stats['cache_entries']} entries"
    )
    return stats


def handle_clear_cache(arguments: dict[str, Any]) -> dict[str, Any]:
    """Clear analysis cache."""
    older_than_days = arguments.get("older_than_days")

    cleared = cache.clear(older_than_days=older_than_days)

    message = f"Cleared {cleared} cache entries"
    if older_than_days:
        message += f" older than {older_than_days} days"

    logger.info(message)

    return {"cleared_entries": cleared, "message": message, "cache_stats": cache.get_stats()}


async def main():
    """Run the Code Analysis MCP server."""
    logger.info("Starting Code Analysis MCP Server...")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
