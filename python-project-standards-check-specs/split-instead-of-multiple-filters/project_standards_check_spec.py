import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.pat_tools import md_print_list

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
    def run(self):
        """
        Check if a split recipe ca replace multiple filters
        """
        
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')
        
        message = "No datasets with multiple filter recipes branching out from them could be identified."

        all_datasets = self.project.list_datasets(as_type="objects")
        merge_candidates = []
        removable_filters = 0
        for dataset in all_datasets:
            child_recipes = dataset.get_info().get_raw()["recipes"]
            if len(child_recipes) > 1:
                filter_recipes = 0
                for recipe in child_recipes:
                    if recipe["type"] == "sampling":
                        filter_recipes += 1
                if filter_recipes > 1:
                    merge_candidates.append(dataset.id)
                    removable_filters += filter_recipes - 1


        message = f"Identified {len(merge_candidates)} datasets that have 2+ filter recipes branching out from them. Consider replacing them with a split recipe to refactor {removable_filters} filters"

        details = {
            "merge_candidates": md_print_list(merge_candidates, "dataset", self.original_project_key),
            "total_removable_filters" : removable_filters
        }
        
        if removable_filters >= critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = message,
                details = details
            )
        elif removable_filters >= high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = message,
                details = details
            )
        elif removable_filters >= medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = message,
                details = details
            )
        elif removable_filters >= low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = message,
                details = details
            )
        elif removable_filters >= lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = message,
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = f"No filter recipes to refactor as split recipes",
                details = details
            )
        
