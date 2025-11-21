import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig 
    
    
class NumberRecipesContainerizedExec(ProjectMetric):
    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject
    ):
        super().__init__(
            client = client,
            config = config,
            project = project,
            name = "nbr_recipes_with_containerized_exec",
            metric_type = AssessmentMetricType.INT,
            description = "Number of recipes with Containerized Exec",
            dss_version_min = Version("12.0.0"),
            dss_version_max = None,
            tags = ["DESIGN_PATTERN"]
        )

    def run(self) -> ProjectMetric:
        """
        Finds all the recipes in the Flow that use containerized exec.
        Recipes that can use containerized execution are:
        - Visual recipes. (When the DSS engine is selected and the project setting for recipes is Containerized)
        - Code recipes.
        - Plugin recipes.
        """
        default_project_visual_recipe_exec_config = self.get_default_project_visual_exec_config(self.project)
        default_project_code_recipe_exec_config = self.get_default_project_code_exec_config(self.project)
       
        containerized_recipes = []
        for r in self.project.list_recipes(as_type = "objects"):

            # Get recipe engine
            engine = r.get_status().data.get("selectedEngine",{}).get("type", "NOT_SELECTED")
            containerized_config = None
            is_containerized = False

            # Case for Visual Recipes with DSS engine selected
            if engine == "DSS":
                if default_project_visual_recipe_exec_config != "DSS":
                    containerized_config = default_project_visual_recipe_exec_config
                    is_containerized = True

            # Case for python/R code recipe and plugin recipes 
            elif engine in ["USER_CODE","PLUGIN_CODE"]:
                container_selection = r.get_settings().get_recipe_params().get("containerSelection",{})
                code_recipe_engine = self.get_code_engine_from_container_selection(project = self.project, 
                                                                                   default_project_code_recipe_exec_config = default_project_code_recipe_exec_config, 
                                                                                   **container_selection)
                if code_recipe_engine != "DSS":
                    containerized_config = code_recipe_engine
                    is_containerized = True

            # All other cases don't run locally on Dataiku
            else: # SPARK, etc..
                is_containerized = False

            if is_containerized:
                containerized_recipes.append({"name" :r.name, 
                                           "type":r.get_settings().data.get('recipe',{}).get('type'),
                                             "containerized_config" : containerized_config 
                                          })
        
        run_result = {"containerized_recipes" : containerized_recipes}
        self.value = len(containerized_recipes)
        self.run_result = run_result
        return self  
    
    
    
    
    