import dataiku
from typing import List, Union
import logging
import dataikuapi
from datetime import datetime
import io
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

from project_advisor.pat_logging import logger

class PATBackendClient():
    """
    Client to Manage the building, saving and loading of PAT precomputation data over time.
    """

    # Precomputed data
    data = {
        "project_dependencies" : None,
        "project_deployments": None,
        "plugins_usage" : None,
        "project_to_folder_path": None,
        "projects": None,
        "users" : None,
        "user_to_project_mapping": None,
        "scenarios" : None
    }

    backend_folder : dataiku.Folder = None
    
    def __init__(self, dss_client :dataikuapi.dssclient.DSSClient , 
                 run_config : dict, 
                 deployer_client : dataikuapi.dssclient.DSSClient = None,
                 infra_to_client : dict = None):
        
        self.client = dss_client
        self.data_tables : List[str] = list(self.data.keys()) # Consider all the data
        self.run_config : dict = run_config
        self.deployer_client : dict = deployer_client
        self.infra_to_client : dict = infra_to_client
        self.backend_folder : dataiku.Folder = run_config.get("pat_backend_folder")
    
    def process_data_tables(self, data_tables : Union[list, str]) -> List[str]:
        if data_tables == "ALL":
            return list(self.data.keys())
        if isinstance(data_tables, str):
            return [data_tables]
        if isinstance(data_tables, List):
            return data_tables
        return []
    
    def get_table(self, name : str) -> pd.DataFrame:
        """
        Return data table
        """
        return self.data.get(name)
    
    def build(self, data_tables : Union[list, str] = "ALL"):
        """
        Build all of the tables in data_tables
        """
        data_tables = self.process_data_tables(data_tables)
        logger.info(f"Building the following PAT backend tables : {data_tables}")   
        build_methods = {
            "project_dependencies": self.build_project_dependencies,
            "project_deployments": self.build_project_deployments,
            "plugins_usage": self.build_plugins_usage,
            "project_to_folder_path": self.build_project_to_folder_path,
            "projects": self.build_projects,
            "users": self.build_users,
            "user_to_project_mapping": self.build_user_to_project_mapping,
            "scenarios": self.build_scenarios,
        }

        for table in data_tables:
            build_fn = build_methods.get(table)
            if build_fn:
                logger.info(f"Building PAT Backend Table : {table}")
                try:
                    build_fn()
                except Exception as error:
                    logger.warning(f"Failed to build PAT Backend Table : {table} with error : {type(error).__name__}:{str(error)}")
            else:
                logger.warning(f"Table {table} does not exist. Please provide a table name that exists")
                
    
    def save(self, dt = datetime.now(), data_tables : Union[list, str] = "ALL"):
        """
        Save all of the tables in data_tables
        """
        data_tables = self.process_data_tables(data_tables)  
        logger.info(f"Saving the following PAT backend tables : {data_tables}")
            
        dt_str = dt.isoformat().split(".")[0]
        for table in data_tables:
            df = self.data.get(table)
            if df is not None:
                logger.info(f"Saving Table : {table}")
                self.write_dataframe_to_folder(table,dt_str, df)
            else:
                logger.warning(f"Table {table} was not built properly. It cannot be saved")
    
    def load_latest(self, data_tables : Union[list, str] = "ALL"):
        """
        Load all off the tables in data_tables
        """
        data_tables = self.process_data_tables(data_tables)
        logger.info(f"Loading the following PAT backend tables : {data_tables}")
        
        all_files = {}
        for full_path in self.backend_folder.list_paths_in_partition():
            path, file = os.path.split(full_path)
            all_files.setdefault(path[1:], []).append(file)
        
        latest_files = {}
        for topic in all_files.keys():
            latest_files[topic] =  max(all_files[topic])
        
        for table in data_tables:
            latest_file = latest_files.get(table)
            if latest_file:
                logger.info(f"Loading the latest version of table : {table} with file name {latest_file}")
                self.data[table] = self.read_dataframe_from_folder(table,latest_file)
            else:
                logger.warning(f"There is no data to load for table : {table}")
                
            
    ###########################
    # Saving Helper Functions #
    ###########################
    
    def write_dataframe_to_folder(self, path_in_folder: str, filename: str, df : pd.DataFrame):
        """
        Writes a pandas DataFrame to a Dataiku folder as a CSV using the stream method.

        Parameters:
        - folder: dataiku.Folder object where the file will be written
        - path_in_folder: Path inside the folder (can be empty string for root)
        - filename: Name of the CSV file to create
        - df: pandas DataFrame to write
        """
        # Construct full path in folder
        filename = filename +".csv"
        full_path = f"{path_in_folder}/{filename}" if path_in_folder else filename

        # Write DataFrame to a CSV string
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)

        with self.backend_folder.get_writer(full_path) as stream:
            stream.write(buffer.getvalue().encode("utf-8"))
    
    def read_dataframe_from_folder(self, path_in_folder: str, filename: str) -> pd.DataFrame:
        """
        Reads a CSV file from a Dataiku folder using the stream method and returns a pandas DataFrame.

        Parameters:
        - folder: dataiku.Folder object to read from
        - path_in_folder: Path inside the folder (can be empty string for root)
        - filename: Name of the CSV file to read

        Returns:
        - A pandas DataFrame containing the CSV contents
        """
        # Construct full path in folder
        full_path = f"{path_in_folder}/{filename}" if path_in_folder else filename

        # Read the file stream and load into DataFrame
        with self.backend_folder.get_download_stream(full_path) as stream:
            return pd.read_csv(stream)

    ##################################
    # Precompuation Helper Functions #
    ##################################
    
    def safe_get_attr(self, py_object, attr_name, default_value):
        """safer version of getattr"""
        try:
            return getattr(py_object, attr_name, default_value)
        except:
            return default_value
    
    ##########################
    # Precomputation Methods #
    ##########################
    
    def build_project_dependencies(self):
        """
        project_dependencies : Dict[str, set] = {} # ProjectKey to list of projects it is dependent on (that share an object with it)
        """
        try: 
            shared_objects = []
            project_keys = self.client.list_project_keys()

            for source_project_key in project_keys:
                project = self.client.get_project(source_project_key)
                exposed_objects = project.get_settings().get_raw()["exposedObjects"]["objects"]
                for exposed_object in exposed_objects:
                    for rule in exposed_object["rules"]:
                        shared_objects.append({
                            "source_project_key" : source_project_key,
                            "target_project_key" : rule.get("targetProject"),
                            "appearOnFlow" : rule.get("appearOnFlow"),
                            "type" : exposed_object.get("type"),
                            "local_name" : exposed_object.get("localName"),
                            "quick_sharing_enabled" : exposed_object.get("quickSharingEnabled"),
                        })
            self.data["project_dependencies"] = pd.DataFrame.from_dict(shared_objects)
        except Exception as e:
            logger.warning(f"Project inter-dependencies computation failed with error : {e}")
            self.data["project_dependencies"] = None
        return
    
    def build_project_deployments(self):
        """
        build_project_deployments
        """
        logger.info("Running computation of project deployment mapping")
        deployment_project_mapping = []
        try:
            deployments = self.deployer_client.get_projectdeployer().list_deployments()
            for deployment in deployments:
                deployment_info = deployment.get_status().get_light()

                # Build extra deployment insights
                active_bundle_id = deployment_info["deploymentBasicInfo"]["bundleId"]
                active_bundle_info = next((b for b in deployment_info["packages"] if b["id"] == active_bundle_id), {})
                bundles_have_same_source = len(set(b["designNodeInfo"]["installId"] for b in deployment_info["packages"]))==1

                deployment_info.update({
                    "deployment_id" : deployment_info["deploymentBasicInfo"]["id"],
                    "active_bundle_id" : active_bundle_id,
                    "infra_id" :  deployment_info["infraBasicInfo"]["id"],
                    "bundles_have_same_source" : bundles_have_same_source,
                    "active_bundle_source_project_key" : active_bundle_info.get("designNodeInfo",{}).get("projectKey"),
                    "published_project_key" : deployment_info["projectBasicInfo"]["id"],
                    "deployed_project_key" :deployment_info["deploymentBasicInfo"]["deployedProjectKey"]
                })
                deployment_project_mapping.append(deployment_info)

            self.data["project_deployments"] = pd.DataFrame.from_dict(deployment_project_mapping)
            logger.debug(self.data["project_deployments"])
        except Exception as e:
            logger.info(f"compute_deployments_projects_mapping failed with error : {e}")
            self.data["project_deployments"] = None
        return 

    def build_plugins_usage(self):
        """
        Returns the usage of plugins for all projects.
        Dict[str, set] = {} # ProjectId to PluginID Mapping
        """
        logger.info("Running plugin usage computation")
        def plugin_usage_run(plugin_dict : dict):
            plugin_id = plugin_dict["id"]
            try:
                plugin_usages = self.client.get_plugin(plugin_id).list_usages()
                return (plugin_id, plugin_usages)
            except Exception as error:
                logger.warning(f"Plugin dependency calculation for plugin {plugin_id} failed with error : {type(error).__name__}:{str(error)}")
                return (plugin_id, None)

        try: 
            if self.run_config.get("run_pat_in_parallel", False):  
                n_jobs = self.run_config.get("nbr_parallel_runs",1)
                logger.info(f"Running {n_jobs} Plugin usage in parallel at a time")

                with ThreadPoolExecutor(max_workers = n_jobs) as executor:
                    all_plugin_usage = list(executor.map(plugin_usage_run, self.client.list_plugins())) 
            else:
                logger.info(f"Running Plugin usage one at a time")
                all_plugin_usage = []
                for plugin_dict in self.client.list_plugins():
                    plugin_usage_run_result = plugin_usage_run(plugin_dict)
                    all_plugin_usage.append(plugin_usage_run_result)

            project_plugin_usage = []
            for plugin_id, plugin_usages in all_plugin_usage:
                if plugin_usages is not None:
                    for usage in plugin_usages.usages:
                        # Attempt to access a attributes that might not exist
                        project_plugin_usage.append({
                            "object_id" : self.safe_get_attr(usage, "object_id", "NONE"),
                            "object_type" : self.safe_get_attr(usage, "object_type", "NONE"),
                            "element_type" : self.safe_get_attr(usage, "element_type", "NONE"),
                            "element_kind" : self.safe_get_attr(usage, "element_kind", "NONE"),
                            "project_key" : self.safe_get_attr(usage, "project_key", "NONE"),
                            "plugin_id" : plugin_id
                        })

            self.data["plugins_usage"] = pd.DataFrame.from_dict(project_plugin_usage)
        except Exception as error:
            logger.warning(f"The plugins usage table failed with error : {type(error).__name__}:{str(error)}")
            self.data["plugins_usage"] = None 

    def build_project_to_folder_path(self):
        """
        project_to_folder_path : Dict[str, str] = None # Project to Folder Path Mapping
        """
        project_to_folder_path = []
        def set_project_to_folder_path(folder : dataikuapi.dss.projectfolder.DSSProjectFolder):
            path = folder.get_path()
            for f in folder.list_child_folders():
                set_project_to_folder_path(f)
            for p in folder.list_project_keys():
                project_to_folder_path.append({
                    "project_key" : p,
                    "path" : path
                })
        root = self.client.get_root_project_folder()
        set_project_to_folder_path(root)
        self.data["project_to_folder_path"] = pd.DataFrame.from_dict(project_to_folder_path)

    def build_projects(self):
        """
        List all of the projects on the instance with their metadata
        """
        projects = self.client.list_projects()
        projects_df = pd.DataFrame.from_dict(projects)
        self.data["projects"] = projects_df
    
    def build_users(self):
        """
        List all of the users on the instance with their metadata
        """
        users = self.client.list_users(as_objects = True)
        users_data = []
        for user in users:
            user_dict = {}
            user_dict.update(user.get_info().get_raw())
            user_dict.update(user.get_activity().get_raw())
            users_data.append(user_dict)
        users_df = pd.DataFrame.from_dict(users_data)
        self.data["users"] = users_df
        

    def build_groups(self):
        """
        List all of the users on the instance with their metadata
        """
        groups = self.client.list_groups()
        groups_df = pd.DataFrame.from_dict(groups)
        self.data["groups"] = groups_df
    
    def build_user_to_project_mapping(self):
        """
        List all of the users to project relationships on the instance
        """
        client = self.client
        users = client.list_users()
        groups = client.list_groups()
        projects = client.list_projects()

        # Enrich projects
        for p in projects:
            project_key = p["projectKey"]
            project = self.client.get_project(project_key)
            p.update({"permissions": project.get_permissions()["permissions"]})

        user_to_project_mapping = []
        for user in users:
            user_login = user["login"]
            user_groups = user["groups"]

            for p in projects:
                project_key = p["projectKey"]
                project_owner = p["ownerLogin"]

                is_project_owner = False
                is_shared_by_user = False
                is_shared_by_group = False
                if user_login == project_owner:
                    is_project_owner = True
                else:
                    for permission in p["permissions"]:
                        # If permission at least write
                        if any([permission['admin'],
                               permission['writeProjectContent']]):

                            if permission.get("user") == user_login:
                                is_shared_by_user = True

                            if permission.get("group") in user_groups:
                                is_shared_by_group = True

                if any([is_project_owner,is_shared_by_user, is_shared_by_group]):
                    user_to_project_mapping.append({
                        "user_login" : user_login,
                        "project_key" : project_key,
                        "is_project_owner" : is_project_owner,
                        "is_shared_by_user" : is_shared_by_user,
                        "is_shared_by_group" : is_shared_by_group
                    })
        # Write recipe outputs
        user_to_project_df = pd.DataFrame.from_dict(user_to_project_mapping)
        self.data["user_to_project_mapping"] = user_to_project_df
        
    def build_scenarios(self):
        """
        List all the scenarios throughout the whole instance.
        """
        scenarios = []
        for p_key in self.client.list_project_keys():
            try:
                p = self.client.get_project(p_key)
                for s in p.list_scenarios(as_type = "objects"):
                    s_data = s.get_settings().data
                    s_data.update({"last_runs" : [run.get_info() for run in s.get_last_runs()]})
                    scenarios.append(s_data)
            except Exception as error:
                self.checks = []
                logger.warning(f"Failed to fetch scenarios for project {p_key} with error : {type(error).__name__}:{str(error)}")
        
        scenarios_df = pd.DataFrame.from_dict(scenarios)
        self.data["scenarios"] = scenarios_df