# File to contain the DSSMetric, DSSProjetMetric & DSSInstanceMetric classes.

import pandas as pd
import dataiku
import dataikuapi

from typing import Any, List
from typing_extensions import Self
from abc import ABC, abstractmethod
from enum import Enum, auto
from packaging.version import Version

from project_advisor.assessments.dss_assessment import DSSAssessment
from project_advisor.assessments.config import DSSAssessmentConfig 


class AssessmentMetricType(Enum):
    """
    Enumeration representing different categories of project checks.
    """
    INT = auto()
    FLOAT = auto()
    BOOLEAN = auto()
    LIST = auto()
    

class DSSMetric(DSSAssessment):
    """
    An abstract class to run and store DSS metric computations
    """
    value : Any = None
    metric_type: AssessmentMetricType = None
    metric_unit : str = None

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config : DSSAssessmentConfig,
        name: str,
        metric_type : AssessmentMetricType,
        description: str,
        tags : List[str] = [],
        dss_version_min = None,
        dss_version_max = None
    ):
        super().__init__(client = client,
                         config = config,
                         name = name,
                         description = description,
                         tags = tags,
                         dss_version_min = dss_version_min,
                         dss_version_max = dss_version_max)
        self.metric_type = metric_type

    def get_metadata(self) -> dict:
        metadata = super().get_metadata()
        metadata.update(
            {"value": self.value, 
             "metric_type": self.metric_type.name,
             "metric_unit" : self.metric_unit}
        )
        return metadata
    
    @abstractmethod
    def run() -> Self:
        """
        Abstract method to run a metric.
        Saves the result of a metric run & return the result of a metric run.
        """
        return

