import dataiku

from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

class MyProjectStandardsCheckSpec(ProjectStandardsCheckSpec):

    def run(self):
        """
        Runs the check to determine if the project has a wiki page.

        :returns: the run result.
            Use `ProjectStandardsCheckRunResult.success(message)` or `ProjectStandardsCheckRunResult.failure(severity, message)` depending on the result.
            Use `ProjectStandardsCheckRunResult.not_applicable(message)` if the check is not applicable to the project.
            Use `ProjectStandardsCheckRunResult.error(message)` if you want to mark the check as an error. You can also raise an Exception.
        """

        check_pass = True
        message = "This Project has a wiki"
        result = {}

        if len(self.project.get_wiki().list_articles()) == 0:
            message = "This Project does not have a wiki"
            check_pass = False

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
