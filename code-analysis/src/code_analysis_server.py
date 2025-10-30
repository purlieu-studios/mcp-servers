"""Code Analysis MCP Server - AST parsing and code quality analysis."""

import logging
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .analyzers.python_analyzer import PythonAnalyzer
from .analyzers.javascript_analyzer import JavaScriptAnalyzer
from .analyzers.csharp_analyzer import CSharpAnalyzer
from .complexity import calculate_complexity
from .code_smells import detect_code_smells
from .dependency_analyzer import DependencyAnalyzer

logger = logging.getLogger(__name__)

# Initialize server
server = Server("code-analysis-server")

# Initialize analyzers
analyzers = {
    '.py': PythonAnalyzer(),
    '.js': JavaScriptAnalyzer(),
    '.ts': JavaScriptAnalyzer(),
    '.jsx': JavaScriptAnalyzer(),
    '.tsx': JavaScriptAnalyzer(),
    '.cs': CSharpAnalyzer(),
}

dependency_analyzer = DependencyAnalyzer()


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
                        "description": "Path to the code file to parse"
                    },
                    "include_body": {
                        "type": "boolean",
                        "description": "Include function/method bodies in output (default: false)"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="analyze_complexity",
            description="Calculate cyclomatic and cognitive complexity metrics for code",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file to analyze"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "Optional: specific function/method to analyze"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="find_code_smells",
            description="Detect code smells and quality issues (long methods, complexity, duplicated code)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file to analyze"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "all"],
                        "description": "Minimum severity level (default: all)"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="analyze_functions",
            description="Extract and analyze all functions/methods with signatures, parameters, and types",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file to analyze"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="find_dependencies",
            description="Analyze import statements and map file dependencies",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file or directory to analyze"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Recursively analyze all files in directory (default: false)"
                    }
                },
                "required": ["file_path"]
            }
        ),
        types.Tool(
            name="analyze_classes",
            description="Analyze class definitions, methods, properties, and inheritance",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file to analyze"
                    }
                },
                "required": ["file_path"]
            }
        )
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
        else:
            raise ValueError(f"Unknown tool: {name}")

        return [types.TextContent(type="text", text=str(result))]

    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        return [types.TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]


async def handle_parse_ast(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Parse file and return AST."""
    file_path = Path(arguments["file_path"])
    include_body = arguments.get("include_body", False)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get analyzer based on file extension
    analyzer = analyzers.get(file_path.suffix)
    if not analyzer:
        raise ValueError(f"No analyzer available for {file_path.suffix} files")

    # Parse and return AST
    ast_data = await analyzer.parse_file(file_path, include_body=include_body)

    return {
        "file_path": str(file_path),
        "language": analyzer.language,
        "ast": ast_data
    }


async def handle_analyze_complexity(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze code complexity."""
    file_path = Path(arguments["file_path"])
    function_name = arguments.get("function_name")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    analyzer = analyzers.get(file_path.suffix)
    if not analyzer:
        raise ValueError(f"No analyzer available for {file_path.suffix} files")

    # Calculate complexity metrics
    complexity_data = await calculate_complexity(
        file_path,
        analyzer,
        function_name=function_name
    )

    return {
        "file_path": str(file_path),
        "complexity": complexity_data
    }


async def handle_find_code_smells(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Find code smells and quality issues."""
    file_path = Path(arguments["file_path"])
    severity = arguments.get("severity", "all")

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    analyzer = analyzers.get(file_path.suffix)
    if not analyzer:
        raise ValueError(f"No analyzer available for {file_path.suffix} files")

    # Detect code smells
    smells = await detect_code_smells(
        file_path,
        analyzer,
        min_severity=severity
    )

    return {
        "file_path": str(file_path),
        "code_smells": smells,
        "total_issues": len(smells)
    }


async def handle_analyze_functions(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze functions and methods."""
    file_path = Path(arguments["file_path"])

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    analyzer = analyzers.get(file_path.suffix)
    if not analyzer:
        raise ValueError(f"No analyzer available for {file_path.suffix} files")

    # Extract function information
    functions = await analyzer.analyze_functions(file_path)

    return {
        "file_path": str(file_path),
        "functions": functions,
        "function_count": len(functions)
    }


async def handle_analyze_classes(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze class definitions."""
    file_path = Path(arguments["file_path"])

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    analyzer = analyzers.get(file_path.suffix)
    if not analyzer:
        raise ValueError(f"No analyzer available for {file_path.suffix} files")

    # Extract class information
    classes = await analyzer.analyze_classes(file_path)

    return {
        "file_path": str(file_path),
        "classes": classes,
        "class_count": len(classes)
    }


async def handle_find_dependencies(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze file dependencies."""
    file_path = Path(arguments["file_path"])
    recursive = arguments.get("recursive", False)

    if not file_path.exists():
        raise FileNotFoundError(f"Path not found: {file_path}")

    # Analyze dependencies
    dependencies = await dependency_analyzer.analyze(
        file_path,
        recursive=recursive
    )

    return {
        "path": str(file_path),
        "dependencies": dependencies
    }


async def main():
    """Run the Code Analysis MCP server."""
    logger.info("Starting Code Analysis MCP Server...")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
