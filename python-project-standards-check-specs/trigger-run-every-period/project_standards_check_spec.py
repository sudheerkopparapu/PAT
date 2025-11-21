import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.pat_tools import md_print_list

class MyProjectStandardsCheckSpec(ProjectStandardsCheckSpec):

    def run(self):
        """
        Runs the check to determine if all non-time-based scenario triggers have a period greater than 7200 seconds.
        """
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')

        min_scenario_trigger_time_period = lowest_threshold

        result = {}
        details = {}
        trigger_periods = []
        
        scenarios = self.project.list_scenarios(as_type="objects")        
        for scenario in scenarios:

            scenario_settings = scenario.get_settings().get_raw()
            for trigger in scenario_settings.get('triggers', []):
                if trigger['type'] != 'temporal':  # Checking for time-based triggers
                    frequency_in_seconds = trigger['delay']

                    trigger_periods.append(frequency_in_seconds)

                    if frequency_in_seconds <= min_scenario_trigger_time_period:
                        result[scenario.id] = {
                            "scenario_name": scenario.get_definition().get('name'),
                            "period_in_seconds": frequency_in_seconds
                        }
        
        # not applicable if there are no time-based scenarios
        if not trigger_periods:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = f"This project has no time-based scenarios.",
                details = details
            ) 
        
        if result:
            min_scenario_id = min(result, key=lambda k: result[k]['period_in_seconds'])
            min_scenario = result[min_scenario_id]
            min_name = min_scenario['scenario_name']
            min_period = min_scenario['period_in_seconds']

            if len(result) == 1:
                message = f"The scenario {min_name} has a trigger period of {min_period} seconds(s). In total there is 1 scenario which has a trigger period less than {int(lowest_threshold)} seconds."
            if len(result) > 1:
                message = f"The scenario {min_name} has a trigger period of {min_period} seconds(s). In total there are {len(result)} scenarios which have a trigger period lower than {int(lowest_threshold)}." 
        else:
            min_period = min(trigger_periods)

        details["nbr_time_triggers"] = len(trigger_periods)
        details["avg_period_in_minutes"] = (
                sum(trigger_periods) / len(trigger_periods)
                if trigger_periods else None
            )
        details['scenarios_to_modify'] = md_print_list(result.keys(),'scenario',self.original_project_key)
        
        if min_period < critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = message,
                details = details
            )
        elif min_period < high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = message,
                details = details
            )
        elif min_period < medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = message,
                details = details
            )
        elif min_period < low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = message,
                details = details
            )
        elif min_period < lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = message,
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = f"All time-based scenario triggers have a period greater than {int(lowest_threshold)} minutes.",
                details = details
            )

        
