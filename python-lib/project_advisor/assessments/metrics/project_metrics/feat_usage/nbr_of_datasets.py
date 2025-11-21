import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig
from collections import Counter

class NumberOfDatasets(ProjectMetric):
    """
    List all the datasets in a project.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject
    ):
        """
        Initializes the Metric class with the provided client, config, and project.
        """
        super().__init__(
            client = client,
            config = config,
            project = project,
            name = "nbr_of_datasets",
            metric_type = AssessmentMetricType.INT,
            description = "Number of datasets",
            dss_version_min = Version("3.0.0"),
            dss_version_max = None, # Latest
            tags = ["FEATURE_USAGE"]
        )

    def run(self) -> ProjectMetric:
        """
        Computes the number of datasets in the project.
        :return: self
        """
        result = {}
        datasets = self.project.list_datasets()
        
        d_names = [d["name"] for d in datasets]
        result["dataset_names"] = d_names

        self.value = len(datasets)
        self.run_result = result
        return self