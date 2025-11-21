# Batch Report Generation (in the main display)

from dash import dcc, html
import dash_bootstrap_components as dbc
from typing import Dict, List, Any, Set

from project_advisor.pat_logging import logger

from project_advisor.report.full_pat_report.style import styles
from project_advisor.report.full_pat_report.config import configs
from project_advisor.report.full_pat_report.components import (build_hist_card,
                                                               build_agg_metric_card,
                                                               build_severities_by_tag_cards
                                                              )


def get_filtered_project_ids(settings : Dict[str, Any], data : Dict[str, Any]) -> set:
    """
    Return a set of project ids relevant to the selected filters
    """
    status_to_project = data["status_to_project"]
    tag_to_project = data["tag_to_project"]
    
    project_ids = set(settings.get("project_ids", []))
    status_filter = settings.get("status_filter", [])
    tag_filter = settings.get("tag_filter", [])
    
    logger.info(f"all projects count  {len(project_ids)}")
    logger.info(f"status_filter : {status_filter}")
    logger.info(f"tag_filter : {tag_filter}")
    
    # Projects with requested status
    project_ids_status = set()
    for status in status_filter:
        project_ids_status.update(status_to_project[status])
    logger.info(f"nbr of project with correct status : {len(project_ids_status)}")
    
    # Projects containing at least one of the listed tags
    project_ids_tags = set()
    if tag_filter == []:
        project_ids_tags = project_ids
    else:
        for tag in tag_filter:
            project_ids_tags.update(tag_to_project[tag])
    logger.info(f"nbr of project with at least one of the required tags : {len(project_ids_tags)}")
    
    filtered_project_ids = project_ids & project_ids_status & project_ids_tags
    logger.info(f"nbr of project with at least one of the required tags : {len(filtered_project_ids)}")
    return filtered_project_ids
    


def generate_layout_batch_pat(settings : Dict[str, Any], data : Dict[str, Any]) -> html.Div:
    """
    settings : dict -> filter settings for the display generation.
    data : dict -> Loaded once at start of webapp  
    """
    
    project_ids = get_filtered_project_ids(settings, data)
    
    project_metric_df = data["project_metric_df"]
    project_check_df = data["project_check_df"]
    severity_by_project_tag_df = data["severity_by_project_tag_df"]
    severity_by_project_df = data["severity_by_project_df"]

    # Filter check & metrics df to only keep relevant projects (removing instance metrics & checks)
    project_metric_df = project_metric_df[project_metric_df["project_id"].isin(project_ids)]
    project_check_df = project_check_df[project_check_df["project_id"].isin(project_ids)]
    project_tag_severity_df = severity_by_project_tag_df[severity_by_project_tag_df["project_id"].isin(project_ids)]
    project_severity_df = severity_by_project_df[severity_by_project_df["project_id"].isin(project_ids)]
    
    # Filter for the latest results
    most_recent_timestamp = severity_by_project_df['timestamp'].max()
    most_recent_timestamp_str = most_recent_timestamp.strftime("%Y/%m/%d, %H:%M:%S")
    
    project_metrics_latest_df = project_metric_df[project_metric_df["timestamp"]== most_recent_timestamp]
    project_check_latest_df = project_check_df[project_check_df["timestamp"]== most_recent_timestamp]
    project_tag_severity_latest_df = project_tag_severity_df[project_tag_severity_df['timestamp'] == most_recent_timestamp]
    project_severity_latest_df = project_severity_df[project_severity_df['timestamp'] == most_recent_timestamp]
    
    mean_project_metric_cards = []
    project_metric_hists = []
    
    # Create cards & hist for INT metrics
    for p_metric in set(project_metrics_latest_df[project_metrics_latest_df["metric_type"].isin(["INT"])]["metric_name"]):
        df_metric = project_metrics_latest_df[project_metrics_latest_df["metric_name"] == p_metric]
        df_metric = df_metric.astype({'metric_value': 'float64'})
        df_metric = df_metric.astype({'metric_value': 'int64'})
        mean_project_metric_cards.append(build_agg_metric_card(f"avg {p_metric}", "{:.2f}".format(df_metric["metric_value"].mean())))
        project_metric_hists.append(build_hist_card(p_metric, df_metric))
    
    # Create cards & hist for FLOAT metrics
    for p_metric in set(project_metrics_latest_df[project_metrics_latest_df["metric_type"].isin(["FLOAT"])]["metric_name"]):
        df_metric = project_metrics_latest_df[project_metrics_latest_df["metric_name"] == p_metric]
        df_metric = df_metric.astype({'metric_value': 'float64'})
        mean_project_metric_cards.append(build_agg_metric_card(f"avg {p_metric}", "{:.2f}".format(df_metric["metric_value"].mean())))
        project_metric_hists.append(build_hist_card(p_metric, df_metric))
    
    # Create cards & hist for BOOLEAN metrics
    # TODO.
    
    ### Project & Instance Check Category Pie Charts ###
    project_tag_check_severities_cards = build_severities_by_tag_cards(project_tag_severity_latest_df)
    
    
    ### Generate Display
    ROW_STYLE = {
                "margin-top" : "10px",
            }
    display = []   

    if len(mean_project_metric_cards) > 0:
        display.extend([
                        dbc.Row(html.H2("Project Agg Metrics"),style = ROW_STYLE),
                        dbc.Row(html.Div(mean_project_metric_cards),style = ROW_STYLE),
                        dbc.Row(html.H2("Project Metric Distributions"),style = ROW_STYLE),
                        dbc.Row(html.Div(project_metric_hists),style = ROW_STYLE)
                       ])
    
    if len(project_tag_check_severities_cards) > 0:
        display.extend([
                        dbc.Row(html.H2("Project Checks Summary"),style = ROW_STYLE),
                        dbc.Row(html.Div(project_tag_check_severities_cards),style = ROW_STYLE)
                       ])
    
    return html.Div(display)


def generate_batch_details(settings : Dict[str, Any], data : Dict[str, Any]) -> str:
    project_ids = settings.get("project_ids", [])
    project_ids = get_filtered_project_ids(settings, data)
    return f"Batch report running on {len(project_ids)} projects."


