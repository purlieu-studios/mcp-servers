"""DbContext class analyzer."""

import re
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional


class DbContextAnalyzer:
    """Analyze EF Core DbContext classes."""

    async def analyze(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a DbContext file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding='utf-8')

        # Extract DbContext class name
        dbcontext_name = self._extract_dbcontext_name(content)

        # Extract DbSet properties
        dbsets = self._extract_dbsets(content)

        # Extract connection string configuration
        connection_config = self._extract_connection_config(content)

        # Extract OnModelCreating configurations
        model_configurations = self._extract_model_configurations(content)

        # Extract inheritance
        base_class = self._extract_base_class(content, dbcontext_name)

        return {
            "name": dbcontext_name,
            "base_class": base_class,
            "dbsets": dbsets,
            "entity_count": len(dbsets),
            "connection_config": connection_config,
            "model_configurations": model_configurations,
            "uses_fluent_api": len(model_configurations) > 0
        }

    def _extract_dbcontext_name(self, content: str) -> Optional[str]:
        """Extract the DbContext class name."""
        match = re.search(r'class\s+(\w+)\s*:\s*DbContext', content)
        return match.group(1) if match else None

    def _extract_dbsets(self, content: str) -> List[Dict[str, str]]:
        """Extract DbSet properties."""
        dbsets = []

        # Match DbSet<Entity> PropertyName
        pattern = r'public\s+DbSet<(\w+)>\s+(\w+)\s*{\s*get;\s*set;\s*}'

        for match in re.finditer(pattern, content):
            dbsets.append({
                "entity_type": match.group(1),
                "property_name": match.group(2)
            })

        return dbsets

    def _extract_connection_config(self, content: str) -> Dict[str, Any]:
        """Extract connection string configuration."""
        config = {
            "method": None,
            "connection_string_name": None,
            "uses_options_builder": False
        }

        # Check for OnConfiguring method
        if 'OnConfiguring' in content:
            config["method"] = "OnConfiguring"
            config["uses_options_builder"] = True

            # Try to extract connection string name
            conn_match = re.search(r'\.UseSqlServer\(["\'](.+?)["\']\)', content)
            if conn_match:
                config["connection_string_name"] = conn_match.group(1)

        # Check for constructor injection
        if 'DbContextOptions' in content:
            config["uses_dependency_injection"] = True

        return config

    def _extract_model_configurations(self, content: str) -> List[Dict[str, Any]]:
        """Extract OnModelCreating configurations."""
        configurations = []

        # Find OnModelCreating method
        model_creating_match = re.search(
            r'protected\s+override\s+void\s+OnModelCreating\(ModelBuilder\s+modelBuilder\)(.*?)(?=protected|public|private|$)',
            content,
            re.DOTALL
        )

        if model_creating_match:
            model_creating_body = model_creating_match.group(1)

            # Extract entity configurations
            entity_configs = re.findall(
                r'modelBuilder\.Entity<(\w+)>\(\)',
                model_creating_body
            )

            for entity in entity_configs:
                configurations.append({
                    "entity": entity,
                    "type": "fluent_configuration"
                })

            # Extract ApplyConfiguration calls
            apply_configs = re.findall(
                r'modelBuilder\.ApplyConfiguration\(new\s+(\w+)\(\)\)',
                model_creating_body
            )

            for config_class in apply_configs:
                configurations.append({
                    "configuration_class": config_class,
                    "type": "separate_configuration"
                })

        return configurations

    def _extract_base_class(self, content: str, class_name: Optional[str]) -> str:
        """Extract the base class."""
        if not class_name:
            return "DbContext"

        match = re.search(rf'class\s+{class_name}\s*:\s*(\w+)', content)
        return match.group(1) if match else "DbContext"
