import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.assessments.config_builder import DSSAssessmentConfigBuilder # Needed when using advanced PAT config

class ProjectStandardsCheck(ProjectStandardsCheckSpec):

    def run(self):
        """
        Runs the check to determine if the project has at least one deployment on the deployer.
        """  
        self.pat_config = DSSAssessmentConfigBuilder.build_from_macro_config(self.config, self.plugin_config) # Use only for advanced usage
        self.client = self.pat_config.admin_design_client
        
        check_pass = False
        message = f"Project {self.original_project_key} doesn't have a deployment on the deployer"
        run_result = {}
        
        if not self.pat_config.deployer_client:
            return ProjectStandardsCheckRunResult.not_applicable( message = "PAT is not configured to run DEPLOYMENT checks")

        try:
            self.pat_config.deployer_client.get_instance_info()

            deployer = self.pat_config.deployer_client.get_projectdeployer()
            deployment_ids = []
            for deployment in deployer.list_deployments():
                if deployment.get_settings().get_raw()["publishedProjectKey"] == self.original_project_key:
                    deployment_ids.append(deployment.get_settings().get_raw()["id"])
                    check_pass = True
                    message = f"Project {self.original_project_key} has a deployment on the deployer"

            run_result["deployment_ids"] = deployment_ids

        except Exception as error:
            message = "Error fetching deployment information",
            run_result = {
                "error" : type(error).__name__,
                "error_message" : str(error)
            }

        if check_pass:
            return ProjectStandardsCheckRunResult.success(
                message = message,
                details = run_result
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                severity = int(self.config.get("severity")), 
                message = message,
                details = run_result
            )
