import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from dataikuapi.dss.flow import DSSProjectFlowGraph
from dataikuapi.dss.project import DSSProject

from project_advisor.pat_tools import md_print_list

class MyProjectStandardsCheckSpec(ProjectStandardsCheckSpec):

    def get_output_dataset_ids(self, graph: DSSProjectFlowGraph) -> list:
        """
        Retrieves the IDs of output datasets in the project's flow.
        """
        nodes = graph.nodes
        output_dataset_ids = []

        for node_id in nodes.keys():
            if (
                "DATASET" in nodes[node_id]["type"]
                and len(nodes[node_id]["successors"]) == 0
            ):
                output_dataset_ids.append(nodes[node_id]["ref"])

        return output_dataset_ids
    
    def get_published_dataset_ids(self, project: DSSProject) -> list:
        """
        Retrieves the IDs of published datasets in the project's flow.
        """
        return [d["name"] for d in project.list_datasets() if d["featureGroup"]]
    
    def get_dataset_ids_in_scenarios_with_check_step(self) -> set:
        """
        Retrieves the IDs of datasets verified in scenarios with check steps.

        :return: A set of dataset IDs.
        :rtype: set
        """
        scenarios = self.project.list_scenarios(as_type="objects")
        dataset_ids = []

        for s in scenarios:
            scenario_settings = s.get_settings().get_raw()
            if scenario_settings["type"] == "step_based":
                for step in scenario_settings["params"]["steps"]:
                    if step["type"] == "check_dataset":
                        for check in step["params"]["checks"]:
                            dataset_ids.append(check["itemId"])

        return set(dataset_ids)
    
    def run(self):
        """
        Runs the check to ensure input, shared, and output datasets have data quality rules.
        """
       
        details = {}

        # find all input (source), output and published (shared) datasets
        graph = self.project.get_flow().get_graph()
        source_dataset_ids = [d.id for d in graph.get_source_datasets()]
        output_dataset_ids = self.get_output_dataset_ids(graph)
        published_dataset_ids = self.get_published_dataset_ids(self.project)
        
        # Find unconnected datasets.
        unconnected_datasets = set(source_dataset_ids) & set(output_dataset_ids)
        # removed unconnected datasets from input and output lists
        source_dataset_set = set(source_dataset_ids) - unconnected_datasets
        output_dataset_set = set(output_dataset_ids) - unconnected_datasets
        
        # add details
        details["source_datasets"] = list(source_dataset_set)
        details["output_datasets"] = list(output_dataset_set)
        details["published_dataset"] = published_dataset_ids
        
        # datasets with check step in a scenario
        scenario_verified_dataset_ids = self.get_dataset_ids_in_scenarios_with_check_step()
        
        # identify the datasets to check
        to_check_dataset_ids = set()
        datasets_to_consider = self.config["datasets_to_consider"]
        if "input" in datasets_to_consider:
            to_check_dataset_ids.update(source_dataset_set)
        if "output" in datasets_to_consider:
            to_check_dataset_ids.update(output_dataset_set)
        if "shared" in datasets_to_consider:
            to_check_dataset_ids.update(published_dataset_ids)
        
        if not to_check_dataset_ids:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = f"This project has no input, output or shared datasets.",
                details = details
            ) 
           
        # datasets with no data quality check scenario step
        non_verified_dataset_ids = to_check_dataset_ids - scenario_verified_dataset_ids
        # Remove all imported datasets from another project.
        to_check_dataset_ids = [d_id for d_id in to_check_dataset_ids if "." not in d_id]
          
        # compute coverage
        if to_check_dataset_ids:
            coverage = 100 - (len(non_verified_dataset_ids)/len(to_check_dataset_ids))*100
        else:
            coverage=100
       
        details["coverage"] = str(coverage) + '%'
        details["no_checks_datasets"] = list(non_verified_dataset_ids)
        details['add_data_quality_checks_datasets'] = md_print_list(non_verified_dataset_ids,'dataset',self.original_project_key)
        
        target_coverage = self.config.get("coverage")
        if coverage == 100:
            return ProjectStandardsCheckRunResult.success(
                message = f"The project has {int(coverage)}% data quality check scenario step coverage.",
                details = details
            )
        elif coverage >=target_coverage:
            return ProjectStandardsCheckRunResult.success(
                message = f"The project has a {int(coverage)}% data quality check scenario step coverage which is equal to or above the target coverage of {int(target_coverage)}.",
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                severity = int(self.config.get("severity")), 
                message = f"The project has a {int(coverage)}% data quality check scenario step coverage which is below the target of coverage of {int(target_coverage)}%",
                details = details
            )

