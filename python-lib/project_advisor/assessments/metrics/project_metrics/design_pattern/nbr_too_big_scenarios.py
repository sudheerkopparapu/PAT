import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig


class NumberOfTooBigScenarios(ProjectMetric):
    """
    Count the number of "too big" scenarios in a project.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
    ):
        """
        Initializes the NumberOfTooBigScenarios metric class with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            name="nbr_of_too_big_scenarios",
            metric_type=AssessmentMetricType.INT,
            description="Number of too big scenarios",
            dss_version_min=Version("3.0.0"),
            dss_version_max=None,  # Latest
            tags = ["DESIGN_PATTERN"]
        )
    
    def get_step_based_scenario_ids(self) -> List[str]:
        """
        Retrieves the IDs of all step-based scenarios in the project.
        :return: self
        """
        scenario_items = self.project.list_scenarios()
        ids = [
            scenario_item["id"]
            for scenario_item in scenario_items
            if scenario_item["type"] == "step_based"
        ]
        return ids

    def run(self) -> ProjectMetric:
        """
        Computes the number of too big scenarios in the project.
        :return: self
        """
        max_nbr_steps_in_scenarios = 20
        step_based_scenario_ids = self.get_step_based_scenario_ids()
        result = {
            'max_nbr_steps_in_scenarios': max_nbr_steps_in_scenarios,
            'scenarios': {}
        }
                
        for id in step_based_scenario_ids:
            nbr_scenario_steps = len(self.project.get_scenario(id).get_settings().raw_steps)
            if nbr_scenario_steps > max_nbr_steps_in_scenarios:
                result['scenarios'][id] = nbr_scenario_steps
        
        self.value = len(result['scenarios'])
        self.run_result = result
        return self
