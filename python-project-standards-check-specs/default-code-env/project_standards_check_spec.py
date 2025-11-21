import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.pat_tools import md_print_list

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
        
    def get_recipe_by_type(self, recipe_type: str) -> bool:
        """
        Returns the list of recipe with the specified type
        """
        return [recipe["name"] for recipe in self.project.list_recipes() if recipe["type"] == recipe_type]
    
    def get_scenario_by_type(self, scenario_type: str) -> bool:
        """
        Returns the list of scenarios with the specified type
        """
        return [scenario["id"] for scenario in self.project.list_scenarios() if scenario['type'] == scenario_type ]
    

    def run(self):
        """
        Check that the project has a default code env if code is used in the project.
        """
        
        # Fetch the settings for Python and R code environments
        code_envs_settings = self.project.get_settings().get_raw().get('settings').get('codeEnvs')
        python_code_env_settings = code_envs_settings.get('python')
        r_code_env_settings = code_envs_settings.get('r')
        
        details = {}

        # Determine if Python or R recipes/scenarios exist
        python_recipes = self.get_recipe_by_type("python")
        python_scenarios = self.get_scenario_by_type("custom_python")
        r_recipes = self.get_recipe_by_type("r")
        
        details["python_recipes"] = md_print_list(python_recipes, "recipe", self.original_project_key)
        details["python_scenarios"] = md_print_list(python_scenarios, "scenario", self.original_project_key)
        details["r_recipes"] = md_print_list(r_recipes, "recipe", self.original_project_key)
        
        has_python = len(python_recipes) >0 or len(python_scenarios) >0
        has_r = len(r_recipes)>0
        
        details["has_python"] = has_python
        details["has_r"] = has_r

        # Initialize the check_pass flag
        check_pass = True
        
        if has_python or has_r:
            message = "The project contains:\n"
            
            # Validate the environment settings for Python
            if has_python:
                if (not python_code_env_settings.get('mode') or python_code_env_settings.get('mode') != "EXPLICIT_ENV"):
                    check_pass = False
                    message += "python code and is missing a default project level code env\n"
                else:
                    message += "python code and a default project level code env has been set\n"


            # Validate the environment settings for R
            if has_r:
                if (not r_code_env_settings.get('mode') or r_code_env_settings.get('mode') != "EXPLICIT_ENV"):
                    check_pass = False
                    message += "R code and is missing default project level code env\n"
                else:
                    message += "R code and a default project level code env has been set\n"
        else:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = f"Skipping check as the project doesn't contain python or R code",
                details = details
            )

        if check_pass:
            return ProjectStandardsCheckRunResult.success(
                message = message,
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = message,
                    details = details
                )


