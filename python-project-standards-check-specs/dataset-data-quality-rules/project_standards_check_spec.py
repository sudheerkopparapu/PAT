from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from dataikuapi.dss.flow import DSSProjectFlowGraph
from dataikuapi.dss.project import DSSProject

from project_advisor.pat_tools import md_print_list

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
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
    
    def run(self):
        """
        Runs the check to ensure input, shared, and output datasets have data quality rules.
        """

        details = {}

        graph = self.project.get_flow().get_graph()
        source_dataset_ids = [d.id for d in graph.get_source_datasets()]
        output_dataset_ids = self.get_output_dataset_ids(graph)
        published_dataset_ids = self.get_published_dataset_ids(self.project)

        # Find unconnected datasets.
        unconnected_datasets = set(source_dataset_ids) & set(output_dataset_ids)
        
        source_dataset_set = set(source_dataset_ids) - unconnected_datasets
        output_dataset_set = set(output_dataset_ids) - unconnected_datasets
        details["source_datasets"] = md_print_list(source_dataset_set,"dataset",self.original_project_key)
        details["output_datasets"] = md_print_list(output_dataset_set,"dataset",self.original_project_key)
        details["published_dataset"] = md_print_list(published_dataset_ids,"dataset",self.original_project_key)

        to_check_dataset_ids = set()
        datasets_to_consider = self.config["datasets_to_consider"]
        if "input" in datasets_to_consider:
            to_check_dataset_ids.update(source_dataset_set)
        if "output" in datasets_to_consider:
            to_check_dataset_ids.update(output_dataset_set)
        if "shared" in datasets_to_consider:
            to_check_dataset_ids.update(published_dataset_ids)
                  
        # Remove all imported datasets from another project.
        
        to_check_dataset_ids = [d_id for d_id in to_check_dataset_ids if "." not in d_id]
        
        no_rules_dataset_ids = []
        if to_check_dataset_ids:
            for d_id in to_check_dataset_ids:
                d = self.project.get_dataset(d_id)
                if not d.get_data_quality_rules().list_rules():
                    no_rules_dataset_ids.append(d_id)
            coverage = 100 - (len(no_rules_dataset_ids)/len(to_check_dataset_ids))*100
        else:
            coverage = 100
        

        details["coverage"] = coverage
        details["no_rules_datasets"] = md_print_list(no_rules_dataset_ids,"dataset",self.original_project_key)

        target_coverage = self.config.get("coverage")
        if coverage >=target_coverage:
            return ProjectStandardsCheckRunResult.success(
                message = f"The project has a {int(coverage)}% data quality coverage rule coverage with {len(no_rules_dataset_ids)} datasets missing data quality rules",
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = f"The project has a data quality coverage of {int(coverage)}% which is under the target of coverage of{int(target_coverage)}%. \nAdd Data quality rules to : {md_print_list(no_rules_dataset_ids,'dataset',self.original_project_key)}",
                    details = details
                )

