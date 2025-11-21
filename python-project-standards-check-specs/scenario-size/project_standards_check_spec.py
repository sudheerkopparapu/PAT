from collections import defaultdict
from typing import List

from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

class ScenarioSizeCheckSpec(ProjectStandardsCheckSpec):
    """
    Check that the number of steps in a scenario is below a certain threshold.
    """

    def get_step_based_scenario_ids(self) -> List[str]:
        """
        Retrieves the IDs of all step-based scenarios in the project.
        :return: self
        """
        scenario_items = self.project.list_scenarios()
        ids = [scenario_item["id"] for scenario_item in scenario_items if scenario_item["type"] == "step_based"]
        return ids

    def run(self):
        """
        Runs the check to determine if any scenarios exceed the maximum number of allowed steps.

        :returns: the run result.
            Use `ProjectStandardsCheckRunResult.success(message)` or `ProjectStandardsCheckRunResult.failure(severity, message)` depending on the result.
            Use `ProjectStandardsCheckRunResult.not_applicable(message)` if the check is not applicable to the project.
            Use `ProjectStandardsCheckRunResult.error(message)` if you want to mark the check as an error. You can also raise an Exception.
        """

        lowest_threshold = self.config.get("lowest")
        low_threshold = self.config.get("low")
        medium_threshold = self.config.get("medium")
        high_threshold = self.config.get("high")
        critical_threshold = self.config.get("critical")
        severities_thresholds = [lowest_threshold, low_threshold, medium_threshold, high_threshold, critical_threshold]

        big_scenarios_by_severity = defaultdict(list)

        step_based_scenario_ids = self.get_step_based_scenario_ids()
        for id in step_based_scenario_ids:
            scenario = self.project.get_scenario(id)
            nbr_scenario_steps = len(scenario.get_settings().raw_steps)

            for idx, max_nbr_steps_in_scenarios in enumerate(severities_thresholds):
                if nbr_scenario_steps > max_nbr_steps_in_scenarios:
                    big_scenarios_by_severity[idx].append(id)

        if len(big_scenarios_by_severity.keys()) > 0:
            max_severity_index = max(big_scenarios_by_severity.keys())
            big_scenarios = big_scenarios_by_severity[max_severity_index]
            max_nbr_steps_in_scenarios = severities_thresholds[max_severity_index]
            max_severity = max_severity_index + 1
            return ProjectStandardsCheckRunResult.failure(
                max_severity,
                f"{len(big_scenarios)} scenarios identified with more than {max_nbr_steps_in_scenarios} steps. See : {big_scenarios}",
                {"big_scenarios": big_scenarios},
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                f"All scenarios are under the max number of steps : {lowest_threshold}"
            )
