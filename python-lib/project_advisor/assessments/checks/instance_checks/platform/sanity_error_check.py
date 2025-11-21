import dataikuapi
from typing import List

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import InstanceCheckCategory, CheckSeverity
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.instance_check import InstanceCheck

from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

class InstanceErrorCheck(InstanceCheck):
    """
    Check for errors on the instance sanity report
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the InstanceError instance with the provided client, config.
        """
        super().__init__(
            client=client,
            config=config,
            batch_project_advisor = batch_project_advisor,
            metrics = metrics,
            tags=[InstanceCheckCategory.PLATFORM.name],
            name="instance_error_check",
            description="Checks that there are no errors in the DSS sanity report"
        )
       
    def run(self) -> InstanceCheck:
        """
        Runs the check to determine if there are any instance errors from the instance sanity check.
        :return: self
        """
        
        metric = self.get_metric("nbr_sanity_check_errors")
        check_pass = True
        message = "There are no instance sanity errors"
        sanity_errors_dict = {}
        
        if metric.value > 0:
            check_pass = False
            sanity_errors = metric.run_result.get("sanity_errors", [])
            sanity_errors_dict = {}
            message = f"There are {metric.value} errors on the instance sanity check report:\n"
            for error in sanity_errors:
                message = message + f"{error.get('title')}\n"
                sanity_errors_dict[error.get("title")] = error.get("details")
                
        if check_pass:    
            self.check_severity = CheckSeverity.OK
        else:
            self.check_severity = CheckSeverity.HIGH
        self.message = message
        self.run_result = {"sanity_errors" :sanity_errors_dict}
        return self


