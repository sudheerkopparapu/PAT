import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
    def run(self):
        """
        Check that the project has a test scenario
        """

        self.required_steps = ['flow_test', 'exec_pytest', 'check_dataset', 'check_consistency']
        
        details = {}
        required_steps = self.config.get( "required_scenario_steps", [])
        scenarios = self.project.list_scenarios(as_type = "objects")
        test_scenarios = [scenario for scenario in scenarios if scenario.get_settings().data.get("markedAsTest")]
        print ("test_scenario",test_scenarios)

        if not test_scenarios:
            return ProjectStandardsCheckRunResult.failure(
                severity = int(self.config.get("severity")), 
                message =  "Project has no scenarios marked as test",
                details = details
            )

        all_steps_type = [step.get('type')
                          for scenario in test_scenarios
                          for step in scenario.get_settings().raw_steps
                          if  step.get('enabled')]

        missing_steps = list(set(required_steps) - set(all_steps_type))
        
        details["required_steps"] = ", ".join(required_steps)
        details["missing_steps"] = ", ".join(missing_steps)
 
  
        if len(missing_steps) == 0:
            return ProjectStandardsCheckRunResult.success(
                message = f"The project has a test scenario present and all required steps.",
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = f"The project has a test scenario but is missing the following scenario test steps : {', '.join(missing_steps)}",
                    details = details
                )

