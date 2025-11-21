# Data Loader
import dataiku
from datetime import datetime
import numpy as np
import pandas as pd

from project_advisor.pat_logging import logger

from project_advisor.report.full_pat_report.config import configs
from project_advisor.report.full_pat_report.tools import (get_status_to_project_mapping,
                                                          get_tag_to_project_mapping,
                                                          build_user_to_project_mapping,
                                                          compute_severity_max_and_count)


def format_pat_report(df : pd.DataFrame) -> None:
    df["timestamp"] = df["timestamp"].transform(lambda ts : datetime.fromisoformat(ts))
    df["tags"] = df["tags"].fillna("NO TAGS")
    df["tags"] = df['tags'].str.split('|')
    df = df[df["status"]=="RUN_SUCCESS"]
    return df
    
def load_report_from_folder(folder_handle : dataiku.Folder, folder_path : str, n : int) -> pd.DataFrame:
    files = folder_handle.list_paths_in_partition()
    files = [f for f in files if f.startswith(folder_path)]
    files.sort(reverse = True)
    reports = []
    for file_path in files[:n]:
        logger.debug(f"loading file {file_path}")
        try:
            with folder_handle.get_download_stream(file_path) as stream:
                reports.append(pd.read_csv(stream))
        except pd.errors.EmptyDataError:
            logger.debug(f"file {file_path} is empty, skipping")
    if reports:
        return format_pat_report(pd.concat(reports))
    else:
        return None


def load_pat_report_data(input_config):
    """
    Load data from the flow and run pre-computations.
    """
    logger.info("Loading Metrics & Checks Datasets and precomputing score")

    # INIT
    data = {}

    last_n_reports = int(input_config['last_n_reports'])
    pat_report_folder_id = input_config['pat_report_folder']
    pat_report_folder = dataiku.Folder(pat_report_folder_id)
    
    logger.info(f"Loading the last {last_n_reports} PAT reports from folder {pat_report_folder_id}")
    instance_check_df = load_report_from_folder(pat_report_folder,"/checks/instance", last_n_reports)
    project_check_df = load_report_from_folder(pat_report_folder,"/checks/project", last_n_reports)
    instance_metric_df = load_report_from_folder(pat_report_folder,"/metrics/instance", last_n_reports)
    project_metric_df = load_report_from_folder(pat_report_folder,"/metrics/project", last_n_reports)
    logger.info(f"Input Metric & Check Reports have been loaded")

    has_instance_report = True if instance_check_df is not None else False
    logger.info(f"Webapp is running on instance report datasets : {has_instance_report}")

    # Get all the unique project keys in the PAT report.
    list_pat_project_ids = list(project_check_df["project_id"].unique())

    ### Precompute mapping tables
    # user_to_project mapping
    user_to_project_df = build_user_to_project_mapping()

    # tag_to_project mapping
    tag_to_project = get_tag_to_project_mapping()

    # status_to_project mapping
    status_to_project = get_status_to_project_mapping()

    # Precompute dataframes to build the charts
    logger.info("Precomputing scores for project and instance checks")

    # Precompute project check data
    logger.info("Precomputing Project metrics and checks")
    severity_by_project_df = compute_severity_max_and_count(project_check_df, ['timestamp','project_id'])
    project_check_with_tag_df = project_check_df.explode('tags').reset_index(drop=True)
    severity_by_project_tag_df = compute_severity_max_and_count(project_check_with_tag_df, ['timestamp','project_id', 'tags'])

    # Preompute instance check data
    severity_by_instance_df = None
    instance_check_with_tag_df = None
    severity_by_instance_tag_df = None

    if has_instance_report:
        logger.info("Precomputing Instance metrics and checks")
        severity_by_instance_df = compute_severity_max_and_count(instance_check_df, ['timestamp'])
        instance_check_with_tag_df = instance_check_df.explode('tags').reset_index(drop=True)
        severity_by_instance_tag_df = compute_severity_max_and_count(instance_check_with_tag_df, ['timestamp','tags'])
    else:
        severity_by_instance_df = None
        instance_check_with_tag_df = None
        severity_by_instance_tag_df = None

    # Precompute dataframes to build the charts
    logger.info("Precomputing scores for project and instance checks")

    data = {
        "has_instance_report" : has_instance_report,
        "user_to_project_df" : user_to_project_df,
        "status_to_project" : status_to_project,
        "tag_to_project" : tag_to_project,
        "list_pat_project_ids" : list_pat_project_ids,

        "project_check_df" : project_check_df,
        "severity_by_project_df" : severity_by_project_df,
        "project_check_with_tag_df" : project_check_with_tag_df,
        "severity_by_project_tag_df" : severity_by_project_tag_df,
        "project_metric_df" : project_metric_df,

        "instance_check_df" : instance_check_df,
        "severity_by_instance_df" : severity_by_instance_df,
        "instance_check_with_tag_df" : instance_check_with_tag_df,
        "severity_by_instance_tag_df" : severity_by_instance_tag_df,
        "instance_metric_df" : instance_metric_df
    }
    logger.info("All data is loaded and precomputed!")
    return data