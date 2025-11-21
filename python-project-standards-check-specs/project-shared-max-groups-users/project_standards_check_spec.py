from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)


class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
    def run(self):
        """
        Runs the check to determine if the project is shared to no more than X groups or users.
        """
        
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')
        
        project_permissions = self.project.get_permissions().get("permissions")

        groups = [permission["group"] for permission in project_permissions if "group" in permission]
        users = [permission["user"] for permission in project_permissions if "user" in permission]
        
        n_groups = len(groups)
        n_users = len(users)
        total_entities = n_groups + n_users

        details = {"users": users, "groups": groups}
        
        # Check not shared
        if n_groups == 0 and n_users == 0:
            return ProjectStandardsCheckRunResult.failure(
                severity = int(self.config["not_shared_severity"]),
                message = "Project wasn't shared with anyone. Please share it with the relevant users/groups.",
                details = details
            )
        
        message = f"The project was shared to {n_groups} groups and {n_users} user, try grouping users in groups to reduce the number of shared to entities"
        
        if total_entities > critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = message,
                details = details
            )
        elif total_entities > high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = message,
                details = details
            )
        elif total_entities > medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = message,
                details = details
            )
        elif total_entities > low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message =message,
                details = details
            )
        elif total_entities > lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = message,
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = f"The project's permission's list is under the recommended max number of {int(lowest_threshold)} entities",
                details = details
            )
        
