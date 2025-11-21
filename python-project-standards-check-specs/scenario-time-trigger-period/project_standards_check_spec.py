import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.pat_tools import md_print_list


class MyProjectStandardsCheckSpec(ProjectStandardsCheckSpec):

    def calculate_trigger_period_in_minutes(self, frequency, repeat_frequency):
        """
        Calculates the period in minutes based on the frequency and repeatFrequency values.
        """
        
        if frequency == 'Minutely':
            return repeat_frequency
        elif frequency == 'Hourly':
            return repeat_frequency * 60
        elif frequency == 'Daily':
            return repeat_frequency * 24 * 60
        elif frequency == 'Weekly':
            return repeat_frequency * 7 * 24 * 60
        elif frequency == 'Monthly':
            # Assuming 30 days in a month for simplicity
            return repeat_frequency * 30 * 24 * 60
        else:
            # Handle unknown or unsupported frequencies
            return float('inf')
    
    def run(self):
        """
        Runs the check to determine if all time-based scenario triggers have a period great than 120 minutes.
        """
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')

        min_scenario_trigger_time_period = lowest_threshold

        result = {}
        details = {}
        time_trigger_periods = []
        
        scenarios = self.project.list_scenarios(as_type="objects")
        for scenario in scenarios:
            scenario_settings = scenario.get_settings().get_raw()
            for trigger in scenario_settings.get('triggers', []):
                if trigger['type'] == 'temporal':  # Checking for time-based triggers
                    frequency = trigger['params'].get('frequency')
                    repeat_frequency = trigger['params'].get('repeatFrequency', 1)

                    # Convert the frequency to minutes
                    period_in_minutes = self.calculate_trigger_period_in_minutes(frequency, repeat_frequency)
                    
                    # collect all time-based scenario trigger periods
                    time_trigger_periods.append(period_in_minutes)

                    # collect time-based scenario info with period lenght less than minimum threshold
                    if period_in_minutes <= min_scenario_trigger_time_period:
                        result[scenario.id] = {
                            "scenario_name": scenario.get_definition().get('name'),
                            "period_in_minutes": period_in_minutes
                        }
        # not applicable if there are no time-based scenarios
        if not time_trigger_periods:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = f"This project has no time-based scenarios.",
                details = details
            ) 
                
        if result:
            min_scenario_id = min(result, key=lambda k: result[k]['period_in_minutes'])
            min_scenario = result[min_scenario_id]
            min_name = min_scenario['scenario_name']
            min_period = min_scenario['period_in_minutes']

            if len(result) == 1:
                message = f"The scenario {min_name} has a trigger period of {min_period} minute(s). In total there is 1 scenario which has a trigger period less than {lowest_threshold} minutes."
                details['scenarios_to_modify'] = md_print_list(result.keys(),'scenario',self.original_project_key)
            if len(result) > 1:
                message = f"The scenario {min_name} has a trigger period of {min_period} minute(s). In total there are {len(result)} scenarios which have a trigger period lower than {lowest_threshold} minutes."
                details['scenarios_to_modify'] = md_print_list(result.keys(),'scenario',self.original_project_key)
        else:
            min_period = min(time_trigger_periods)

        details["nbr_time_triggers"] = len(time_trigger_periods)
        details["avg_period_in_minutes"] = (
                sum(time_trigger_periods) / len(time_trigger_periods)
                if time_trigger_periods else None
            )
        
        
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
