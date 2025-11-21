# PAT Tools & Functions

import re
from typing import Optional

import dataikuapi

def is_project_standards(project : dataikuapi.dss.project.DSSProject ):
    """Check if a project is an Project Standards execution project"""
    if project.get_summary().get("projectType") == "PROJECT_STANDARDS":
        return True
    else:
        return False

#def get_source_project_key(project : dataikuapi.dss.project.DSSProject):
#    """
#    Return the source project key given a Project Standards execution project key.
#    """
#    if is_project_standards(project):
#        return re.sub(r'_(\w{8})$', '', project.project_key)
#    else:
#        return project.project_key

def dss_obj_to_dss_obj_md_link(dss_obj : str,project_key : str, name : str, display_name : str = None) -> str:
    """
    Return a formatted string to display md links.
    """
    if not display_name:
        display_name = name
    if dss_obj == "dataset":
        return f"[{display_name}](dataset:{project_key}.{name})"
    elif dss_obj == "flow_zone":
        return f"[{display_name}](flow_zone:{project_key}.{name})"
    elif dss_obj == "project":
        return f"[{display_name}](project:{name})"
    elif dss_obj == "recipe":
        return f"[{display_name}](recipe:{project_key}.{name})"
    elif dss_obj == "jupyter_notebook":
        return f"[{display_name}](jupyter_notebook:{project_key}.{name})"
    elif dss_obj == "scenario":
        return f"[{display_name}](scenario:{project_key}.{name})"
    elif dss_obj == "dashboard":
        return f"[{display_name}](dashboard:{project_key}.{name})"
    elif dss_obj == "insight":
        return f"[{display_name}](insight:{project_key}.{name})"
    elif dss_obj == "webapp":
        return f"[{display_name}](web_app:{project_key}.{name})"
    elif dss_obj == "wiki":
        return f"[{display_name}](wiki:{project_key}.{name})"
    elif dss_obj == "py_code_env":
        return f"[{display_name}](py_code_env:{name})"
    else:
        return display_name

def md_print_list(name_list : list, dss_obj : str, project_key : str = None) -> str:
    """
    Return a formatted list of dss friendly md links
    """
    return ", ".join([dss_obj_to_dss_obj_md_link(dss_obj = dss_obj,name = name,project_key = project_key) for name in name_list])

def throw_if_not_an_url(url: Optional[str], name: str = ""):
    """
    Throw an error if the url is not valid.
    """
    if not url:
        raise ValueError(f"{name} URL should not be empty")

    regex = re.compile(r"^https?:\/\/\S+$")  # http:// or https://
    if not re.match(regex, url):
        raise ValueError(f"Invalid {name} URL: {url}")

