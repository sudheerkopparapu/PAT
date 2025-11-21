import dataikuapi
from typing import List
from packaging.version import Version
from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.instance_metric import InstanceMetric
from project_advisor.assessments.config import DSSAssessmentConfig 
from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

class NumberDataCollections(InstanceMetric):

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor
    ):
        super().__init__(
            client = client,
            config = config,
            batch_project_advisor = batch_project_advisor,
            name = "nbr_data_collections",
            metric_type = AssessmentMetricType.INT,
            description = "Number of data collections on the instance"
        )

    
    def run(self) -> InstanceMetric:
        """
        Computes the number of data collections on the instance.
        """
        dcs = self.client.list_data_collections()
        run_result = {"data_colections_info" : [{"name" : dc.display_name, "item_count": dc.item_count} 
                                                for dc in dcs]
                     }

        self.value = len(dcs)
        self.run_result = run_result
        return self
    
    
    