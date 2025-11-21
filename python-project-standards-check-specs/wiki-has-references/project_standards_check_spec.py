import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from dataikuapi.dss.flow import DSSProjectFlowGraph
from dataikuapi.dss.project import DSSProject

from project_advisor.pat_tools import md_print_list, dss_obj_to_dss_obj_md_link

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
    def get_output_dataset_ids(self, graph: DSSProjectFlowGraph) -> list:
        """
        Retrieves the IDs of output datasets in the project's flow.
        """
        nodes = graph.nodes
        output_dataset_ids = []

        for node_id in nodes.keys():
            if (
                "DATASET" in nodes[node_id]["type"]
                and len(nodes[node_id]["successors"]) == 0
            ):
                output_dataset_ids.append(nodes[node_id]["ref"])

        return output_dataset_ids
    
    def get_published_dataset_ids(self, project: DSSProject) -> list:
        """
        Retrieves the IDs of published datasets in the project's flow.
        """
        return [d["name"] for d in project.list_datasets() if d["featureGroup"]]
    
    def has_reference_in_wiki(self, lookup_list : list, wiki : str):
        """
        Find any of the stings in the loop in the wiki
        """
        for lookup in lookup_list:
            if lookup in wiki:
                return True
        return False
    
    def find_missing_references(self,dss_obj_list :list, wiki : str):
        missing_references = []
        for dss_obj in dss_obj_list:
            if not self.has_reference_in_wiki([dss_obj["id"],dss_obj["name"]], wiki):
                missing_references.append(dss_obj)
        return [mr["md_link"] for mr in missing_references]
        
        
    
    def run(self):
        """
        Runs the check to determine if the project's wiki has references to certain DSS objects.
        """

        details = {}
        
        list_to_check = self.config.get("dss_objects_to_check")

        graph = self.project.get_flow().get_graph()
        
        concatenated_wiki = " ".join(
            [a.get_data().get_body() for a in self.project.get_wiki().list_articles() if isinstance(a.get_data().get_body(), str)] # Capture edge case of empty article.
        )
        
        dss_objects_to_check = []
        missing_references = {}
        
        if "scenario" in list_to_check:
            scenarios = []
            for s in self.project.list_scenarios():
                scenarios.append({
                    "id": s["id"], 
                    "name": s["name"], 
                    "type": "scenario",
                    "md_link" : dss_obj_to_dss_obj_md_link("scenario", self.original_project_key,s["id"], s["name"])
                })
            
            dss_objects_to_check.extend(scenarios)
            missing_references["missing_scenario"] = self.find_missing_references(scenarios, concatenated_wiki)
                
            
        if "saved_model" in list_to_check:
            saved_models = []
            for m in self.project.list_saved_models():
                saved_models.append({
                    "id": m["id"], 
                    "name": m["name"], 
                    "type": "saved_model",
                    "md_link" : dss_obj_to_dss_obj_md_link("saved_model", self.original_project_key,m["id"], m["name"])
                })
            dss_objects_to_check.extend(saved_models)
            missing_references["missing_saved_models"] = self.find_missing_references(saved_models, concatenated_wiki)

        if "webapp" in list_to_check:
            webapps = []
            for w in self.project.list_webapps():
                webapps.append({
                    "id": w["id"], 
                    "name": w["name"], 
                    "type": "web_app",
                    "md_link" : dss_obj_to_dss_obj_md_link("webapp", self.original_project_key,w["id"], w["name"])
                })
            dss_objects_to_check.extend(webapps)
            missing_references["missing_webapps"] = self.find_missing_references(webapps, concatenated_wiki)


        if "dashboard" in list_to_check:
            dashboards = []
            for d in self.project.list_dashboards():
                dashboards.append({
                    "id": d["id"], 
                    "name": d["name"], 
                    "type": "dashboard",
                    "md_link" : dss_obj_to_dss_obj_md_link("dashboard", self.original_project_key,d["id"], d["name"])
                })
            dss_objects_to_check.extend(dashboards)
            missing_references["missing_dashboards"] = self.find_missing_references(dashboards, concatenated_wiki)


        if "flow_zone" in list_to_check:
            flow_zones = []
            for f in self.project.get_flow().list_zones():
                flow_zones.append({
                    "id": f.id, 
                    "name": f.name, 
                    "type": "flow_zone",
                    "md_link" : dss_obj_to_dss_obj_md_link("flow_zone", self.original_project_key,f.id, f.name)
                })
            dss_objects_to_check.extend(flow_zones)
            missing_references["missing_flow_zones"] = self.find_missing_references(flow_zones, concatenated_wiki) 


        if "source_dataset" in list_to_check:
            source_datasets = []
            for sd in self.project.get_flow().get_graph().get_source_datasets():
                source_datasets.append({
                    "id": sd.id, 
                    "name": sd.name, 
                    "type": "source_dataset",
                    "md_link" : dss_obj_to_dss_obj_md_link("dataset", self.original_project_key,sd.id, sd.name)
                })
            dss_objects_to_check.extend(source_datasets)
            missing_references["missing_source_datasets"] = self.find_missing_references(source_datasets, concatenated_wiki)


        if "shared_datasets" in list_to_check:
            shared_datasets = []
            for pd in self.project.list_datasets(as_type="object"):
                if pd.get_settings().is_feature_group:
                    shared_datasets.append({
                        "id": pd.id,
                        "name": pd.name,
                        "type": "published_dataset",
                        "md_link" : dss_obj_to_dss_obj_md_link("dataset", self.original_project_key,pd.id, pd.name)
                    })
            dss_objects_to_check.extend(shared_datasets)
            missing_references["missing_shared_datasets"] = self.find_missing_references(shared_datasets, concatenated_wiki)


        if "output_dataset" in list_to_check:
            output_datasets = []
            for od_id in self.get_output_dataset_ids(graph):
                name = self.project.get_dataset(od_id).name
                output_datasets.append(
                    {
                        "id": od_id,
                        "name": name,
                        "type": "output_dataset",
                        "md_link" : dss_obj_to_dss_obj_md_link("dataset", self.original_project_key,od_id, name)
                    }
                )
            dss_objects_to_check.extend(output_datasets)
            missing_references["missing_output_datasets"] = self.find_missing_references(output_datasets, concatenated_wiki)

        
        nbr_dss_objects_not_referenced = 0
        for key in missing_references.keys():
            nbr_dss_objects_not_referenced+= len(missing_references[key])
            
        
        if dss_objects_to_check:
            coverage = 100 - (nbr_dss_objects_not_referenced/len(dss_objects_to_check))*100
        else:
            coverage = 100
        
        details.update(missing_references)
        details["coverage"] = coverage
        
        target_coverage = self.config.get("coverage")
        if coverage >= target_coverage:
            return ProjectStandardsCheckRunResult.success(
                message = f"The project has references to {int(coverage)}% of checked DSS objects",
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = f"This Project's wiki is missing {nbr_dss_objects_not_referenced} reference(s) to important objects in your project. See details",
                    details = details
                )

       
        target_coverage = self.config.get("coverage")
        if coverage >=target_coverage:
            return ProjectStandardsCheckRunResult.success(
                message = f"The project has a {int(coverage)}% data quality coverage rule coverage for {', '.join(datasets_to_consider)} datasets.",
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = f"The project has a data quality coverage of {int(coverage)}% which is under the target of coverage of{int(target_coverage)}%. \nAdd Data quality rules to : {md_print_list(no_rules_dataset_ids,'dataset',self.original_project_key)}",
                    details = details
                )

