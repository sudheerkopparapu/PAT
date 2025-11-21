import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig

class NumberOfProjectCollaborators(ProjectMetric):
    """
    Compute the number of collaborators on a given project.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
    ):
        """
        Initializes the NumberOfProjectCollaborators metric class with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            name="nbr_of_collaborators",
            metric_type=AssessmentMetricType.INT,
            description="Number of project collaborators",
            dss_version_min=Version("3.0.0"),
            dss_version_max=None,  # Latest
            tags = ["ACTIVITY"]
        )

    def run(self) -> ProjectMetric:
        """
        Get the number of collaborators on a particular project.
        :return: self
        """
        result = {}

        all_contributors = self.project.get_timeline()["allContributors"]
        result["contributors"] = [i.get("displayName") for i in all_contributors]

        self.value = len(all_contributors)
        self.run_result = result
        return self
