from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.pat_tools import md_print_list

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
 
    def find_connected_datasets(self, nodes: dict, node_id: str, direction: str = "upstream") -> list:
        """
        Uses Depth-First Search (DFS) to traverse the graph and find all datasets
        that are either upstream or downstream of a specified node.
        """
        visited = set()
        connected_nodes = []
        def dfs(current_id):
            visited.add(current_id)
            current_node = nodes.get(current_id)
            if current_node: # Only if the node exists in the graph
                if direction == "upstream":
                    neighbors = current_node.get("predecessors")
                else:
                    neighbors = current_node.get("successors")

                for neighbor_id in neighbors:
                    if neighbor_id not in visited:
                        dfs(neighbor_id)
                connected_nodes.append(current_id)
            else:
                pass

        dfs(node_id)
        return connected_nodes
    
    def get_item_ids_in_scenarios_with_build_step(self) -> list:
        """
        Retrieves the IDs of items built in scenarios with a build step.
        """
        scenarios = self.project.list_scenarios(as_type="objects")
        items = []

        for s in scenarios:
            scenario_settings = s.get_settings().get_raw()
            if scenario_settings.get("type") == "step_based":
                for step in scenario_settings.get("params",{}).get("steps"):
                    if step.get("type") == "build_flowitem" and step.get("enabled") == True:
                        for build in step.get("params",{}).get("builds"):
                            item = {
                                "id": build.get("itemId"),
                                "item_type" : build.get("type"),
                                "job_type": step.get("params",{}).get("jobType"),
                            }
                            items.append(item)
        return items
        

    def run(self):
        """
        Runs the check to ensure all datasets are either explicitly built or are part of the dependencies of a build job in a scenario.
        """

        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')
        
        message = "All datasets in this project are either explicitly built or are part of the dependencies of a build step in a scenario."
        result = {}

        nodes = self.project.get_flow().get_graph().nodes
        items_to_check = self.get_item_ids_in_scenarios_with_build_step()
        datasets_used = [d.get("id") for d in items_to_check if d.get("build_type") == "DATASET"]
        datasets_all = [
            d_id for d_id in nodes if nodes.get(d_id,{}).get("type") == "COMPUTABLE_DATASET"
        ]

        for d in items_to_check:
            if d.get("job_type") in ["RECURSIVE_BUILD", "RECURSIVE_FORCED_BUILD"]:
                datasets_upstream = self.find_connected_datasets(nodes, d.get("id"), direction = "upstream")
                datasets_used += datasets_upstream
            elif d["job_type"] in ["REVERSE_FORCED_BUILD"]:
                datasets_downstream = self.find_connected_datasets(
                    nodes, d["id"], direction="downstream"
                )
                datasets_used += datasets_downstream
            elif d.get("job_type") == "NON_RECURSIVE_FORCED_BUILD":
                datasets_used += [d.get("id")]
        datasets_unused = list(set(datasets_all) - set(datasets_used))
        
        nbr_datasets_unused = len(datasets_unused)

        result["datasets_unused"] = md_print_list(datasets_unused, "dataset", self.project.project_key)
        result["nbr_datasets_unused"] = len(datasets_unused)
        message = f"{len(datasets_unused)} datasets in this project are not covered by a scenario (unused). See Details."
        if nbr_datasets_unused > critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = message,
                details = result
            )
        elif nbr_datasets_unused > high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = message,
                details = result
            )
        elif nbr_datasets_unused > medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = message,
                details = result
            )
        elif nbr_datasets_unused > low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = message,
                details = result
            )
        elif nbr_datasets_unused > lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = message,
                details = result
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = f"All datasets in this project are used!",
                details = result
            )
        
