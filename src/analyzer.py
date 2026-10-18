class DependencyAnalyzer:
    """
    Analyzes documented dependencies between application components.

    The analyzer is environment-independent.
    """

    def __init__(self, components, dependencies):
        self.components = components
        self.dependencies = dependencies
        self.graph = self.build_graph()

    def build_graph(self):
        """
        Build an adjacency list representing change-impact relationships.
        """

        # Register every component, including isolated components.
        graph = {component["id"]: [] for component in self.components}

        # Add documented dependency relationships.
        for dependency in self.dependencies:
            source = dependency["source"]
            target = dependency["target"]

            if source not in graph:
                raise ValueError(f"Unknown source component: {source}")

            if target not in graph:
                raise ValueError(f"Unknown target component: {target}")

            graph[source].append(target)

        return graph

    def find_impacted_components(self, component_id):
        """
        Discover downstream components and preserve impact paths.
        """

        if component_id not in self.graph:
            raise ValueError(f"Unknown component: {component_id}")

        impacts = {}

        def visit(current, path):
            for neighbor in self.graph[current]:

                # Prevent infinite loops caused by circular dependencies.
                if neighbor in path:
                    continue

                next_path = path + [neighbor]

                if neighbor not in impacts:
                    impacts[neighbor] = {
                        "component_id": neighbor,
                        "paths": []
                    }

                if next_path not in impacts[neighbor]["paths"]:
                    impacts[neighbor]["paths"].append(next_path)

                visit(neighbor, next_path)

        visit(component_id, [component_id])

        for impact in impacts.values():
            path_lengths = [
                len(path) - 1
                for path in impact["paths"]
            ]

            impact["impact_types"] = []

            if 1 in path_lengths:
                impact["impact_types"].append("DIRECT")

            if any(length > 1 for length in path_lengths):
                impact["impact_types"].append("INDIRECT")

        return list(impacts.values())