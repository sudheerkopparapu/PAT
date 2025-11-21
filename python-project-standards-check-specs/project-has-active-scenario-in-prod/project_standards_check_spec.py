import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.assessments.config_builder import DSSAssessmentConfigBuilder # Needed when using advanced PAT config

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
    def run(self):
        """
        Check that the project has at least one auto-trigger scenario in for each deployment.
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
  
        project_deployer = self.pat_config.deployer_client.get_projectdeployer()
        
        deployments = project_deployer.list_deployments(as_objects = False)
        proj_deployments = [d for d in deployments if d["projectBasicInfo"]["id"] == self.original_project_key]

        if len(proj_deployments) == 0:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = f"Project has no deployment in production.",
                details = details
            )
        
        not_active_deployment = dict()
        for d in proj_deployments:
            never_ever_deployed = d["neverEverDeployed"]
            infra_id = d["deploymentBasicInfo"]["infraId"]
            deployed_project_key = d["deploymentBasicInfo"]["deployedProjectKey"]
            
            if not never_ever_deployed:
                infra_client = self.pat_config.infra_to_client[infra_id]
                deployed_project = infra_client.get_project(deployed_project_key)
                scenarios_info = [s.get_settings().get_raw() for s in deployed_project.list_scenarios(as_type = "objects")]
                active_scenarios = [s.get('active')==True and any([t["active"] for t in s.get('triggers', [])]) for s in scenarios_info]

                if not any(active_scenarios):
                    not_active_deployment.setdefault(infra_id, []).append(deployed_project_key)
            else:
                not_active_deployment.setdefault(infra_id, []).append(deployed_project_key)
        
        details["not_active_deployment"] = not_active_deployment

        if not not_active_deployment:
            return ProjectStandardsCheckRunResult.success(
                message = "project has at least one active scenario for every one of it's deployments",
                details = details,
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = "Project has at least one production deployment that is not active",
                    details = details
                )
