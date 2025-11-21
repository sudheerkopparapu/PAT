import dataikuapi
from packaging.version import Version
import os
import subprocess

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig

class DiskSpaceJobLogs(ProjectMetric):
    """
    Computes how much disk space is used by all job logs in a project.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject
    ):
        """
        Initializes the ScenarioSizeCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client = client,
            config = config,
            project = project,
            name = "disk_space_job_logs",
            metric_type = AssessmentMetricType.INT,
            description = "Disk space taken by all jobs logs in the project",
            dss_version_min = Version("3.0.0"),
            dss_version_max = None,
            tags = ["FILE_SYSTEM"]
        )
        self.datadir_path = client.get_instance_info().raw["dataDirPath"]
        self.folder_name= "jobs"
        self.uses_fs = True
        self.metric_unit = "kb"
    
    def run(self) -> ProjectMetric:
        """
        Computes how much disk space is used by all job logs in a project.
        :return: self
        """
        project_folder_path = os.path.join(self.datadir_path,self.folder_name,self.project.project_key)
        folder_size_in_kb = 0
        if os.path.isdir(project_folder_path):
            result = subprocess.run(["du", "-s", "-k", project_folder_path], stdout=subprocess.PIPE)
            folder_size_in_kb = int(result.stdout.decode('utf-8').strip().split("\t")[0])
        self.value = folder_size_in_kb
        self.run_result = {}
        return self