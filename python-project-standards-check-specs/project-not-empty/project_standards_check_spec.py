from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

class ProjectStandardsCheck(ProjectStandardsCheckSpec):

    def run(self):
        """
        A project is not empty when is has:
        - No managed Folders
        - No datasets
        - No recipes 
        - No notebooks
        - No webapps
        - No Scenarios
        - No Wikis
        """
        
        nbr_managed_folders = len(self.project.list_managed_folders())
        nbr_dataset = len(self.project.list_datasets())
        nbr_recipes = len(self.project.list_recipes())
        nbr_notebooks = len(self.project.list_jupyter_notebooks())
        nbr_webapps = len(self.project.list_webapps())
        nbr_scenarios = len(self.project.list_scenarios())
        nbr_wiki_articles = len(self.project.get_wiki().list_articles())
        
        message = "Project is not empty"
        check_pass = True
        if (nbr_managed_folders == 0
            and nbr_dataset == 0
            and nbr_recipes == 0
            and nbr_notebooks  == 0
            and nbr_webapps  == 0
            and nbr_scenarios  == 0
            and nbr_wiki_articles  == 0):
            message = "Project is empty as it doesn't have a managed folders, dataset, recipe, notebook, webapp, scenario or wiki article"
            check_pass = False

        run_result = {"nbr_managed_folders" : nbr_managed_folders, 
                      "nbr_dataset" : nbr_dataset, 
                      "nbr_recipes" : nbr_recipes, 
                      "nbr_notebooks" : nbr_notebooks, 
                      "nbr_webapps" : nbr_webapps, 
                      "nbr_scenarios" : nbr_scenarios, 
                      "nbr_wiki_articles" : nbr_wiki_articles
                     }

        if check_pass:
            return ProjectStandardsCheckRunResult.success(
                message = message,
                details = run_result
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = message,
                    details = run_result
                )

