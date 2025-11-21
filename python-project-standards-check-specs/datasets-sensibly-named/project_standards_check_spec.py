from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.pat_tools import md_print_list
import re


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

        # Define the regex pattern
        pattern = self.config.get('pattern')
        # connections to consider
        connections_in_scope = self.config.get('connection_types')
        
        # collect relevant details
        details = {}
        non_conforming_names = []
        connections = []

        datasets = [dataset for dataset in self.project.list_datasets() if dataset['type'] in connections_in_scope]

        # Check each dataset name
        for dataset in datasets:
            if re.fullmatch(pattern, dataset['name']):
                continue
            else:
                non_conforming_names.append(dataset['name'])
                connections.append(dataset['type'])
        
        connections = list(set(connections))
        num_non_conforming_dataset_names = len(non_conforming_names)
        non_conforming_datasets_md_formatted = md_print_list(non_conforming_names, "dataset", self.original_project_key)
        
        details['datasets_to_consider_renaming'] = non_conforming_datasets_md_formatted
        message = f"There is/are {num_non_conforming_dataset_names} input dataset(s) using a non conforming naming convention. Consider renaming them."

        if not non_conforming_names:
            return ProjectStandardsCheckRunResult.success(
                message = "All input datasets use the appropriate naming convention specified.",
                details = details
            )
        
        if num_non_conforming_dataset_names >= critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = message,
                details = details
            )
        elif num_non_conforming_dataset_names >= high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = message,
                details = details
            )
        elif num_non_conforming_dataset_names >= medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = message,
                details = details
            )
        elif num_non_conforming_dataset_names >= low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = message,
                details = details
            )
        elif num_non_conforming_dataset_names >= lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = message,
                details = details
            )
        
        
 

                
                
                
