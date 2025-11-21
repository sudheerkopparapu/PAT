from typing import Any, Dict, List, Tuple

from project_advisor.assessments.config_builder import DSSAssessmentConfigBuilder


def do(payload, config, plugin_config, inputs):
    
    parameter_name = payload["parameterName"]
    
    design_client = DSSAssessmentConfigBuilder.build_admin_design_client(plugin_config)
    local_client = design_client # Update this if running PAT on the automation node so a connection on the automation node llm can be picked up.

    try:
        current_project = local_client.get_default_project()
        current_project.get_metadata() # try project
    except:
        current_project = local_client.get_project(local_client.list_project_keys()[0]) # Pick a random project
    
    if parameter_name == "llm_id":
        return {
            "choices": [
                {"value": llm.get("id"), "label": llm.get("friendlyName")} for llm in current_project.list_llms() if llm.get('type') != 'RETRIEVAL_AUGMENTED'
            ]
        }
    elif parameter_name == "folder_id":
        root = design_client.get_root_project_folder()
        folders = list_project_folders(root)
        folders.sort(key=lambda x: x.name if x.name else x.id)
        return {"choices": [{"value": f.id, "label": f"{f.name if f.name else f.id} ({f.id})"} for f in folders]}
    elif parameter_name == "project_status_list":
        settings = design_client.get_general_settings()
        return {
            "choices": [
                {"value": status["name"], "label": status["name"]} for status in settings.get_raw()["projectStatusList"]
            ]
        }
    elif parameter_name == "project_keys":
        project_keys = design_client.list_project_keys()
        return {"choices": [{"value": key, "label": key} for key in project_keys]}

    else:
        return {
            "choices": [
                {
                    "value": "wrong",
                    "label": f"Problem getting the name of the parameter.",
                }
            ]
        }


def list_project_folders(root: "DSSProjectFolder") -> List["DSSProjectFolder"]:
    folders = []
    to_explore = [root]
    while len(to_explore) > 0:
        current = to_explore.pop()
        folders.append(current)
        to_explore.extend(current.list_child_folders())
    return folders
