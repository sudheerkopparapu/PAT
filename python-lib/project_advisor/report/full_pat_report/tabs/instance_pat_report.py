# Instance Report Generation (in the main display)

from dash import dcc, html
import dash_bootstrap_components as dbc
from typing import List, Dict, Any

from project_advisor.pat_logging import logger

from project_advisor.report.full_pat_report.config import configs
from project_advisor.report.full_pat_report.style import styles, severity_color_mapping

from project_advisor.report.full_pat_report.components import (display_severity_counts,
                                                               severity_level_evolution,
                                                               severity_by_tag,
                                                               max_severity_by_tag_evolution,
                                                               create_latest_severity_change_table,
                                                               create_check_reco_accordion,
                                                               generate_metric_cards,
                                                               metric_evolution
                                                              )

from project_advisor.report.full_pat_report.tools import (compute_change_of_severity_level_df)

# Load constants
severity_name_mapping = configs["severity_name_mapping"]

def generate_layout_instance_pat(project_list : List, data : Dict[str, Any]):
    """
    Generate Layout for the instance PAT TAB
    """
    logger.info("Generate Layout for the instance PAT TAB")
    
    ### Load relevant precomputed datasets
    instance_check_df = data["instance_check_df"]
    instance_metric_df = data["instance_metric_df"]
    severity_by_instance_tag_df = data["severity_by_instance_tag_df"]
    severity_by_instance_df = data["severity_by_instance_df"]
    
    project_metric_df = data["project_metric_df"]
    project_check_df = data["project_check_df"]
    severity_by_project_tag_df = data["severity_by_project_tag_df"]
    severity_by_project_df = data["severity_by_project_df"] 
    
    # Filter for the latest results
    most_recent_timestamp = severity_by_instance_df['timestamp'].max()
    most_recent_timestamp_str = most_recent_timestamp.strftime("%Y/%m/%d, %H:%M:%S")
    
    project_metric_latest_df = project_metric_df[project_metric_df['timestamp'] == most_recent_timestamp]
    project_check_latest_df = project_check_df[project_check_df['timestamp'] == most_recent_timestamp]
    project_tag_severity_latest_df = severity_by_project_tag_df[severity_by_project_tag_df['timestamp'] == most_recent_timestamp]
    project_severity_latest_df = severity_by_project_df[severity_by_project_df['timestamp'] == most_recent_timestamp]
    
    instance_metric_latest_df = instance_metric_df[instance_metric_df['timestamp'] == most_recent_timestamp]
    instance_check_latest_df = instance_check_df[instance_check_df['timestamp'] == most_recent_timestamp]
    instance_tag_severity_latest_df = severity_by_instance_tag_df[severity_by_instance_tag_df['timestamp'] == most_recent_timestamp]
    instance_severity_latest_df = severity_by_instance_df[severity_by_instance_df['timestamp'] == most_recent_timestamp]
    

    # Compute Instance max severity
    instance_max_severity = instance_severity_latest_df['max_severity'].iloc[0]
    instance_max_severity_str = f"Instance Max Severity : {severity_name_mapping[instance_max_severity]}"
    
    # Generate Counts of Instance severity levels
    instance_severity_counts = display_severity_counts(instance_severity_latest_df)
    
    # Generate Counts of project Max Severities
    project_max_severity_counts_df = project_severity_latest_df[list(severity_name_mapping.keys())].sum().to_frame().T
    project_max_severity_counts = display_severity_counts(project_max_severity_counts_df)

    # Generate Instance severity levels over time
    fig_instance_severity_evolution = severity_level_evolution(instance_check_df, 
                                                               title = "Instance Severity Levels over time")
    
    # Generate Instance severity evolution
    fig_projects_max_severity_evolution = severity_level_evolution(severity_by_project_df, 
                                                                   title = "Instance Severity Levels over time",
                                                                   severity_col = "max_severity")
 
    # Instance severity by tag.
    fig_instance_severity_by_tag = severity_by_tag(instance_tag_severity_latest_df)
    
    # Instance max severity by tag over time
    fig_instance_max_severity_by_tag_evolution = max_severity_by_tag_evolution(severity_by_instance_tag_df)

    # Instance Check Severity Change Dataframe and Table
    severity_change_df = compute_change_of_severity_level_df(df = instance_check_df, severity_col = "severity")
    table_change_of_severity = create_latest_severity_change_table(severity_change_df) if not severity_change_df.empty else html.P("No changes in Instance checks severity during the last run.", className="text-muted")

    # Check recommendations table
    table_check_reco = create_check_reco_accordion(check_latest_df = instance_check_latest_df, 
                                                   tag_severity_latest_df =instance_tag_severity_latest_df
                                                  )

    # Metric cards and evolution chart
    instance_metric_cards = generate_metric_cards(instance_metric_latest_df)
    fig_instance_metric_evolution = metric_evolution(instance_metric_df)

    # Layout structure
    layout = dbc.Row([
        dbc.Col([
            
            # Row containing project score and report date
            dbc.Row(
                [
                    # Col for the Project Score
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H3([dbc.Badge(instance_max_severity_str, id="instance_max_severity", color=severity_color_mapping[instance_max_severity], text_color="white", className="me-1")], style={"display": "inline-block"}),
                                    html.I(className="bi bi-info-circle-fill me-2", id="target_info", style={'display': 'inline-block', 'margin-left':'5px', 'font-size': 20}),
                                    dbc.Tooltip(
                                        "The Instance Max Severity Level is the highest severity returned out of all the instance checks ran in the latest run.",
                                        target="target_info",
                                        style={"font-size": 13}
                                    )
                                ],
                                style={"font-size": "24px", "font-weight": "bold"},
                            ),
                            html.Div(["Instance Check Severities"]),
                            instance_severity_counts,
                            html.Div(["Project Check Severities"]),
                            project_max_severity_counts
                        ],
                        width=6,  # Adjust the width for alignment
                    ),
                    
                    # Col for the Report Date
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("Last report date: ", style={"font-weight": "bold", "font-size": 20}),
                                html.Span(most_recent_timestamp_str, id="report_date"),
                            ],
                            style={"font-size": "16px", "text-align": "right"},
                        ),
                        width=6,  # Adjust width as needed
                    ),
                ],
                className="align-items-center",  # Ensures vertical alignment
                style= {"margin-bottom": "20px"}
            ),
            
            # Instance and project score evolution
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Instance Severity Levels over time", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_instance_severity_evolution), 
                        ]),
                    ], className="mb-4"),
                ], md=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Project Max Severities over time", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_projects_max_severity_evolution), 
                        ]),
                    ], className="mb-4"),
                ], md=6),
            ]),
            
            # Checks Summary - Instance Check severity by tag and evolution of max severity by tag over 
            html.H3("Checks summary", className="display-6", style={"padding": "10px", "font-size": "24px"}),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Instance Severity by Tag (last run)", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_instance_severity_by_tag), 
                        ]),
                    ], className="mb-4"),
                ], md=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Instance Max Severity by tag over time", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_instance_max_severity_by_tag_evolution)
                        ]),
                    ], className="mb-4"),
                ], md=8),
            ]),
            
            # Checks details
            html.H3("Check details", className="display-6", style={"padding": "10px", "font-size": "24px"}),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Flag changing check severity (last run)", style={"font-size": 20}),
                        dbc.CardBody([
                            table_change_of_severity
                        ]),
                    ], className="mb-4"),
                ], md=12),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Check recommendations", style={"font-size": 20}),
                        dbc.CardBody([
                            table_check_reco
                        ]),
                    ], className="mb-4"),
                ], md=12),
            ]),
            
            # Metrics summary
            html.H3("Instance Metrics summary", className="display-6", style={"padding": "10px", "font-size": "24px"}),
            html.P("Instance Metrics below are computed during the last run", style={"padding": "10px", "font-style": "italic"}),
            
            html.Div(instance_metric_cards, style={"width": "100%"}),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Instance Metrics evolution over time", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_instance_metric_evolution), 
                        ]),
                    ], className="mb-4"),
                ], md=8),
            ]),
        ], style=styles["content_page"])
    ], style=styles["content_page_row"])

    return layout
    
def generate_instance_details(all_project_list : List, data : Dict[str, Any]):
    """
    Instance Details to be displayed in the side Bar.
    """
    logger.info("Generate generate_instance_details")
    
    return f"Instance Report running on {len(all_project_list)} projects."