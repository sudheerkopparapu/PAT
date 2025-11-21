import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.pat_tools import dss_obj_to_dss_obj_md_link

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
    def run(self):
        """
        Runs the check to determine if there are any consecutive prepare recipes using the same computation engine.
        """
        
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')
        
        all_datasets = self.project.list_datasets(as_type="objects")
        consecutive_prepare_issues = []

        for dataset in all_datasets:

            child_recipes = dataset.get_info().get_raw()["recipes"]
            parent_recipes = []
            try:
                parent_recipes.append(dataset.get_info().get_raw()["creatingRecipe"])
            except KeyError:
                pass

            if len(parent_recipes) == 1 and len(child_recipes) == 1:
                parent_recipe_id = parent_recipes[0]["id"]
                parent_recipe_type = parent_recipes[0]["type"]
                child_recipe_id = child_recipes[0]["id"]
                child_recipe_type = child_recipes[0]["type"]

                if parent_recipe_type == "shaker" and child_recipe_type == "shaker":
                    parent_recipe_engine = (
                        self.project.get_recipe(parent_recipe_id)
                        .get_status()
                        .get_selected_engine_details()["type"]
                    )
                    child_recipe_engine = (
                        self.project.get_recipe(child_recipe_id)
                        .get_status()
                        .get_selected_engine_details()["type"]
                    )

                    if parent_recipe_engine == child_recipe_engine:
                        consecutive_prepare_issues.append(
                            {
                                "dataset": dataset.name,
                                "parent_recipe": parent_recipe_id,
                                "child_recipe": child_recipe_id,
                                "engine": parent_recipe_engine,
                            }
                        )


        nbr_removable_datasets = len(consecutive_prepare_issues)
        message = "Identified datasets between two prepare recipes that could be combined:\n"
        for issue in consecutive_prepare_issues:
            message += f"Dataset {dss_obj_to_dss_obj_md_link('dataset',self.original_project_key, issue['dataset'])} between prepare recipe {dss_obj_to_dss_obj_md_link('recipe',self.original_project_key, issue['parent_recipe'])} and {dss_obj_to_dss_obj_md_link('recipe',self.original_project_key, issue['child_recipe'])} using engine '{issue['engine']}' could be optimized.\n"

        details = {
            "consecutive_prepare_issues": consecutive_prepare_issues,
            "nbr_removable_datasets" : nbr_removable_datasets
        }
        
        if nbr_removable_datasets >= critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = message,
                details = details
            )
        elif nbr_removable_datasets >= high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = message,
                details = details
            )
        elif nbr_removable_datasets >= medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = message,
                details = details
            )
        elif nbr_removable_datasets >= low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = message,
                details = details
            )
        elif nbr_removable_datasets >= lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = message,
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = f"No consecutive prepare recipes with the same computation engine can be merged",
                details = details
            )
        
