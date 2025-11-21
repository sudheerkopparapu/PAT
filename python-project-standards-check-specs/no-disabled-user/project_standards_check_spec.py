import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)


class MyProjectStandardsCheckSpec(ProjectStandardsCheckSpec):
    
    def user_is_enabled(self, user_id : str) -> bool:
        """
        Check if user exists and is enabled.
        If not returns False.
        """
        try:
            return self.client.get_user(user_id).get_settings().get_raw().get('enabled')
        except:
            return False

    def run(self):
        """
        Run the check

        :returns: the run result.
            Use `ProjectStandardsCheckRunResult.success(message)` or `ProjectStandardsCheckRunResult.failure(severity, message)` depending on the result.
            Use `ProjectStandardsCheckRunResult.not_applicable(message)` if the check is not applicable to the project.
            Use `ProjectStandardsCheckRunResult.error(message)` if you want to mark the check as an error. You can also raise an Exception.
        """

        
        self.client = dataiku.api_client()
        self.source_project = self.client.get_project(self.original_project_key)

        disabledUsers=[]
        disabledUser_count=0
        
        owner= self.source_project.get_permissions().get("owner")
        owner_enabled=self.user_is_enabled(owner)
        if not owner_enabled:
            disabledUsers.append(f'Owner: {owner} (enabled: {owner_enabled})')
            disabledUser_count=disabledUser_count+1

        sharedUsers = []

        for user in self.source_project.get_permissions().get("permissions"):
            user_type="user" in user
            if user_type:
                current_user=user.get('user')
                current_user_enabled=self.user_is_enabled(current_user)
                sharedUsers.append(f'{current_user} (enabled: {current_user_enabled})')
                if not current_user_enabled:
                    disabledUsers.append(f'Shared with: {current_user} (enabled: {current_user_enabled})')
                    disabledUser_count=disabledUser_count+1

        effective_run_as_users=[]
        for s in self.project.list_scenarios():
            effective_run_as_user= self.project.get_scenario(s.get("id")).get_settings().effective_run_as
            current_user_enabled=self.user_is_enabled(effective_run_as_user)
            effective_run_as_users.append(f'Scenario "{s.get("id")}" by {effective_run_as_user} (enabled: {current_user_enabled})')
            if not current_user_enabled:
                disabledUsers.append(f'Scenario "{s.get("id")}" by {effective_run_as_user} (enabled: {current_user_enabled})')
                disabledUser_count=disabledUser_count+1

        code_studio_owners=[]
        code_studios=self.project.list_code_studios(as_type='objects')
        for cs in code_studios:
            try:
                cs_owner=cs.get_settings().owner
                cs_name=cs.get_settings().name
                cs_owner_enabled=self.user_is_enabled(cs_owner)
                code_studio_owners.append(f'Code Studio "{cs_name}" owned by {cs_owner} (enabled: {cs_owner_enabled})')
                if not cs_owner_enabled:
                    disabledUsers.append(f'Code Studio "{cs_name}" owned by {cs_owner} (enabled: {cs_owner_enabled})')
                    disabledUser_count=disabledUser_count+1
            except Exception as e:
                self.config.logger.warning(f"Error loading code studio info : {type(e).__name__}–{str(e)}") # Typically caused by missing template 
        
        if not disabledUsers:
            return ProjectStandardsCheckRunResult.success(
                message = "The project has no disabled users.",
                details = {"total_disabled_users": disabledUser_count}
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = f"The project has {disabledUser_count} place(s) with disabled user(s) referenced.",
                    details = {"total_disabled_users": disabledUser_count, "disabled_users" : disabledUsers}
                )
