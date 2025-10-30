# EF Core Analysis Server - Claude Guide

Specialized Entity Framework Core analysis, optimization, and migration support for .NET applications.

## 🎯 What This Server Does

Analyzes your EF Core code to provide:
- **DbContext Analysis**: Structure, configuration, and DbSet properties
- **Entity Validation**: Model configuration and relationship checking
- **Migration Generation**: Automatic migration code from model changes
- **LINQ Optimization**: Query analysis and performance suggestions
- **Index Recommendations**: AI-powered database index suggestions
- **Relationship Mapping**: Complete entity relationship graphs

## 🔧 Available Tools (7)

### 1. `analyze_dbcontext` - Inspect DbContext

Analyze DbContext class structure, configuration, and entity mappings.

**Parameters:**
```json
{
  "file_path": "/path/to/ApplicationDbContext.cs"
}
```

**Returns:**
```json
{
  "file_path": "/path/to/ApplicationDbContext.cs",
  "dbcontext": {
    "name": "ApplicationDbContext",
    "base_class": "DbContext",
    "dbsets": [
      {"entity_type": "User", "property_name": "Users"},
      {"entity_type": "Order", "property_name": "Orders"},
      {"entity_type": "Product", "property_name": "Products"}
    ],
    "entity_count": 3,
    "connection_config": {
      "method": "OnConfiguring",
      "uses_options_builder": true,
      "uses_dependency_injection": true
    },
    "model_configurations": [
      {"entity": "User", "type": "fluent_configuration"},
      {"configuration_class": "UserConfiguration", "type": "separate_configuration"}
    ],
    "uses_fluent_api": true
  }
}
```

**Example Usage:**
```
"Analyze my ApplicationDbContext"
"What entities are in my DbContext?"
"Show me the DbContext configuration"
```

**Use Cases:**
- Understanding DbContext structure
- Reviewing entity mappings
- Checking configuration approach
- Auditing database setup

---

### 2. `analyze_entity` - Analyze Entity Models

Deep analysis of entity models with properties, relationships, and configurations.

**Parameters:**
```json
{
  "file_path": "/path/to/Models/User.cs",
  "entity_name": "User"                      // Optional: specific entity
}
```

**Returns:**
```json
{
  "file_path": "/path/to/Models/User.cs",
  "entities": [
    {
      "name": "User",
      "properties": [
        {
          "name": "Id",
          "type": "int",
          "annotations": ["Key"],
          "nullable": false,
          "required": false
        },
        {
          "name": "Email",
          "type": "string",
          "annotations": ["Required", "EmailAddress"],
          "nullable": false,
          "required": true
        },
        {
          "name": "CreatedAt",
          "type": "DateTime",
          "annotations": [],
          "nullable": false,
          "required": false
        }
      ],
      "navigation_properties": [
        {
          "name": "Orders",
          "type": "ICollection<Order>",
          "related_entity": "Order",
          "relationship_type": "one_to_many",
          "is_collection": true
        },
        {
          "name": "Profile",
          "type": "UserProfile",
          "related_entity": "UserProfile",
          "relationship_type": "many_to_one",
          "is_collection": false
        }
      ],
      "primary_key": "Id",
      "indexes": [
        {"property": "Email", "is_unique": true}
      ],
      "relationships": ["uses_foreign_key_attribute"]
    }
  ]
}
```

**Example Usage:**
```
"Analyze the User entity model"
"What properties does the Order entity have?"
"Show me all relationships for the Product entity"
```

**Use Cases:**
- Understanding entity structure
- Reviewing property configurations
- Mapping relationships
- Checking annotations

---

### 3. `generate_migration` - Create Migration Code

Generate EF Core migration code from model changes.

**Parameters:**
```json
{
  "old_model_path": "/path/to/User.old.cs",
  "new_model_path": "/path/to/User.cs",
  "migration_name": "AddUserEmailIndex"
}
```

**Returns:**
```json
{
  "migration_name": "AddUserEmailIndex",
  "migration_code": "using Microsoft.EntityFrameworkCore.Migrations;\n\nnamespace YourNamespace.Migrations\n{\n    public partial class AddUserEmailIndex : Migration\n    {\n        protected override void Up(MigrationBuilder migrationBuilder)\n        {\n            migrationBuilder.AddColumn<string>(\n                name: \"Email\",\n                table: \"Users\",\n                type: \"nvarchar(max)\",\n                nullable: true);\n            \n            migrationBuilder.CreateIndex(\n                name: \"IX_Users_Email\",\n                table: \"Users\",\n                column: \"Email\",\n                unique: true);\n        }\n        \n        protected override void Down(MigrationBuilder migrationBuilder)\n        {\n            migrationBuilder.DropIndex(\n                name: \"IX_Users_Email\",\n                table: \"Users\");\n            \n            migrationBuilder.DropColumn(\n                name: \"Email\",\n                table: \"Users\");\n        }\n    }\n}"
}
```

**Example Usage:**
```
"Generate a migration for the User model changes"
"Create migration code for adding Email property"
"Generate migration comparing old and new Product models"
```

**Use Cases:**
- Planning migrations
- Understanding migration impact
- Reviewing Up/Down operations
- Learning migration patterns

---

### 4. `analyze_linq` - Optimize LINQ Queries

Analyze LINQ queries for optimization opportunities and potential issues.

**Parameters:**
```json
{
  "file_path": "/path/to/UserRepository.cs"
}
```

**Returns:**
```json
{
  "file_path": "/path/to/UserRepository.cs",
  "linq_analysis": {
    "total_queries": 5,
    "analyzed_queries": [
      {
        "query": "var users = dbContext.Users.Where(u => u.IsActive).ToList();",
        "issues": [
          {
            "type": "sync_execution",
            "severity": "medium",
            "message": "Using synchronous ToList()",
            "suggestion": "Consider using ToListAsync() for async execution"
          }
        ],
        "suggestions": []
      },
      {
        "query": "var user = dbContext.Users.Include(u => u.Orders).FirstOrDefault(u => u.Id == userId);",
        "issues": [],
        "suggestions": [
          {
            "type": "optimization",
            "message": "Consider using FirstOrDefaultAsync for better performance"
          }
        ]
      },
      {
        "query": "var orders = user.Orders.ToList();",
        "issues": [
          {
            "type": "potential_n_plus_1",
            "severity": "high",
            "message": "Potential N+1 query problem detected",
            "suggestion": "Consider using .Include() to eager load related entities"
          }
        ],
        "suggestions": []
      }
    ],
    "issues": [
      {
        "type": "sync_execution",
        "severity": "medium",
        "message": "Using synchronous ToList()",
        "suggestion": "Consider using ToListAsync() for async execution"
      },
      {
        "type": "potential_n_plus_1",
        "severity": "high",
        "message": "Potential N+1 query problem detected",
        "suggestion": "Consider using .Include() to eager load related entities"
      }
    ],
    "total_issues": 2
  }
}
```

**Detected Issues:**
- **N+1 Query Problems**: Missing eager loading
- **Sync Operations**: Using ToList() instead of ToListAsync()
- **Query Ordering**: Inefficient Select/Where ordering
- **Missing Predicates**: FirstOrDefault without Where

**Example Usage:**
```
"Analyze LINQ queries in UserRepository.cs"
"Find N+1 query problems in my repository"
"Optimize the queries in OrderService.cs"
```

**Use Cases:**
- Performance optimization
- Pre-deployment review
- Learning LINQ best practices
- Finding common mistakes

---

### 5. `suggest_indexes` - Recommend Database Indexes

AI-powered database index recommendations based on query patterns.

**Parameters:**
```json
{
  "project_path": "/path/to/project",
  "dbcontext_name": "ApplicationDbContext"   // Optional
}
```

**Returns:**
```json
{
  "project_path": "/path/to/project",
  "index_suggestions": [
    {
      "entity": "User",
      "property": "Email",
      "reason": "Frequently used in WHERE clause",
      "priority": "high",
      "query_file": "/path/to/UserRepository.cs",
      "suggested_index": "CREATE INDEX IX_User_Email ON Users (Email)"
    },
    {
      "entity": "Order",
      "property": "OrderDate",
      "reason": "Used in ORDER BY clause",
      "priority": "medium",
      "query_file": "/path/to/OrderRepository.cs",
      "suggested_index": "CREATE INDEX IX_Order_OrderDate ON Orders (OrderDate)"
    },
    {
      "entity": "Product",
      "property": "CategoryId",
      "reason": "Frequently used in WHERE clause",
      "priority": "high",
      "query_file": "/path/to/ProductService.cs",
      "suggested_index": "CREATE INDEX IX_Product_CategoryId ON Products (CategoryId)"
    }
  ]
}
```

**Priority Levels:**
- **High**: Used in WHERE clauses (filters)
- **Medium**: Used in ORDER BY clauses (sorting)
- **Low**: Less frequently used

**Example Usage:**
```
"Suggest database indexes for my project"
"What indexes should I add to improve performance?"
"Analyze query patterns and recommend indexes"
```

**Use Cases:**
- Performance optimization
- Database design review
- Query pattern analysis
- Index planning

---

### 6. `validate_model` - Validate Entity Configuration

Validate entity models for common EF Core configuration issues.

**Parameters:**
```json
{
  "file_path": "/path/to/Models/User.cs"
}
```

**Returns:**
```json
{
  "file_path": "/path/to/Models/User.cs",
  "validation": {
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
}
```

**Validation Rules:**
- ❌ Missing primary keys
- ❌ Missing foreign keys for navigation properties
- ❌ Misconfigured relationships
- ❌ Invalid data annotations

**Example Usage:**
```
"Validate the User entity model"
"Check for EF Core configuration issues"
"Are my entities properly configured?"
```

**Use Cases:**
- Pre-deployment checks
- Code review
- Learning EF Core conventions
- Preventing runtime errors

---

### 7. `find_relationships` - Map Entity Relationships

Map all entity relationships across the project.

**Parameters:**
```json
{
  "project_path": "/path/to/project"
}
```

**Returns:**
```json
{
  "project_path": "/path/to/project",
  "relationships": [
    {
      "from_entity": "User",
      "to_entity": "Order",
      "property_name": "Orders",
      "relationship_type": "one_to_many",
      "file": "/path/to/Models/User.cs"
    },
    {
      "from_entity": "Order",
      "to_entity": "User",
      "property_name": "User",
      "relationship_type": "many_to_one",
      "file": "/path/to/Models/Order.cs"
    },
    {
      "from_entity": "Order",
      "to_entity": "Product",
      "property_name": "Products",
      "relationship_type": "one_to_many",
      "file": "/path/to/Models/Order.cs"
    }
  ]
}
```

**Relationship Types:**
- **one_to_many**: Collection navigation properties
- **many_to_one**: Reference navigation properties
- **many_to_many**: Both sides have collections

**Example Usage:**
```
"Map all entity relationships in my project"
"Show me how User and Order are related"
"What's the relationship graph for my models?"
```

**Use Cases:**
- Understanding data model
- Database design review
- Documentation
- Planning schema changes

---

## 💡 Common Workflows

### Database Design Review
```
1. "Analyze my ApplicationDbContext"
   → See all entities and configuration

2. "Validate all entity models"
   → Find configuration issues

3. "Map entity relationships"
   → Understand data model
```

### Performance Optimization
```
1. "Analyze LINQ queries in UserRepository"
   → Find N+1 queries and sync operations

2. "Suggest database indexes for my project"
   → Get AI-powered index recommendations

3. "Analyze query patterns"
   → Understand usage patterns
```

### Migration Planning
```
1. "Analyze the User entity before changes"
   → Understand current state

2. "Generate migration for User model changes"
   → Create migration code

3. "Review migration Up and Down operations"
   → Verify correctness
```

---

## 🎓 Best Practices

### DbContext Analysis
✅ **Do:**
- Review configuration method (DI vs OnConfiguring)
- Check for Fluent API usage
- Verify all entities are mapped

❌ **Don't:**
- Hardcode connection strings in OnConfiguring
- Mix configuration approaches
- Forget to register DbContext in DI

### Entity Validation
✅ **Do:**
- Always define primary keys
- Use proper foreign keys for relationships
- Add appropriate indexes
- Use data annotations for validation

❌ **Don't:**
- Skip primary key definition
- Rely only on conventions
- Ignore relationship configuration
- Forget to test model configuration

### LINQ Optimization
✅ **Do:**
- Use async operations (ToListAsync, FirstOrDefaultAsync)
- Eager load related data with Include()
- Filter before selecting
- Use proper predicates

❌ **Don't:**
- Use synchronous operations in async controllers
- Load all data then filter in memory
- Create N+1 query patterns
- Select unnecessary columns

### Index Strategy
✅ **Do:**
- Index foreign keys
- Index frequently filtered columns
- Index frequently sorted columns
- Consider composite indexes for multi-column queries

❌ **Don't:**
- Over-index (slows writes)
- Index low-cardinality columns
- Ignore query patterns
- Blindly add indexes

---

## 📊 Issue Severity Guide

### Validation Issues

**High Severity (🔴 Critical)**
- Missing primary keys
- Invalid relationships
- Configuration conflicts

**Medium Severity (⚠️ Warning)**
- Missing foreign keys
- Suggested optimizations
- Convention reliance

**Low Severity (💡 Info)**
- Documentation gaps
- Style improvements
- Minor optimizations

### LINQ Issues

**High Severity (🔴 Critical)**
- N+1 query problems
- Memory leaks
- Performance killers

**Medium Severity (⚠️ Warning)**
- Sync operations in async code
- Inefficient query patterns
- Missing optimizations

**Low Severity (💡 Info)**
- Style improvements
- Minor optimizations
- Best practice suggestions

---

## 🎯 Index Recommendation Guide

### High Priority (Must Have)
- Foreign keys
- Properties used in WHERE clauses frequently
- Login/authentication fields (Email, Username)

### Medium Priority (Should Have)
- Properties used in ORDER BY
- Properties used in JOIN conditions
- Date fields for range queries

### Low Priority (Nice to Have)
- Properties used occasionally in filters
- Properties for admin queries only
- Report-specific columns

---

## 🐛 Troubleshooting

### "No entities found"
- Check file path is correct
- Verify file contains entity classes
- Ensure proper C# class syntax

### "Cannot parse DbContext"
- Verify file is a DbContext class
- Check for syntax errors
- Ensure class inherits from DbContext

### "Migration generation failed"
- Verify both old and new model files exist
- Check for syntax errors in models
- Ensure models are comparable

### "No LINQ queries found"
- Check file contains LINQ expressions
- Verify file is a repository or service class
- Look for .Where(), .Select(), etc.

---

## 🔗 EF Core Resources

### Common Patterns

**Repository Pattern:**
```csharp
public class UserRepository
{
    private readonly ApplicationDbContext _context;

    public async Task<User> GetByIdAsync(int id)
    {
        return await _context.Users
            .Include(u => u.Orders)  // Eager loading
            .FirstOrDefaultAsync(u => u.Id == id);  // Async
    }

    public async Task<List<User>> GetActiveUsersAsync()
    {
        return await _context.Users
            .Where(u => u.IsActive)  // Filter first
            .OrderBy(u => u.Name)     // Then order
            .ToListAsync();           // Async execution
    }
}
```

**Fluent API Configuration:**
```csharp
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    modelBuilder.Entity<User>(entity =>
    {
        entity.HasKey(e => e.Id);
        entity.HasIndex(e => e.Email).IsUnique();
        entity.Property(e => e.Name).IsRequired().HasMaxLength(100);

        entity.HasMany(e => e.Orders)
            .WithOne(o => o.User)
            .HasForeignKey(o => o.UserId);
    });
}
```

---

## 🔗 Related Resources

- [README](./README.md) - Full documentation
- [EF Core Docs](https://docs.microsoft.com/ef/core/) - Official documentation
- [Main MCP Guide](../claude.md) - All servers

---

**Need help with EF Core?**
- DbContext setup → `analyze_dbcontext`
- Model issues → `validate_model`
- Performance → `analyze_linq` + `suggest_indexes`
- Relationships → `find_relationships`
- Migrations → `generate_migration`
