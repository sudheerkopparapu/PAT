import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

class ProjectStandardsCheck(ProjectStandardsCheckSpec):

    def run(self):
        """
        Check that the project has at least one scenario.
        """
        scenarios = self.project.list_scenarios()
        if scenarios:
            return ProjectStandardsCheckRunResult.success(
                message = "The project has at least one scenarios",
                details = {"scenario_count": len(scenarios)}
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = "The project doesn't have a scenario",
                    details = {"scenario_count": 0}
                )

