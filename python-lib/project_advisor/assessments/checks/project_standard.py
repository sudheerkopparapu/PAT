import pandas as pd
import dataiku
import dataikuapi

from types import ModuleType
from typing import Any, List
from typing_extensions import Self
from abc import ABC, abstractmethod
from enum import Enum, auto
from packaging.version import Version
import json

from dataikuapi.dss.flow import DSSProjectFlowGraph
from dataikuapi.dss.project import DSSProject
from dataikuapi.dss.project_standards import DSSProjectStandardsCheckRunInfo
from dataiku.project_standards import ProjectStandardsCheckRunResult

from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments import CheckSeverity
from project_advisor.assessments import DSSAssessmentStatus

from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.config_builder import DSSAssessmentConfigBuilder

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments.checks import DSSCheck
from project_advisor.assessments.checks.project_check import ProjectCheck


from project_advisor.pat_logging import logger, set_logging_level


class ProjectStandardResult(ProjectCheck):
    """
    A class representing a Project Standard Result
    """
    
    project_standard_result: DSSProjectStandardsCheckRunInfo = None

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        project_standard_result : DSSProjectStandardsCheckRunInfo
    ):
        super().__init__(
            client=client,
            config=config,
            project=project,
            name="PROJECT_STANDARD_CHECK_NAME",
            description="PROJECT_STANDARD_CHECK_DESCRIPTION"
        )
        self.project_standard_result = project_standard_result
        self.populate_project_check()
    
    def populate_project_check(self):
        """
        Populate the ProjectCheck Fields based on the DSSProjectStandardsCheckRunInfo
        Acts as a dataclass
        """
        data = self.project_standard_result.data
        
        self.runtime = data.get("durationMs")
        
        check_info = data.get("check")
        self.check_id = check_info.get("id")
        self.name = check_info.get("name")
        self.description = check_info.get("description")
        self.check_element_type = check_info.get("checkElementType")
        self.tags = check_info.get("tags", [])
        
        check_params = data.get("expandedCheckParams")
        self.check_params = check_params
        
        check_result = data.get("result", {})
        self.status = DSSAssessmentStatus[check_result.get("status", DSSAssessmentStatus.NOT_RUN)] # RUN_SUCCESS, RUN_ERROR or NOT_APPLICABLE
        self.check_severity = CheckSeverity(check_result.get("severity",-1))
        self.message = check_result.get("message")
        self.run_result = check_result.get("details", {})
    
    def get_metadata(self) -> dict:
        metadata = super().get_metadata()
        metadata["check_id"] = self.check_id
        metadata["check_element_type"] = self.check_element_type
        return metadata

    def run(self) -> Self:
        """
        Run function. Not to be called.
        """
        raise Exception("Do not run a ProjectStandardResult, only use this class for serialization of check results from Project Standards")

    
