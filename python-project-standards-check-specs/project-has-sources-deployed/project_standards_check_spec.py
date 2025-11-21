import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)
import dataikuapi

from project_advisor.assessments.config_builder import DSSAssessmentConfigBuilder # Needed when using advanced PAT config
from project_advisor.pat_tools import md_print_list

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
    def _fetch_project_depencencies(self):
        
        # Load all project dependencies projects
        self.pat_backend_client.load_latest(["project_dependencies"])
        project_dependencies_df = self.pat_backend_client.get_table("project_dependencies")
        project_dependencies_df = project_dependencies_df[project_dependencies_df["target_project_key"] == self.original_project_key]
        imported_objects = []
        shared_objs = {}
        source_projects = set()
        for idx, shared_obj in project_dependencies_df.iterrows():
            source_projects.add(shared_obj["source_project_key"])
            imported_objects.append(f"{shared_obj['source_project_key']}:{shared_obj['type']}:{shared_obj['local_name']}")
            shared_objs.setdefault(shared_obj["source_project_key"], []).append({
                "type" : shared_obj["type"],
                "local_name" : shared_obj["local_name"]
            })
        
        return {
            "imported_objects" : imported_objects,
            "source_projects" : md_print_list(source_projects, "project", self.original_project_key),
            "source_projects_list" : source_projects,
            "shared_objs" : shared_objs
        }
    
    def _find_all_missing_deployments_from_pat_backend(self,source_projects):

        self.pat_backend_client.load_latest(["project_deployments"])
        project_deployments_df = pat_backend_client.get_table("project_deployments")

        # Load all deployments for the project
        target_project_deployments_df = project_deployments_df[project_deployments_df["active_bundle_source_project_key"] == self.original_project_key]
        project_infras = set(target_project_deployments_df["infra_id"])
        
        result["project_infras"] = list(project_infras)

        # Load all the relevant source project deployments.
        source_project_deployments_df = project_deployments_df[
            project_deployments_df["deployed_project_key"].isin(source_projects) & 
            project_deployments_df["infra_id"].isin(project_infras) & 
            ~project_deployments_df["neverEverDeployed"]
        ]

        # Find all of the missing deployments
        all_missing_projects = {}
        missing_projects_count = 0
        for infra_id in project_infras:
            infra_projs = source_project_deployments_df[source_project_deployments_df["infra_id"] == infra_id]
            missing_projects_on_infra = source_projects - set(infra_projs)
            if missing_projects_on_infra:
                missing_projects_count += 1
            all_missing_projects[infra_id] = list(missing_projects_on_infra)
        
        return {
            "project_infras" : list(project_infras),
            "all_missing_projects" : all_missing_projects
        }
    
    def _has_shared_object(self,project : dataikuapi.dss.project.DSSProject, shared_object_type : str, object_id : str):
        try:
            if shared_object_type == "DATASET":
                if not project.get_dataset(object_id).exists():
                    raise f"Dataset {object_id} doesn't exist in project {project.project_key}"
            elif shared_object_type == "SCENARIO":
                project.get_scenario(object_id).get_settings()
            elif shared_object_type == "MANAGED_FOLDER":
                project.get_managed_folder(object_id).get_settings()
            elif shared_object_type == "RETRIEVABLE_KNOWLEDGE":
                project.get_knowledge_bank(object_id).get_settings()
            elif shared_object_type == "WEB_APP":
                project.get_webapp(object_id).get_settings()
            elif shared_object_type == "JUPYTER_NOTEBOOK":
                project.get_jupyter_notebook(object_id).get_content()
            elif shared_object_type == "SAVED_MODEL":
                project.get_saved_model(object_id).get_settings()
            elif shared_object_type == "MODEL_EVALUATION_STORE":
                project.get_model_evaluation_store(object_id).get_settings()
            elif shared_object_type == "REPORT":
                pass # No API to check them
            return True
        except:
            return False
    
    def _find_all_missing_deployments(self, source_projects, shared_objs):
        
        deployer_client = self.pat_config.deployer_client
        infra_to_client = self.pat_config.infra_to_client
        project_deployer = deployer_client.get_projectdeployer()
        published_projects = project_deployer.list_projects(as_objects = False)
      
        # Find all the deployments of the target project's source projects
        all_deployed_source_projects = {}
        projects_to_update = {}
        target_infras = []
        sources_to_update_count = 0
        for pp in published_projects:
            pp_id = pp.get("projectBasicInfo",{}).get("id")
            p_deployments = pp.get("deployments")
            if pp_id == self.original_project_key: # Assuming that the pp_id is the same as the source
                for d in p_deployments:
                    target_infras.append(d["infraId"])

            if pp_id in source_projects: # If the project is source, check it's deployments

                for d in p_deployments: # Source project deployments

                    deployed_key = d["deployedProjectKey"] 

                    infra_id = d["infraId"]
                    if deployed_key == pp_id: # If not, then the source will not work

                        all_deployed_source_projects.setdefault(infra_id, []).append(deployed_key) # Add deployed proj on infra
                        # Check that all required objects are in the project
                        deployed_project = infra_to_client[infra_id].get_project(deployed_key)
                        for obj in shared_objs[deployed_key]:
                            if not self._has_shared_object(deployed_project, obj["type"], obj["local_name"]):
                                projects_to_update.setdefault(deployed_key, []).append(f"{obj['type']}:{obj['local_name']}")
                        if projects_to_update.get(deployed_key):
                            sources_to_update_count += 1


        missing_sources_count = 0
        all_missing_projects = {}
        for infra_id in target_infras:
            missing_projects = list(source_projects - set(all_deployed_source_projects.get(infra_id, [])))
            missing_sources_count += len(missing_projects)
            all_missing_projects[infra_id] = missing_projects
        
        return {
            "project_infras" : target_infras,
            "deployed_sources" : all_deployed_source_projects,
            "sources_to_update" : projects_to_update,
            "missing_sources" : all_missing_projects,
            "missing_sources_count" : missing_sources_count,
            "sources_to_update_count" : sources_to_update_count
        }
    
    def run(self):
        """
        Check that the project has all of it's source projects deployed.
        """

        self.pat_config = DSSAssessmentConfigBuilder.build_from_macro_config(self.config, self.plugin_config) # Use only for advanced usage

        details = {}
        
        # Check if the deployer client has been successful loaded, if not, notify that the check is not possible
        if self.pat_config.deployer_client == None:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = "PAT is not configured to run DEPLOYMENT checks",
                details = details
            )
        
        # Check if the infrastruture clients has been successful loaded, if not, notify that the check is not possible
        if any(infra_client is None for infra_id, infra_client in self.pat_config.infra_to_client.items()):
            return ProjectStandardsCheckRunResult.not_applicable(
                message = "PAT is not configured to run DEPLOYMENT checks",
                details = details
            )
        
        # Check if the PAT backend has been configured
        self.pat_backend_client = self.pat_config.pat_backend_client
        if self.pat_config.pat_backend_client is None:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = "PAT backend is not configured to run this check",
                details = details
            )
        
        # Load all project dependencies projects
        project_dependencies = self._fetch_project_depencencies()
        shared_objs = project_dependencies.pop("shared_objs")
        source_projects = project_dependencies.pop("source_projects_list")
        details.update(project_dependencies)
        
        # Find all missing deployments
        #project_deployments = self._find_all_missing_deployments_from_pat_backend(source_projects) # In case needed in the future
        project_deployments = self._find_all_missing_deployments(source_projects, shared_objs)
        details.update(project_deployments)
        
        bad_sources = project_deployments["missing_sources_count"] + project_deployments["sources_to_update_count"]
       
        if bad_sources> 0:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = f"There are {bad_sources} source project(s) that need to be reviewed before being able to deploy this project.",
                    details = details
                )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = "All the required source projects for this project are deployed on the relevant infrastructures",
                details = details
            )

