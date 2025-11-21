from typing import List

import dataiku
import dataikuapi
from project_advisor.assessments import InstanceCheckCategory
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.pat_tools import throw_if_not_an_url


class DSSAssessmentConfigBuilder():
    
    @classmethod
    def build_from_macro_config(cls, config : dict = {}, plugin_config : dict = {}):
        """
        Input : Macro component settings
        Output : DSSAssessmentConfig
        Build the DSSAssessmentConfig
        """
        
        ### Loading parameters ###
        check_filters = DSSAssessmentConfigBuilder.build_check_filters(config)
        
        # Project & Instance Check Configs
        check_configs = DSSAssessmentConfigBuilder.build_check_configs(config)
        
        # Deployment Settings
        deployment_config = DSSAssessmentConfigBuilder.build_deployment_config(plugin_config)
        
        # Setup Design Clients
        client = dataiku.api_client()
        if not deployment_config["verify_ssl_certificate"]:
            client._session.verify = False
        admin_client = DSSAssessmentConfigBuilder.build_admin_design_client(plugin_config)
        
        # Run Config
        run_config = DSSAssessmentConfigBuilder.build_run_config(plugin_config)
        
        ### Defining the final DSSAssessemntConfig
        return DSSAssessmentConfig({
             "design_client" : client,
             "admin_design_client" : admin_client,
             "deployment_config" : deployment_config,
             "check_filters" : check_filters,
             "check_configs" : check_configs,
             "run_config" : run_config
            })

    
    @classmethod
    def build_check_configs(clf, config : dict):
        """
        Preprocess any config parameters needed for configuring assessments
        Input : config : dict of component level config
        Output : dict of config
        """
        # Instance Check Filter preset parameters
        instance_check_config_preset = config.get("instance_check_config_preset",{})
        config.pop("instance_check_config_preset", None)
        config.update(instance_check_config_preset)  # Add preset content as top level keys 
        return config    

  
    @classmethod
    def build_check_filters(clf, config : dict):
        """
        Preprocess any config parameters needed for filtering of assessments
        Input : plugin_config : dict of plugin level configs 
        Output : dict of deployment config
        """
        
        # Instance Check Filter preset parameters 
        instance_check_filter_preset = config.get("instance_check_filter_preset",{})
        config.pop("instance_check_filter_preset", None)
        config.update(instance_check_filter_preset) # Add preset content as top level keys 
        
        # Build Assessment filter config
        config.update ({
            "instance_check_categories": [InstanceCheckCategory[category] for category in config.get("instance_check_categories",[])]
        })
        return config
        
    @classmethod
    def build_admin_design_client(clf, plugin_config : dict):       
        """
        Input : plugin_config : dict of plugin level configs 
        Output : return : admin design node client
        """
        design_admin_api_key = plugin_config.get("design_admin_api_key", None)
        verify_ssl_certificate = plugin_config.get("verify_ssl_certificate", True)

        if plugin_config.get("use_external_design_node", False):
            design_host = plugin_config.get("design_host", None)
            throw_if_not_an_url(design_host, "Design Host")
        else:
            design_host = dataiku.api_client().host
        
        ### Build Admin Design Node Client
        admin_design_client = dataikuapi.DSSClient(host=design_host, api_key=design_admin_api_key)
        if not verify_ssl_certificate:
            admin_design_client._session.verify = False
        return admin_design_client
        
    
    @classmethod
    def build_deployment_config(clf, plugin_config : dict):
        """
        Input : plugin_config : dict of plugin level configs 
        Output : return : dict of deployment config
        Helper function to build the deployment_config
        """

        # Plugin (Instance) level config
        connect_to_automation_nodes = plugin_config.get("connect_to_automation_nodes", False)
        deployment_method = plugin_config.get("deployment_method", "manual") if connect_to_automation_nodes else None
        fm_host = plugin_config.get("fm_host", None)
        fm_api_key_id = plugin_config.get("fm_api_key_id", None)
        fm_api_key_secret = plugin_config.get("fm_api_key_secret", None)
        verify_ssl_certificate = plugin_config.get("verify_ssl_certificate", True)
        use_external_deployer_node = plugin_config.get("use_external_deployer_node", False)
        infras = plugin_config.get("infras", [])

        # For manual definition of deployer, test-auto & auto
        deployer_host = plugin_config.get("deployer_host", None)
        deployer_api_key = plugin_config.get("deployer_api_key", None)

        ### Build Assessment deployment config
        fm_client = None
        external_deployer_client = None
        automation_nodes = {}
        if deployment_method == "fm-azure":
            throw_if_not_an_url(fm_host, "Cloud Stacks Host")
            fm_client = dataikuapi.fmclient.FMClientAzure(fm_host, fm_api_key_id, fm_api_key_secret)

        elif deployment_method == "fm-aws":
            throw_if_not_an_url(fm_host, "Cloud Stacks Host")
            fm_client = dataikuapi.fmclient.FMClientAWS(fm_host, fm_api_key_id, fm_api_key_secret)

        elif deployment_method == "fm-gcp":
            throw_if_not_an_url(fm_host, "Cloud Stacks Host")
            fm_client = dataikuapi.fmclient.FMClientGCP(fm_host, fm_api_key_id, fm_api_key_secret)

        elif deployment_method == "manual":
            # Manually entered automation nodes
            for infra_config in infras:
                infra_id = infra_config.get("infra_id", None)
                automation_nodes_clients = clf._build_automation_nodes_clients(infra_config, verify_ssl_certificate)
                automation_nodes[infra_id] = automation_nodes_clients

            if use_external_deployer_node:
                # Manually entered deployer
                throw_if_not_an_url(deployer_host, "Deployer Host")
                external_deployer_client = dataikuapi.DSSClient(host=deployer_host, api_key=deployer_api_key)
                if not verify_ssl_certificate:
                    external_deployer_client._session.verify = False

        if not verify_ssl_certificate and fm_client != None:
            fm_client._session.verify = False

        deployment_config = {
            "deployment_method": deployment_method,
            "external_deployer_client": external_deployer_client,
            "automation_nodes": automation_nodes,
            "fm_client": fm_client,
            "verify_ssl_certificate": verify_ssl_certificate,
        }
        return deployment_config

    @classmethod
    def _build_automation_nodes_clients(
        clf, infra_config: dict, verify_ssl_certificate: bool
    ) -> List[dataikuapi.dssclient.DSSClient]:
        infra_id = infra_config.get("infra_id", None)
        infra_type = infra_config.get("infra_type", "single")

        if infra_type == "multi":
            auto_multi_nodes = infra_config.get("auto_multi_nodes", [])
            auto_clients = [
                dataikuapi.DSSClient(host=node.get("auto_host", None), api_key=node.get("auto_api_key", None))
                for node in auto_multi_nodes
            ]
        else:
            auto_host = infra_config.get("auto_host", None)
            auto_api_key = infra_config.get("auto_api_key", None)
            auto_clients = [dataikuapi.DSSClient(host=auto_host, api_key=auto_api_key)]

        for auto_client in auto_clients:
            throw_if_not_an_url(auto_client.host, f"Automation Node Host for infra {infra_id}")
            if not verify_ssl_certificate:
                auto_client._session.verify = False

        return auto_clients

    @classmethod
    def build_run_config(clf, plugin_config : dict):
        """
        Input : plugin_config : dict of plugin level configs 
        Output : return : dict of deployment config
        Helper function to build the run_config
        """

        # Plugin (Instance) level config
        run_pat_in_parallel = plugin_config.get("run_pat_in_parallel", None)
        nbr_parallel_runs = plugin_config.get("nbr_parallel_runs", None)
        logging_level = plugin_config.get("logging_level", "DEBUG")
        
        pat_backend_folder_full_id = plugin_config.get("pat_backend_folder_full_id", None)
        pat_backend_folder = dataiku.Folder(pat_backend_folder_full_id)
            
        use_llm_powered_checks = plugin_config.get("use_llm_powered_checks", False)
        llm_id = plugin_config.get("llm_id", None)
        
        return {
            "run_pat_in_parallel" : run_pat_in_parallel,
            "nbr_parallel_runs" : nbr_parallel_runs,
            "logging_level" : logging_level,
            "pat_backend_folder" : pat_backend_folder,
            "use_llm_powered_checks" : use_llm_powered_checks,
            "llm_id" : llm_id
        }
    