import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

class ProjectStandardsCheck(ProjectStandardsCheckSpec):

    def run(self):
        """
        Check that the home page is properly populated
        """
        check_pass = True
        fail_message = "The main project is missing elements to be fully populated."
        result = {}
        
        project_summary = self.project.get_summary()
        project_summary.get("isProjectImg")

        if self.config.get("check_short_description"):
            if "shortDesc" in project_summary and project_summary["shortDesc"] != "":
                result["short_description"] = project_summary["shortDesc"]
            else:
                check_pass = False
                result["short_description"] = ""
                fail_message += " It does not have a short description."
        
        if self.config.get("check_long_description"):
            if "description" in project_summary and project_summary["description"] != "":
                result["long_description"] = project_summary["description"]
            else:
                check_pass = False
                result["long_description"] = ""
                fail_message += "It does not have a long description."
        
        if self.config.get("check_project_image"):
            if "description" in project_summary and project_summary["description"] != "":
                result["has_project"] = project_summary["description"]
            else:
                check_pass = False
                result["has_project_image"] = False
                fail_message += "It does not have a project image."
        
        if check_pass:
            return ProjectStandardsCheckRunResult.success(
                message = "The project home page is properly populated!",
                details = result
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = fail_message,
                    details = result
                )

