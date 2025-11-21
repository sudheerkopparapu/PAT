import dataikuapi
import pandas as pd
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import InstanceCheckCategory, CheckSeverity
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.instance_check import InstanceCheck


from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor
from project_advisor.pat_tools import md_print_list

class CodeEnvUsageCheck(InstanceCheck):
    """
    A class used to check that all code environments are used in at least one project.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the CodeEnvUsageCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            metrics=metrics,
            batch_project_advisor=batch_project_advisor,
            tags=[InstanceCheckCategory.USAGE.name],
            name="code_env_usage_check",
            description="Checks all code environments are used at least once."
        )

    def run(self) -> InstanceCheck:
        """
        Runs the check to determine if all code environments are used in at least one project.
        :return: self
        """
        # Fetch and filter code environments
        code_envs_df = pd.DataFrame(self.client.list_code_envs())
        code_envs_df_dm = code_envs_df[code_envs_df["deploymentMode"] == "DESIGN_MANAGED"]
        code_envs_list = code_envs_df_dm["envName"].tolist()

        # Fetch code environment usages
        code_env_usages_df = pd.DataFrame(self.client.list_code_env_usages())
        if code_env_usages_df.empty:
            code_envs_used = []
        else:
            code_env_usages_df = code_env_usages_df.dropna(subset=["envName"])
            code_envs_used = code_env_usages_df["envName"].unique()

        # Determine unused code environments
        code_envs_not_used = [env for env in code_envs_list if env not in code_envs_used]

        check_pass = True
        message = "All code environments are used at least once."
        result = {}

        if code_envs_not_used:
            check_pass = False
            message = f"{len(code_envs_not_used)} code environments are not used."
            result["code_env_not_used"] = md_print_list(code_envs_not_used, "py_code_env")

        # Store results
        if check_pass:    
            self.check_severity = CheckSeverity.OK
        else:
            self.check_severity = CheckSeverity.MEDIUM
        self.message = message
        self.run_result = result
        
        return self