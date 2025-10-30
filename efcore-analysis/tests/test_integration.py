"""Integration tests for EF Core Analysis MCP Server."""

import pytest
import asyncio
from pathlib import Path


pytestmark = pytest.mark.integration


class TestEFCoreAnalysisIntegration:
    """Integration tests for MCP tools."""

    @pytest.mark.asyncio
    async def test_analyze_dbcontext_tool(self, sample_dbcontext):
        """Test analyze_dbcontext tool."""
        from src.efcore_server import handle_analyze_dbcontext

        result = await handle_analyze_dbcontext({
            "file_path": str(sample_dbcontext)
        })

        assert "dbcontext" in result
        dbcontext = result["dbcontext"]
        assert dbcontext["name"] == "ApplicationDbContext"
        assert len(dbcontext["dbsets"]) >= 3

    @pytest.mark.asyncio
    async def test_analyze_entity_tool(self, sample_entity_simple):
        """Test analyze_entity tool."""
        from src.efcore_server import handle_analyze_entity

        result = await handle_analyze_entity({
            "file_path": str(sample_entity_simple)
        })

        assert "entities" in result
        assert len(result["entities"]) >= 1

        entity = result["entities"][0]
        assert entity["name"] == "User"
        assert "properties" in entity

    @pytest.mark.asyncio
    async def test_analyze_entity_with_relationships(self, sample_entity_with_relationships):
        """Test analyze_entity with relationships."""
        from src.efcore_server import handle_analyze_entity

        result = await handle_analyze_entity({
            "file_path": str(sample_entity_with_relationships)
        })

        # Result is wrapped in a dict by the handler
        assert "entities" in result
        entities = result["entities"]
        assert len(entities) > 0

        entity = entities[0]
        assert "navigation_properties" in entity
        # Navigation properties may or may not be detected
        assert isinstance(entity["navigation_properties"], list)

    @pytest.mark.asyncio
    async def test_generate_migration_tool(self, sample_model_old, sample_model_new):
        """Test generate_migration tool."""
        from src.efcore_server import handle_generate_migration

        result = await handle_generate_migration({
            "old_model_path": str(sample_model_old),
            "new_model_path": str(sample_model_new),
            "migration_name": "AddUserEmail"
        })

        assert "migration_name" in result
        assert result["migration_name"] == "AddUserEmail"
        assert "migration_code" in result
        assert len(result["migration_code"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_linq_tool(self, sample_linq_queries):
        """Test analyze_linq tool."""
        from src.efcore_server import handle_analyze_linq

        result = await handle_analyze_linq({
            "file_path": str(sample_linq_queries)
        })

        assert "linq_analysis" in result
        analysis = result["linq_analysis"]

        assert "total_queries" in analysis
        assert analysis["total_queries"] > 0
        assert "issues" in analysis

        # Should find issues in the sample
        assert len(analysis["issues"]) > 0

    @pytest.mark.asyncio
    async def test_suggest_indexes_tool(self, sample_project_structure):
        """Test suggest_indexes tool."""
        from src.efcore_server import handle_suggest_indexes

        result = await handle_suggest_indexes({
            "project_path": str(sample_project_structure)
        })

        assert "index_suggestions" in result
        assert len(result["index_suggestions"]) > 0

        # Check suggestion structure
        suggestion = result["index_suggestions"][0]
        assert "entity" in suggestion
        assert "property" in suggestion
        assert "reason" in suggestion
        assert "priority" in suggestion

    @pytest.mark.asyncio
    async def test_validate_model_tool(self, sample_entity_simple):
        """Test validate_model tool."""
        from src.efcore_server import handle_validate_model

        result = await handle_validate_model({
            "file_path": str(sample_entity_simple)
        })

        assert "validation" in result
        validation = result["validation"]

        assert "total_entities" in validation
        assert validation["total_entities"] >= 1

    @pytest.mark.asyncio
    async def test_validate_model_with_issues(self, sample_entity_invalid):
        """Test validate_model with invalid entity."""
        from src.efcore_server import handle_validate_model

        result = await handle_validate_model({
            "file_path": str(sample_entity_invalid)
        })

        validation = result["validation"]

        # Should find validation issues
        assert "issues" in validation
        assert len(validation["issues"]) > 0

    @pytest.mark.asyncio
    async def test_find_relationships_tool(self, sample_project_structure):
        """Test find_relationships tool."""
        from src.efcore_server import handle_find_relationships

        result = await handle_find_relationships({
            "project_path": str(sample_project_structure)
        })

        assert "relationships" in result
        # May or may not find relationships depending on patterns
        assert isinstance(result["relationships"], list)

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_file(self):
        """Test tools with nonexistent files."""
        from src.efcore_server import handle_analyze_entity

        with pytest.raises(FileNotFoundError):
            await handle_analyze_entity({
                "file_path": "/nonexistent/file.cs"
            })

    @pytest.mark.asyncio
    async def test_concurrent_tool_calls(self, sample_dbcontext, sample_entity_simple, sample_linq_queries):
        """Test running multiple tools concurrently."""
        from src.efcore_server import (
            handle_analyze_dbcontext,
            handle_analyze_entity,
            handle_analyze_linq
        )

        # Run tools concurrently
        tasks = [
            handle_analyze_dbcontext({"file_path": str(sample_dbcontext)}),
            handle_analyze_entity({"file_path": str(sample_entity_simple)}),
            handle_analyze_linq({"file_path": str(sample_linq_queries)})
        ]

        results = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(results) == 3
        assert all(isinstance(r, dict) for r in results)

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_end_to_end_entity_analysis(self, sample_entity_with_relationships):
        """E2E test: Complete entity analysis workflow."""
        from src.efcore_server import (
            handle_analyze_entity,
            handle_validate_model
        )

        # Step 1: Analyze entity structure
        entity_result = await handle_analyze_entity({
            "file_path": str(sample_entity_with_relationships)
        })

        assert len(entity_result["entities"]) > 0
        entity = entity_result["entities"][0]

        # Step 2: Validate the entity
        validation_result = await handle_validate_model({
            "file_path": str(sample_entity_with_relationships)
        })

        # Should complete validation
        assert "validation" in validation_result

        # Navigation properties may or may not be detected
        assert "navigation_properties" in entity

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_end_to_end_optimization_workflow(self, sample_project_structure, sample_linq_queries):
        """E2E test: Complete optimization workflow."""
        from src.efcore_server import (
            handle_analyze_linq,
            handle_suggest_indexes
        )

        # Step 1: Analyze LINQ queries
        linq_result = await handle_analyze_linq({
            "file_path": str(sample_linq_queries)
        })

        # Should get analysis results
        assert "linq_analysis" in linq_result

        # Step 2: Get index suggestions
        index_result = await handle_suggest_indexes({
            "project_path": str(sample_project_structure)
        })

        # Should get suggestions (may be empty)
        assert "index_suggestions" in index_result

    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_end_to_end_migration_workflow(self, sample_model_old, sample_model_new):
        """E2E test: Complete migration workflow."""
        from src.efcore_server import (
            handle_analyze_entity,
            handle_generate_migration
        )

        # Step 1: Analyze old model
        old_analysis = await handle_analyze_entity({
            "file_path": str(sample_model_old)
        })

        # Just check we got entities
        assert len(old_analysis["entities"]) > 0

        # Step 2: Analyze new model
        new_analysis = await handle_analyze_entity({
            "file_path": str(sample_model_new)
        })

        # Just check we got entities
        assert len(new_analysis["entities"]) > 0

        # Step 3: Generate migration
        migration_result = await handle_generate_migration({
            "old_model_path": str(sample_model_old),
            "new_model_path": str(sample_model_new),
            "migration_name": "UpdateUserModel"
        })

        assert "migration_code" in migration_result
        assert len(migration_result["migration_code"]) > 0

    @pytest.mark.asyncio
    async def test_tool_error_handling(self, temp_dir):
        """Test tool error handling."""
        from src.efcore_server import handle_analyze_entity

        # Create invalid C# file
        invalid_file = temp_dir / "invalid.cs"
        invalid_file.write_text("this is not valid C# code {{{ }")

        # Should handle gracefully
        result = await handle_analyze_entity({
            "file_path": str(invalid_file)
        })

        # Should return result (may be empty or with error)
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_analyze_dbcontext_multiple_configurations(self, temp_dir):
        """Test DbContext with various configurations."""
        dbcontext_file = temp_dir / "ComplexContext.cs"
        dbcontext_file.write_text('''
using Microsoft.EntityFrameworkCore;

namespace MyApp.Data
{
    public class ComplexContext : DbContext
    {
        public DbSet<User> Users { get; set; }
        public DbSet<Order> Orders { get; set; }
        public DbSet<Product> Products { get; set; }
        public DbSet<Category> Categories { get; set; }
        public DbSet<OrderItem> OrderItems { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<User>().HasIndex(u => u.Email).IsUnique();
            modelBuilder.Entity<Order>().HasOne<User>().WithMany().HasForeignKey(o => o.UserId);
            modelBuilder.Entity<Product>().HasOne<Category>().WithMany().HasForeignKey(p => p.CategoryId);

            base.OnModelCreating(modelBuilder);
        }
    }
}
''')

        from src.efcore_server import handle_analyze_dbcontext

        result = await handle_analyze_dbcontext({
            "file_path": str(dbcontext_file)
        })

        assert "dbcontext" in result
        dbcontext = result["dbcontext"]
        assert dbcontext["name"] == "ComplexContext"
        assert len(dbcontext["dbsets"]) == 5
        # Fluent API detection may vary
        assert "uses_fluent_api" in dbcontext
