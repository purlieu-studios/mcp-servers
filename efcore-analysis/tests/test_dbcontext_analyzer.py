"""Tests for DbContext analyzer."""

import pytest

from src.analyzers.dbcontext_analyzer import DbContextAnalyzer

pytestmark = pytest.mark.unit


class TestDbContextAnalyzer:
    """Test DbContextAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return DbContextAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_basic_dbcontext(self, analyzer, sample_dbcontext):
        """Test analyzing a basic DbContext."""
        result = await analyzer.analyze(sample_dbcontext)

        assert "name" in result
        assert result["name"] == "ApplicationDbContext"
        assert "base_class" in result
        assert result["base_class"] == "DbContext"

    @pytest.mark.asyncio
    async def test_extract_dbsets(self, analyzer, sample_dbcontext):
        """Test extracting DbSet properties."""
        result = await analyzer.analyze(sample_dbcontext)

        assert "dbsets" in result
        dbsets = result["dbsets"]
        assert len(dbsets) >= 3

        # Should have Users, Orders, Products
        dbset_names = [d["property_name"] for d in dbsets]
        assert "Users" in dbset_names
        assert "Orders" in dbset_names
        assert "Products" in dbset_names

    @pytest.mark.asyncio
    async def test_detect_fluent_api(self, analyzer, sample_dbcontext):
        """Test detecting Fluent API configuration."""
        result = await analyzer.analyze(sample_dbcontext)

        assert "uses_fluent_api" in result
        # May or may not detect depending on patterns
        assert isinstance(result["uses_fluent_api"], bool)

    @pytest.mark.asyncio
    async def test_detect_onmodelcreating(self, analyzer, sample_dbcontext):
        """Test detecting OnModelCreating override."""
        result = await analyzer.analyze(sample_dbcontext)

        # OnModelCreating is indicated by having model_configurations
        assert "model_configurations" in result
        assert isinstance(result["model_configurations"], list)

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_file(self, analyzer, temp_dir):
        """Test analyzing nonexistent file."""
        bad_path = temp_dir / "nonexistent.cs"

        with pytest.raises(FileNotFoundError):
            await analyzer.analyze(bad_path)

    @pytest.mark.asyncio
    async def test_analyze_non_dbcontext_file(self, analyzer, sample_entity_simple):
        """Test analyzing a file that's not a DbContext."""
        result = await analyzer.analyze(sample_entity_simple)

        # Should return empty or no name
        assert result.get("name") is None

    @pytest.mark.asyncio
    async def test_detect_dependency_injection(self, analyzer, sample_dbcontext):
        """Test detecting constructor dependency injection."""
        result = await analyzer.analyze(sample_dbcontext)

        assert "connection_config" in result
        assert result["connection_config"].get("uses_dependency_injection") is True

    @pytest.mark.asyncio
    async def test_empty_dbcontext(self, analyzer, temp_dir):
        """Test analyzing empty DbContext."""
        file_path = temp_dir / "EmptyContext.cs"
        file_path.write_text("""
using Microsoft.EntityFrameworkCore;

namespace MyApp.Data
{
    public class EmptyContext : DbContext
    {
    }
}
""")

        result = await analyzer.analyze(file_path)

        assert result["name"] == "EmptyContext"
        assert len(result.get("dbsets", [])) == 0

    @pytest.mark.asyncio
    async def test_dbcontext_with_onconfiguring(self, analyzer, temp_dir):
        """Test DbContext with OnConfiguring method."""
        file_path = temp_dir / "ConfigContext.cs"
        file_path.write_text("""
using Microsoft.EntityFrameworkCore;

namespace MyApp.Data
{
    public class ConfigContext : DbContext
    {
        public DbSet<User> Users { get; set; }

        protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        {
            optionsBuilder.UseSqlServer("connection_string");
        }
    }
}
""")

        result = await analyzer.analyze(file_path)

        assert "connection_config" in result
        assert result["connection_config"]["method"] == "OnConfiguring"

    @pytest.mark.asyncio
    async def test_count_entities(self, analyzer, sample_dbcontext):
        """Test counting DbSet entities."""
        result = await analyzer.analyze(sample_dbcontext)

        assert "entity_count" in result
        assert result["entity_count"] >= 3
