# File to contain the DSSMetric, DSSProjetMetric & DSSInstanceMetric classes.

import pandas as pd
import dataiku
import dataikuapi

from typing import Any, List
from typing_extensions import Self
from abc import ABC, abstractmethod
from enum import Enum, auto
from packaging.version import Version

from project_advisor.assessments.metrics import (DSSMetric, AssessmentMetricType)
from project_advisor.assessments.config import DSSAssessmentConfig 

from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor

class InstanceMetric(DSSMetric):
    """
    An abstract class to run and store Instance specific DSS metric computations
    """
    batch_project_advisor : BatchProjectAdvisor = None
     
    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config : DSSAssessmentConfig, 
        name: str,
        description: str,
        metric_type : AssessmentMetricType,
        batch_project_advisor : BatchProjectAdvisor,
        tags : List[str] = [],
        dss_version_min = None,
        dss_version_max = None,
    ):

        super().__init__(client = client,
                         config = config,
                         name = name,
                         metric_type = metric_type,
                         description = description,
                         tags = tags,
                         dss_version_min = dss_version_min,
                         dss_version_max = dss_version_max)
        self.batch_project_advisor = batch_project_advisor
    
    def get_metadata(self) -> dict:
        """
        Returns a json serializable payload of the assessment.
        """
        metadata = super().get_metadata()
        return metadata
    
    @abstractmethod
    def run() -> Self:
        """
        Abstract method to run an instance metric.
        Saves the result of a metric run & return the result of a metric run.
        """
        return
        