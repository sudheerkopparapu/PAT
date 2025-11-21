import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import InstanceCheckCategory, CheckSeverity
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.instance_check import InstanceCheck

from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

class AllAutomationNodeProjectHaveDeploymentCheck(InstanceCheck):

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor,
        metrics : List[DSSMetric]
    ):
        super().__init__(
            client=client,
            config=config,
            batch_project_advisor = batch_project_advisor,
            metrics = metrics,
            tags=[InstanceCheckCategory.PLATFORM.name],
            name="all_automation_projects_have_deployement_check",
            description="Check that all projects on the automtion node have associated deployments"
        )
       
    def run(self) -> InstanceCheck:
        """
        For every project on the automation node, check that it has an associated deployment.
        """
        # Precomputation - get all deployed projects
        deployer_client = self.config.deployer_client
        project_deployer = deployer_client.get_projectdeployer()
        deployed_projects = [d.get('deploymentBasicInfo', {}).get("deployedProjectKey") for d in project_deployer.list_deployments(as_objects= False)]
        deployed_projects

        orphan_projects_on_auto = []
        projects_on_auto_count = {}
        infra_ids = self.config.infra_to_client.keys()
        for infra_id, auto_client in self.config.infra_to_client.items():
            projects_on_auto = [p.get("projectKey") for p in auto_client.list_projects()]
            projects_on_auto_count[infra_id] = len(projects_on_auto)
            # Find all non deployed projects.
            orphan_projects_on_auto.extend([(p,infra_id) for p in list(set(projects_on_auto) - set(deployed_projects))])

        message = f"All {len(deployed_projects)} deployed projects accross {len(infra_ids)} infra(s) have an associated deployment"
        check_pass = True
        run_result = {
            "orphan_auto_node_projects" : orphan_projects_on_auto,
            "projects_on_auto_count" : projects_on_auto_count}
        if len(orphan_projects_on_auto)>0:
            message = f"{len(orphan_projects_on_auto)} orphan automation node project(s) have been identified. Please see metadata for the list of projects with their associated infra."
            check_pass = False

        if check_pass:    
            self.check_severity = CheckSeverity.OK
        else:
            self.check_severity = CheckSeverity.MEDIUM
        self.message = message
        self.run_result = run_result
        return self


