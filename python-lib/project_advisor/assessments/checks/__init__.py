import pandas as pd
import dataiku
import dataikuapi

from typing import Any, List
from typing_extensions import Self
from abc import ABC, abstractmethod
from enum import Enum, auto
from packaging.version import Version

from project_advisor.assessments import CheckSeverity
from project_advisor.assessments import DSSAssessmentStatus
from project_advisor.assessments.dss_assessment import DSSAssessment
from project_advisor.assessments.config import DSSAssessmentConfig 
from project_advisor.assessments.metrics import DSSMetric

from project_advisor.pat_logging import logger

class DSSCheck(DSSAssessment):
    """
    Abstract base class for DSS checks.
    """
    check_severity : CheckSeverity = CheckSeverity.NO_SEVERITY
    check_params : dict = {}
    message : str = None
    metrics : List[DSSMetric] = None
        
    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        name: str,
        description: str,
        tags : List[str],
        check_params : dict = {},
        metrics : List[DSSMetric] = [],
        dss_version_min: Version = None,
        dss_version_max : Version = None
    ):
        super().__init__(client = client, 
                         config = config,
                         name = name,
                         description = description,
                         dss_version_min = dss_version_min,
                         dss_version_max = dss_version_max,
                         tags = tags)
        
        self.metrics = metrics
        self.check_params = check_params
   
    @abstractmethod
    def run(self) -> Self:
        """
        Abstract method to run the check then save and return the result.
        """
        return
    
    def get_metadata(self) -> dict:
        metadata = super().get_metadata()
        metadata["check_severity"] = self.check_severity.name
        metadata["check_params"] = self.check_params
        return metadata
    
    def get_metric(self, metric_name : str) -> DSSMetric:
        """
        Function to use in a check to run get a previously computed metric object.
        """
        logger.debug(f"Fetching metric {metric_name} from list of metrics")
        for m in self.metrics:
            if m.name == metric_name:
                return m
        return None
    
    def get_lc_model(self, llm_id, temperature):
        """
        Return langchain model from llm_id regardless of DSS version
        """
        
        dss_version = Version(self.client.get_instance_info()._data["dssVersion"])
        dss_13_1_0 = Version("13.1.0")
        if dss_version >= dss_13_1_0:
            model = self.project.get_llm(llm_id).as_langchain_llm()
            model.temperature = temperature
            return model
        else:
            from dataiku.langchain.dku_llm import DKUChatLLM
            return DKUChatLLM(llm_id=llm_id, temperature=temperature)


    

