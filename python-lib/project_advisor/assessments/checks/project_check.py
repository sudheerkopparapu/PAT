import pandas as pd
import dataiku
import dataikuapi

from typing import Any, List
from typing_extensions import Self
from abc import ABC, abstractmethod
from enum import Enum, auto
from packaging.version import Version

from dataikuapi.dss.flow import DSSProjectFlowGraph
from dataikuapi.dss.project import DSSProject

from project_advisor.assessments.dss_assessment import DSSAssessment
from project_advisor.assessments.checks import DSSCheck
from project_advisor.assessments import ProjectCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.metrics import DSSMetric

from project_advisor.pat_logging import logger

class ProjectCheck(DSSCheck): # DEPRECATED
    """
    
    A class representing a project check.
    """
    
    project: dataikuapi.dss.project.DSSProject = None

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
        name: str,
        description: str,
        check_params : dict = {},
        tags: List[str] = [],
        metrics : List[DSSMetric] = [],
        dss_version_min: Version = None,
        dss_version_max: Version = None,
        
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

    def count_datasets_in_graph(self, graph: DSSProjectFlowGraph):
        nodes = graph.nodes
        count = len([name for name in nodes.keys() if "DATASET" in nodes[name]["type"]])
        return count

    def get_output_dataset_ids(self, graph: DSSProjectFlowGraph) -> list:
        """
        Retrieves the IDs of output datasets in the project's flow.
        """
        nodes = graph.nodes
        output_dataset_ids = []

        for node_id in nodes.keys():
            if (
                "DATASET" in nodes[node_id]["type"]
                and len(nodes[node_id]["successors"]) == 0
            ):
                output_dataset_ids.append(nodes[node_id]["ref"])

        return output_dataset_ids
    
    def get_published_dataset_ids(self, project: DSSProject) -> list:
        """
        Retrieves the IDs of published datasets in the project's flow.
        """
        return [d["name"] for d in project.list_datasets() if d["featureGroup"]]



