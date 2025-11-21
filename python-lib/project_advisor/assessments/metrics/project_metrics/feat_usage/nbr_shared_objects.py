import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig 
    
    
class NumberSharedObject(ProjectMetric):
    """
    Count the number of Objects shared by this project.
    """

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
            name = "nbr_shared_objects",
            metric_type = AssessmentMetricType.INT,
            description = "Number of shared objects",
            dss_version_min = Version("12.0.0"),
            dss_version_max = None, # Latest
            tags = ["FEATURE_USAGE"]
        )

    def run(self) -> ProjectMetric:
        """
        Computes the number of Objects shared by the project.
        Computes the distinct dependent projects and saves in the run_result 
        """
        # get all shared objects
        p_settings = self.project.get_settings()
        exposed_objects = p_settings.get_raw().get("exposedObjects",{}).get("objects")

        dependent_projects = set()
        for exposed_object in exposed_objects:
            dependent_projects.update([r.get("targetProject") for r in exposed_object.get("rules")])

        run_result = {"exposed_objects" :exposed_objects,
                    "dependent_projects" : list(dependent_projects)}

        self.value = len(exposed_objects)
        self.run_result = run_result
        return self    