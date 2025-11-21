import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig
from collections import Counter

class NumberOfUsedDatasetConectionsMetric(ProjectMetric):
    """
    List all the connections used by datasets in a project.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject
    ):
        """
        Initializes the Metric with a client, config, and project.
        """
        super().__init__(
            client = client,
            config = config,
            project = project,
            name = "nbr_distinct_used_dataset_connections",
            metric_type = AssessmentMetricType.INT,
            description = "Number of distinct dataset connections used by datasets in a project.",
            dss_version_min = Version("3.0.0"),
            dss_version_max = None,
            tags = ["FEATURE_USAGE"]
        )

    
    def run(self) -> ProjectMetric:
        """
        Computes the number of distinct connections used in a project.
        :return: self
        """
        cnxs = []
        unmanaged_datasets = []
        result = {}
        datasets = self.project.list_datasets()
        
        for dataset in datasets:
            try:
                if dataset["type"] == "UploadedFiles":
                    cnxs.append(("UploadedFiles",dataset["params"]["uploadConnection"]))
                elif dataset["type"] == "Inline":
                    cnxs.append(("Inline", "editable"))
                elif dataset["type"] == "FilesInFolder":
                    cnxs.append(("FilesInFolder", "Folder"))
                else:
                    cnxs.append((dataset["type"], dataset["params"]["connection"]))
            except:
                unmanaged_datasets.append(dataset)

        result["unmanaged_datasets"] = unmanaged_datasets
        
        dist_cnxs = []
        counter = Counter(cnxs)     
        for cnx in counter.keys():
            dist_cnxs.append((cnx[0], cnx[1],counter[cnx]))
        
        result["dist_cnxs"] = dist_cnxs
        
        self.value = len(dist_cnxs)
        self.run_result = result
        return self