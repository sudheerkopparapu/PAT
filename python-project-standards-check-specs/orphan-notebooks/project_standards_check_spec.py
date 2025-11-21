import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.pat_tools import md_print_list

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
    def run(self):
        """
        Check that the project doesn't have any orphan notebooks
        """

        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')
        
        """
        Find all the Notebooks that are not assiciated with a Code Recipe or exported in a scenario step.
        """
        # List notebooks executed in a scenario
        exported_notebooks = []
        for scenario in self.project.list_scenarios(as_type = "objects"):
            if scenario.get_definition().get("type") == "step_based":
                for step in scenario.get_settings().raw_steps:
                    if (step.get("type") == "create_jupyter_export" 
                        and step.get("params",{}).get("executeNotebook") == True) :
                        exported_notebooks.append(step.get("params",{}).get("notebookId"))


        # List recipe editor notebooks
        recipe_editor_notebooks = []
        for n in self.project.list_jupyter_notebooks():
            associated_recipe = n.get_content().get_raw().get('metadata',{}).get('associatedRecipe')
            if associated_recipe != None:
                recipe_editor_notebooks.append(n.notebook_name)


        all_notebooks = [n.notebook_name for n in self.project.list_jupyter_notebooks()]
        orphan_notebooks = list(set(all_notebooks) - set(recipe_editor_notebooks + exported_notebooks))

        details = {
            "all_notebooks" : ", ".join(all_notebooks),
            "orphan_notebooks" : md_print_list(orphan_notebooks, "jupyter_notebook", self.original_project_key),
            "recipe_notebooks" : md_print_list(recipe_editor_notebooks, "jupyter_notebook", self.original_project_key),
            "exported_notebooks" : md_print_list(exported_notebooks, "jupyter_notebook", self.original_project_key)
        }
        
        count = len(orphan_notebooks)
        error_message = f"Out of the {len(all_notebooks)} notebooks there are {len(orphan_notebooks)} that are orphan notebooks."

        if count >= critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = error_message,
                details = details
            )
        elif count >= high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = error_message,
                details = details
            )
        elif count >= medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = error_message,
                details = details
            )
        elif count >= low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = error_message,
                details = details
            )
        elif count >= lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = error_message,
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = f"There are no orphan notebooks, all notebooks are linked to a recipe OR a scenario step",
                details = details
            )
        
