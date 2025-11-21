from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from dateutil import parser
from datetime import datetime, timezone

class ProjectStandardsCheck(ProjectStandardsCheckSpec):

    def run(self):
        """
        Check if the Project has not been run past a certain number of days after the last edit
        """
        
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')
        
        details = {}
        # Last commit
        last_commit_ts_str = self.project.get_project_git().log().get("entries")[0].get("timestamp")
        last_commit_dt = parser.isoparse(last_commit_ts_str)
        current_dt = datetime.now(timezone.utc)
        last_modified_days = round((current_dt - last_commit_dt).days,1)
        details["last_commit_date"]= f"{last_commit_dt}"
        details["last_commit_days"]= f"{last_modified_days}"
        
        # Last job
        project_jobs = self.project.list_jobs()
        if project_jobs:
            last_job_timestamp=self.project.list_jobs()[0]["def"]["initiationTimestamp"]
            last_job_dt=datetime.fromtimestamp(round(last_job_timestamp / 1000))
            details['last_job_date'] = f'{last_job_dt}'
            details['days_since_last_job'] = f"{(datetime.now() - last_job_dt).days}"
        else:
            details['last_job_date'] = None
            return ProjectStandardsCheckRunResult.success(
                message = "No jobs have run on this project",
                details = details
            )
        
        days_since_modified = (last_job_dt - last_commit_dt.replace(tzinfo=None)).days
        details["days_between_job_and_modified"] = days_since_modified
        message = f"A job was run {days_since_modified} days after the last update on the project"
        if days_since_modified > critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = message,
                details = details
            )
        elif days_since_modified > high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message =  message,
                details = details
            )
        elif days_since_modified > medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = message,
                details = details
            )
        elif days_since_modified > low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = message,
                details = details
            )
        elif days_since_modified > lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = message,
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = message,
                details = details
            )
        