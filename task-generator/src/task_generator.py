"""Task generator for project planning and breakdown."""

import json
import re
from typing import Dict, List, Any, Optional
from .task_templates import get_template, list_templates


class TaskGenerator:
    """Generates structured task breakdowns from project descriptions."""

    def __init__(self):
        self.default_max_loc = 500
        self.default_include_tests = True
        self.default_include_docs = True

    def generate_task_plan(
        self,
        description: str,
        template: str = 'custom',
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate task plan from description.

        Args:
            description: Project/feature description
            template: Template to use (mcp_server, api_integration, database, testing, custom)
            constraints: Optional constraints (max_loc_per_commit, include_tests, include_docs)

        Returns:
            Task plan dictionary with project info and tasks
        """
        if constraints is None:
            constraints = {}

        # Apply defaults
        constraints.setdefault('max_loc_per_commit', self.default_max_loc)
        constraints.setdefault('include_tests', self.default_include_tests)
        constraints.setdefault('include_docs', self.default_include_docs)

        # Extract project name from description
        project_name = self._extract_project_name(description)

        # Build context
        context = {
            'description': description,
            'constraints': constraints,
            'server_name': project_name,
            'api_name': project_name,
            'db_type': self._detect_db_type(description)
        }

        # Generate tasks from template or custom analysis
        if template != 'custom':
            try:
                template_obj = get_template(template)
                tasks = template_obj.generate_tasks(context)
            except KeyError:
                # Fall back to custom generation
                tasks = self._generate_custom_tasks(description, constraints)
        else:
            tasks = self._generate_custom_tasks(description, constraints)

        # Calculate total LOC and determine commit splits
        total_loc = sum(task['estimated_loc'] for task in tasks)
        commits_needed = self._calculate_commits(tasks, constraints['max_loc_per_commit'])

        return {
            'project': project_name,
            'description': description,
            'template': template,
            'total_estimated_loc': total_loc,
            'commits_needed': commits_needed,
            'max_loc_per_commit': constraints['max_loc_per_commit'],
            'tasks': tasks,
            'task_count': len(tasks)
        }

    def refine_task_plan(
        self,
        original_plan: Dict[str, Any],
        adjustments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Refine an existing task plan with adjustments.

        Args:
            original_plan: Original task plan
            adjustments: Adjustments to make (remove_tasks, split_tasks, adjust_estimates, etc.)

        Returns:
            Refined task plan
        """
        tasks = original_plan['tasks'].copy()

        # Remove tasks
        if 'remove_task_ids' in adjustments:
            remove_ids = set(adjustments['remove_task_ids'])
            tasks = [t for t in tasks if t['id'] not in remove_ids]

        # Remove tasks by type
        if 'remove_task_types' in adjustments:
            remove_types = set(adjustments['remove_task_types'])
            tasks = [t for t in tasks if t.get('type') not in remove_types]

        # Split tasks
        if 'split_task_id' in adjustments:
            task_id = adjustments['split_task_id']
            split_count = adjustments.get('split_count', 2)
            tasks = self._split_task(tasks, task_id, split_count)

        # Adjust LOC estimates
        if 'adjust_estimates' in adjustments:
            for task_id, new_estimate in adjustments['adjust_estimates'].items():
                for task in tasks:
                    if task['id'] == task_id:
                        task['estimated_loc'] = new_estimate

        # Renumber task IDs
        for idx, task in enumerate(tasks, 1):
            old_id = task['id']
            task['id'] = idx
            # Update dependencies
            if 'dependencies' in task:
                task['dependencies'] = [
                    tasks[i-1]['id'] for i in task['dependencies'] if i <= len(tasks)
                ]

        # Recalculate totals
        total_loc = sum(task['estimated_loc'] for task in tasks)
        commits_needed = self._calculate_commits(tasks, original_plan['max_loc_per_commit'])

        return {
            **original_plan,
            'tasks': tasks,
            'task_count': len(tasks),
            'total_estimated_loc': total_loc,
            'commits_needed': commits_needed
        }

    def estimate_complexity(
        self,
        description: str
    ) -> Dict[str, Any]:
        """Estimate project complexity.

        Args:
            description: Project description

        Returns:
            Complexity estimates
        """
        # Count features/requirements
        feature_keywords = [
            'analyze', 'generate', 'search', 'find', 'create', 'update',
            'delete', 'monitor', 'track', 'integrate', 'parse', 'process'
        ]
        feature_count = sum(1 for kw in feature_keywords if kw in description.lower())

        # Detect complexity indicators
        complexity_indicators = {
            'async': 'async' in description.lower() or 'concurrent' in description.lower(),
            'database': any(db in description.lower() for db in ['database', 'sqlite', 'postgres']),
            'api': 'api' in description.lower() or 'http' in description.lower(),
            'caching': 'cache' in description.lower(),
            'real_time': 'real-time' in description.lower() or 'websocket' in description.lower()
        }

        # Estimate LOC
        base_loc = 200
        feature_loc = feature_count * 80
        complexity_loc = sum(100 for indicator in complexity_indicators.values() if indicator)
        total_loc = base_loc + feature_loc + complexity_loc

        # Estimate time (very rough)
        # Assume 50 LOC per hour for development + testing
        estimated_hours = total_loc / 50

        return {
            'feature_count': feature_count,
            'complexity_indicators': complexity_indicators,
            'estimated_loc': total_loc,
            'estimated_hours': round(estimated_hours, 1),
            'complexity_level': self._get_complexity_level(total_loc, complexity_indicators)
        }

    def list_available_templates(self) -> List[Dict[str, str]]:
        """List all available task templates.

        Returns:
            List of template info
        """
        return list_templates()

    # Private helper methods

    def _extract_project_name(self, description: str) -> str:
        """Extract project name from description."""
        # Look for patterns like "build a X server" or "create Y integration"
        patterns = [
            r'build (?:a |an )?([a-z\-]+)',
            r'create (?:a |an )?([a-z\-]+)',
            r'implement (?:a |an )?([a-z\-]+)',
            r'([a-z\-]+) (?:server|integration|system|module)'
        ]

        for pattern in patterns:
            match = re.search(pattern, description.lower())
            if match:
                name = match.group(1).strip()
                # Clean up common words
                name = re.sub(r'\b(server|integration|system|module)\b', '', name).strip()
                return name.replace(' ', '-')

        return 'new-project'

    def _detect_db_type(self, description: str) -> str:
        """Detect database type from description."""
        db_types = {
            'postgres': ['postgres', 'postgresql'],
            'mysql': ['mysql'],
            'sqlite': ['sqlite'],
            'mongodb': ['mongo', 'mongodb'],
            'redis': ['redis']
        }

        desc_lower = description.lower()
        for db_type, keywords in db_types.items():
            if any(kw in desc_lower for kw in keywords):
                return db_type

        return 'sqlite'  # Default

    def _generate_custom_tasks(
        self,
        description: str,
        constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate custom tasks based on description analysis."""
        complexity = self.estimate_complexity(description)
        feature_count = complexity['feature_count']

        tasks = []
        task_id = 1

        # Task 1: Core implementation
        tasks.append({
            'id': task_id,
            'title': 'Implement core functionality',
            'description': f'Core logic based on: {description[:100]}...',
            'estimated_loc': complexity['estimated_loc'] // 2,
            'dependencies': [],
            'files_to_create': ['src/core.py'],
            'type': 'core_logic'
        })
        task_id += 1

        # Task 2: Integration/interface
        if feature_count > 3:
            tasks.append({
                'id': task_id,
                'title': 'Build interface/integration layer',
                'description': 'External interfaces and integrations',
                'estimated_loc': complexity['estimated_loc'] // 4,
                'dependencies': [1],
                'files_to_create': ['src/interface.py'],
                'type': 'integration'
            })
            task_id += 1

        # Task 3: Tests
        if constraints.get('include_tests', True):
            tasks.append({
                'id': task_id,
                'title': 'Write test suite',
                'description': 'Comprehensive tests for all components',
                'estimated_loc': complexity['estimated_loc'] // 3,
                'dependencies': list(range(1, task_id)),
                'files_to_create': ['tests/test_core.py'],
                'type': 'tests'
            })
            task_id += 1

        # Task 4: Documentation
        if constraints.get('include_docs', True):
            tasks.append({
                'id': task_id,
                'title': 'Create documentation',
                'description': 'README, usage examples, API docs',
                'estimated_loc': 150,
                'dependencies': [1],
                'files_to_create': ['README.md'],
                'type': 'documentation'
            })

        return tasks

    def _calculate_commits(self, tasks: List[Dict[str, Any]], max_loc: int) -> int:
        """Calculate number of commits needed."""
        total_loc = sum(task['estimated_loc'] for task in tasks)
        return max(1, (total_loc + max_loc - 1) // max_loc)  # Ceiling division

    def _split_task(
        self,
        tasks: List[Dict[str, Any]],
        task_id: int,
        split_count: int
    ) -> List[Dict[str, Any]]:
        """Split a task into multiple subtasks."""
        result = []
        new_task_id = 1

        for task in tasks:
            if task['id'] == task_id:
                # Split this task
                loc_per_split = task['estimated_loc'] // split_count
                for i in range(split_count):
                    result.append({
                        **task,
                        'id': new_task_id,
                        'title': f"{task['title']} - Part {i + 1}",
                        'estimated_loc': loc_per_split
                    })
                    new_task_id += 1
            else:
                result.append({**task, 'id': new_task_id})
                new_task_id += 1

        return result

    def _get_complexity_level(
        self,
        total_loc: int,
        indicators: Dict[str, bool]
    ) -> str:
        """Determine complexity level."""
        active_indicators = sum(1 for v in indicators.values() if v)

        if total_loc < 300 and active_indicators <= 1:
            return 'low'
        elif total_loc < 600 and active_indicators <= 2:
            return 'medium'
        else:
            return 'high'
