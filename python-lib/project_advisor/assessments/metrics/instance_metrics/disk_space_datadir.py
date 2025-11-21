import dataikuapi
from packaging.version import Version
import os
import subprocess


from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.instance_metric import InstanceMetric
from project_advisor.assessments.config import DSSAssessmentConfig 
from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

class DiskSpaceDatadir(InstanceMetric):
    """
    Computes how much disk space is used by the Data Directory.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor       
    ):
        """
        Initializes the ScenarioSizeCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client = client,
            config = config,
            batch_project_advisor = batch_project_advisor,
            name = "disk_space_datadir",
            metric_type = AssessmentMetricType.INT,
            description = "Disk space taken by the Data Directory",
            dss_version_min = Version("3.0.0"),
            dss_version_max = None
        )
        self.datadir_path = client.get_instance_info().raw["dataDirPath"]
        self.uses_fs = True
        self.metric_unit = "kb"
    
    def run(self) -> InstanceMetric:
        """
        Computes how much disk space is used by the Data Directory.
        :return: self
        """
        folder_size_in_kb = 0
        if os.path.isdir(self.datadir_path):
            result = subprocess.run(["du", "-s", "-k", self.datadir_path], stdout=subprocess.PIPE)
            folder_size_in_kb = int(result.stdout.decode('utf-8').strip().split("\t")[0])
        
        self.value = folder_size_in_kb
        self.run_result = {}
        return self