import socket
from abc import ABC
from typing import Dict, List

import dataikuapi
from project_advisor.pat_backend import PATBackendClient
from project_advisor.pat_logging import logger


# File to contain the DSSAssessment class implementation.
class DSSAssessmentConfig(ABC):
    """
    Class for the configuration of DSS Assessments - the core components of PAT.
    It contains:
    - Filters for all Assessments (checks and metrics)
    - Project & Instance Assessment Configurations Ex: Check thresholds.
    - Deployment Configurations
    - Precomputed reusable mappings
    """
    
    config: dict = {}
    design_client : dataikuapi.dssclient.DSSClient = None
    admin_design_client : dataikuapi.dssclient.DSSClient = None
    
    # Deployment configs
    deployer_client : dataikuapi.dssclient.DSSClient = None
    infra_to_clients : Dict[str, List[dataikuapi.dssclient.DSSClient]] = {}
    deployment_method : str = None # fm_managed or manual
    deployment_mode : str = None # local or remote
    
    # Precomputed mappings
    pat_backend_client : PATBackendClient = None

    @property
    def infra_to_client(self) -> Dict[str, dataikuapi.dssclient.DSSClient]:
        """
        Returns a mapping between infrastructure IDs and a single associated DSSClient.
        If multiple automation nodes are associated with an infrastructure, only the first one is returned.

        :return: the mapping
        :rtype: Dict[str, dataikuapi.dssclient.DSSClient]
        """
        return {infra_id: clients[0] for infra_id, clients in self.infra_to_clients.items() if len(clients) > 0}

    def __init__(self, config: dict, logging_level : str = "WARNING"):
        """
        Initializes the DSSAssessmentConfig with the provided configuration dictionary.
        """
        logger.info("Init of DSSAssessmentConfig")
        
        self.config = config
        self.design_client = self.config.get("design_client", None)
        self.admin_design_client = self.config.get("admin_design_client", None)
        check_filters = self.config.get("check_filters", {})
        
        logger.info("Running DEPLOYMENT related computations")
        
        # Set deployer_client & infra_to_clients attributs
        self.set_deployement_method_and_mode()
        if self.deployment_method != None:
            self.set_deployer_client()
            self.set_infra_to_clients_mapping()
            logger.info("deployer_client and infra_to_clients mapping have been created & set")
        else:
            logger.info("deployment_method is set to None - skipping connection to deployement infra")

        # Set PAT backend client
        self.set_pat_backend_client()

    def get_config(self) -> dict:
        return self.config
    
    def set_pat_backend_client(self):

        self.pat_backend_client = PATBackendClient(
            dss_client = self.admin_design_client,
            run_config = self.config.get("run_config"),
            deployer_client = self.deployer_client,
            infra_to_client = self.infra_to_client
        )
        
    ###############################
    # Deployment Helper functions #
    ###############################
    
    def _get_vn_id(self, fm_client :dataikuapi.fmclient.FMClient) -> str:
        """
        Return Virtual Network of current design node
        """
        logger.debug("Get the Virtual Network Id")
        design_private_ip = socket.gethostbyname(socket.gethostname()) # Requires to be on the Design Node to work.
        for instance in fm_client.list_instances():
            if design_private_ip == instance.get_status().get("privateIP", None):
                return instance.instance_data.get("virtualNetworkId", None)
        return None
    
    
    def _get_fm_deployment_config(self, fm_client :dataikuapi.fmclient.FMClient):
        """
        Return FM deployement configuration settings
        """
        logger.debug("Get the FM deployment configuration settings")
        vn_id = self._get_vn_id(fm_client)
        vn_data = fm_client.get_virtual_network(vn_id).vn_data 
        managedNodesDirectory = vn_data.get("managedNodesDirectory", False)
        nodesDirectoryDeployerMode = vn_data.get("nodesDirectoryDeployerMode",None)
        return (managedNodesDirectory, nodesDirectoryDeployerMode)
    
    def _get_current_instance_deployment_mode(self) -> str:
        """
        Fetch the deployment_mode for manually connected Nodes (deployment_method : manual)
        """
        logger.debug("Get the deployment mode for manually connected nodes")
        mode = self.admin_design_client.get_general_settings().settings.get("deployerClientSettings", {}).get("mode", None)
        if mode == "LOCAL":
            return "local"
        elif mode == "REMOTE":
            return "remote"
        else:
            return mode

    
    def _get_available_instance_clients_in_vn(self, fm_client :dataikuapi.fmclient.FMClient) -> List[dataikuapi.dssclient.DSSClient]:
        """
        List all of the client for all available (Running) instances managed by the FM in the current Virtual Network.
        """
        logger.debug("List all instance clients in Virtual Network")
        instances = fm_client.list_instances()
        vn_id = self._get_vn_id(fm_client)
        instance_clients = []
        for instance in instances:
            if instance.get_status()["cloudMachineIsUp"]== True and instance.instance_data.get("virtualNetworkId") == vn_id:
                client = instance.get_client()
                if not self.config.get("deployment_config",{}).get("verify_ssl_certificate",True):
                    client._session.verify = False
                instance_clients.append(client)
        return instance_clients   
    
    ### Fetch and set the Node Deployment Configuration ###
    
    def set_deployement_method_and_mode(self):
        """
        Set the deployment_method and deployement_mode attributes based on deployment_config. 
        """
        logger.info("Set deployment method and mode")
        
        deployment_method = self.config.get("deployment_config", {}).get("deployment_method", None)
        fm_client = self.config.get("deployment_config", {}).get("fm_client", None)
        
        if deployment_method in ["fm-aws", "fm-gcp", "fm-azure"]:
            managedNodesDirectory, nodesDirectoryDeployerMode = self._get_fm_deployment_config(fm_client)
            if managedNodesDirectory:
                if nodesDirectoryDeployerMode == "CENTRAL_DEPLOYER":
                    self.deployment_method = "fm_managed"
                    self.deployment_mode = "remote"

                elif nodesDirectoryDeployerMode == "NO_MANAGED_DEPLOYER":
                    self.deployment_method = "manual"  # Doesn't require the FM.
                    self.deployment_mode = self._get_current_instance_deployment_mode()

                elif nodesDirectoryDeployerMode == "EACH_DESIGN_NODE":
                    self.deployment_method = "fm_managed"
                    self.deployment_mode = "local"
            else:
                self.deployment_method = "fm_managed"
                self.deployment_mode = self._get_current_instance_deployment_mode()
        
        elif deployment_method == "manual":
            self.deployment_method = "manual"
            self.deployment_mode = self._get_current_instance_deployment_mode()
        
        else:
            logger.info(f"The deployment method {deployment_method} is not supported OR disabled")
        
        logger.debug(f"self.deployment_method : {self.deployment_method}")
        logger.debug(f"self.deployment_mode : {self.deployment_mode}")
        
        return
    
    
    ### Setting the deployer client methods ###

    def set_deployer_client(self) -> None:
        """
        Sets the *deployer_client* attribute based on the deployment configurations.
        """
        logger.info("Set deployment method and mode")
        fm_client = self.config.get("deployment_config", {}).get("fm_client", None)
        external_deployer_client = self.config.get("deployment_config", {}).get("external_deployer_client", None)

        if self.deployment_method == "fm_managed":
            if self.deployment_mode == "local":
                self.deployer_client = self.admin_design_client
            elif self.deployment_mode == "remote":
                self.deployer_client = self.get_fm_remote_deployer_client(fm_client)  
            else:
                logger.info(f"The deployment mode {self.deployment_mode} is not supported")
        
        elif self.deployment_method == "manual":
            if external_deployer_client:
                self.deployer_client = external_deployer_client
            elif self.deployment_mode == "local":
                self.deployer_client = self.admin_design_client
            elif self.deployment_mode == "remote":
                # "remote" + no external_deployer_client -> impossible to get the deployer client
                raise Exception(
                    "Current instance is using a remote deployer. You need to enter the deployer details in the plugin settings."
                )
            else:
                logger.info(f"The deployment mode {self.deployment_mode} is not supported")

        else:
            logger.info(f"The deployment method {self.deployment_method} is not supported")
        return


    def get_fm_remote_deployer_client(self, fm_client :dataikuapi.fmclient.FMClient) -> dataikuapi.dssclient.DSSClient:
        """
        Return the deployer from a cloud stacks deployment given a Fleet Manager Client. (Assuming there is only one Deployer Node)
        """
        logger.info(f"Fetching deployer client for Cloud Stacks remote deployment")
        instance_clients = self._get_available_instance_clients_in_vn(fm_client)

        deployer_client = None
        for client in instance_clients:
            if client.get_instance_info().raw["nodeType"] == "DEPLOYER":
                deployer_client = client
        return deployer_client
    
    
    ### Setting the infra to client mapping functions ###
    
    def set_infra_to_clients_mapping(self) -> None:
        """
        Sets the *infra_to_clients* attribut regardless of the deployment method.
        """
        logger.info(f"Setting infra to client mapping")
        fm_client = self.config.get("deployment_config")["fm_client"]    
        
        if self.deployer_client == None:
            logger.warning("No deployer_client, please set the deployer_client before building the infra_to_clients mapping")
            return

        if self.deployment_method == "fm_managed":
            self.infra_to_clients = self.get_fm_infra_to_clients_mapping(fm_client)
        elif self.deployment_method == "manual":
            self.infra_to_clients = self.config.get("deployment_config", {}).get("automation_nodes", {})
        else:
            logger.warning(f"The deployment method {self.deployment_method} is not supported")
        return

    def get_fm_infra_to_clients_mapping(
        self, fm_client: dataikuapi.dssclient.DSSClient
    ) -> Dict[str, List[dataikuapi.dssclient.DSSClient]]:
        """
        Returns a mapping between all infras on the deployer and their associated Client for Cloud Stacks deployments.
        """
        logger.info(f"Building infra to clients for Cloud Stacks managed infrastructure")
        instance_clients = self._get_available_instance_clients_in_vn(fm_client)
        proj_deployer = self.deployer_client.get_projectdeployer()

        infra_to_clients = {}
        for infra in proj_deployer.list_infras():
            infra_settings = infra.get_settings().settings
            infra_type = infra_settings.get("type", "AUTOMATION_NODE")
            if infra_type == "MULTI_AUTOMATION_NODE":
                automation_nodes = [node["nodeId"] for node in infra_settings["automationNodes"]]
            else:  # SINGLE AUTOMATION NODE
                node_id = infra_settings["nodeId"]
                automation_nodes = [node_id]

            clients = []
            for client in instance_clients:
                instance_info = client.get_instance_info().raw
                if instance_info["nodeType"] == "AUTOMATION" and instance_info["nodeId"] in automation_nodes:
                    clients.append(client)

            infra_id = infra_settings["id"]
            infra_to_clients[infra_id] = clients

        return infra_to_clients

    ##########################
    # Precomputation Methods #
    ##########################
    #def compute_project_dependencies(self) -> None:
    #    """
    #    Update the configuration with the project dependencies.
    #    """
    #    logger.info("Running computation of project inter-dependencies")
    #    try: 
    #        shared_objects = {}
    #        project_keys = self.admin_design_client.list_project_keys()

    #        for sharing_project_key in project_keys:
    #            project = self.admin_design_client.get_project(sharing_project_key)
    #            exposed_objects = project.get_settings().get_raw()["exposedObjects"]["objects"]
    #            for exposed_object in exposed_objects:
    #                for rule in exposed_object["rules"]:
    #                    target_project = rule["targetProject"]
    #                    if target_project not in shared_objects:
    #                        shared_objects[target_project] = set()
    #                    shared_objects[target_project].add(sharing_project_key)

    #        self.project_dependencies = shared_objects
    #    except Exception as e:
    #        logger.warning(f"Project inter-dependencies computation failed with error : {e}")
    #        self.project_dependencies = None
    #    return

    #def compute_plugins_usage(self) -> None:
    #    """
    #    Returns the usage of plugins for all projects.
    #    """
    #    logger.info("Running plugin usage computation")
    #    
    #    try: 
    #        if self.config.get("run_config",{}).get("run_pat_in_parallel", False):  
    #            n_jobs = self.config.get("run_config",{}).get("nbr_parallel_runs",1)
    #            logger.info(f"Running {n_jobs} Plugin usage in parallel at a time")
    #            def parallel_run(plugin_dict : dict):
    #                plugin_id = plugin_dict["id"]
    #                plugin_usages = self.admin_design_client.get_plugin(plugin_id).list_usages()
    #                return (plugin_id, plugin_usages)

    #            with ThreadPoolExecutor(max_workers = n_jobs) as executor:
    #                all_plugin_usage = list(executor.map(parallel_run, self.admin_design_client.list_plugins())) 
    #        else:
    #            logger.info(f"Running Plugin usage one at a time")
    #            all_plugin_usage = []
    #            for plugin_dict in self.admin_design_client.list_plugins():
    #                plugin_id = plugin_dict["id"]
    #                plugin_usages = self.admin_design_client.get_plugin(plugin_id).list_usages()
    #                all_plugin_usage.append((plugin_id, plugin_usages))
    #            
    #        project_plugin_usage = dict()
    #        for plugin_id, plugin_usages in all_plugin_usage:
    #            for usage in plugin_usages.usages:
    #                # Attempt to access a key that might not exist
    #                try:
    #                    project_key = usage.project_key
    #                except KeyError:
    #                    project_key = "NONE"
    #                project_plugin_usage.setdefault(project_key, set()).add(plugin_id)

    #        self.plugins_usage = project_plugin_usage
    #    except Exception as e:
    #        logger.warning(f"Plugin dependency calculation failed with error : {e}")
    #        self.plugins_usage = None
    #    return 
    
    #def compute_deployments_projects_mapping(self) -> None:
    #    """
    #    Returns the mapping between design and deployment project keys.
    #    """
    #    logger.info("Running computation of project deployment mapping")
    #    deployment_project_mapping = dict()
    #    try:
    #        deployments = self.deployer_client.get_projectdeployer().list_deployments()
    #        for deployment in deployments:
    #            deployments_info = deployment.get_status().get_light()
    #            design_project_key = deployments_info["packages"][-1]["designNodeInfo"]["projectKey"]
    #            deployed_project_key = deployments_info["deploymentBasicInfo"]["deployedProjectKey"]
    #            deployment_project_mapping.setdefault(design_project_key, list()).append(deployed_project_key)
    #
    #        self.deployment_project_mapping = deployment_project_mapping
    #    except Exception as e:
    #        logger.info(f"compute_deployments_projects_mapping failed with error : {e}")
    #        self.deployment_project_mapping = None
    #    return 
    
    #def compute_project_to_folder_path_mapping(self) -> None:
    #    """
    #    Pre compute a project to project_folder_path Mapping (To avoid looking expensive computation for all projects)
    #    """
    #    self.project_to_folder_path = {}
    #    def set_project_to_folder_path(folder : dataikuapi.dss.projectfolder.DSSProjectFolder):
    #        path = folder.get_path()
    #        for f in folder.list_child_folders():
    #            set_project_to_folder_path(f)
    #        for p in folder.list_project_keys():
    #            self.project_to_folder_path[p] = path
    #
    #    root = self.admin_design_client.get_root_project_folder()
    #    set_project_to_folder_path(root)
    #    return

        

                             