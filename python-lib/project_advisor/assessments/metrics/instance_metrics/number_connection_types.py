import dataikuapi
from typing import List
from packaging.version import Version
from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.instance_metric import InstanceMetric
from project_advisor.assessments.config import DSSAssessmentConfig 
from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

class NumberConnectionTypesMetric(InstanceMetric):
    """
    This class is used to determine the number of distinct connection types on the instance.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor
    ):
        """
        Initializes the NumberConnectionTypesMetric class with the provided client, config.
        """
        super().__init__(
            client = client,
            config = config,
            batch_project_advisor = batch_project_advisor,
            name = "nbr_conn_types",
            metric_type = AssessmentMetricType.INT,
            description = "Counts the number of distinct connection types on the instance."
        )

    
    def run(self) -> InstanceMetric:
        """
        Computes the number of distinct connection types on the instance.
        :return: self
        """
        connections = self.client.list_connections()

        connection_types = set()  
        for connection in connections:
            connection_details = self.client.get_connection(connection)
            connection_type = connection_details.get_definition().get('type')
            connection_types.add(connection_type)
            
        connection_types = list(connection_types)
        self.value = len(connection_types)
        self.run_result = {"conn_types": connection_types}
        return self
    
    
    