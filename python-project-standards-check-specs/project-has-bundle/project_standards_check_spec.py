
import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)
from datetime import datetime

class ProjectStandardsCheck(ProjectStandardsCheckSpec):

    def run(self):
        """
        Check that the The project has a least one bundle
        """
 
        flow = self.project.get_flow()
        
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')
        
        # Calculate project age in days
        project_git = self.project.get_project_git()
        commits = project_git.log()
        next_commit = commits.get("nextCommit")
        while next_commit:
            commits = project_git.log(start_commit = next_commit)
            next_commit = commits.get("nextCommit")
        last_commit = commits["entries"][-1]
        last_commit_dt = datetime.fromisoformat(last_commit.get("timestamp").split(".")[0])
        project_age_days = (datetime.now() - last_commit_dt).days
        
        # Perform check only if project is older than the grace period
        details = {}
        bundles = self.project.list_exported_bundles().get('bundles', [])
        details["nbr_bundles"] = len(bundles)
        details["project_age_days"] = project_age_days
        details["grace_period_days"] = int(lowest_threshold)
        
        error_message = f"Project does not have any bundles, but one is required. Project age is: {project_age_days} days"
        
        if bundles:
            return ProjectStandardsCheckRunResult.success(
                message = f"Project has at least one bundle created",
                details = details
            )
        elif project_age_days > critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = error_message,
                details = details
            )
        elif project_age_days > high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = error_message,
                details = details
            )
        elif project_age_days > medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = error_message,
                details = details
            )
        elif project_age_days > low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = error_message,
                details = details
            )
        elif project_age_days > lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = error_message,
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = f"Check is skipped. Project doesn't have a bundle but is under the grace period of {int(lowest_threshold)} days",
                details = details
            )
        

