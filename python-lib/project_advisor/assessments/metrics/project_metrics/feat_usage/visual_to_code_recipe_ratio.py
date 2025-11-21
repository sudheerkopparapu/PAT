import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig

class PercentageOfCodeRecipes(ProjectMetric):
    """
    Percentage 
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject
    ):
        """
        Initializes the Metric with a client, config, and project.
        """
        super().__init__(
            client = client,
            config = config,
            project = project,
            name = "percentage_of_code_recipe",
            metric_type = AssessmentMetricType.FLOAT,
            description = "Percentage of code recipes over all recipes in the flow",
            dss_version_min = Version("12.0.0"),
            dss_version_max = None,
            tags = ["FEATURE_USAGE"]
        )

    
    def run(self) -> ProjectMetric:
        """
        Computes the Percentage of code recipes over all recipes in the flow
        :return: self
        """
        
        result = {}
        code_recipe_types = ["python", "sql_query", "sql_script", "r", "shell"]
        
        recipes = self.project.list_recipes()
        
        nbr_recipes = len(recipes)
        code_recipe_counter = 0
        if nbr_recipes > 0:
            for r in recipes:
                if r.type in code_recipe_types:
                    code_recipe_counter += 1
            code_recipe_percentage = round(code_recipe_counter / nbr_recipes, 2)
        else:
            code_recipe_percentage = 0
        
        result["nbr_code_recipes"] = code_recipe_counter
        result["nbr_recipes"] = nbr_recipes

        self.value = code_recipe_percentage
        self.run_result = result
        return self