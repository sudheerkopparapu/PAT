import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import InstanceCheckCategory, CheckSeverity
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.instance_check import InstanceCheck


from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

class InstanceWarningCheck(InstanceCheck):
    """
    Check that the number of steps in a scenario is below a certain threshold.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the InstanceError instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            batch_project_advisor = batch_project_advisor,
            metrics = metrics,
            tags=[InstanceCheckCategory.PLATFORM.name],
            name="instance_warning_check",
            description="Checks that there are no warnings on the DSS sanity report",
        )

        
    def run(self) -> InstanceCheck:

        """
        Runs the check to determine if there are any instance errors from the instance sanity check.
        :return: self
        """
        
        metric = self.get_metric("nbr_sanity_check_warnings")
        check_pass = True
        message = "There are no instance sanity warnings"
        run_results = {}
        
        if metric.value > 0:
            check_pass = False
            sanity_warnings = metric.run_result.get("sanity_warnings", [])
            sanity_warnings_dict = {}
            message = f"There are {metric.value} warnings on the instance sanity check report:\n"
            for warning in sanity_warnings:
                message = message + f"{warning.get('title') }\n"
                sanity_warnings_dict[warning.get("title")] = warning.get("details")
                
        if check_pass:    
            self.check_severity = CheckSeverity.OK
        else:
            self.check_severity = CheckSeverity.MEDIUM
        self.message = message
        self.run_result = {"sanity_warnings" :sanity_warnings_dict}
        return self
