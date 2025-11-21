from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.pat_tools import md_print_list, dss_obj_to_dss_obj_md_link

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
    def run(self):
        """
        Check if the project has any mergeable recipes
        """
        
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')
        
        all_datasets = self.project.list_datasets(as_type="objects")
        mergeable_recipes = []

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

                if (
                    parent_recipe_type in ["sampling", "distinct"]
                    and child_recipe_type in ["join", "grouping", "window"]
                ) or (
                    parent_recipe_type in ["join", "grouping", "window"]
                    and child_recipe_type in ["sampling", "distinct"]
                ):

                    parent_recipe_engine = (
                        self.project.get_recipe(parent_recipe_id)
                        .get_status().data.get("selectedEngine",{}).get("type")
                    )
                    child_recipe_engine = (
                        self.project.get_recipe(child_recipe_id)
                        .get_status().data.get("selectedEngine",{}).get("type")
                    )

                    if parent_recipe_engine == child_recipe_engine:
                        mergeable_recipes.append(
                            {
                                "dataset": dataset.name,
                                "parent_recipe": parent_recipe_id,
                                "child_recipe": child_recipe_id,
                                "engine": parent_recipe_engine,
                            }
                        )

        message = "Identified datasets where the input and output recipes could be combined:\n"
        for issue in mergeable_recipes:
            message += f"Dataset {dss_obj_to_dss_obj_md_link('dataset',self.original_project_key, issue['dataset'])} between recipe {dss_obj_to_dss_obj_md_link('recipe',self.original_project_key, issue['parent_recipe'])} and {dss_obj_to_dss_obj_md_link('recipe',self.original_project_key, issue['child_recipe'])} using engine '{issue['engine']}' could be optimized.\n"
        nbr_mergeable_recipes = len(mergeable_recipes)

        details = {
            "removable_datasets" : md_print_list([mr["dataset"] for mr in mergeable_recipes], "dataset", self.original_project_key),
            "nbr_mergeable_recipes" : len(mergeable_recipes),
            "raw_mergeable_recipes" : mergeable_recipes
        }

        if nbr_mergeable_recipes >= critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = message,
                details = details
            )
        elif nbr_mergeable_recipes >= high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = message,
                details = details
            )
        elif nbr_mergeable_recipes >= medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = message,
                details = details
            )
        elif nbr_mergeable_recipes >= low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = message,
                details = details
            )
        elif nbr_mergeable_recipes >= lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = message,
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = f"This project datasets doesn't have any reciped to merge",
                details = details
            )
        
