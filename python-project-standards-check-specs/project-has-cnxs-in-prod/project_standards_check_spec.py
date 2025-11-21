import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.assessments.config_builder import DSSAssessmentConfigBuilder # Needed when using advanced PAT config


class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
    def run(self):
        """
        Check that all the DATA connections are available in all the infrastructures it has deployments on.
        """

        self.pat_config = DSSAssessmentConfigBuilder.build_from_macro_config(self.config, self.plugin_config) # Use only for advanced usage
        
        check_pass = True
        message = f"Project has all its connections already created in the production infrastructure(s)."
        run_result = {}

        # Check if the deployer client has been successful loaded, if not, notify that the check is not possible
        if self.pat_config.deployer_client == None:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = "PAT is not configured to run DEPLOYMENT checks",
                details = run_result
            )
        # Check if the infrastruture clients has been successful loaded, if not, notify that the check is not possible
        if any(infra_client is None for infra_id, infra_client in self.pat_config.infra_to_client.items()):
            return ProjectStandardsCheckRunResult.not_applicable(
                message = "PAT is not configured to run DEPLOYMENT checks",
                details = run_result
            )

        project_deployer = self.pat_config.deployer_client.get_projectdeployer()

        # Compute the connection usage across the instance
        data_object_descs = self.project.list_datasets() + self.project.list_managed_folders()
        connections = set()
        for data_object_desc in data_object_descs:
            if "connection" in data_object_desc["params"]:
                connections.add(data_object_desc["params"]["connection"])

        # Retrieve the existing connection remappings from the deployments        
        connection_remappings = dict()
        for deployment in project_deployer.list_deployments():
            deployment_remappings = deployment.get_settings().get_raw()["bundleContainerSettings"]["remapping"]["connections"]
            for deployment_remapping in deployment_remappings:
                connection_remappings[deployment_remapping["source"]] = deployment_remapping["target"]

        infra_missing_connections = dict()
        infra_project_remappings = dict()

        # Compute the missing connections per infrastructure
        for infra_id, infra_client in self.pat_config.infra_to_client.items():
            # List the connections in the infra
            infra_connections = set(infra_client.list_connections().keys())
            # List the remappings in the deployer with a valid target in the infra
            valid_remappings = {source: target for source, target in connection_remappings.items() if target in infra_connections}
            # Compute the missing connections according to the infra
            missing_connections = connections - infra_connections
            # Take into account the valid remappings
            missing_connections_after_remapping = missing_connections - set(valid_remappings.keys())
            infra_missing_connections[infra_id] = list(missing_connections_after_remapping)
            # Compute the remappings relevant to the project
            valid_project_remmapings = missing_connections.intersection(set(valid_remappings.keys()))
            infra_project_remappings[infra_id] = {source: target for source, target in valid_remappings.items() if source in valid_project_remmapings}

        if any(len(infra_missing_connection) != 0 for infra_id, infra_missing_connection in infra_missing_connections.items()):
            check_pass = False
            message = f"Connections are missing in production infrastructures for project {self.original_project_key}."  
            run_result["missing_cnx"] = infra_missing_connections

        if any(len(infra_project_remapping) != 0 for infra_id, infra_project_remapping in infra_project_remappings.items()):
            run_result["valid_remappings"] = infra_project_remappings
        
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

