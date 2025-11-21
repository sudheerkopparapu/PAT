import dataikuapi
from typing import List
from packaging.version import Version
from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.instance_metric import InstanceMetric
from project_advisor.assessments.config import DSSAssessmentConfig 

from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

class SanityCheckErrorsMetric(InstanceMetric):
    """
    List the sanity check erros for a DSS instance.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor
    ):
        """
        Initializes the DSS Instance Sanity Check with the provided client, config.
        """
        super().__init__(
            client = client,
            config = config,
            batch_project_advisor = batch_project_advisor,
            name = "nbr_sanity_check_errors",
            metric_type = AssessmentMetricType.INT,
            description = "Counts the errors on the instance sanity check.",
            dss_version_min = Version("11.3.2"),
            dss_version_max = None
        )

    
    def run(self) -> InstanceMetric:
        """
        Computes the list of connections used in a project.
        :return: self
        """
        sc = self.client.perform_instance_sanity_check()
        sanity_errors = []

        for message in sc.messages:
            if message.severity == 'ERROR':
                sanity_errors.append({'title': message.title, 'details': message.details})

        self.value = len(sanity_errors)
        self.run_result = {"sanity_errors" : sanity_errors}
        return self
    
    
    