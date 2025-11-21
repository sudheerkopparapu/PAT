import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig


class NumberOfCodeRecipesMetric(ProjectMetric):
    """
    Count the number of code recipes in a project.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
    ):
        """
        Initializes the NumberOfCodeRecipesMetric metric class with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            name="nbr_of_code_recipes",
            metric_type=AssessmentMetricType.INT,
            description="Number of code recipes",
            dss_version_min=Version("3.0.0"),
            dss_version_max=None,  # Latest
            tags = ["FEATURE_USAGE"]
        )

    def run(self) -> ProjectMetric:
        """
        Computes the number of code recipes in the project.
        :return: self
        """
        result = {}

        code_recipe_types = ["python", "sql_query", "sql_script", "r", "shell", "spark_sql_query", "spark_scala", "sparkr", "pyspark"]
        code_recipe_counter = 0
        code_recipe_ids = []
        recipes = self.project.list_recipes()

        for r in recipes:
            if r.type in code_recipe_types:
                code_recipe_counter += 1
                code_recipe_ids.append(r.id)
        
        result["code_recipe_ids"] = code_recipe_ids
        self.value = code_recipe_counter
        self.run_result = result
        return self
