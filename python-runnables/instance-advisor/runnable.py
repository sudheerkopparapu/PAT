# This file is the actual code for the Python runnable instance-advisor
from dataiku.runnables import Runnable

import dataiku
import dataikuapi
import os, json
import logging

from project_advisor.advisors.instance_advisor import InstanceAdvisor
from project_advisor.assessments.config_builder import DSSAssessmentConfigBuilder

from project_advisor.pat_logging import logger, set_logging_level

class MyRunnable(Runnable):
    """The base interface for a Python runnable"""

    def __init__(self, project_key, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        client = dataiku.api_client()
        
        ### INITIALISATION 
        set_logging_level(logger, plugin_config)
        
        # Load component specific parameters
        pat_report_folder_id = config.get("pat_report_folder",None)
        self.rebuild_pat_backend = config.get("rebuild_pat_backend", False)
        
        # Init Advisor
        pat_report_folder = dataiku.Folder(pat_report_folder_id)
        assessment_config = DSSAssessmentConfigBuilder.build_from_macro_config(config = config, plugin_config = plugin_config)

        logger.info(f"Macro instantating instance advisor")
        self.instance_advisor = InstanceAdvisor(client = client, # Requires an admin client 
                                                config = assessment_config, 
                                                pat_report_folder = pat_report_folder)
        
        logger.info(f"Macro sucessfully instantiated instance advisor")
        
    def get_progress_target(self):
        """
        If the runnable will return some progress info, have this function return a tuple of 
        (target, unit) where unit is one of: SIZE, FILES, RECORDS, NONE
        """
        return None

        
    def run(self, progress_callback):
        """
        Run the Instance advisor and save the report.
        """
        
        if self.rebuild_pat_backend:
            logger.info("Rebuilding the PAT backend before the run")
            self.instance_advisor.config.pat_backend_client.client = dataiku.api_client() # Workaround because of user API permission issue
            self.instance_advisor.config.pat_backend_client.build()
            self.instance_advisor.config.pat_backend_client.save()
        else:
            logger.info("Skipping the rebuilding of the PAT backend before the run")
        
        self.instance_advisor.run()
        self.instance_advisor.save()

        return f"Checks have run for all the projects with max severity : {self.instance_advisor.batch_project_advisor.get_max_severity()} and on the instance as a whole with a max severity of : {self.instance_advisor.get_max_severity()}"      
        
        