from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.pat_tools import md_print_list

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
    def run(self):
        """
        Runs the check to determine if Python recipes are under a specified number of rows.
        """
        
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')
        
        details = {}

        python_recipes = []
        for recipe in self.project.list_recipes():
            if recipe["type"] == "python":
                python_recipes.append(recipe)
        
        details["nbr_py_recipes"] = len(python_recipes)

        if not python_recipes:
            return ProjectStandardsCheckRunResult.not_applicable(
                message =   f"The project does not contain python recipes",
                details = details
            )
        
        big_python_recipes = []
        python_recipe_row_count = []
        for recipe in python_recipes:
            recipe_name = recipe["name"]
            recipe = self.project.get_recipe(recipe_name)
            settings = recipe.get_settings()
            python_code = settings.get_code()
            if python_code == None:
                python_code = ""
            lines = python_code.split("\n")
            lines = [line for line in lines if line != ""]
            lines = [line for line in lines if not line.startswith("#")]
            lines = [line for line in lines if not line.startswith("import")]
            lines = [line for line in lines if not line.startswith("from")]
            recipe_py_lines = len(lines)
            python_recipe_row_count.append(recipe_py_lines)
            if len(lines) > lowest_threshold:
                big_python_recipes.append(recipe_name)
        
        
        nbr_big_py_recipes = len(big_python_recipes)
        
        max_row_count = max(python_recipe_row_count)
        avg_row_count = sum(python_recipe_row_count)/len(python_recipes)

        
        details["big_python_recipes"] = md_print_list(big_python_recipes, "recipe", self.original_project_key)
        details["nbr_big_py_recipes"] = nbr_big_py_recipes
        details["max_row_count"] = max_row_count
        details["avg_row_count"] = avg_row_count
        
        error_message = f"{nbr_big_py_recipes} too big python recipe(s) have been identified. See Details."
        
        if max_row_count > critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = error_message,
                details = details
            )
        elif max_row_count > high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = error_message,
                details = details
            )
        elif max_row_count > medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = error_message,
                details = details
            )
        elif max_row_count > low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = error_message,
                details = details
            )
        elif max_row_count > lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = error_message,
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = f"All python recipes in the Flow are under {int(lowest_threshold)} lines of code.",
                details = details
            )
        
