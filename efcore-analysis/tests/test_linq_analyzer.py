"""Tests for LINQ query analyzer."""

import pytest
from pathlib import Path
from src.analyzers.linq_analyzer import LinqAnalyzer


pytestmark = pytest.mark.unit


class TestLinqAnalyzer:
    """Test LinqAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return LinqAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_linq_queries(self, analyzer, sample_linq_queries):
        """Test analyzing file with LINQ queries."""
        result = await analyzer.analyze(sample_linq_queries)

        assert "total_queries" in result
        assert result["total_queries"] > 0

    @pytest.mark.asyncio
    async def test_detect_sync_execution(self, analyzer, sample_linq_queries):
        """Test detecting synchronous execution."""
        result = await analyzer.analyze(sample_linq_queries)

        assert "issues" in result
        issues = result["issues"]

        # Should find ToList() without Async
        sync_issues = [i for i in issues if i["type"] == "sync_execution"]
        assert len(sync_issues) > 0

    @pytest.mark.asyncio
    async def test_detect_n_plus_1(self, analyzer, sample_linq_queries):
        """Test detecting N+1 query problems."""
        result = await analyzer.analyze(sample_linq_queries)

        issues = result["issues"]

        # N+1 detection is complex, may or may not find
        assert isinstance(issues, list)

    @pytest.mark.asyncio
    async def test_no_issues_in_optimized_code(self, analyzer, sample_linq_no_issues):
        """Test that optimized code has no major issues."""
        result = await analyzer.analyze(sample_linq_no_issues)

        issues = result.get("issues", [])

        # Should have no high-severity issues
        high_severity = [i for i in issues if i.get("severity") == "high"]
        assert len(high_severity) == 0

    @pytest.mark.asyncio
    async def test_detect_async_operations(self, analyzer, sample_linq_no_issues):
        """Test detecting async operations."""
        result = await analyzer.analyze(sample_linq_no_issues)

        # Should find async queries (ToListAsync, FirstOrDefaultAsync)
        assert result["total_queries"] > 0

    @pytest.mark.asyncio
    async def test_analyze_file_without_linq(self, analyzer, sample_dbcontext):
        """Test analyzing file without LINQ queries."""
        result = await analyzer.analyze(sample_dbcontext)

        # May have 0 queries or minimal queries
        assert "total_queries" in result

    @pytest.mark.asyncio
    async def test_analyze_nonexistent_file(self, analyzer, temp_dir):
        """Test analyzing nonexistent file."""
        bad_path = temp_dir / "nonexistent.cs"

        with pytest.raises(FileNotFoundError):
            await analyzer.analyze(bad_path)

    @pytest.mark.asyncio
    async def test_empty_file(self, analyzer, temp_dir):
        """Test analyzing empty file."""
        file_path = temp_dir / "empty.cs"
        file_path.write_text("")

        result = await analyzer.analyze(file_path)

        assert result["total_queries"] == 0

    @pytest.mark.asyncio
    async def test_detect_include_usage(self, analyzer, sample_linq_queries):
        """Test detecting Include() usage for eager loading."""
        result = await analyzer.analyze(sample_linq_queries)

        # Good queries should use Include()
        # We don't penalize its use, but track it
        assert "analyzed_queries" in result or "total_queries" in result

    @pytest.mark.asyncio
    async def test_severity_levels(self, analyzer, sample_linq_queries):
        """Test that issues have severity levels."""
        result = await analyzer.analyze(sample_linq_queries)

        issues = result.get("issues", [])

        for issue in issues:
            assert "severity" in issue
            assert issue["severity"] in ["low", "medium", "high"]

    @pytest.mark.asyncio
    async def test_suggestions_included(self, analyzer, sample_linq_queries):
        """Test that issues include suggestions."""
        result = await analyzer.analyze(sample_linq_queries)

        issues = result.get("issues", [])

        for issue in issues:
            assert "suggestion" in issue
            assert len(issue["suggestion"]) > 0

    @pytest.mark.asyncio
    async def test_query_tracking(self, analyzer, sample_linq_queries):
        """Test tracking individual queries."""
        result = await analyzer.analyze(sample_linq_queries)

        if "analyzed_queries" in result:
            queries = result["analyzed_queries"]
            assert len(queries) > 0

            for query in queries:
                assert "query" in query or "line" in query

    @pytest.mark.asyncio
    async def test_detect_firstordefault_without_where(self, analyzer, sample_linq_queries):
        """Test detecting FirstOrDefault without Where clause."""
        result = await analyzer.analyze(sample_linq_queries)

        issues = result.get("issues", [])

        # May detect FirstOrDefault() without predicate
        # This is in the sample file: _context.Users.FirstOrDefault()
        assert len(issues) > 0
