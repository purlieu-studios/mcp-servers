"""Session Memory MCP Server - Conversation history and context tracking."""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for shared imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server import Server
from mcp.types import TextContent, Tool

from shared.workspace_state import get_workspace_state

from .session_store import get_session_store

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SessionMemoryServer:
    """MCP server providing session memory and conversation tracking."""

    def __init__(self):
        self.server = Server("session-memory-server")
        self.store = get_session_store()
        self.workspace_state = get_workspace_state()

        self._register_handlers()

    def _register_handlers(self):
        """Register MCP tool handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="log_message",
                    description="Log a conversation message to session history",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "role": {
                                "type": "string",
                                "enum": ["user", "assistant", "system"],
                                "description": "Message role",
                            },
                            "content": {"type": "string", "description": "Message content"},
                            "tokens": {
                                "type": "number",
                                "description": "Token count (optional)",
                                "default": 0,
                            },
                        },
                        "required": ["role", "content"],
                    },
                ),
                Tool(
                    name="get_session_history",
                    description="Get conversation history from current or specified session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "number",
                                "description": "Session ID (optional, uses current session)",
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum number of messages (default: 50)",
                                "default": 50,
                            },
                            "role": {"type": "string", "description": "Filter by role (optional)"},
                        },
                    },
                ),
                Tool(
                    name="get_current_session",
                    description="Get information about the current active session",
                    inputSchema={"type": "object", "properties": {}},
                ),
                Tool(
                    name="search_sessions",
                    description="Search past sessions by query or tag",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (searches messages and decisions)",
                            },
                            "tag": {"type": "string", "description": "Filter by tag"},
                            "limit": {
                                "type": "number",
                                "description": "Maximum results (default: 10)",
                                "default": 10,
                            },
                        },
                    },
                ),
                Tool(
                    name="log_decision",
                    description="Log a key decision or action taken during the session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "decision": {"type": "string", "description": "Decision description"},
                            "context": {
                                "type": "string",
                                "description": "Additional context (optional)",
                            },
                        },
                        "required": ["decision"],
                    },
                ),
                Tool(
                    name="end_session",
                    description="End the current session with optional summary",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "Session summary (optional)",
                            }
                        },
                    },
                ),
                Tool(
                    name="get_session_stats",
                    description="Get statistics about session memory usage",
                    inputSchema={"type": "object", "properties": {}},
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name == "log_message":
                    return await self._handle_log_message(arguments)
                elif name == "get_session_history":
                    return await self._handle_get_session_history(arguments)
                elif name == "get_current_session":
                    return await self._handle_get_current_session(arguments)
                elif name == "search_sessions":
                    return await self._handle_search_sessions(arguments)
                elif name == "log_decision":
                    return await self._handle_log_decision(arguments)
                elif name == "end_session":
                    return await self._handle_end_session(arguments)
                elif name == "get_session_stats":
                    return await self._handle_get_session_stats(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error handling tool {name}: {e}", exc_info=True)
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _handle_log_message(self, arguments: dict) -> list[TextContent]:
        """Handle log_message tool."""
        role = arguments.get("role")
        content = arguments.get("content")
        tokens = arguments.get("tokens", 0)

        message_id = self.store.log_message(role=role, content=content, tokens=tokens)

        return [TextContent(type="text", text=f"Message logged (ID: {message_id})")]

    async def _handle_get_session_history(self, arguments: dict) -> list[TextContent]:
        """Handle get_session_history tool."""
        session_id = arguments.get("session_id")
        limit = arguments.get("limit", 50)
        role = arguments.get("role")

        messages = self.store.get_session_messages(session_id=session_id, limit=limit, role=role)

        if not messages:
            return [TextContent(type="text", text="No messages found")]

        output = f"📝 Session History ({len(messages)} messages):\n\n"
        for msg in reversed(messages):  # Show chronologically
            output += f"[{msg['role'].upper()}] {msg['timestamp']}\n"
            output += f"{msg['content'][:200]}\n"
            if len(msg["content"]) > 200:
                output += "...\n"
            output += f"Tokens: {msg['tokens']}\n"
            output += "-" * 60 + "\n\n"

        return [TextContent(type="text", text=output)]

    async def _handle_get_current_session(self, arguments: dict) -> list[TextContent]:
        """Handle get_current_session tool."""
        session_info = self.store.get_session_info()

        if not session_info:
            return [TextContent(type="text", text="No active session")]

        output = "📊 Current Session\n\n"
        output += f"Session ID: {session_info['id']}\n"
        output += f"Started: {session_info['start_time']}\n"
        output += f"Status: {session_info['status']}\n"
        output += f"Messages: {session_info['message_count']}\n"
        output += f"Total tokens: {session_info['total_tokens']}\n"

        if session_info.get("tags"):
            output += "\nTags:\n"
            for tag, value in session_info["tags"].items():
                output += f"  {tag}: {value}\n"

        if session_info.get("summary"):
            output += f"\nSummary: {session_info['summary']}\n"

        return [TextContent(type="text", text=output)]

    async def _handle_search_sessions(self, arguments: dict) -> list[TextContent]:
        """Handle search_sessions tool."""
        query = arguments.get("query")
        tag = arguments.get("tag")
        limit = arguments.get("limit", 10)

        sessions = self.store.search_sessions(query=query, tag=tag, limit=limit)

        if not sessions:
            return [TextContent(type="text", text="No sessions found")]

        output = f"🔍 Found {len(sessions)} sessions:\n\n"
        for session in sessions:
            output += f"Session {session['id']}\n"
            output += f"Started: {session['start_time']}\n"
            output += f"Messages: {session['message_count']}, Tokens: {session['total_tokens']}\n"
            if session.get("summary"):
                output += f"Summary: {session['summary'][:100]}\n"
            output += "-" * 60 + "\n\n"

        return [TextContent(type="text", text=output)]

    async def _handle_log_decision(self, arguments: dict) -> list[TextContent]:
        """Handle log_decision tool."""
        decision = arguments.get("decision")
        context = arguments.get("context")

        decision_id = self.store.log_decision(decision=decision, context=context)

        # Also log to workspace state as a task
        try:
            self.workspace_state.add_task(
                description=decision,
                status="completed",
                metadata={"source": "session_memory", "decision_id": decision_id},
            )
        except Exception as e:
            logger.error(f"Error updating workspace state: {e}")

        return [TextContent(type="text", text=f"Decision logged (ID: {decision_id})")]

    async def _handle_end_session(self, arguments: dict) -> list[TextContent]:
        """Handle end_session tool."""
        summary = arguments.get("summary")

        self.store.end_session(summary=summary)

        return [
            TextContent(
                type="text", text="Session ended" + (f" with summary: {summary}" if summary else "")
            )
        ]

    async def _handle_get_session_stats(self, arguments: dict) -> list[TextContent]:
        """Handle get_session_stats tool."""
        stats = self.store.get_stats()

        output = "📈 Session Memory Statistics\n\n"
        output += f"Total sessions: {stats['total_sessions']}\n"
        output += f"Active sessions: {stats['active_sessions']}\n"
        output += f"Total messages: {stats['total_messages']}\n"
        output += f"Total tokens: {stats['total_tokens']:,}\n"
        output += f"Avg messages/session: {stats['avg_messages_per_session']}\n"
        output += f"\nDatabase: {stats['db_path']}\n"

        return [TextContent(type="text", text=output)]

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting Session Memory MCP Server...")

        # Run server
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream, write_stream, self.server.create_initialization_options()
            )


async def main():
    """Main entry point."""
    server = SessionMemoryServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
