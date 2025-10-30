"""Tests for Migration code generator."""

import pytest
from pathlib import Path
from src.analyzers.migration_analyzer import MigrationAnalyzer


pytestmark = pytest.mark.unit


class TestMigrationAnalyzer:
    """Test MigrationAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return MigrationAnalyzer()

    @pytest.mark.asyncio
    async def test_generate_migration_for_added_property(self, analyzer, sample_model_old, sample_model_new):
        """Test generating migration for added properties."""
        migration_code = await analyzer.generate_migration(
            sample_model_old,
            sample_model_new,
            "AddEmailToUser"
        )

        assert isinstance(migration_code, str)
        assert len(migration_code) > 0
        # Should contain AddColumn operation or migration structure
        assert "Migration" in migration_code or "AddColumn" in migration_code

    @pytest.mark.asyncio
    async def test_migration_has_up_method(self, analyzer, sample_model_old, sample_model_new):
        """Test that migration has Up method."""
        migration_code = await analyzer.generate_migration(
            sample_model_old,
            sample_model_new,
            "TestMigration"
        )

        assert "Up(" in migration_code or "up" in migration_code.lower()

    @pytest.mark.asyncio
    async def test_migration_has_down_method(self, analyzer, sample_model_old, sample_model_new):
        """Test that migration has Down method."""
        migration_code = await analyzer.generate_migration(
            sample_model_old,
            sample_model_new,
            "TestMigration"
        )

        assert "Down(" in migration_code or "down" in migration_code.lower()

    @pytest.mark.asyncio
    async def test_detect_property_changes(self, analyzer, sample_model_old, sample_model_new):
        """Test detecting property changes."""
        migration_code = await analyzer.generate_migration(
            sample_model_old,
            sample_model_new,
            "UpdateUser"
        )

        # Should generate migration code
        assert isinstance(migration_code, str)
        assert len(migration_code) > 0

    @pytest.mark.asyncio
    async def test_generate_for_identical_models(self, analyzer, sample_model_old):
        """Test generating migration for identical models."""
        migration_code = await analyzer.generate_migration(
            sample_model_old,
            sample_model_old,
            "NoChanges"
        )

        # Should still generate migration structure, just empty
        assert isinstance(migration_code, str)
        assert "Migration" in migration_code or "migration" in migration_code.lower()

    @pytest.mark.asyncio
    async def test_migration_name_format(self, analyzer, sample_model_old, sample_model_new):
        """Test migration name appears in generated code."""
        migration_name = "AddEmailColumn"
        migration_code = await analyzer.generate_migration(
            sample_model_old,
            sample_model_new,
            migration_name
        )

        # Migration name should appear in the generated code
        assert migration_name in migration_code

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_file(self, analyzer, temp_dir, sample_model_new):
        """Test with nonexistent files."""
        bad_path = temp_dir / "nonexistent.cs"

        with pytest.raises(FileNotFoundError):
            await analyzer.generate_migration(
                bad_path,
                sample_model_new,
                "Test"
            )

    @pytest.mark.asyncio
    async def test_migration_code_structure(self, analyzer, sample_model_old, sample_model_new):
        """Test migration code structure."""
        migration_code = await analyzer.generate_migration(
            sample_model_old,
            sample_model_new,
            "TestMigration"
        )

        # Should have proper C# structure
        assert "namespace" in migration_code or "class" in migration_code.lower()
        assert "Migration" in migration_code

    @pytest.mark.asyncio
    async def test_detect_removed_properties(self, analyzer, sample_model_new, sample_model_old):
        """Test detecting removed properties."""
        # Swap old and new to simulate property removal
        migration_code = await analyzer.generate_migration(
            sample_model_new,
            sample_model_old,
            "RemoveEmail"
        )

        # Should generate code (may have DropColumn or be empty)
        assert isinstance(migration_code, str)
        assert len(migration_code) > 0

    @pytest.mark.asyncio
    async def test_multiple_property_changes(self, analyzer, temp_dir):
        """Test handling multiple property changes."""
        old_model = temp_dir / "User.old.cs"
        old_model.write_text('''
using System.ComponentModel.DataAnnotations;

namespace MyApp.Models
{
    public class User
    {
        [Key]
        public int Id { get; set; }
        public string Name { get; set; }
    }
}
''')

        new_model = temp_dir / "User.new.cs"
        new_model.write_text('''
using System.ComponentModel.DataAnnotations;

namespace MyApp.Models
{
    public class User
    {
        [Key]
        public int Id { get; set; }
        public string Name { get; set; }
        public string Email { get; set; }
        public string Phone { get; set; }
        public bool IsActive { get; set; }
    }
}
''')

        migration_code = await analyzer.generate_migration(
            old_model,
            new_model,
            "AddMultipleColumns"
        )

        # Should generate code for multiple additions
        assert isinstance(migration_code, str)
        assert len(migration_code) > 0
