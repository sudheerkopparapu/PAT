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


class ProjectMetric(DSSMetric):
    """
    An abstract class to run and store Project specific DSS metric computations
    """
    project : dataikuapi.dss.project.DSSProject = None
     
    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config : DSSAssessmentConfig,
        project : dataikuapi.dss.project.DSSProject,
        name: str,
        metric_type : AssessmentMetricType,
        description: str,
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
        self.project = project
    
    def get_metadata(self) -> dict:
        """
        Returns a json serializable payload of the assessment.
        """
        metadata = super().get_metadata()
        metadata.update(
            {
             "project_info" : self.get_project_info(self.project)
            }
        )
        return metadata
    
    @abstractmethod
    def run() -> Self:
        """
        Abstract method to run a project metric.
        Saves the result of a metric run & return the result of a metric run.
        """
        return
    
    ####################
    # Shared Functions #
    ####################
    def get_default_project_visual_exec_config(self, project : dataikuapi.dss.project.DSSProject) -> str:
        """
        Return the default containerized exec config for a visual recipe
        """
        DSS_ENGINE = "DSS"

        # Instance defaults
        instance_exec_conf = self.client.get_general_settings().settings.get("containerSettings")
        instance_default_visual_exec_config = instance_exec_conf.get('defaultExecutionConfigForVisualRecipesWorkloads')
        # Project defaults
        p_settings = project.get_settings().settings.get("settings",{})
        project_visual_exec_mode = p_settings.get("containerForVisualRecipesWorkloads",{}).get("containerMode")
        project_visual_exec_config = p_settings.get("containerForVisualRecipesWorkloads",{}).get("containerConf")

        if project_visual_exec_mode in [None, "NONE"]:
            engine = DSS_ENGINE
        elif project_visual_exec_mode == "INHERIT":
            if instance_default_visual_exec_config in [None, ""]:
                engine = DSS_ENGINE
            else:
                engine = instance_default_visual_exec_config
        elif project_visual_exec_mode == "EXPLICIT_CONTAINER":
            engine = project_visual_exec_config
        else:
            engine = "UNKNOWN_ENGINE"
        return engine

    def get_default_project_code_exec_config(self, project : dataikuapi.dss.project.DSSProject) -> str:
        """
        Return the default containerized exec config for a code recipe
        """
        DSS_ENGINE = "DSS"

        # Instance defaults
        instance_exec_conf = self.client.get_general_settings().settings.get("containerSettings")
        instance_default_code_exec_config = instance_exec_conf.get('defaultExecutionConfig')

        # Project defaults
        p_settings = project.get_settings().settings.get("settings",{})
        project_code_exec_mode = p_settings.get("container",{}).get("containerMode")
        project_code_exec_config = p_settings.get("container",{}).get("containerConf")

        if project_code_exec_mode in [None, "NONE"]:
            engine = DSS_ENGINE
        elif project_code_exec_mode == "INHERIT":
            if instance_default_code_exec_config in [None, ""]:
                engine = DSS_ENGINE
            else:
                engine = instance_default_code_exec_config
        elif project_code_exec_mode == "EXPLICIT_CONTAINER":
            engine = project_code_exec_config
        else:
            engine = "UNKNOWN_ENGINE"
        return engine

    def get_code_engine_from_container_selection(self,project : dataikuapi.dss.project.DSSProject ,
                                                 default_project_code_recipe_exec_config : str, 
                                                 containerMode : str = None, 
                                                 containerConf : str = None) -> str:
        """
        The containerMode and containerConf information can be fetched from the containerSelection attribute of recipes.
        """
        engine = "DSS"
        if containerMode in [None, "NONE"]:
            pass # DSS engine
        elif containerMode == "INHERIT":
            engine = default_project_code_recipe_exec_config
        elif containerMode == "EXPLICIT_CONTAINER":
            engine = containerConf
        else:
            engine = "UNKNOWN_ENGINE"
        return engine

        