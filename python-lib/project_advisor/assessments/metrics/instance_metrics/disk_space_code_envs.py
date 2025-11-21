import dataikuapi
from packaging.version import Version
import os
import subprocess
from collections import Counter
import glob

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.instance_metric import InstanceMetric
from project_advisor.assessments.config import DSSAssessmentConfig 
from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

class DiskSpaceCodeEnvs(InstanceMetric):
    """
    Computes how much disk space is used by all Code envs on a Dku instance.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor
    ):
        """
        Initializes the DSS Instance Sanity Check with the provided client, config.
        """
        super().__init__(
            client = client,
            config = config,
            batch_project_advisor = batch_project_advisor,
            name = "disk_space_code_envs",
            metric_type = AssessmentMetricType.INT,
            description = "Disk space taken by all Code envs on a Dku instance",
            dss_version_min = Version("11.3.2"),
            dss_version_max = None
        )
        self.datadir_path = client.get_instance_info().raw["dataDirPath"]
        self.folder_name= "code-envs"
        self.uses_fs = True
        self.metric_unit = "kb"

    def get_size(self,folder_path,sub_folder):
        size = {}
        subfolder_path = os.path.join(folder_path,sub_folder) + "/*"
        files = glob.glob(subfolder_path)
        if files:
            for file in files:
                c=subprocess.run(["du", "-s", "-k", file], stdout=subprocess.PIPE)
                folder_size_in_kb = int(c.stdout.decode('utf-8').strip().split("\t")[0])
                code_env_name = file.split("/")[-1]
                size[code_env_name] = folder_size_in_kb     
        return Counter(size)
    
    def get_size_by_code_env(self,folder_path):
        sub_folders = ["python","R","resources/python"]
        sizes = [self.get_size(folder_path,f) for f in sub_folders]
        total_size = Counter()
        for size in sizes:
            total_size += size      
        return dict(total_size)


    def run(self) -> InstanceMetric:
        """
        Computes how much disk space is used by all Code envs on a Dataiku instance.
        :return: self
        """

        # Compute the total size of the code-envs directory
        folder_path = os.path.join(self.datadir_path,self.folder_name)
        folder_size_in_kb = 0
        if os.path.isdir(folder_path):
            result = subprocess.run(["du", "-s", "-k", folder_path], stdout=subprocess.PIPE)
            folder_size_in_kb = int(result.stdout.decode('utf-8').strip().split("\t")[0])
        self.value = folder_size_in_kb

        # Compute size for each code-env
        self.run_result = self.get_size_by_code_env(folder_path)
        return self