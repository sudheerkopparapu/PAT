import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig
from dateutil import parser
from datetime import datetime, timezone

class DaysSinceUpdateMetric(ProjectMetric):
    """
    Compute the time (in days) since last update of the Project.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
    ):
        """
        Initializes the DaysSinceUpdateMetric metric class with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            name="days_since_update",
            metric_type=AssessmentMetricType.INT,
            description="Days since last commit on the project",
            dss_version_min=Version("12.0.0"),
            dss_version_max=None,  # Latest
            tags = ["ACTIVITY"]
        )

    def run(self) -> ProjectMetric:
        """
        Compute the time (in days) since last update of the Project.
        :return: self
        """
        result = {}

        last_commit_ts_str = self.project.get_project_git().log().get("entries")[0].get("timestamp")
        last_commit_dt = parser.isoparse(last_commit_ts_str)

        current_dt = datetime.now(timezone.utc)
        last_modified_days = (current_dt - last_commit_dt).days
        last_modified_days = round(last_modified_days,1)
        result["last_update_timestamp"]= f"{last_commit_ts_str}"
        result["last_update_days"]= f"{last_modified_days}"

        self.value = last_modified_days
        self.run_result = result
        return self
