# Session Memory MCP Server

Tracks conversation history and session context across Claude Code restarts for improved context retention.

## Features

- **Conversation Tracking**: Logs all messages with role, content, and token counts
- **Session Management**: Auto-detects session boundaries (30min inactivity = new session)
- **Decision Logging**: Track key decisions and actions taken
- **Session Search**: Full-text search across past conversations
- **Statistics**: Track message counts, token usage, and session patterns
- **Persistence**: SQLite storage in `~/.claude-session-memory.db`

## Available Tools (7)

### 1. `log_message`
Log a conversation message to session history.

**Parameters:**
- `role`: Message role (user, assistant, system)
- `content`: Message content
- `tokens`: Token count (optional)

### 2. `get_session_history`
Get conversation history from current or specified session.

**Parameters:**
- `session_id`: Session ID (optional, uses current)
- `limit`: Max messages (default: 50)
- `role`: Filter by role (optional)

### 3. `get_current_session`
Get information about the current active session.

### 4. `search_sessions`
Search past sessions by query or tag.

**Parameters:**
- `query`: Search query (searches messages and decisions)
- `tag`: Filter by tag
- `limit`: Max results (default: 10)

### 5. `log_decision`
Log a key decision or action taken.

**Parameters:**
- `decision`: Decision description
- `context`: Additional context (optional)

### 6. `end_session`
End the current session with optional summary.

**Parameters:**
- `summary`: Session summary (optional)

### 7. `get_session_stats`
Get statistics about session memory usage.

## Database Schema

**sessions**
- id, start_time, end_time, status, summary, message_count, total_tokens

**messages**
- id, session_id, role, content, timestamp, tokens, metadata

**decisions**
- id, session_id, decision, context, timestamp

**session_tags**
- id, session_id, tag, value

## Use Cases

### Context Retention
- Automatically track conversation flow
- Resume context after Claude Code restart
- Search past conversations

### Session Analysis
- Understand token usage patterns
- Review key decisions made
- Track conversation history

### Integration
- Works with workspace state for unified context
- Decisions auto-logged as tasks in workspace

## Installation

```bash
cd session-memory
pip install -r requirements.txt
```

## Usage

Add to Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "session-memory": {
      "command": "python",
      "args": ["-m", "src.session_memory_server"],
      "cwd": "/path/to/session-memory"
    }
  }
}
```

## Testing

```bash
pytest tests/ -v
```

## Performance

- **Storage**: ~1-5KB per message
- **Operations**: <5ms per message logged
- **Sessions**: Auto-expires after 30min inactivity
- **No impact**: on conversation response time (async logging)

## Examples

### View Session History
```
"Show me the conversation history for this session"
→ Returns last 50 messages with timestamps
```

### Search Past Sessions
```
"Find sessions where we discussed authentication"
→ Searches all messages and decisions
```

### Track Decisions
```
"Log that we decided to refactor the auth module"
→ Logs decision with timestamp, adds to workspace tasks
```

## Integration with Workspace State

Session Memory integrates with the workspace state system:
- Decisions are logged as completed tasks
- Session activity contributes to session metadata
- Unified view of work across servers
