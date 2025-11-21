import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.assessments.config_builder import DSSAssessmentConfigBuilder # Needed when using advanced PAT config


class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
    def run(self):
        """
        Check that the project has all the required plugins in production
        """
        self.pat_config = DSSAssessmentConfigBuilder.build_from_macro_config(self.config, self.plugin_config) # Use only for advanced usage

        details = {}

        # Check if the deployer client has been successful loaded, if not, notify that the check is not possible
        if self.pat_config.deployer_client == None:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = "PAT is not configured to run DEPLOYMENT checks",
                details = details
            )
        

        # Check if the infrastruture clients has been successful loaded, if not, notify that the check is not possible
        if any(infra_client is None for infra_id, infra_client in self.pat_config.infra_to_client.items()):
            return ProjectStandardsCheckRunResult.not_applicable(
                message = "PAT is not configured to run DEPLOYMENT checks",
                details = details
            )
        
        # Check if the PAT backend has been configured
        pat_backend_client = self.pat_config.pat_backend_client
        if self.pat_config.pat_backend_client is None:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = "PAT backend is not configured to run this check",
                details = details
            )

        pat_backend_client.load_latest(["plugins_usage"])
        plugins_usage = pat_backend_client.get_table("plugins_usage")
        
        if plugins_usage is None:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = "Plugin usage was not computed as part of the PAT Backend",
                details = details
            ) 
        
        plugins_usage = plugins_usage[plugins_usage["project_key"] == self.original_project_key]
        used_plugins = set(plugins_usage["plugin_id"])
        plugins_usage.drop_duplicates()
        project_plugin_usage = {}
        for plugin_id in used_plugins:
            uses = []
            for idx, row in plugins_usage[plugins_usage["plugin_id"] == plugin_id].iterrows():
                uses.append((row["object_type"], row["object_id"]))
            project_plugin_usage[plugin_id] = uses
        details["all_plugin_usage"] = project_plugin_usage
 
        if not used_plugins:
            return ProjectStandardsCheckRunResult.success(
                message = "No plugins used in the project",
                details = details
            )
        
        # Retrieve projects on the deployer and the infrastructures
        deployer_projects_to_publish = list()
        infra_projects_to_deploy = dict()

        project_deployer = self.pat_config.deployer_client.get_projectdeployer()
        
        infra_missing_plugins = dict()
        # Compute the missing plugins in every automation node for the current project
        for infra_id, infra_client in self.pat_config.infra_to_client.items():
            if infra_id not in self.config.get("infras_to_ignore"):
                infra_plugins = set(plugin["id"] for plugin in infra_client.list_plugins())
                missing_plugins = used_plugins - infra_plugins
                infra_missing_plugins[infra_id] = list(missing_plugins)
 
        details["missing_plugins"] = infra_missing_plugins

        if not infra_missing_plugins.keys():
            return ProjectStandardsCheckRunResult.success(
                message = f"All the plugins used by the project are installed on all the production infrastructure(s)",
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = "Some plugins used by the project are not installed in production",
                    details = details
                )

