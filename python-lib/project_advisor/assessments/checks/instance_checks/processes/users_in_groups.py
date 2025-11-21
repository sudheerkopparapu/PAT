import dataikuapi
import pandas as pd
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import InstanceCheckCategory, CheckSeverity
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.instance_check import InstanceCheck


from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor
from project_advisor.pat_tools import md_print_list


class UsersInGroups(InstanceCheck):
    """
    A class that checks that each user belongs to at least 1 group.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the UsersInGroups instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            metrics = metrics,
            batch_project_advisor = batch_project_advisor,
            tags=[InstanceCheckCategory.PROCESSES.name],
            name="users_in_groups",
            description="Checks that each user belongs to at least 1 group."
        )

    def run(self) -> InstanceCheck:
        """
        Runs the check to confirm each user belongs to at least 1 group.
        :return: self
        """
        
        check_pass = True
        message = "All users belong to at least 1 group"
        result = []
        
        # Retrieve the list of active users
        users = [user for user in self.client.list_users() if user['enabled'] == True]

        # Check each user for group membership
        users_without_groups = []
        for user in users:
            groups = user.get('groups', [])
            if not groups:
                users_without_groups.append(user['login'])
        
        # Prepare check results
        if users_without_groups:
            check_pass = False
            message = f"{len(users_without_groups)} user(s) is(are) do not belong to any groups"
            result = {"users_without_groups": md_print_list(users_without_groups, "user")}                

        if check_pass:    
            self.check_severity = CheckSeverity.OK
        else:
            self.check_severity = CheckSeverity.LOW
        self.message = message
        self.run_result = result
        return self