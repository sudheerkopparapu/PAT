import dataikuapi
from typing import List
from packaging.version import Version
from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.instance_metric import InstanceMetric
from project_advisor.assessments.config import DSSAssessmentConfig 

from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

class NumberPluginsMetric(InstanceMetric):
    """
    This class is used to determine the number of installed plugins in a instance.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor
    ):
        """
        Initializes the NumberPluginsMetric class with the provided client, config.
        """
        super().__init__(
            client = client,
            config = config,
            batch_project_advisor = batch_project_advisor,
            name = "nbr_plugins",
            metric_type = AssessmentMetricType.INT,
            description = "Counts the number of plugins in the instance."
        )
    
    def run(self) -> InstanceMetric:
        """
        Computes the number of installed plugins in the instance.
        :return: self
        """
        plugin_list = self.client.list_plugins()
        
        nb_plugin = len(plugin_list)
        nb_plugin_not_dev = len([plugin for plugin in plugin_list if not plugin["isDev"]])
        nb_plugin_dev = len([plugin for plugin in plugin_list if plugin["isDev"]])
                
        nb_plugin_details = {
                "number_of_plugins_installed_not_in_dev_mode": nb_plugin_not_dev,
                "number_of_plugins_in_dev_mode": nb_plugin_dev
            }

        self.value = nb_plugin
        self.run_result = nb_plugin_details
        return self
    
    
    