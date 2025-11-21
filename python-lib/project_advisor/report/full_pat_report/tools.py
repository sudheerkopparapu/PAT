# tools.py

import pandas as pd
from typing import List

from project_advisor.pat_logging import logger

from project_advisor.report.full_pat_report.config import configs
from project_advisor.report.full_pat_report.style import styles

import re

#########################
## User Auth functions ##
#########################

def user_is_admin(user_login):
    """
    Return user admin status
    """
    logger.info("Checking if user is admin")
    client = configs["client"]
    
    groups = client.list_groups()
    user = client.get_user(user_login)
    settings = user.get_settings()
    groups = settings.get_raw().get("groups",[])
    
    is_admin = False
    for group_name in groups:
        group = client.get_group(group_name)
        if group.get_definition().get("admin", False):
            is_admin = True
    return is_admin 


def build_user_to_project_mapping():
    """
    Building access to user to project mapping
    """
    logger.info("Building user to project mapping")
    
    pat_backend_client = configs.get("pat_backend_client")
    pat_backend_client.load_latest("user_to_project_mapping")
    return pat_backend_client.get_table("user_to_project_mapping")
    
    
    # Old code
    """
    client = configs["client"]
    users = client.list_users()
    groups = client.list_groups()
    projects = client.list_projects()

    # Enrich projects (precomputation)
    for p in projects:
        project_key = p["projectKey"]
        project = client.get_project(project_key)
        p.update({"permissions": project.get_permissions()["permissions"]})

    user_to_project_mapping = []
    for user in users:
        user_login = user.get("login")
        user_groups = user.get("groups")

        for p in projects:
            project_key = p.get("projectKey")
            project_owner = p.get("ownerLogin")

            is_project_owner = False
            is_shared_by_user = False
            is_shared_by_group = False
            
            if user_login == project_owner:
                is_project_owner = True
            
            else:
                for permission in p.get("permissions", []):
                    # If has read, write or admin permissions on project -> set if shared by user or group
                    if any([permission.get('admin'),
                           permission.get('writeProjectContent'),
                           permission.get('readProjectContent')]):

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
    return pd.DataFrame.from_dict(user_to_project_mapping)
    """

def get_user_project_keys(user_login : str, mapping_df : pd.DataFrame) -> list:
    """
    Get user project keys based on the latest mapping of user permissions
    """
    if user_is_admin(user_login): # Needed as even if admin is not references in project security, they have access to it.
        return configs["client"].list_project_keys()
    else:   
        return list(mapping_df[mapping_df["user_login"]==user_login]["project_key"])

#########################
## Mapping Functions   ##
#########################

def get_all_project_global_tags() -> set:
    """
    Not use for now
    """
    client = configs["client"]
    settings = client.get_general_settings()
    len(settings.settings["globalTagsCategories"])
    tag_names = set()
    for gt_cat in settings.settings["globalTagsCategories"]:
        if "PROJECT" in gt_cat["appliesTo"]:
            tags = gt_cat["globalTags"]
            for tag in tags:
                tag_names.add(f"{gt_cat['name']}:{tag['name']}")
    return tag_names


def get_status_to_project_mapping() -> dict:
    """
    Get project status to project mapping
    """
    logger.info("Building status to project mapping")
    client = configs["client"]
    status_to_project = {}   
    for project in client.list_projects():
        status = project.get("projectStatus", "NO STATUS")
        status_to_project.setdefault(status, set())
        status_to_project[status].add(project.get("projectKey", "NO PROJECT KEY"))
    return status_to_project


def get_tag_to_project_mapping():
    """
    Get project tag to project mapping
    """
    logger.info("Building tag to project mapping")
    client = configs["client"]
    tag_to_project = {}
    for project in client.list_projects():
        project_tags = project.get("tags", [])
        for tag in project_tags:
            proj_set = tag_to_project.setdefault(tag, set())
            tag_to_project[tag].add(project.get("projectKey", "NO PROJECT KEY"))
    return tag_to_project

###############################
## Dynamic Display Functions ##
###############################

def truncate_text(text: str, max_characters=200, cut_indicator : str = "...") -> str:
    """Truncate a string that is too long"""
    if len(str(text)) <= max_characters:
        return text
    return text[:max_characters] + cut_indicator

def truncate_text_in_object(input_obj: dict, max_characters=500, cut_indicator : str = "...") -> dict:
    """Truncate a dict of list that is too big"""
    max_list_items = 50
    if isinstance(input_obj, dict):
        truncated_dict = {}
        for key, value in input_obj.items():
            if isinstance(value, str):
                truncated_dict[key] = truncate_text(value, max_characters, cut_indicator = cut_indicator)
            elif isinstance(value, list):
                truncated_dict[key] = truncate_text_in_object(value, max_characters, cut_indicator = cut_indicator)
            elif isinstance(value, dict):
                truncated_dict[key] = truncate_text_in_object(value, max_characters, cut_indicator = cut_indicator)
            else:
                truncated_dict[key] = value  # Leave other types untouched
        return truncated_dict   
    elif isinstance(input_obj, list):
        early_end = [cut_indicator] if len(input_obj)>max_list_items else []
        truncated_list = []
        for l_item in input_obj[:max_list_items]:
            truncated_list.append(truncate_text_in_object(l_item, max_characters, cut_indicator = cut_indicator))
        return truncated_list + early_end
    elif isinstance(input_obj, str):
        return truncate_text(input_obj, max_characters, cut_indicator = cut_indicator)
    else:
        return input_obj


def enrich_project_list(project_keys):
    """
    Enrich project keys with project metadata.
    """
    logger.info("Enriching Projects with metadata")
    client = configs["client"]
    
    projects_all = client.list_projects()
    projects_in_list_but_not_on_instance = set(project_keys).difference(set(client.list_project_keys()))
    logger.info(f"There are {len(projects_in_list_but_not_on_instance)} projects in project list not on the instance")


    enriched_projects = []
    projects_not_in_input_list = []
    for project in projects_all:
        if project['projectKey'] in project_keys:
            enriched_projects.append(
                {
                    project['projectKey']: {
                        "name": project.get("name", "NO_NAME"),
                        "owner": project.get("ownerDisplayName", "UNKNOWN_OWNER"),
                        "project_type": project.get("projectType", "UNKNOWN_PROJECT_TYPE")
                    }
                }
            )
        else:
            projects_not_in_input_list.append(project['projectKey'])
            
    logger.info(f"There are {len(projects_not_in_input_list)} projects on the instance not in the project key list")
    
    return enriched_projects


def format_md_links(md_text : str, default_project_key = None):
    """
    Replace all DSS friends MD link with webapp friendly MD links.
    """
    return re.sub(
           r"(\[[A-Za-z0-9 _]*\] *\([A-Za-z0-9 _.:]*\))", 
           lambda x: dss_obj_md_link_to_md_link(x.group(1), default_project_key), 
           md_text
    )
    
    
def dss_obj_md_link_to_md_link(dss_md_link : str, default_project_key = None):
    """
    Convert a DSS friends MD link to a webapp friendly MD link
    """
    
    # Get display value
    val_matches = re.findall(r'\[(.*?)\]', dss_md_link)
    if len(val_matches) == 1:
        display_val = val_matches[0].strip()
    else:
        logger.warning("Error with link display")
        return dss_md_link

    # Strip link
    link_matches = re.findall(r'\((.*?)\)', dss_md_link)
    if len(val_matches) == 1:
        dss_link = link_matches[0].strip().split(":")
        if len(dss_link) ==1:
            # case of non DSS specific URL
            return dss_md_link
        if len(dss_link) ==2:
            dss_obj = dss_link[0]
            dss_obj_ref = dss_link[1]
            dss_obj_ref = dss_obj_ref.strip().split(".")
            if len(dss_obj_ref) == 1:
                # Case where default project key should be used
                project_key = default_project_key
                obj_name = dss_obj_ref[0]
            elif len(dss_obj_ref) == 2:
                project_key = dss_obj_ref[0]
                obj_name = dss_obj_ref[1]
            else:
                logger.warning("Link value not well formatted")
                return dss_md_link

        else:
            logger.warning("DSS link not well formatted")
            return dss_md_link
    else:
        logger.warning("Link not well formatted")
        return dss_md_link

    if dss_obj == "dataset":
        return f"[{display_val}](/projects/{project_key}/datasets/{obj_name}/explore/)"
    elif dss_obj == "project":
        return f"[{display_val}](/projects/{obj_name})"
    elif dss_obj == "recipe":
        return f"[{display_val}](/projects/{project_key}/recipes/{obj_name}/)"
    elif dss_obj == "jupyter_notebook":
        return f"[{display_val}](/projects/{project_key}/notebooks/jupyter/{obj_name}/)"
    elif dss_obj == "scenario":
        return f"[{display_val}](/projects/{project_key}/scenarios/{obj_name}/settings/)"
    elif dss_obj == "dashboard":
        return f"[{display_val}](/projects/{project_key}/dashboards/{obj_name}_/view/)"
    elif dss_obj == "insight":
        return f"[{display_val}](/projects/{project_key}/insights/{obj_name}_/view/)"
    elif dss_obj == "webapp":
        return f"[{display_val}](/projects/{project_key}/webapps/{obj_name}_/view/)"
    elif dss_obj == "wiki":
        return f"[{display_val}](/projects/{project_key}/wiki/{obj_name}/)"
    elif dss_obj == "py_code_env":
        return f"[{display_val}](/admin/code-envs/design/python/{obj_name}/)"
    else:
        logger.debug(f"Object type {dss_obj} not supported")
        return dss_md_link

###############################
## Precomputations functions ##
###############################
def compute_severity_max_and_count(df : pd.DataFrame, grouping_cols : List[str]) -> pd.DataFrame:
    """
    Compute Project Max Severity over time.
    """
    logger.info(f"Compute Project Max Severity over time grouped by {grouping_cols}")

    # Compute severity count columns
    severity_counts = df.groupby(grouping_cols)['severity'].value_counts().unstack(fill_value=0)

    # Compute max severity level per group
    max_severity = df.groupby(grouping_cols)['severity'].max()

    # Merge the severity counts with the max severity column
    result = severity_counts.merge(max_severity, on=grouping_cols, how='left')

    # Rename the max severity column
    result = result.rename(columns={'severity': 'max_severity'})

    # Reset index to make it a proper DataFrame
    result = result.reset_index()

    # Ensure all severity levels [-1, 0, 1, 2, 3, 4, 5] exist as columns
    severity_levels = range(-1, 6)
    for level in severity_levels:
        if level not in result.columns:
            result[level] = 0  # Add missing severity columns with default value 0

    # Compute severity level
    result['count'] = result[severity_levels].sum(axis=1)
    
    # Reorder columns: Category, Subcategory, severity levels, and max severity
    column_order = grouping_cols + list(severity_levels) + ['max_severity', "count"]
    
    return result[column_order]



def compute_change_of_severity_level_df(df : pd.DataFrame, severity_col: str = "max_severity" ,time_column : str = "timestamp"):
    """
    Compute Change of any level of severity & Change of max severity
    """
    logger.info(f"Compute Change of any level of Severity & Change of max severity")
    
    # Check that there are at least two distinct timestamps
    if df[time_column].nunique() <= 1:
        return pd.DataFrame()
    
    df = df.sort_values(by=time_column)

    # Load the two most recent unique timestamps
    last_two_timestamps = df[time_column].drop_duplicates().nlargest(2)

    # Extract the rows corresponding to these two timestamps
    most_recent_df = df[df[time_column] == last_two_timestamps.iloc[0]]
    previous_df = df[df[time_column] == last_two_timestamps.iloc[1]]

    # Merge the two dataframes to compare the 'pass' status (left merge)
    comparison_df = previous_df[['check_name', severity_col]].merge(
        most_recent_df[['check_name', severity_col]], 
        on='check_name', 
        suffixes=('_previous', '_current'),
        how='left'
    )

    # Identify the checks that changed severity
    comparison_df[f"severity_change"] = comparison_df[f"{severity_col}_current"] - comparison_df[f"{severity_col}_previous"]
    comparison_df = comparison_df.rename(columns={f"{severity_col}_current": 'severity_current', f"{severity_col}_previous": 'severity_previous'})
    changed_severities = comparison_df[comparison_df["severity_change"] != 0]
    return changed_severities

# Probs not needed ? 
def compute_check_reco_table_df(df, category=None):
    """
    Compute Check reco Table df
    """
    logger.info(f" Compute recommendation df")

    most_recent_timestamp = df['timestamp'].max()
    most_recent_rows = df[df['timestamp'] == most_recent_timestamp]

    # Create a new column 'status' that marks whether the check passed or failed
    most_recent_rows['status'] = most_recent_rows['pass'].apply(lambda x: 'Pass' if x else 'Fail')
    return most_recent_rows

# Probs not needed?
def compute_metric_df(df_metric, instance=True):
    """
    Compute Check reco Table df
    """
    logger.info(f"Compute Fail to pass df, instance : {instance}")
    
    if instance:
        df_metric = df_metric[df_metric["project_id"].isna()]

    return df_metric
