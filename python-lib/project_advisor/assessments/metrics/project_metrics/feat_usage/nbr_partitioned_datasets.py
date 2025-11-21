import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig 
    
    
class NumberPartitionedDatasets(ProjectMetric):
    """
    Count the number of partitioned datasets in the Flow
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject
    ):
        super().__init__(
            client = client,
            config = config,
            project = project,
            name = "nbr_partitioned_datasets",
            metric_type = AssessmentMetricType.INT,
            description = "Number of shared objects",
            dss_version_min = Version("12.0.0"),
            dss_version_max = None, # Latest
            tags = ["FEATURE_USAGE"]
        )

    def run(self) -> ProjectMetric:
        """
        Computes the number of Partitioned datasets.
        """
        datasets = self.project.list_datasets()
        partitioned_datasets = [d for d in datasets if len(d.get("partitioning",{}).get("dimensions",[]))>0]
        run_result = {"partitioned_datasets" : [
                            {
                                "type" : d.get("type"),
                                "name" : d.get("name"),
                                "dimentions" : d.get("partitioning",{}).get("dimensions",[]),
                            } for d in partitioned_datasets
                        ]
                   }

        self.value = len(partitioned_datasets)
        self.run_result = run_result
        return self    