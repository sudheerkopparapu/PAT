#config.py

import dataiku

from project_advisor.assessments.config_builder import DSSAssessmentConfigBuilder
from project_advisor.pat_backend import PATBackendClient

def setup_configs(plugin_config : dict) -> None:
    # Set admin client
    admin_client = DSSAssessmentConfigBuilder.build_admin_design_client(plugin_config)
    run_config = DSSAssessmentConfigBuilder.build_run_config(plugin_config)
    
    configs["client"] = admin_client    
    configs["pat_backend_client"] = PATBackendClient(dss_client = admin_client,run_config = run_config) # Not use so far

configs = {
    # Define local client
    "client" : None, #dataiku.api_client(),
    "severity_name_mapping" : {
        5 : "CRITICAL",
        4 : "HIGH",
        3 : "MEDIUM",
        2 : "LOW",
        1 : "LOWEST",
        0 : "OK",
        -1: "OTHER"
    },
    
    # Columns in metric and check dataset
    "metric_required_columns" : ['timestamp','project_id','tags', 'metric_name', 'metric_value', 'metric_type', 'status', 'result_data'],
    "check_required_columns" : ['timestamp','project_id', 'tags','check_name','severity', 'message', 'check_params','status', 'result_data'],

}