import pandas as pd
import dataiku
import dataikuapi

from typing import Any, List
from abc import ABC, abstractmethod
from datetime import datetime
import json
import sys, inspect
import logging
from pathlib import Path
import os
import importlib


from project_advisor.assessments import CheckSeverity
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.metrics.instance_metric import InstanceMetric
from project_advisor.assessments.checks.instance_check import InstanceCheck

from project_advisor.advisors import DSSAdvisor
from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor, ProjectFilters

import project_advisor
import project_advisor.assessments.checks.instance_checks # for loading
import project_advisor.assessments.metrics.instance_metrics # for loading

from project_advisor.pat_logging import logger

class InstanceAdvisor(DSSAdvisor):
    """
    The Instance Advisor Class runs Instance checks on a given DSS instance.
    Before each run, the checks are filtered according the the DSSAssessmentConfig.
    The result of the assessments can be logged to logging datasets.
    """
    batch_project_advisor: BatchProjectAdvisor = None

    def __init__(self,
                 client: dataikuapi.dssclient.DSSClient, 
                 config: DSSAssessmentConfig,
                 pat_report_folder : dataiku.Folder
    ):

        super().__init__(client = client, 
                         config = config,
                         pat_report_folder = pat_report_folder
                       )
        logger.info("Init of InstanceAdvisor")
        self.batch_project_advisor = BatchProjectAdvisor(client=client,
                                                             config=config, 
                                                             project_filters=ProjectFilters(), # No Filters
                                                             pat_report_folder=pat_report_folder)
        logger.info("BatchProjectAdvisor successfully created")
            
        self.init_instance_metric_list()
        self.init_instance_check_list()

        
    def run_metrics(self) -> List[InstanceMetric]:
        """
        Run all available instance metrics.
        Note : Do not run directly, use the *run* function instead.
        """
        logger.info(f"Running Instance Metrics")

        [metric.safe_run() for metric in self.metrics]
        
        return self.metrics
    
    def run_checks(self) -> List[InstanceCheck]:
        """
        Run all available instance checks.
        Note : The metrics should be run before running all the checks.
        Note : Do not run directly, use the *run* function instead.
        """
        logger.info(f"Running Instance Checks")
        
        if self.metrics == None:
            raise Exception('Run project metrics before running project checks')

        [check.safe_run() for check in self.checks]
        
        return self.checks

    def run(self) -> None:
        """
        Run all the available metrics and checks for all projects and the instance.
        """
        
        self.batch_project_advisor.run()
        logger.info(f"Sucessfully ran Batch Project Advisor")
        
        self.run_metrics()
        logger.info(f"Successfully ran Instance Metrics")
        
        self.run_checks()
        logger.info(f"Successfully ran Instance Checks")
        return
    
    def save(self, timestamp : datetime = datetime.now()) -> None:
        """
        Save all the checks and metrics for this ProjectAdvisor
        """
        logger.info(f"Logging all of the instance and project reports for InstanceAdvisor")
        
        self.batch_project_advisor.save(timestamp = timestamp)
        logger.info(f"Successfully saved Project Metrics and checks")
        
        self.save_metrics(self.metrics, timestamp = timestamp, metric_type = "instance")
        logger.info(f"Successfully saved Instance Metrics")
        
        self.save_checks(self.checks, timestamp = timestamp, check_type = "instance")
        logger.info(f"Successfully saved Instance Checks")
        
        return
            
    def get_max_severity(self) -> str:
        """
        Compute the project score.
        The Project score is the ratio between the passed checks and the overall relevant checks.
        """
        logger.debug(f"Computing Instance Max Severity")
        if len(self.checks) == 0:
            return CheckSeverity.OK.name
        return CheckSeverity(max([c.check_severity.value for c in self.checks])).name  
    
    def init_instance_metric_list(self) -> None:
        """
        Load all the ProjectMetric Classes under the metrics/project_metrics folder of the library.
        Instantiated each one and stores them in the checks class attribute.
        """
        logger.info(f"Building full list of Instance Metrics")
        
        # Load all the Intance Metric classes 
        instance_metric_classes = self.fetch_built_in_and_add_on_classes(root_module = project_advisor.assessments.metrics.instance_metrics,
                                                                           module_class = InstanceMetric)
        # Instantiate all the Instancemetrics
        all_metrics = []
        for instance_metric_class in instance_metric_classes:
            all_metrics.append(instance_metric_class(client = self.client, 
                                                     config = self.config,
                                                     batch_project_advisor = self.batch_project_advisor
                                                    ))
            
        # Filter all the checks according the assessment config & save
        self.metrics = self.filter_assessments(all_metrics)
        return
  
    def init_instance_check_list(self) -> None:
        """
        Load all the ProjectCheck Classes under the checks/project_metrics folder of the library.
        Instantiated each one and stores them in the checks class attribute.
        """
        logger.info(f"Building full list of Instance Checks")

        # Load all the Instance Check classes 
        instance_check_classes = self.fetch_built_in_and_add_on_classes(root_module = project_advisor.assessments.checks.instance_checks,
                                                                       module_class = InstanceCheck)

        # Instantiate all the Instance Checks
        all_checks = []
        for instance_check_class in instance_check_classes:
            all_checks.append(instance_check_class(client = self.client, 
                                                  config = self.config,
                                                  batch_project_advisor = self.batch_project_advisor,
                                                  metrics = self.metrics))

        # Filter all the checks according the assessment config & save
        self.checks = self.filter_assessments(all_checks)
        return

     
    