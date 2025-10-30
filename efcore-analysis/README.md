# EF Core Analysis MCP Server

A specialized Model Context Protocol (MCP) server for comprehensive Entity Framework Core analysis, including DbContext inspection, entity model validation, migration generation, LINQ query optimization, and index recommendations.

## Features

### 7 Powerful Analysis Tools

#### 1. **analyze_dbcontext**
Analyze DbContext classes to extract configuration and structure.

```json
{
  "file_path": "/path/to/ApplicationDbContext.cs"
}
```

**Returns:**
- DbContext name and base class
- All DbSet properties and entity types
- Connection configuration method
- Model configurations (Fluent API usage)
- Entity count

#### 2. **analyze_entity**
Deep analysis of entity models with relationships and configurations.

```json
{
  "file_path": "/path/to/User.cs",
  "entity_name": "User"  // optional
}
```

**Returns:**
- All properties with types and annotations
- Navigation properties (collections and references)
- Primary key detection
- Indexes
- Relationship mappings

#### 3. **generate_migration**
Generate EF Core migration code from model changes.

```json
{
  "old_model_path": "/path/to/User.old.cs",
  "new_model_path": "/path/to/User.cs",
  "migration_name": "AddUserEmailIndex"
}
```

**Returns:** Complete migration class with Up() and Down() methods

#### 4. **analyze_linq**
Analyze LINQ queries for optimization opportunities and issues.

```json
{
  "file_path": "/path/to/UserRepository.cs"
}
```

**Detects:**
- N+1 query problems
- Missing async operations (ToListAsync)
- Inefficient query patterns
- Optimization suggestions

#### 5. **suggest_indexes**
AI-powered index recommendations based on query patterns.

```json
{
  "project_path": "/path/to/project",
  "dbcontext_name": "ApplicationDbContext"  // optional
}
```

**Analyzes:**
- WHERE clauses (high priority indexes)
- ORDER BY clauses (medium priority indexes)
- Query frequency and patterns
- Generates CREATE INDEX statements

#### 6. **validate_model**
Validate entity models for common EF Core configuration issues.

```json
{
  "file_path": "/path/to/User.cs"
}
```

**Validates:**
- Missing primary keys
- Missing foreign keys for navigation properties
- Misconfigured relationships
- Data annotation issues

#### 7. **find_relationships**
Map all entity relationships across the project.

```json
{
  "project_path": "/path/to/project"
}
```

**Returns:** Complete relationship graph with:
- One-to-many relationships
- Many-to-one relationships
- Many-to-many relationships
- Navigation property mappings

## Installation

```bash
cd efcore-analysis
pip install -r requirements.txt
```

## Usage

### With Claude Code

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "efcore-analysis": {
      "command": "python",
      "args": ["-m", "src.efcore_server"],
      "cwd": "/path/to/efcore-analysis"
    }
  }
}
```

### Standalone

```bash
python -m src.efcore_server
```

## Examples

### Analyze DbContext

```csharp
// Input: ApplicationDbContext.cs
public class ApplicationDbContext : DbContext
{
    public DbSet<User> Users { get; set; }
    public DbSet<Order> Orders { get; set; }
    public DbSet<Product> Products { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<User>()
            .HasMany(u => u.Orders)
            .WithOne(o => o.User);

        modelBuilder.ApplyConfiguration(new UserConfiguration());
    }
}
```

```json
// Server Output:
{
  "name": "ApplicationDbContext",
  "base_class": "DbContext",
  "dbsets": [
    {"entity_type": "User", "property_name": "Users"},
    {"entity_type": "Order", "property_name": "Orders"},
    {"entity_type": "Product", "property_name": "Products"}
  ],
  "entity_count": 3,
  "model_configurations": [
    {"entity": "User", "type": "fluent_configuration"},
    {"configuration_class": "UserConfiguration", "type": "separate_configuration"}
  ],
  "uses_fluent_api": true
}
```

### Validate Entity Model

```csharp
// Input: User.cs (with issues)
public class User
{
    // Missing: No primary key!
    public string Name { get; set; }
    public string Email { get; set; }

    // Navigation property without foreign key
    public ICollection<Order> Orders { get; set; }
}
```

```json
// Server Output:
{
  "total_entities": 1,
  "total_issues": 2,
  "issues": [
    {
      "entity": "User",
      "severity": "high",
      "issue": "missing_primary_key",
      "message": "Entity 'User' has no primary key defined",
      "suggestion": "Add a property named 'Id' or 'UserId', or use [Key] attribute"
    },
    {
      "entity": "User",
      "severity": "medium",
      "issue": "missing_foreign_key",
      "message": "Navigation property 'Orders' may be missing foreign key",
      "suggestion": "Consider adding OrderId property"
    }
  ]
}
```

### LINQ Query Analysis

```csharp
// Input: UserRepository.cs
var users = dbContext.Users
    .Where(u => u.IsActive)
    .ToList();  // Should be ToListAsync!

var user = dbContext.Users
    .Include(u => u.Orders)
    .FirstOrDefault(u => u.Id == userId);
```

```json
// Server Output:
{
  "total_queries": 2,
  "total_issues": 1,
  "issues": [
    {
      "type": "sync_execution",
      "severity": "medium",
      "message": "Using synchronous ToList()",
      "suggestion": "Consider using ToListAsync() for async execution"
    }
  ]
}
```

### Index Recommendations

```json
// Query: "Suggest indexes for my project"
// Server analyzes all LINQ queries and returns:
{
  "index_suggestions": [
    {
      "entity": "User",
      "property": "Email",
      "reason": "Frequently used in WHERE clause",
      "priority": "high",
      "suggested_index": "CREATE INDEX IX_User_Email ON Users (Email)"
    },
    {
      "entity": "Order",
      "property": "OrderDate",
      "reason": "Used in ORDER BY clause",
      "priority": "medium",
      "suggested_index": "CREATE INDEX IX_Order_OrderDate ON Orders (OrderDate)"
    }
  ]
}
```

## Architecture

```
efcore-analysis/
├── src/
│   ├── efcore_server.py                # Main MCP server
│   └── analyzers/
│       ├── dbcontext_analyzer.py       # DbContext inspection
│       ├── entity_analyzer.py          # Entity model analysis
│       ├── migration_analyzer.py       # Migration generation
│       ├── linq_analyzer.py            # LINQ optimization
│       └── index_recommender.py        # Index suggestions
├── requirements.txt
└── README.md
```

## Common Use Cases

### 1. Code Review
"Validate all entity models in my Models directory"

### 2. Performance Optimization
"Analyze LINQ queries in UserRepository.cs and suggest optimizations"

### 3. Database Design
"Suggest indexes for my e-commerce project"

### 4. Migration Planning
"Generate a migration for the changes I made to the User entity"

### 5. Relationship Mapping
"Show me all relationships between entities in my project"

## Future Enhancements

- [ ] Support for EF Core 8+ features (complex types, etc.)
- [ ] Visual relationship diagrams (Mermaid/PlantUML)
- [ ] Performance profiling integration
- [ ] Migration conflict detection
- [ ] Seed data analysis
- [ ] Database-first model generation
- [ ] Integration with SQL Server Management Studio

## Contributing

This server uses regex-based parsing for C# code analysis. For more accurate results, consider integrating with Roslyn (Microsoft.CodeAnalysis).

## License

MIT
