import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.pat_tools import md_print_list
from collections import Counter


class MyProjectStandardsCheckSpec(ProjectStandardsCheckSpec):

    def run(self):
        """
        Check that project doesn't have any recipe with status ERROR.
        
        """     
        
        error_recipes = []
        error_status = []
        details = {}
        
        recipes = self.project.list_recipes(as_type='objects') 
        
        #Checking Engine Status for All Project Recipes
        for recipe in recipes:
            try:
                recipe_status = recipe.get_status().get_selected_engine_details().get('statusWarnLevel')
                recipe_name = recipe.name
                if recipe_status != 'OK':
                    error_recipes.append(recipe_name, recipe_status)
                    error_status.append(recipe_status)
                
            except Exception as e:
                # Recipe status could not be checked - Ignore
                pass # This can happen for virtual recipes (e.g., link) that have no engine


        # Create a Counter object
        error_status_counter = Counter(error_status) 
        details["incorrect_recipes"] = md_print_list(error_recipes, "recipe", self.original_project_key)
        details.update(error_status_counter)
        error_count = len(error_recipes)
        if error_count==0:
            return ProjectStandardsCheckRunResult.success(
                message = "All recipe engines are OK"
            )
        
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = f"Identified {error_count} recipe(s) with incorrect Engine status.",
                    details = details
                )
            
