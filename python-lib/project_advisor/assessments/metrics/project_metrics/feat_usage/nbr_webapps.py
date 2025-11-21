import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig


class UsageOfWebapps(ProjectMetric):
    """
    Assess if webapps are present in a project.
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
            name="usage_webapps",
            metric_type=AssessmentMetricType.BOOLEAN,
            description="Usage of Webapps",
            dss_version_min=Version("3.0.0"),
            dss_version_max=None,  # Latest
            tags = ["FEATURE_USAGE"]
        )

    def run(self) -> ProjectMetric:
        """
        Computes the number of webapps in the project.
        :return: self
        """
        result = {}

        webapps = self.project.list_webapps()

        webapp_counter = 0
        webapp_ids = []
        webapp_metric_BOOL = False

        for w in webapps:
            webapp_counter += 1
            webapp_ids.append(w.id)

        if webapp_counter >0:
            webapp_metric_BOOL=True

        result["webapp_ids"] = webapp_ids
        result["webapp_counter"] = webapp_counter
        self.value = webapp_metric_BOOL
        self.run_result = result
        return self
