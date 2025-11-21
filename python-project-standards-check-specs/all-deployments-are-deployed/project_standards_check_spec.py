import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.assessments.config_builder import DSSAssessmentConfigBuilder # Needed when using advanced PAT config

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
    def run(self) -> ProjectStandardsCheckRunResult:
        """
        Check that every deployment for a give project has been deployed
        """
        self.pat_config = DSSAssessmentConfigBuilder.build_from_macro_config(self.config, self.plugin_config) # Use only for advanced usage


        if not self.pat_config.deployer_client:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = "PAT is not configured to run DEPLOYMENT checks"
            )
        
        project_deployer = self.pat_config.deployer_client.get_projectdeployer()
        pp = project_deployer.get_project(self.original_project_key)
        
        # Check the project has a published project
        try:
            pp_status = pp.get_status().light_status
            project_deployments = pp_status.get("deployments")
        except:
            project_deployments = [] # No Deployments as the project has not been deployed yet

        incomplete_deployments = []
        for project_deployement in project_deployments:
            deployment_id = project_deployement.get("id")
            deployedProjectKey = project_deployement.get("deployedProjectKey")
            infraId = project_deployement.get("infraId")

            # Get infra client
            auto_client = self.pat_config.infra_to_client.get(infraId)
            auto_project = auto_client.get_project(deployedProjectKey)

            try:
                auto_project.get_metadata() # Check project exists
            except:
                incomplete_deployments.append(deployment_id)


        missing_deployments = len(incomplete_deployments)
        details = {"all_project_deployements" :project_deployments}


        if missing_deployments == 0:
            return ProjectStandardsCheckRunResult.success(
                message = f"All {len(project_deployments)} deployments for project {self.original_project_key} have been deployed to their respective Infrastructures",
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = f"The following {len(incomplete_deployments)} deployment(s) have not been deployed to their respective infrastructures : {', '.join(incomplete_deployments)}",
                    details = details
                )


