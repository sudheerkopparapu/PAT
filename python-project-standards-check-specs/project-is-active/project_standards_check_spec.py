import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from dateutil import parser
from datetime import datetime, timezone

class ProjectStandardsCheck(ProjectStandardsCheckSpec):

    def run(self):
        """
        Runs the check to determine if the project is active:
        A project is considered active if:
        - edited in the last X days
        - a job ran in the last X days
        - there is an active scenario
        - a bundle is deployed on the automation node
        """
        
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')
        
        result = {}
        current_dt_utc = datetime.now(timezone.utc)

        # Check time since last projet modification
        last_commit_ts_str = self.project.get_project_git().log().get("entries")[0].get("timestamp")
        last_commit_dt = parser.isoparse(last_commit_ts_str)
        
        last_modified_days = (current_dt_utc - last_commit_dt).days
        last_modified_days = round(last_modified_days,1)
        result['Last modified'] = f'Project has been modified in the last {round(last_modified_days)} day(s).'

        # Check time since last job run
        if self.project.list_jobs():
            last_job_timestamp=self.project.list_jobs()[0]["def"]["initiationTimestamp"]
            last_job_dt_utc = datetime.fromtimestamp(round(last_job_timestamp / 1000)).replace(tzinfo=timezone.utc)
            last_job_days=(current_dt_utc - last_job_dt_utc).days
            result['Last job'] = f'Project ran a job {round(last_job_days)} day(s) ago.'
        else:
            last_job_days=99999
            result['Last job'] = f'Project never ran a job.'
        
        # Check for active scenarios
        active_scenario=0
        all_scenarios=self.project.list_scenarios(as_type='listitems')
        for scenario in all_scenarios:
            if scenario["active"]==True:
                active_scenario=active_scenario+1
        result['Active scenario'] = f'Project has {active_scenario} active scenario(s).'

        # Check for published bundles
        published_bundles=0
        all_bundles= self.project.list_exported_bundles()
        for bundle in all_bundles["bundles"]:
            if bundle.get('publishedBundleState', False):
                published_bundles=published_bundles+1  
        result['Deployed bundles'] = f'Project has {published_bundles} deployed bundle(s).'
                
        
        # Check if project is active
        
        if active_scenario>0:
            return ProjectStandardsCheckRunResult.success(
                message = f"Project has an active Scenario making the project active",
                details = result
            )
        
        if published_bundles>0:
            return ProjectStandardsCheckRunResult.success(
                message = f"Project is deployed in production making it by default active",
                details = result
            )
        
        day_inactive = min(last_modified_days,last_job_days)
        message = f"The project has been inactive for {day_inactive} days"
        
        if day_inactive > critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = message,
                details = result
            )
        elif day_inactive > high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = message,
                details = result
            )
        elif day_inactive > medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = message,
                details = result
            )
        elif day_inactive > low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = message,
                details = result
            )
        elif day_inactive > lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = message,
                details = result
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = f"The project has been active for less days that the grace threshold of {int(lowest_threshold)} days",
                details = result
            )
        
