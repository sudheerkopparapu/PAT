import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from typing import List

from project_advisor.pat_tools import md_print_list

class MyProjectStandardsCheckSpec(ProjectStandardsCheckSpec):

    def run(self):
        """
        Runs the check to identify recipes that could leverage SQL push-down computation.
        """
        
        recipe_types_to_check = [
            "shaker",
            "sampling",
            "grouping",
            "window",
            "join",
            "distinct",
            "split",
            "topn",
            "sort",
            "pivot",
            "vstack",
        ]
        
        recipe_items = [
            r for r in self.project.list_recipes() if r.type in recipe_types_to_check
        ]
        sql_recipes = []
        flagged_recipes = []

        for r in recipe_items:
            r = r.to_recipe()
            recipe_status = r.get_status()
            try:
                selected_engine_type = recipe_status.get_selected_engine_details()[
                    "type"
                ]
            except:
                selected_engine_type = "not_selected"
            all_selectable_engine_types = [
                e["type"]
                for e in recipe_status.get_engines_details()
                if e["isSelectable"] and e["statusWarnLevel"] == "OK"
            ]
            if "SQL" in all_selectable_engine_types:
                sql_recipes.append({
                        "name": r.name,
                        "type": r.get_settings().type,
                        "engine": selected_engine_type,
                    })
            if "SQL" in all_selectable_engine_types and "SQL" != selected_engine_type:
                flagged_recipes.append(
                    {
                        "name": r.name,
                        "type": r.get_settings().type,
                        "engine": selected_engine_type,
                    }
                )
        
        recipe_names = [recipe['name'] for recipe in recipe_items]
        sql_recipe_names = [recipe["name"] for recipe in sql_recipes]
        flagged_recipe_names = [recipe["name"] for recipe in flagged_recipes]
        
        if not sql_recipe_names:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = f"This project has no recipes where SQL push-down computation is possible.",
                details = {"recipes_checked": recipe_names}
            )
        
        if not flagged_recipes:
            return ProjectStandardsCheckRunResult.success(
                message = "All recipes leverage SQL push-down computation where possible.",
                details = {"recipes_checked": sql_recipe_names}
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = f"Identified {len(flagged_recipes)} recipe(s) that could leverage SQL push-down computation.",
                    details = {"recipes_to_review" : md_print_list(flagged_recipe_names,'recipe',self.original_project_key)}
                )
        
        
        
