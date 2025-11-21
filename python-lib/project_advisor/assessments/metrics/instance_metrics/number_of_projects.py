import dataikuapi
from packaging.version import Version
from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.instance_metric import InstanceMetric
from project_advisor.assessments.config import DSSAssessmentConfig 
from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

class NumberProjectsMetric(InstanceMetric):
    """
    This class is used to determine the number of projects in an instance.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor
    ):
        """
        Initializes the NumberProjectsMetric class with the provided client, config.
        """
        super().__init__(
            client = client,
            config = config,
            batch_project_advisor = batch_project_advisor,
            name = "nbr_projects",
            metric_type = AssessmentMetricType.INT,
            description = "Counts the number of projects in the instance."
        )

    def run(self) -> InstanceMetric:
        """
        Computes the number of projects in the instance.
        :return: self
        """
        project_keys = self.client.list_project_keys()
        
        nb_projects = len(project_keys)
        
        nb_projects_details = {
                "number_of_projects": nb_projects
        }

        self.value = nb_projects
        self.run_result = nb_projects_details
        return self
    
    
    