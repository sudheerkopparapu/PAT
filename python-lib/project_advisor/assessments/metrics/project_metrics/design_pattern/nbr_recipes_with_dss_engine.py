import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig 
    
    
class NumberRecipesWithLocalDSSEngine(ProjectMetric):
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
            name = "nbr_recipes_with_local_dss_engine",
            metric_type = AssessmentMetricType.INT,
            description = "Number of recipes with Local DSS Engine",
            dss_version_min = Version("12.0.0"),
            dss_version_max = None, # Latest
            tags = ["DESIGN_PATTERN"]
        )

    def run(self) -> ProjectMetric:
        """
        Finds all the recipes in the Flow that use the Local DSS engine.
        Recipes that use the Local DSS engines are:
        - Visual recipes that use the DSS engine in project AND where visual recipes are not containerized.
        - Code & Plugin recipes that don't use containerized execution.
        """

        default_project_visual_recipe_exec_config = self.get_default_project_visual_exec_config(self.project)
        default_project_code_recipe_exec_config = self.get_default_project_code_exec_config(self.project)
        dss_engine_recipes = []
        for r in self.project.list_recipes(as_type = "objects"):

            # Get recipe engine
            engine = r.get_status().data.get("selectedEngine",{}).get("type", "NOT_SELECTED")

            # Case for Visual Recipes with DSS engine selected
            if engine == "DSS":
                if default_project_visual_recipe_exec_config == "DSS":
                    uses_dss_engine = True
                else:
                    uses_dss_engine = False
            # Case for python/R code recipe and plugin recipes 
            elif engine in ["USER_CODE","PLUGIN_CODE"]:
                container_selection = r.get_settings().get_recipe_params().get("containerSelection",{})
                print (f"container_selection : {container_selection}")
                
                code_recipe_engine = self.get_code_engine_from_container_selection(self.project, 
                                                                                   default_project_code_recipe_exec_config, 
                                                                                   **container_selection)
                if code_recipe_engine == "DSS":
                    uses_dss_engine = True
                else:
                    uses_dss_engine = False
            # All other cases don't run locally on Dataiku
            else: # SPARK, etc..
                uses_dss_engine = False

            if uses_dss_engine:
                dss_engine_recipes.append({"name" :r.name, 
                                           "type":r.get_settings().data.get('recipe',{}).get('type')
                                          })
        
        run_result = {"dss_engine_recipes" : dss_engine_recipes}
        self.value = len(dss_engine_recipes)
        self.run_result = run_result
        return self  
    
    
    
    
    