import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig


class NumberOfVisualRecipesMetric(ProjectMetric):

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
    ):

        super().__init__(
            client=client,
            config=config,
            project=project,
            name="nbr_of_visual_recipes",
            metric_type=AssessmentMetricType.INT,
            description="Number of visual recipes",
            dss_version_min=Version("3.0.0"),
            dss_version_max=None,  # Latest
            tags = ["FEATURE_USAGE"]
        )

    def run(self) -> ProjectMetric:

        result = {}

        code_recipe_types = ["python", "sql_query", "sql_script", "r", "shell", "spark_sql_query", "spark_scala", "sparkr", "pyspark"]
        visual_recipe_counter = 0
        visual_recipe_types = []
        visual_recipe_ids = []
        recipes = self.project.list_recipes()

        for r in recipes:
            if r.type not in code_recipe_types:
                visual_recipe_types.append(r.type)
                visual_recipe_counter += 1
                visual_recipe_ids.append(r.id)
        
        visual_recipe_distinct_types = list(set(visual_recipe_types))
        result["visual_recipe_ids"] = visual_recipe_ids
        result["visual_recipe_distinct_types"] = visual_recipe_distinct_types
        self.value = len(visual_recipe_ids)
        self.run_result = result
        return self
