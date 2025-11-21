import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.pat_tools import md_print_list

class ProjectStandardsCheck(ProjectStandardsCheckSpec):

    def run(self):
        """
        Check if prepare recipes have no more than X top level steps.
        """
        max_nbr_top_level_steps_prepare_recipe = int(self.config.get("max_top_level_steps"))
        
        # Get a list of all prepare recipes in the project
        prepare_recipes = [recipe.name for recipe in self.project.list_recipes() if recipe.type == 'shaker']

        offending_prepare_recipes = []
        total_steps_count = []
        total_top_level_count = []
        
        for recipe_name in prepare_recipes:
            prep_recipe_settings = self.project.get_recipe(recipe_name).get_settings()
            top_level_steps = prep_recipe_settings.raw_steps
            step_count = 0
            for s in top_level_steps:
                step_count += len(s.get("steps", [])) if s.get("metaType") == "GROUP" else 1
            total_steps_count.append(step_count)
            total_top_level_count.append(len(top_level_steps))
            if len(top_level_steps) > max_nbr_top_level_steps_prepare_recipe:
                offending_prepare_recipes.append(recipe_name)

        details = {
            "offending_prepare_recipes" : md_print_list(offending_prepare_recipes, "recipe", self.original_project_key)
        }
        if prepare_recipes:
            details.update({
                "nbr_of_prepare_recipes" : len(prepare_recipes),
                "max_total_steps" : max(total_steps_count),
                "max_top_level_steps" : max(total_top_level_count),
                "avg_total_steps" : sum(total_steps_count)/len(total_steps_count)
            })
        
        if offending_prepare_recipes:
            return ProjectStandardsCheckRunResult.failure(
                severity = int(self.config.get("severity")), 
                message = f"Found {len(offending_prepare_recipes)} prepare recipes with more than {max_nbr_top_level_steps_prepare_recipe} top level steps",
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = f"All prepare recipes have less than {max_nbr_top_level_steps_prepare_recipe} top level steps",
                details = details
            )


