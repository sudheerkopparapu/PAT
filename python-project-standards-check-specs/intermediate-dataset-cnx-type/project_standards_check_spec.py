import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)
from project_advisor.pat_tools import md_print_list

from typing import Dict, Tuple, List, Any

from collections import namedtuple

Dataset = namedtuple("Dataset", "name type")


class ProjectStandardsCheck(ProjectStandardsCheckSpec):

    def _get_intermediate_dataset(self) -> List[namedtuple]:
        """
        Get all datasets with successor nodes and predecessor nodes.
        Include datasets without predecessor nodes if
        self.include_output_datasets == True
        """

        intermediate_datasets = []

        for dataset in self.all_project_datasets:
            node = self.project_flow_nodes[dataset.name]
            predecessors = node.get("predecessors", [])
            successors = node.get("successors", [])
            if len(predecessors) > 0 and len(successors) > 0:
                intermediate_datasets.append(dataset)
            elif len(predecessors) > 0 and self.include_output_datasets:
                intermediate_datasets.append(dataset)

        return intermediate_datasets

    def _get_non_conforming_datasets(self, intermediate_datasets: List[namedtuple]):

        return [
            dataset.name
            for dataset in intermediate_datasets
            if dataset.type not in self.intermediate_dataset_connection_type
        ]

    def _get_severity(self, value: int) -> int:
        """
        Return severity code based on criticality thresholds
        """
        lowest_threshold = self.config.get("lowest")
        low_threshold = self.config.get("low")
        medium_threshold = self.config.get("medium")
        high_threshold = self.config.get("high")
        critical_threshold = self.config.get("critical")
        severities_thresholds = [
            critical_threshold,
            high_threshold,
            medium_threshold,
            low_threshold,
            lowest_threshold,
        ]

        for i in range(0, len(severities_thresholds)):
            if value >= severities_thresholds[i]:

                return 5 - i
        return 0

    def _get_run_result(
        self,
        non_conforming_datasets: List[str],
        run_details: List[str],
    ) -> Any:
        """
        Determine whether check passed based on num_non_conforming_datasets
        """
        num_non_conforming_datasets = len(non_conforming_datasets)

        if num_non_conforming_datasets > 0:
            message = f"There is/are {num_non_conforming_datasets} non-conforming intermediate dataset(s)"

            return ProjectStandardsCheckRunResult.failure(
                severity=self._get_severity(num_non_conforming_datasets),
                message=message,
                details=run_details,
            )

        else:
            return ProjectStandardsCheckRunResult.success(
                message=f"All intermediate datasets conform to the selected connection type: {self.intermediate_dataset_connection_type}",
                details=run_details,
            )

    def run(self):

        self.include_output_datasets = self.config.get("include_output_datasets")
        self.intermediate_dataset_connection_type = self.config.get(
            "intermediate_dataset_connection_type"
        )
        
        if len(self.intermediate_dataset_connection_type) == 0:
            return ProjectStandardsCheckRunResult.error(
                message = f"No connections selected. This check was not performed. Please ensure that an admin has configured connections in the Project Standard settings."
            )
        
        
        self.project_flow_nodes = self.project.get_flow().get_graph().nodes
        self.all_project_datasets = [
            Dataset(name=dataset.get("name"), type=dataset.get("type"))
            for dataset in self.project.list_datasets()
        ]

        intermediate_datasets = self._get_intermediate_dataset()
        non_conforming_datasets = self._get_non_conforming_datasets(
            intermediate_datasets
        )
        non_conforming_datasets_md_formatted = md_print_list(non_conforming_datasets,"dataset", self.original_project_key)
         
        #[
        #    dss_obj_to_dss_obj_md_link("dataset", self.original_project_key, name, name)
        #    for name in non_conforming_datasets
        #]
        run_details = {
            "non_conforming_datasets": non_conforming_datasets_md_formatted,
        }

        return self._get_run_result(non_conforming_datasets, run_details)
