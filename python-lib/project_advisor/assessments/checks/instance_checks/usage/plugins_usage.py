import dataikuapi
import pandas as pd
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import InstanceCheckCategory, CheckSeverity
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.instance_check import InstanceCheck


from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

from project_advisor.assessments import DSSAssessmentStatus


class PluginUsageCheck(InstanceCheck):
    """
    A class used to check that all plugins are used.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the PluginUsageCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            metrics = metrics,
            batch_project_advisor = batch_project_advisor,
            tags=[InstanceCheckCategory.USAGE.name],
            name="plugin_usage_check",
            description="Checks all plugins are used at least once."
        )
        self.uses_plugin_usage = True

    def run(self) -> InstanceCheck:
        """
        Runs the check to determine if all plugins are used in at least one project.
        :return: self
        """
        
        plugin_list = self.client.list_plugins()

        result = {}
        
        # Check if the PAT backend has been configured
        pat_backend_client = self.config.pat_backend_client
        if self.config.pat_backend_client is None:
            self.message = "PAT Backend is not configured to run this check"
            self.run_result = result
            self.status = DSSAssessmentStatus.NOT_APPLICABLE
            return self

        pat_backend_client.load_latest(["plugins_usage"])
        plugins_usage_df = pat_backend_client.get_table("plugins_usage")
        
        if plugins_usage_df is None:
            self.message = "PAT Backend does not contain plugin usage information to run this check"
            self.run_result = result
            self.status = DSSAssessmentStatus.NOT_APPLICABLE
            return self

        plugin_list = self.client.list_plugins()
        
        all_plugin_ids = set(p.get("id") for p in plugin_list)
        all_plugins_used = set("plugin_id")
        plugins_not_used = list(all_plugin_ids - all_plugins_used)
        
        result["plugins_used"] = all_plugins_used
        result["plugins_not_used"] = plugins_not_used
        
        if len(plugins_not_used) > 0:
            self.check_severity = CheckSeverity.MEDIUM
            self.message = f"{len(plugins_not_used)} plugins are not used."
        else:
            self.check_severity = CheckSeverity.OK
            self.message = f"All plugins are used at least once."
        return self
    
    