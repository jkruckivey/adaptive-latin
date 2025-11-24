"""
Concept Dependency Analyzer

Analyzes prerequisite relationships between concepts in a course.
Detects circular dependencies, orphaned concepts, and suggests optimal ordering.
"""

import logging
from typing import Dict, List, Any, Set, Tuple, Optional
from collections import defaultdict, deque
from pathlib import Path

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Analyzes concept dependency structures for courses."""

    def __init__(self, concepts: List[Dict[str, Any]]):
        """
        Initialize analyzer with course concepts.

        Args:
            concepts: List of concept metadata dictionaries with 'id' and 'prerequisites'
        """
        self.concepts = concepts
        self.concept_map = {c['id']: c for c in concepts}
        self.graph = self._build_graph()

    def _build_graph(self) -> Dict[str, List[str]]:
        """Build adjacency list representation of dependency graph."""
        graph = defaultdict(list)
        for concept in self.concepts:
            concept_id = concept['id']
            prerequisites = concept.get('prerequisites', [])
            # Graph edge: prerequisite -> concept (prerequisite must come before concept)
            for prereq in prerequisites:
                graph[prereq].append(concept_id)
        return dict(graph)

    def find_circular_dependencies(self) -> List[List[str]]:
        """
        Detect circular dependency chains using DFS.

        Returns:
            List of circular dependency chains (cycles)
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str) -> bool:
            """DFS helper to detect cycles."""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle - extract the cycle from path
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for concept_id in self.concept_map.keys():
            if concept_id not in visited:
                dfs(concept_id)

        return cycles

    def find_orphaned_concepts(self) -> List[Dict[str, Any]]:
        """
        Find concepts with invalid prerequisites (prerequisites that don't exist).

        Returns:
            List of dictionaries with concept_id and missing prerequisites
        """
        orphaned = []
        all_concept_ids = set(self.concept_map.keys())

        for concept in self.concepts:
            concept_id = concept['id']
            prerequisites = concept.get('prerequisites', [])

            missing_prereqs = [p for p in prerequisites if p not in all_concept_ids]

            if missing_prereqs:
                orphaned.append({
                    'concept_id': concept_id,
                    'concept_title': concept.get('title', concept_id),
                    'missing_prerequisites': missing_prereqs
                })

        return orphaned

    def topological_sort(self) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Perform topological sort to get optimal concept ordering.
        Uses Kahn's algorithm.

        Returns:
            Tuple of (ordered_concepts, error_message)
            If circular dependency exists, returns (None, error_message)
        """
        # Calculate in-degree for each concept
        in_degree = {concept_id: 0 for concept_id in self.concept_map.keys()}

        for concept in self.concepts:
            concept_id = concept['id']
            prerequisites = concept.get('prerequisites', [])
            in_degree[concept_id] = len(prerequisites)

        # Queue of concepts with no prerequisites
        queue = deque([cid for cid, degree in in_degree.items() if degree == 0])
        ordered = []

        while queue:
            current = queue.popleft()
            ordered.append(current)

            # Reduce in-degree for concepts that depend on current
            for dependent in self.graph.get(current, []):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # If not all concepts are in ordered list, there's a cycle
        if len(ordered) != len(self.concepts):
            return None, "Circular dependency detected - cannot create valid ordering"

        return ordered, None

    def find_bottleneck_concepts(self) -> List[Dict[str, Any]]:
        """
        Identify concepts that are prerequisites for many other concepts.

        Returns:
            List of concepts sorted by number of dependents (descending)
        """
        dependent_count = defaultdict(int)

        for concept in self.concepts:
            prerequisites = concept.get('prerequisites', [])
            for prereq in prerequisites:
                dependent_count[prereq] += 1

        bottlenecks = []
        for concept_id, count in dependent_count.items():
            if count > 0:  # Only include concepts that are prerequisites
                concept = self.concept_map.get(concept_id)
                if concept:
                    bottlenecks.append({
                        'concept_id': concept_id,
                        'concept_title': concept.get('title', concept_id),
                        'dependent_count': count,
                        'dependents': [c['id'] for c in self.concepts
                                      if concept_id in c.get('prerequisites', [])]
                    })

        # Sort by dependent count (descending)
        bottlenecks.sort(key=lambda x: x['dependent_count'], reverse=True)
        return bottlenecks

    def find_parallel_paths(self) -> List[List[str]]:
        """
        Identify groups of concepts that have no dependencies on each other
        and can be learned in parallel.

        Returns:
            List of concept groups that can be studied simultaneously
        """
        # Build reverse dependency graph (concept -> its prerequisites)
        reverse_deps = {}
        for concept in self.concepts:
            concept_id = concept['id']
            prerequisites = set(concept.get('prerequisites', []))
            reverse_deps[concept_id] = prerequisites

        # Find concepts at each "level" (distance from root)
        levels = []
        processed = set()
        current_level = [cid for cid in self.concept_map.keys()
                        if not reverse_deps[cid]]

        while current_level:
            levels.append(current_level)
            processed.update(current_level)

            # Find next level: concepts whose prerequisites are all processed
            next_level = []
            for concept_id in self.concept_map.keys():
                if concept_id not in processed:
                    prereqs = reverse_deps[concept_id]
                    if prereqs.issubset(processed):
                        next_level.append(concept_id)

            current_level = next_level

        # Only return levels with multiple concepts (parallel opportunities)
        parallel_groups = [level for level in levels if len(level) > 1]
        return parallel_groups

    def calculate_complexity_metrics(self) -> Dict[str, Any]:
        """
        Calculate various complexity metrics for the dependency structure.

        Returns:
            Dictionary of complexity metrics
        """
        total_concepts = len(self.concepts)
        total_dependencies = sum(len(c.get('prerequisites', [])) for c in self.concepts)

        # Calculate average dependencies per concept
        avg_dependencies = total_dependencies / total_concepts if total_concepts > 0 else 0

        # Find longest dependency chain (critical path)
        def get_chain_length(concept_id: str, memo: Dict[str, int]) -> int:
            if concept_id in memo:
                return memo[concept_id]

            concept = self.concept_map.get(concept_id)
            if not concept:
                return 0

            prerequisites = concept.get('prerequisites', [])
            if not prerequisites:
                memo[concept_id] = 1
                return 1

            max_prereq_length = max(get_chain_length(p, memo) for p in prerequisites)
            length = max_prereq_length + 1
            memo[concept_id] = length
            return length

        memo = {}
        max_chain_length = max(get_chain_length(cid, memo) for cid in self.concept_map.keys())

        # Concepts with no dependencies
        independent_concepts = sum(1 for c in self.concepts if not c.get('prerequisites', []))

        # Concepts with no dependents
        leaf_concepts = sum(1 for cid in self.concept_map.keys()
                          if cid not in self.graph or not self.graph[cid])

        return {
            'total_concepts': total_concepts,
            'total_dependencies': total_dependencies,
            'average_dependencies_per_concept': round(avg_dependencies, 2),
            'max_dependency_chain_length': max_chain_length,
            'independent_concepts': independent_concepts,
            'leaf_concepts': leaf_concepts,
            'dependency_density': round(total_dependencies / (total_concepts * (total_concepts - 1))
                                       if total_concepts > 1 else 0, 3)
        }

    def get_concept_prerequisites_recursive(self, concept_id: str) -> Set[str]:
        """
        Get all prerequisites for a concept (including transitive dependencies).

        Args:
            concept_id: Concept identifier

        Returns:
            Set of all prerequisite concept IDs
        """
        all_prereqs = set()
        to_process = deque([concept_id])

        while to_process:
            current = to_process.popleft()
            concept = self.concept_map.get(current)
            if not concept:
                continue

            prerequisites = concept.get('prerequisites', [])
            for prereq in prerequisites:
                if prereq not in all_prereqs:
                    all_prereqs.add(prereq)
                    to_process.append(prereq)

        return all_prereqs

    def analyze(self) -> Dict[str, Any]:
        """
        Perform complete dependency analysis.

        Returns:
            Comprehensive analysis report
        """
        logger.info(f"Analyzing dependencies for {len(self.concepts)} concepts")

        circular_deps = self.find_circular_dependencies()
        orphaned = self.find_orphaned_concepts()
        suggested_order, sort_error = self.topological_sort()
        bottlenecks = self.find_bottleneck_concepts()
        parallel_paths = self.find_parallel_paths()
        metrics = self.calculate_complexity_metrics()

        # Determine overall validity
        has_errors = len(circular_deps) > 0 or len(orphaned) > 0

        analysis = {
            'valid': not has_errors,
            'circular_dependencies': circular_deps,
            'orphaned_concepts': orphaned,
            'suggested_order': suggested_order,
            'sort_error': sort_error,
            'bottleneck_concepts': bottlenecks[:10],  # Top 10 bottlenecks
            'parallel_learning_paths': parallel_paths,
            'complexity_metrics': metrics,
            'warnings': [],
            'recommendations': []
        }

        # Generate warnings
        if circular_deps:
            analysis['warnings'].append({
                'type': 'circular_dependency',
                'severity': 'error',
                'message': f"Found {len(circular_deps)} circular dependency chain(s)",
                'details': circular_deps
            })

        if orphaned:
            analysis['warnings'].append({
                'type': 'orphaned_concepts',
                'severity': 'error',
                'message': f"Found {len(orphaned)} concept(s) with missing prerequisites",
                'details': orphaned
            })

        if metrics['max_dependency_chain_length'] > 5:
            analysis['warnings'].append({
                'type': 'long_dependency_chain',
                'severity': 'warning',
                'message': f"Longest prerequisite chain is {metrics['max_dependency_chain_length']} concepts - learners may need significant time before reaching advanced topics"
            })

        # Generate recommendations
        if bottlenecks:
            top_bottleneck = bottlenecks[0]
            if top_bottleneck['dependent_count'] > 3:
                analysis['recommendations'].append({
                    'type': 'bottleneck_concept',
                    'message': f"Concept '{top_bottleneck['concept_title']}' is a prerequisite for {top_bottleneck['dependent_count']} other concepts. Consider providing extra practice and support.",
                    'concept_id': top_bottleneck['concept_id']
                })

        if parallel_paths:
            total_parallel_concepts = sum(len(group) for group in parallel_paths)
            analysis['recommendations'].append({
                'type': 'parallel_learning',
                'message': f"Identified {len(parallel_paths)} groups ({total_parallel_concepts} concepts total) that can be learned in parallel. Consider offering learners choice in their path."
            })

        if metrics['independent_concepts'] == 0 and len(self.concepts) > 1:
            analysis['recommendations'].append({
                'type': 'no_entry_points',
                'message': "All concepts have prerequisites. Consider adding foundational concepts with no dependencies for easier onboarding."
            })

        logger.info(f"Analysis complete: valid={analysis['valid']}, warnings={len(analysis['warnings'])}, recommendations={len(analysis['recommendations'])}")

        return analysis


def analyze_course_dependencies(course_id: str, concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze dependency structure for a course.

    Args:
        course_id: Course identifier
        concepts: List of concept metadata dictionaries

    Returns:
        Analysis report dictionary
    """
    analyzer = DependencyAnalyzer(concepts)
    return analyzer.analyze()
