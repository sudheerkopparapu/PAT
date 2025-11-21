import dataiku

from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)


class MyProjectStandardsCheckSpec(ProjectStandardsCheckSpec):
    
    def main_scenario_tag_exists(self) -> bool:
        """
        Checks that there is a global tag category named 'Scenario Type' that has the tag 'main'.
        :return: boolean
        """
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
        Runs the check to determine if the project has a main scenario that is configured appropriately.

        :returns: the run result.
            Use `ProjectStandardsCheckRunResult.success(message)` or `ProjectStandardsCheckRunResult.failure(severity, message)` depending on the result.
            Use `ProjectStandardsCheckRunResult.not_applicable(message)` if the check is not applicable to the project.
            Use `ProjectStandardsCheckRunResult.error(message)` if you want to mark the check as an error. You can also raise an Exception.
        """

        self.client = dataiku.api_client()

        check_pass = False
        message = "This project does not have a scenario tagged as 'main'."
        result = {}

        if self.main_scenario_tag_exists():

            scenarios = self.project.list_scenarios(as_type="objects")
            for s in scenarios:
                s_raw_settings = s.get_settings().get_raw()
                s_tags = s_raw_settings["tags"]
                if any("Scenario Type:main" in tag for tag in s_tags):
                    if len(s_raw_settings["triggers"]) == 0:
                        message = "Found a scenario tagged as 'main' but no triggers have been set."
                    elif len(s_raw_settings["reporters"]) == 0:
                        message = "Found a scenario tagged as 'main' but no reporters have been set."
                    else:
                        check_pass = True
                        message = "Found a scenario tagged as 'main' that is configured with a trigger and a reporter."
                        break
        else:
            message = "Could not find the global tag 'Scenario Type:main'."

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
