import dataikuapi
import pandas as pd
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import InstanceCheckCategory, CheckSeverity
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.instance_check import InstanceCheck

from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor
from project_advisor.assessments import DSSAssessmentStatus
from project_advisor.pat_tools import md_print_list

class DevPluginUsageCheck(InstanceCheck):
    """
    A class used to check if all development plugins are used in only one project.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the DevPluginUsageCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            metrics = metrics,
            batch_project_advisor = batch_project_advisor,
            tags=[InstanceCheckCategory.USAGE.name],
            name="dev_plugin_usage_check",
            description="Development plugin must be used in only one project."
        )
        self.uses_plugin_usage = True

    def run(self) -> InstanceCheck:
        """
        Runs the check to determine if all development plugins are used in at most one project.
        :return: self
        """ 
        result = {}
        plugins_used_in_more_than_one_project = []
        
        # Check if the PAT backend has been configured
        pat_backend_client = self.config.pat_backend_client
        if self.config.pat_backend_client is None:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = "PAT backend is not configured to run this check",
                details = details
            )

        pat_backend_client.load_latest(["plugins_usage"])
        # returns table of plugin usage
        plugins_usage = pat_backend_client.get_table("plugins_usage")
        
        if plugins_usage is None:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = "Plugin usage was not computed as part of the PAT Backend",
                details = details
            )
        
        plugin_list = self.client.list_plugins()
        dev_plugin_names = [plugin['id'] for plugin in plugin_list if plugin['isDev'] == True]
     
        df = plugins_usage
        df = df[['plugin_id', 'project_key']]
        df = df[df['project_key'] != 'NONE']
        
        filtered_df = df[df['plugin_id'].isin(dev_plugin_names)]
        unique_pairs = filtered_df[['plugin_id', 'project_key']].drop_duplicates()
        # Group by plugin_id to get the list of projects per plugin
        grouped = unique_pairs.groupby('plugin_id')['project_key'].unique()
        
        # Iterate over plugins
        for plugin_id, projects in grouped.items():
            if len(projects) > 1:
                plugins_used_in_more_than_one_project.append(plugin_id)
                md_formatted_projects = md_print_list(projects, "project")
                result[f'usage of {plugin_id}'] = md_formatted_projects
        
        result['dev_plugins_in_more_then_one_project'] = plugin_used_in_more_than_one_project    
        
        if len(plugin_used_in_more_than_one_project) > 0:
            self.check_severity = CheckSeverity.MEDIUM
            self.message = f"{len(plugin_used_in_more_than_one_project)} development plugins are used in more than one project."
            self.run_result = result
        else:
            self.check_severity = CheckSeverity.OK
            self.message = f"All development plugins are used in at most one project."
            self.run_result = result
        return self
    
    