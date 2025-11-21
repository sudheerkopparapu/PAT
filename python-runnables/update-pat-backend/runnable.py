from dataiku.runnables import Runnable
import dataiku

from project_advisor.pat_logging import logger, set_logging_level
from project_advisor.assessments.config_builder import DSSAssessmentConfigBuilder

class MyRunnable(Runnable):
    """The base interface for a Python runnable"""

    def __init__(self, project_key, config, plugin_config):
        """
        Update PAT precomputed backend database
        """
        set_logging_level(logger, plugin_config)
        
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config
        self.pat_config = DSSAssessmentConfigBuilder.build_from_macro_config(config = config, plugin_config = plugin_config)
        
    def get_progress_target(self):
        return None

    def run(self, progress_callback):
        """
        Update PAT Backend with more up to date data by rebuilding and saving it.
        """
        
        pat_backend_tables = self.config.get("pat_backend_tables")
        pat_backend_client = self.pat_config.pat_backend_client
        
        self.pat_config.pat_backend_client.client = dataiku.api_client() # Workaround while waiting for a fix in 14.1? Needed to call the users API.
        
        pat_backend_client.build(data_tables = pat_backend_tables)
        pat_backend_client.save(data_tables = pat_backend_tables)
        
        return f"The following tables have been rebuilt in folder : {pat_backend_client.backend_folder.full_name}\nTables : {', '.join(pat_backend_tables)}"
        
        
        