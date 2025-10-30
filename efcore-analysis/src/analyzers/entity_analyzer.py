"""Entity model analyzer."""

import re
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional


class EntityAnalyzer:
    """Analyze EF Core entity models."""

    async def analyze(self, file_path: Path, entity_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Analyze entity classes in a file."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding='utf-8')

        entities = []
        class_matches = re.finditer(
            r'public\s+class\s+(\w+)(?:\s*:\s*([^{]+))?\s*{',
            content
        )

        for match in class_matches:
            class_name = match.group(1)

            # Skip if specific entity requested and this isn't it
            if entity_name and class_name != entity_name:
                continue

            entity_info = {
                "name": class_name,
                "properties": self._extract_properties(content, class_name),
                "navigation_properties": self._extract_navigation_properties(content, class_name),
                "primary_key": self._find_primary_key(content, class_name),
                "indexes": self._extract_indexes(content, class_name),
                "relationships": self._extract_relationships(content, class_name),
                "validation": []
            }

            entities.append(entity_info)

        return entities

    async def validate(self, file_path: Path) -> Dict[str, Any]:
        """Validate entity model for common issues."""
        entities = await self.analyze(file_path)

        issues = []

        for entity in entities:
            # Check for missing primary key
            if not entity["primary_key"]:
                issues.append({
                    "entity": entity["name"],
                    "severity": "high",
                    "issue": "missing_primary_key",
                    "message": f"Entity '{entity['name']}' has no primary key defined",
                    "suggestion": "Add a property named 'Id' or '{entity_name}Id', or use [Key] attribute"
                })

            # Check for navigation properties without foreign keys
            for nav_prop in entity["navigation_properties"]:
                if not nav_prop.get("foreign_key"):
                    issues.append({
                        "entity": entity["name"],
                        "severity": "medium",
                        "issue": "missing_foreign_key",
                        "message": f"Navigation property '{nav_prop['name']}' may be missing foreign key",
                        "suggestion": f"Consider adding {nav_prop['type']}Id property"
                    })

        return {
            "total_entities": len(entities),
            "total_issues": len(issues),
            "issues": issues
        }

    async def find_relationships(self, project_path: Path) -> List[Dict[str, Any]]:
        """Find all relationships between entities in a project."""
        relationships = []

        # Find all entity files
        for cs_file in project_path.rglob('*.cs'):
            try:
                entities = await self.analyze(cs_file)

                for entity in entities:
                    for nav_prop in entity["navigation_properties"]:
                        relationships.append({
                            "from_entity": entity["name"],
                            "to_entity": nav_prop["type"].replace("ICollection<", "").replace(">", ""),
                            "property_name": nav_prop["name"],
                            "relationship_type": nav_prop.get("relationship_type", "unknown"),
                            "file": str(cs_file)
                        })
            except:
                continue

        return relationships

    def _extract_properties(self, content: str, class_name: str) -> List[Dict[str, Any]]:
        """Extract entity properties."""
        properties = []

        # Find the class body
        class_match = re.search(rf'class\s+{class_name}\s*(?::\s*[^{{]+)?\s*{{([^}}]+)}}', content, re.DOTALL)
        if not class_match:
            return properties

        class_body = class_match.group(1)

        # Extract properties
        prop_pattern = r'public\s+(\w+(?:<\w+>)?)\s+(\w+)\s*{\s*get;\s*set;\s*}'
        for match in re.finditer(prop_pattern, class_body):
            prop_type = match.group(1)
            prop_name = match.group(2)

            # Skip navigation properties (collections)
            if 'ICollection' in prop_type or 'List' in prop_type:
                continue

            # Check for data annotations
            prop_text = class_body[:match.start()]
            last_newline = prop_text.rfind('\n')
            annotations_text = prop_text[last_newline:] if last_newline != -1 else ""

            annotations = self._extract_annotations(annotations_text)

            properties.append({
                "name": prop_name,
                "type": prop_type,
                "annotations": annotations,
                "nullable": "?" in prop_type,
                "required": "Required" in annotations_text
            })

        return properties

    def _extract_navigation_properties(self, content: str, class_name: str) -> List[Dict[str, Any]]:
        """Extract navigation properties."""
        nav_props = []

        # Find class body
        class_match = re.search(rf'class\s+{class_name}\s*(?::\s*[^{{]+)?\s*{{([^}}]+)}}', content, re.DOTALL)
        if not class_match:
            return nav_props

        class_body = class_match.group(1)

        # Extract collection navigation properties
        collection_pattern = r'public\s+(ICollection|List)<(\w+)>\s+(\w+)\s*{\s*get;\s*set;\s*}'
        for match in re.finditer(collection_pattern, class_body):
            nav_props.append({
                "name": match.group(3),
                "type": f"ICollection<{match.group(2)}>",
                "related_entity": match.group(2),
                "relationship_type": "one_to_many",
                "is_collection": True
            })

        # Extract reference navigation properties (simplified detection)
        ref_pattern = r'public\s+(\w+)\s+(\w+)\s*{\s*get;\s*set;\s*}'
        for match in re.finditer(ref_pattern, class_body):
            prop_type = match.group(1)
            prop_name = match.group(2)

            # Check if it's likely a navigation property (not a primitive type)
            if prop_type not in ['string', 'int', 'long', 'decimal', 'DateTime', 'bool', 'double', 'float'] and \
               prop_type[0].isupper() and \
               not prop_name.endswith('Id'):
                nav_props.append({
                    "name": prop_name,
                    "type": prop_type,
                    "related_entity": prop_type,
                    "relationship_type": "many_to_one",
                    "is_collection": False
                })

        return nav_props

    def _find_primary_key(self, content: str, class_name: str) -> Optional[str]:
        """Find the primary key property."""
        # Check for [Key] attribute
        key_match = re.search(r'\[Key\]\s+public\s+\w+\s+(\w+)', content)
        if key_match:
            return key_match.group(1)

        # Check for conventional Id or {ClassName}Id
        class_match = re.search(rf'class\s+{class_name}\s*(?::\s*[^{{]+)?\s*{{([^}}]+)}}', content, re.DOTALL)
        if class_match:
            class_body = class_match.group(1)

            # Look for Id or {ClassName}Id
            for id_name in ['Id', f'{class_name}Id']:
                if re.search(rf'public\s+\w+\s+{id_name}\s*{{', class_body):
                    return id_name

        return None

    def _extract_indexes(self, content: str, class_name: str) -> List[Dict[str, Any]]:
        """Extract index definitions."""
        indexes = []

        # Look for [Index] attributes
        index_pattern = r'\[Index\((?:nameof\()?(\w+)\)?(?:,\s*IsUnique\s*=\s*(true|false))?\)\]'
        for match in re.finditer(index_pattern, content):
            indexes.append({
                "property": match.group(1),
                "is_unique": match.group(2) == 'true' if match.group(2) else False
            })

        return indexes

    def _extract_relationships(self, content: str, class_name: str) -> List[str]:
        """Extract relationship types."""
        relationships = []

        if re.search(r'\[ForeignKey\(', content):
            relationships.append("uses_foreign_key_attribute")

        if re.search(r'\[InverseProperty\(', content):
            relationships.append("uses_inverse_property")

        return relationships

    def _extract_annotations(self, text: str) -> List[str]:
        """Extract data annotations."""
        annotations = re.findall(r'\[(\w+)(?:\([^\]]*\))?\]', text)
        return annotations
