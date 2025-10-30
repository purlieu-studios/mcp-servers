# Task Generator MCP Server

AI-powered project planning and task breakdown. Generates structured task plans with LOC estimates, dependencies, and commit splits from natural language descriptions.

## Features

- **Smart Task Generation**: Convert project descriptions into detailed task breakdowns
- **Template System**: Predefined templates for common patterns (MCP servers, APIs, databases)
- **Complexity Analysis**: Estimate LOC, time, and complexity level
- **Plan Refinement**: Adjust plans by removing, splitting, or modifying tasks
- **Commit Planning**: Automatic calculation of commits needed (respects 500 LOC limit)
- **Dependency Tracking**: Tasks include dependency information

## Available Tools (4)

### 1. `generate_task_plan`
Generate structured task breakdown from project description.

**Parameters:**
- `description`: Project or feature description (required)
- `template`: Template to use (`mcp_server`, `api_integration`, `database`, `testing`, `custom`)
- `max_loc_per_commit`: Max LOC per commit (default: 500)
- `include_tests`: Include test tasks (default: true)
- `include_docs`: Include documentation (default: true)

**Returns**: Complete task plan with estimates and dependencies

### 2. `refine_task_plan`
Refine existing task plan with adjustments.

**Parameters:**
- `original_plan`: Original task plan (required)
- `remove_task_types`: Task types to remove (e.g., `['documentation']`)
- `split_task_id`: Task ID to split into parts
- `split_count`: Number of parts (default: 2)

**Returns**: Refined task plan

### 3. `estimate_complexity`
Estimate project complexity and development time.

**Parameters:**
- `description`: Project description (required)

**Returns**: Complexity analysis with LOC and time estimates

### 4. `list_templates`
List all available task templates.

**Returns**: Template names and descriptions

## Templates

### MCP Server Template
For building new MCP servers:
- Core logic module
- MCP server with tools
- Test suite
- Documentation

### API Integration Template
For integrating with external APIs:
- API client
- Data models
- Error handling
- Integration tests

### Database Template
For database/storage projects:
- Schema definition
- Data access layer
- Migration system
- Database tests

### Testing Infrastructure Template
For test frameworks:
- Pytest configuration
- Test fixtures
- CI/CD integration

## Usage Examples

### Example 1: Generate MCP Server Plan

**User**: "Build a git operations server with commit analysis and branch recommendations"

**Claude**:
```
🔧 Using task-generator: generate_task_plan

# Task Plan: git-operations

Template: mcp_server
Total Estimated LOC: 830
Commits Needed: 2 (max 500 LOC each)
Task Count: 4

## Tasks

### Task 1: Create core git-operations logic
Description: Implement core analysis/processing logic
Estimated LOC: 300
Files: git-operations/src/git_operations_core.py

### Task 2: Build MCP server with 5 tools
Description: Create MCP server exposing tools
Estimated LOC: 230
Dependencies: Task 1
Files: git-operations/src/git_operations_server.py

### Task 3: Write comprehensive test suite
Description: Create unit and integration tests
Estimated LOC: 250
Dependencies: Tasks 1, 2
Files: tests/test_git_operations_core.py

### Task 4: Create documentation
Description: README with features and examples
Estimated LOC: 150
Dependencies: Task 2
Files: README.md, requirements.txt
```

### Example 2: Estimate Complexity

**User**: "I want to build real-time database monitoring with async operations"

**Claude**:
```
🔧 Using task-generator: estimate_complexity

## Complexity Estimate

Estimated LOC: 580
Estimated Time: ~11.6 hours
Feature Count: 3
Complexity Level: HIGH

Complexity Indicators:
  ✓ Async
  ✓ Database
  ✓ Real Time
  ✗ API
  ✗ Caching
```

### Example 3: Refine Plan

**User**: "Actually, skip the documentation for now"

**Claude**:
```
🔧 Using task-generator: refine_task_plan

## Refined Task Plan

Total Estimated LOC: 680  (was 830)
Commits Needed: 2  (was 2)
Task Count: 3  (was 4)

[Documentation task removed]
```

## How It Works

### Task Generation Flow

1. **Parse Description**: Extract project name, features, complexity indicators
2. **Select Template**: Use specified template or analyze for custom generation
3. **Generate Tasks**: Create task breakdown with estimates
4. **Calculate Dependencies**: Determine task ordering
5. **Plan Commits**: Split tasks across commits (500 LOC limit)

### Complexity Estimation

Analyzes description for:
- Feature keywords (analyze, generate, search, etc.)
- Complexity indicators (async, database, API, caching, real-time)
- Calculates base + feature + complexity LOC
- Estimates time (~50 LOC/hour)

### Templates

Each template provides:
- Standard task structure
- LOC estimates based on best practices
- Proper dependency chains
- Common file structures

## Installation

```bash
cd task-generator
pip install -r requirements.txt
```

## Configuration

Add to Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "task-generator": {
      "command": "python",
      "args": ["-m", "src.task_generator_server"],
      "cwd": "/path/to/mcp-servers/task-generator"
    }
  }
}
```

## Testing

```bash
pytest tests/ -v
```

**Test Results**: 14/14 passing ✅

## Integration with Claude Desktop

Once configured, Claude will automatically:
1. Detect when you describe a project/feature
2. Call the task generator behind the scenes
3. Present structured plan for approval
4. Use plan to organize work

**You never directly call the tools** - Claude handles it transparently!

## Example Workflow

```
You: "I want to build an API monitoring system"

Claude: [Automatically calls generate_task_plan]

Claude: "Here's a 5-task breakdown:
1. Core monitoring logic (250 LOC)
2. API client (180 LOC)
3. Alert system (150 LOC)
4. Tests (220 LOC)
5. Docs (100 LOC)

Total: 900 LOC - we'll need 2 commits.
Ready to start?"

You: "Yes, but skip docs for now"

Claude: [Calls refine_task_plan]

Claude: "Updated plan - 4 tasks, 800 LOC, 2 commits.
Starting with core monitoring logic..."
```

## Benefits

**For You:**
- Instant project scope understanding
- Clear LOC estimates
- Proper task dependencies
- Commit planning built-in

**For Claude:**
- Structured execution plan
- Better task management
- Consistent approach
- Reusable patterns

## Extending Templates

Add new templates in `src/task_templates.py`:

```python
class CustomTemplate(TaskTemplate):
    def __init__(self):
        super().__init__(
            name="custom_name",
            description="Template description"
        )

    def generate_tasks(self, context):
        # Return list of task dicts
        return [...]
```

## Limitations

- LOC estimates are approximate
- Templates are Python-focused
- Custom analysis is heuristic-based
- Doesn't account for team size/skill

## Future Enhancements

- Learn from completed projects
- Improve LOC accuracy with ML
- Multi-language templates
- Integration with git history
- Team collaboration features
