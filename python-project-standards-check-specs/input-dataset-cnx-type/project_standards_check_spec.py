import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from collections import defaultdict
from project_advisor.pat_tools import md_print_list


class MyProjectStandardsCheckSpec(ProjectStandardsCheckSpec):
    """
    Write your own logic by modifying the body of the run() method.

    .. important::
        This class will be automatically instantiated by DSS, do not add a custom constructor on it.

    The superclass is setting those fields for you:
    self.config: the dict of the configuration of the object
    self.plugin_config: the dict of the plugin settings
    self.project: the current `DSSProject` to use in your check spec
    self.original_project_key: the project key of the original project

    .. note::
        self.project.project_key and self.original_project_key are different because Project Standards is never run on the original project.
        A temporary project will be created just to run checks on it and will be deleted afterward.
        If you are running Project Standards on a project, the temporary project is a copy of the original one.
        If you are running Project Standards on a bundle, the temporary project is a copy of the content of the bundle.
    """
    def _add(self, usage, connection, where):
        if connection:
            connection = str(connection).strip()
            if connection:
                usage[connection].add(where)
                
    def run(self):
        """
        Run the check

        :returns: the run result.
            Use `ProjectStandardsCheckRunResult.success(message)` or `ProjectStandardsCheckRunResult.failure(severity, message)` depending on the result.
            Use `ProjectStandardsCheckRunResult.not_applicable(message)` if the check is not applicable to the project.
            Use `ProjectStandardsCheckRunResult.error(message)` if you want to mark the check as an error. You can also raise an Exception.
        """
        
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')

        graph = self.project.get_flow().get_graph()
        source_dataset_ids = [d.id for d in graph.get_source_datasets()]
        
        input_connection_usage = defaultdict(set)
        details = {}
        acceptable_connetion_types = self.config['input_dataset_connection_types']
        
        if len(acceptable_connetion_types) == 0:
            return ProjectStandardsCheckRunResult.error(
                message = f"No connections selected. This check was not performed. Please ensure that an admin has configured connections in the Project Standard settings."
            )
        
        connection_types = []
        non_conforming_datasets = []
        non_conforming_connections = []
        for dataset in source_dataset_ids:
            connection_type = self.project.get_dataset(dataset).get_info().get_raw()['type']
            connection_types.append((connection_type))

            self._add(input_connection_usage, connection_type, dataset)
            
            if connection_type not in acceptable_connetion_types:
                non_conforming_datasets.append(dataset)
                non_conforming_connections.append(connection_type)
        
        num_non_conforming_datasets = len(non_conforming_datasets)
        non_conforming_connections = list(set(non_conforming_connections))
        non_conforming_datasets_md_formatted = md_print_list(non_conforming_datasets, "dataset", self.original_project_key)
        
        connection_types = list(set(connection_types))
        
        summary = {
                    conn: {
                        "total": len(tbls),
                        "tables": sorted(tbls)               
                    }
                    for conn, tbls in input_connection_usage.items()
                }
        
        for connection, locs in dict(summary).items():
            details[connection] = locs
        
        details['acceptable_connections'] = acceptable_connetion_types
        details['non_conformning_datasets'] = non_conforming_datasets_md_formatted
        details['non_conforming_connections'] = non_conforming_connections
        message = f"There is/are {num_non_conforming_datasets} input dataset(s) using non conforming connections."        
        
        if not source_dataset_ids:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = f"This project has no input datasets.",
                details = details
            )
        
        if not non_conforming_datasets:
            return ProjectStandardsCheckRunResult.success(
                message = "All input datasets in this project use an acceptable connection.",
                details = details
            )
        
        if num_non_conforming_datasets >= critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = message,
                details = details
            )
        elif num_non_conforming_datasets >= high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = message,
                details = details
            )
        elif num_non_conforming_datasets >= medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = message,
                details = details
            )
        elif num_non_conforming_datasets >= low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = message,
                details = details
            )
        elif num_non_conforming_datasets >= lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = message,
                details = details
            )

    
    
    
    
    
    
    
