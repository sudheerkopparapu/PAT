import dataikuapi
from typing import List
from packaging.version import Version
from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.instance_metric import InstanceMetric
from project_advisor.assessments.config import DSSAssessmentConfig 

from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

class SanityCheckWarningsMetric(InstanceMetric):
    """
    List the warning sanity checks for a DSS instance.
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
            name = "nbr_sanity_check_warnings",
            metric_type = AssessmentMetricType.INT,
            description = "List the results of the sanity check.",
            dss_version_min = Version("11.3.2"),
            dss_version_max = None
        )

    
    def run(self) -> InstanceMetric:
        """
        Computes the list of connections used in a project.
        :return: self
        """
        sc = self.client.perform_instance_sanity_check()
        
        sanity_warnings = []
        for message in sc.messages:
            if message.severity == 'WARNING':
                sanity_warnings.append({'title': message.title, 'details': message.details})

        self.value = len(sanity_warnings)
        self.run_result = {"sanity_warnings" : sanity_warnings}
        return self
    
    
    