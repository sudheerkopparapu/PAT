import pandas as pd
import dataiku
import dataikuapi

from typing import Any, List
from types import ModuleType
from abc import ABC, abstractmethod
from datetime import datetime
import json
import sys, inspect
import logging
from pathlib import Path
import os
import importlib
from statistics import mean 

from project_advisor.advisors import DSSAdvisor
from project_advisor.assessments.config import DSSAssessmentConfig

from project_advisor.assessments import CheckSeverity
from project_advisor.assessments.checks.project_standard import ProjectStandardResult
from project_advisor.assessments.checks.project_check import ProjectCheck
from project_advisor.assessments.metrics.project_metric import ProjectMetric

import project_advisor.assessments.checks.project_checks # for dynamic loading
import project_advisor.assessments.metrics.project_metrics # for dynamic loading

from project_advisor.pat_logging import logger

class ProjectAdvisor(DSSAdvisor):
    """
    The project Advisor Class runs project assessments on a given project.
    Before each run, the assessments are filtered according the the DSSAssessmentConfigs.
    The result of the project assessments can be logged to a logging dataset.
    """

    project: dataikuapi.dss.project.DSSProject
    
    def __init__(self,
                 client: dataikuapi.dssclient.DSSClient, 
                 config: DSSAssessmentConfig,
                 project: dataikuapi.dss.project.DSSProject,
                 pat_report_folder : dataiku.Folder
    ):
        
        super().__init__(client = client, 
                         config = config,
                         pat_report_folder = pat_report_folder
                       )
        logger.info("Init ProjectAdvisor")
        self.project = project
        self.init_project_metric_list()

    def run_metrics(self) -> List[ProjectMetric]:
        """
        Run all available metrics.
        Note : Do not run directly, use the *run* function instead.
        """
        logger.debug(f"Running Project Metrics for project {self.project.project_key}")

        [metric.safe_run() for metric in self.metrics]
        return self.metrics
    
    def run_checks(self) -> List[ProjectCheck]:
        """
        Run all available checks.
        Note : The metrics should be run before running all the checks.
        Note : Do not run directly, use the *run* function instead.
        """
        logger.info(f"Running Project Checks for project {self.project.project_key}")

        try:
            results_future = self.project.start_run_project_standards_checks()
            results_future.wait_for_result()
            results = results_future.get_result()

            self.checks = []
            for key, result in results.checks_run_info.items():
                self.checks.append(
                    ProjectStandardResult(
                        client = self.client, 
                        config = self.config,
                        project = self.project,
                        project_standard_result = result
                    )
                )
        except Exception as error:
            self.checks = []
            logger.warning(f"Failed to run Project Standards for project {self.project.project_key} with error : {type(error).__name__}:{str(error)}")
        return self.checks

    @classmethod
    def get_auth_user(cls):
        """
        Return the current authenticated user_id OR impersonated user in the case of api authentication.
        """
        auth_info = dataiku.api_client().get_auth_info()
        user_id = auth_info["authIdentifier"]
        if user_id[:4] == "api:": # Case client is authenticated with an API.
            user_id = auth_info["userForImpersonation"]
        return user_id
    
    
    def user_has_permissions(self, user_id : str) -> bool:
        """
        Return boolean assessing if a user has permissions to run PAT on a project.
        To run PAT on a project, the user needs to have access (as least read only) to the project on the design Node.
        """
        try:
            user = self.config.admin_design_client.get_user(user_id)
            user_client = user.get_client_as()
            project = user_client.get_project(self.project.project_key)
            project.get_metadata() # Checks if the user has at least read only access
            return True
        except:
            return False
    
    def run(self) -> None:
        """
        Run all the availalbe metrics and checks for a project.
        """
        logger.info(f"Running PAT on project {self.project.project_key}")
        self.run_metrics()
        self.run_checks()
        return
    
    def save(self, timestamp : datetime = datetime.now()) -> None:
        """
        Save all the checks and metrics for this ProjectAdvisor
        """
        logger.info(f"Logging PAT results for project {self.project.project_key}")
        self.save_metrics(self.metrics, timestamp = timestamp, metric_type = "project")
        self.save_checks(self.checks, timestamp = timestamp, check_type = "project")
        return
          
    def get_max_severity(self) -> str:
        """
        Compute the project max severity.
        This will be based on the critical checks.
        """
        logger.debug(f"Computing Max Severity for project {self.project.project_key}")
        return CheckSeverity(self.get_max_severity_level()).name
    
    def get_max_severity_level(self) -> int:
        """
        Compute the project max severity.
        This will be based on the critical checks.
        """
        if self.checks == None:
            raise Exception('Run project checks before computing the project score')
        
        if len(self.checks) == 0:
            return CheckSeverity.OK.value
        return max([c.check_severity.value for c in self.checks])
        

    def init_project_metric_list(self) -> None:
        """
        Load all the ProjectMetric Classes under the metrics/project_metrics folder of the library.
        Instantiated each one and stores them in the checks class attribute.
        """
        logger.info(f"Building full list of metrics for project {self.project.project_key}")
        
        # Load all the Project Metrics classes 
        project_metric_classes = self.fetch_built_in_and_add_on_classes(root_module = project_advisor.assessments.metrics.project_metrics,
                                                                       module_class = ProjectMetric)
        # Instantiate all the project metrics
        all_metrics = []
        for project_metric_class in project_metric_classes:
            all_metrics.append(project_metric_class(client = self.client, 
                                                  config = self.config, 
                                                  project = self.project))

        # Filter all the checks according the assessment config & save
        self.metrics = self.filter_assessments(all_metrics)
        return
  
    # To be removed as not needed once 14.1 is out
    def init_project_check_list(self) -> None:
        """
        Load all the ProjectCheck Classes under the checks/project_metrics folder of the library.
        Instantiated each one and stores them in the checks class attribute.
        """
        
        logger.info(f"Building full list of checks for project {self.project.project_key}")

        # Load all the Project Check classes 
        project_check_classes = self.fetch_built_in_and_add_on_classes(root_module = project_advisor.assessments.checks.project_checks,
                                                   module_class = ProjectCheck)
        # Instantiate all the project checks
        all_checks = []
        for project_check_class in project_check_classes:
            all_checks.append(project_check_class(client = self.client, 
                                                  config = self.config, 
                                                  project = self.project,
                                                  metrics = self.metrics))

        # Filter all the checks according the assessment config & save
        self.checks = self.filter_assessments(all_checks)
        return
