import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig 
    
    
class NumberRecipesWithSparkEngine(ProjectMetric):
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
            name = "nbr_recipes_with_spark_engine",
            metric_type = AssessmentMetricType.INT,
            description = "Number of recipes with SPARK Engine",
            dss_version_min = Version("12.0.0"),
            dss_version_max = None, # Latest
            tags = ["DESIGN_PATTERN"]
        )

    def run(self) -> ProjectMetric:
        """
        Finds and count all the recipes in the Flow that use the SPARK engine.
        """
        engine_type = "SPARK"
        spark_recipes = [r for r in self.project.list_recipes(as_type = "objects") if r.get_status().data.get("selectedEngine",{}).get("type") == engine_type]
        run_result  = {"spark_recipes" : [r.name for r in spark_recipes]}
        
        self.value = len(spark_recipes)
        self.run_result = run_result
        return self