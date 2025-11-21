import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)


class MainScenarioLastRunSuccessfulCheckSpec(ProjectStandardsCheckSpec):
    """
    Check that the main scenario's last run was successful.
    """
    def main_scenario_tag_exists(self) -> bool:
        """
        Checks that there is a global tag category named 'Scenario Type' that has the tag 'main'.
        :return: boolean
        """
        self.client = dataiku.api_client()

        global_tags = self.client.get_general_settings().get_raw()["globalTagsCategories"]
        if (
            len(global_tags) != 0
            and any(tag["name"] == "Scenario Type" for tag in global_tags)
            and any(tag["name"] == "main" for cat in global_tags for tag in cat["globalTags"])
        ):
            return True
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

        if self.main_scenario_tag_exists():
            scenarios = self.project.list_scenarios(as_type="objects")
            for s in scenarios:
                if any("Scenario Type:main" in tag for tag in s.get_settings().get_raw()["tags"]):
                    try:
                        if s.get_last_finished_run().outcome == "SUCCESS":
                            return ProjectStandardsCheckRunResult.success(
                                "The project's main scenario had a successful last run"
                            )
                    except:
                        return ProjectStandardsCheckRunResult.failure(
                            severity, "The project's main scenario does not have a completed run, but a successful run is required"
                        )
                    break

            return ProjectStandardsCheckRunResult.failure(
                severity, "The project does not have a scenario tagged as 'main'"
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                severity, "Could not find the global tag 'Scenario Type:main'."
            )
