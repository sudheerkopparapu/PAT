from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

class ScenarioWithAutoTriggerOnDesignNodeCheckSpec(ProjectStandardsCheckSpec):
    """
    Checks if any active scenarios have a trigger set up on the design node
    """
    def check_for_active_scenario_triggers(self, scenario) -> bool:
        """
        Checks if a scenario is both active and has an automated trigger set up
        """
        scenario_details = scenario.get_settings().get_raw()
        if (scenario_details.get("active") == True) & (len(scenario_details.get("triggers")) > 0):
            return True
        else:
            return False

    def run(self):
        """
        Run the check

        :returns: the run result.
            Use `ProjectStandardsCheckRunResult.success(message)` or `ProjectStandardsCheckRunResult.failure(severity, message)` depending on the result.
            Use `ProjectStandardsCheckRunResult.not_applicable(message)` if the check is not applicable to the project.
            Use `ProjectStandardsCheckRunResult.error(message)` if you want to mark the check as an error. You can also raise an Exception.
        """

        severity = int(self.config.get("severity"))
        result = []

        scenarios = self.project.list_scenarios(as_type="objects")
        for scenario in scenarios:
            if self.check_for_active_scenario_triggers(scenario):
                result.append(scenario.id)

        if len(result) == 0:
            return ProjectStandardsCheckRunResult.success(
                "No scenarios are active with automatics triggers on the design node"
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                severity, f"{len(result)} scenarios are active with triggers on the design node"
            )
