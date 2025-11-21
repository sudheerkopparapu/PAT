import pandas as pd
import dataiku
import dataikuapi

from typing import Any, List
from typing_extensions import Self
from abc import ABC, abstractmethod
from enum import Enum, auto
from packaging.version import Version

import dataikuapi

from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor
from project_advisor.assessments.checks import DSSCheck 
from project_advisor.assessments import InstanceCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.metrics.instance_metric import InstanceMetric

from project_advisor.pat_logging import logger

class InstanceCheck(DSSCheck):
    """
    A class representing a Instance check.
    """

    batch_project_advisor :BatchProjectAdvisor = None

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        name: str,
        description: str,
        batch_project_advisor : BatchProjectAdvisor,
        metrics : List[InstanceMetric],
        check_params : dict = {},
        tags: List[str] = [],
        dss_version_min: Version = None,
        dss_version_max: Version = None
    ):
        super().__init__(client = client,
                         config = config,
                         name = name,
                         description = description,
                         check_params = check_params,
                         tags = tags,
                         metrics = metrics,
                         dss_version_min = dss_version_min,
                         dss_version_max = dss_version_max)
        
        self.batch_project_advisor = batch_project_advisor
    
    def filter(self, filter_config : dict) -> bool:
        """
        Method filter out Instance Checks Assessments
        """
        remove = super().filter(filter_config)
        matching_tag = False
        if "instance_check_categories" in filter_config.keys():
            categories_to_keep = [c.name for c in filter_config["instance_check_categories"]]
            for tag in self.tags:
                if tag in categories_to_keep:
                    matching_tag = True
        if not matching_tag:
            remove = True
            logger.debug(f"Assessment {self.name} filtered as Instance Check tags {self.tags} are not included in {categories_to_keep}")
        return remove
    
    
    def get_metadata(self) -> dict:
        """
        Returns a json serializable payload of the assessment.
        """
        metadata = super().get_metadata()
        return metadata