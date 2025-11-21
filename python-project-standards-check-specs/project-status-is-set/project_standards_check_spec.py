import dataiku

from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

class MyProjectStandardsCheckSpec(ProjectStandardsCheckSpec):

    def run(self):
        """
        Runs the check to determine if the project's status is set.

        :returns: the run result.
            Use `ProjectStandardsCheckRunResult.success(message)` or `ProjectStandardsCheckRunResult.failure(severity, message)` depending on the result.
            Use `ProjectStandardsCheckRunResult.not_applicable(message)` if the check is not applicable to the project.
            Use `ProjectStandardsCheckRunResult.error(message)` if you want to mark the check as an error. You can also raise an Exception.
        """

        check_pass = True
        message = "This project has its status set."
        result = {}

        project_status = ""
        project_summary = self.project.get_summary()
        project_key = project_summary["projectKey"]

        if "projectStatus" in project_summary:
            project_status = project_summary["projectStatus"]
        else:
            check_pass = False
            message = "This project does not have its status set"

        result["project_key"] = project_key
        result["project_status"] = project_status
        
        if check_pass:    
            return ProjectStandardsCheckRunResult.success(
                message = message,
                details = result
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                severity = int(self.config.get("severity")), 
                message = message,
                details = result
            )
