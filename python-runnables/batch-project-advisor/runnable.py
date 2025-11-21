# This file is the actual code for the Python runnable instance-advisor
from dataiku.runnables import Runnable

import dataiku
import dataikuapi
from dataiku.runnables import Runnable
from project_advisor.advisors.batch_project_advisor import (
    BatchProjectAdvisor,
    ProjectFilters,
)
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
        project_folder_id = config.get("folder_id", "")
        project_status_list = config.get("project_status_list", [])
        project_keys = config.get("project_keys", [])
        project_tags = config.get("project_tags", [])
        pat_report_folder_id = config.get("pat_report_folder", None)
        self.rebuild_pat_backend = config.get("rebuild_pat_backend", False)

        if config.get("run_on") == "current":
            project_filters = ProjectFilters(
                project_keys=[project_key],
                project_statuses=[],
                tags=[],
                folder_id="",
            )
        else:
            project_filters = ProjectFilters(
                project_keys=project_keys,
                project_statuses=project_status_list,
                tags=project_tags,
                folder_id=project_folder_id,
            )

        # Init Advisor
        
        pat_report_folder = dataiku.Folder(pat_report_folder_id)
        
        assessment_config = DSSAssessmentConfigBuilder.build_from_macro_config(config = config, plugin_config = plugin_config)
        
        logger.info(f"Macro instantating batch project advisor")
        self.batch_project_advisor = BatchProjectAdvisor(client = assessment_config.admin_design_client,
                                                    config = assessment_config, 
                                                    project_filters = project_filters,
                                                    pat_report_folder = pat_report_folder)
        
    def get_progress_target(self):
        """
        If the runnable will return some progress info, have this function return a tuple of 
        (target, unit) where unit is one of: SIZE, FILES, RECORDS, NONE
        """
        return None

    def run(self, progress_callback):
        """
        Run the BatchProjectAdvisor and save the report.
        """
        
        if self.rebuild_pat_backend:
            logger.info("Rebuilding the PAT backend before the run")
            self.batch_project_advisor.config.pat_backend_client.client = dataiku.api_client() # Workaround because of user API permission issue
            self.batch_project_advisor.config.pat_backend_client.build()
            self.batch_project_advisor.config.pat_backend_client.save()
        else:
            logger.info("Skipping the rebuilding of the PAT backend before the run")
        
        
        self.batch_project_advisor.run()
        self.batch_project_advisor.save()
        return f"The project Assessment Ran accross all of the projects : {self.batch_project_advisor.get_max_severity()} \n {[(pa.project.project_key, pa.get_max_severity()) for pa in self.batch_project_advisor.project_advisors]}"
        
        