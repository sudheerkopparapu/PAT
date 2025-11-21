import dataikuapi

from typing import Any, Dict, List
from typing_extensions import Self
from abc import ABC, abstractmethod

from packaging.version import Version
import time
import re

from project_advisor.assessments.config import DSSAssessmentConfig

from project_advisor.pat_logging import logger
from project_advisor.assessments import DSSAssessmentStatus

class DSSAssessment(ABC):
    """
    Abstract base class for DSS metrics & checks.
    An Assessment:
    -> Has a unique name & description.
    -> Can be run.
    -> Shares a config with all other Assessments.
    -> Saves it's latest run results.
    -> Has a compatible DSS version range (None meaning no limit)
    -> Has class parameters that can be used for filtering.
    """

    client: dataikuapi.dssclient.DSSClient = None
    config : DSSAssessmentConfig = None # Shared config between all the assessments.
    name: str = None
    description: str = None
    dss_version_min: Version = None
    dss_version_max: Version = None
    runtime = None
    tags : List[str] = []
    status : DSSAssessmentStatus = DSSAssessmentStatus.NOT_RUN
    
    # Filter Params
    has_llm = False
    uses_fs = False
    uses_plugin_usage = False
        
    run_result: dict = None

    def __init__(
        self, 
        client: dataikuapi.dssclient.DSSClient, 
        config : DSSAssessmentConfig,
        name: str,
        description: str,
        tags = [],
        dss_version_min : Version = Version("12.0.0"),
        dss_version_max : Version = None,
    ):
        """
        Initializes a DSS Assessment with the provided parameters.
        """
        self.config = config
        self.client = client
        self.name = name
        self.description = description
        self.tags = tags
        if dss_version_min is not None:
            self.dss_version_min = dss_version_min
        if dss_version_max is not None:
            self.dss_version_max = dss_version_max
        
        logger.debug(f"Init of Assessment of name {self.name}")
        
    @abstractmethod
    def run(self) -> Self:
        """
        Abstract method to run an assessment.
        Save an assessment & return the result of an assessment.
        """
        return self
    
    
    def safe_run(self) -> Self:
        """
        Method to run an assessment catching any errors
        """
        logger.debug(f"Safe run of Assessment of name {self.name}")
        start_time = time.time()
        try:
            self.run()
            self.status = DSSAssessmentStatus.RUN_SUCCESS
        except Exception as error:
            self.status = DSSAssessmentStatus.RUN_ERROR
            error_dict = {
                            "error" : type(error).__name__,
                            "error_message" : str(error)
                         }
            if isinstance(self.run_result, dict):
                self.run_result.update()
            else:
                self.run_result = error_dict
        
        self.runtime = time.time() - start_time
        return self
    
    def print_tags(self) -> str:
        if isinstance(self.tags, list):
            return "|".join(self.tags)
        elif isinstance(self.tags, str):
            return self.tags
        else:   
            return ""
    
    @classmethod
    def load_tags_str(cls, tags : str) -> list:
        if isinstance(tags, str):
            return tags.split("|")
        else:
            logger.debug(f"tags {self.tags} are not in a list format")
            return f"Cannot parse tags for the form : {str(tags)}"

    def filter(self, filter_config : dict) -> bool:
        """
        Method to find if an assessment should be filtered (removed) or not.
        """
        # Filter on DSS version assessment compatibility
        remove = False
        if not self.dss_version_in_range():
            remove = True
            logger.debug(f"Assessment {self.name} filtered as current DSS instance version is not supported")
           
        # uses LLM filter : Filter out all llm powered assessments if the llm option is not enabled.
        if "use_llm" in filter_config.keys() and (not filter_config["use_llm"]):
            if self.has_llm == True:
                remove = True
                logger.debug(f"Assessment {self.name} filtered because it uses an LLM")
        
        # uses plugin filter : Filter all assessments that leverage plugin usage
        if "use_plugin_usage" in filter_config.keys() and (not filter_config["use_plugin_usage"]):
            if self.uses_plugin_usage == True:
                remove = True
                logger.debug(f"Assessment {self.name} filtered because it leverages plugin usage")
        
        # uses FS filter : Filter all assessments that leverage the DS File System
        if "use_fs" in filter_config.keys() and (not filter_config["use_fs"]):
            if self.uses_fs == True:
                remove = True
                logger.debug(f"Assessment {self.name} filtered because it leverages the DSS FS")

        return remove
    

    def dss_version_in_range(self):
        """
        Method to determin if an Assessment is compatible with current the DSS verion
        """
        dss_version_raw = self.client.get_instance_info().raw["dssVersion"]
        match = re.match(r"(\d+)\.(\d+)\.(\d+).*", dss_version_raw) # Manage edge case where version has trailing characters.
        if match:
            x, y, z = match.groups()
            dss_version_str = f"{x}.{y}.{z}"
            if dss_version_str == "0.0.0": # Edge case when working with Dataiku Kits
                dss_version_str = "20.0.0"
        else:
            dss_version_str = "20.0.0"
        
        
        dss_version = Version(dss_version_str)
        return (self.dss_version_min is None or dss_version >= self.dss_version_min) and (self.dss_version_max is None or dss_version <= self.dss_version_max)
    
    def get_metadata(self) -> dict:
        """
        Returns a json serializable payload of the assessment.
        """
        return {
                    "name": self.name,
                    "description" : self.description,
                    "dss_version_min" :str(self.dss_version_min),
                    "dss_version_max" : str(self.dss_version_max),
                    "run_result" : self.run_result,
                    "runtime" : self.runtime,
                    "tags" : self.tags,
                    "status" : self.status.name
               }
    
    
    ### Helper Functions ###
    def get_project_info(self, project : dataikuapi.dss.project.DSSProject) -> dict:
        """
        Return a dict with project specific metadata
        """
        try:
            project_to_folder_path_df = self.config.pat_backend_client.get_table("project_to_folder_path")  
            if project_to_folder_path_df is not None:
                project_folder = project_to_folder_path_df[project_to_folder_path_df["project_key"] == project.project_key]["path"][0]
            else:
                project_folder = project.get_project_folder().get_path()
            return {
                "project_key" : project.project_key,
                "project_tags" : project.get_metadata().get("tags",[]),
                "project_status" : project.get_settings().settings.get("projectStatus", "NO_STATUS"),
                "project_folder" : project_folder
            }
        except Exception as error:
            return {"error" : str(error)}
 
        
        
        
        
        