# Project Report Generation (in the main display)

import logging
from dash import dcc, html
import dash_bootstrap_components as dbc
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
                                                               metric_evolution,
                                                               single_project_helper_content
                                                              )

from project_advisor.report.full_pat_report.tools import (compute_change_of_severity_level_df)

# Load constants
severity_name_mapping = configs["severity_name_mapping"]


def generate_project_details(project_key, project_metadata, styles):
    """
    Generate Project Details
    """
    logger.info(f"Generate Project Details for project {project_key}")
    
    
    if project_key is None:
        return "Project Report Details"
    
    # Fetch the relevant project data based on the project_key
    project_name = project_metadata[project_key]["name"]
    project_type = project_metadata[project_key]["project_type"]
    project_owner = project_metadata[project_key]["owner"]

    project_details = html.Div([
        html.H6(
            html.Span([
                html.I(className="fa-solid fa-circle-info", style={'margin-right': '10px'}),
                "Project details"
            ]),
            className="text-white",
            style={"font-size": "16px"}
        ),
        html.Hr(style={"color": "white"}),
        html.P(f"Project name: {project_name}", className="text-light", style={"font-size": "14px", "margin-bottom": "5px"}),
        html.P(f"Project key: {project_key}", className="text-light", style={"font-size": "14px", "margin-bottom": "5px"}),
        html.P(f"Project type: {project_type}", className="text-light", style={"font-size": "14px", "margin-bottom": "5px"}),
        html.P(f"Project owner: {project_owner}", className="text-light", style={"font-size": "14px", "margin-bottom": "5px"}),
    ], id='project-details', style=styles["sidebar_project_details"])

    return project_details


def generate_homepage_single_pat():
    """
    Generate Homepage single PAT
    """
    logger.info("Generate Homepage single PAT")
    
    layout_homepage_single_pat = html.Div([
        html.Div([
            html.Span([
                html.I(className="bi bi-sliders", style={"font-size": "2rem"})
            ]),
            html.H2([
            "Select a project or choose a different tool from the sidebar on the left"
            ], style={"font-size": "22px", "font-color": "#495057", "margin-top": "20px"})
        ], style=styles["homepage_single_pat"])
    ], style=styles["div_homepage_single_pat"])
    return layout_homepage_single_pat


def generate_layout_single_pat(project_key, data):
    """
    Generate the layout for the single PAT Tab
    """
    logger.info(f"Generate the layout for the single PAT Tab for project {project_key}")
    
    if project_key is None:
        return generate_homepage_single_pat()
    
    ### Load & Prepare relevant precomputed datasets
    project_metric_df = data["project_metric_df"]
    project_check_df = data["project_check_df"]
    severity_by_project_tag_df = data["severity_by_project_tag_df"]
    severity_by_project_df = data["severity_by_project_df"] 
    
    # Filter to keep relevant historical data for the project
    project_metric_df = project_metric_df[project_metric_df["project_id"] == project_key] # All checks with their severity
    project_check_df = project_check_df[project_check_df["project_id"] == project_key] # All checks with their severity
    project_tag_severity_df = severity_by_project_tag_df[severity_by_project_tag_df["project_id"] == project_key] # Agg at project + tag level
    project_severity_df = severity_by_project_df[severity_by_project_df["project_id"] == project_key] # Agg at project level
    
    # Filter for the latest results
    most_recent_timestamp = project_severity_df['timestamp'].max()
    most_recent_timestamp_str = most_recent_timestamp.strftime("%Y/%m/%d, %H:%M:%S")
    
    project_metric_latest_df = project_metric_df[project_metric_df['timestamp'] == most_recent_timestamp]
    project_check_latest_df = project_check_df[project_check_df['timestamp'] == most_recent_timestamp]
    project_tag_severity_latest_df = project_tag_severity_df[project_tag_severity_df['timestamp'] == most_recent_timestamp]
    project_severity_latest_df = project_severity_df[project_severity_df['timestamp'] == most_recent_timestamp]
    
    ### Build Dashboard
    # Load project the latest project severity max and count
    project_max_severity = project_severity_latest_df['max_severity'].iloc[0]
    project_max_severity_str = f"Project Max Severity : {severity_name_mapping[project_max_severity]}"

    # Generate project severity evolution chart
    fig_project_severity_evolution = severity_level_evolution(project_check_df, title = "Project Severity levels evolution over time")
    
    # Generate Project severity by tag chart
    fig_project_severity_by_tag = severity_by_tag(project_tag_severity_latest_df)
    
    # Generate Project max severity over time
    fig_project_max_severity_evolution = max_severity_by_tag_evolution(project_tag_severity_df)

    # Generate Project Check Severity change table
    severity_change_df = compute_change_of_severity_level_df(df = project_check_df, severity_col = "severity")
    table_change_of_severity = create_latest_severity_change_table(severity_change_df) if not severity_change_df.empty else html.P("No changes in project check severities during the last run.", className="text-muted")

    # Generate Project Check recommendations table
    table_check_reco = create_check_reco_accordion(check_latest_df = project_check_latest_df, 
                                                   tag_severity_latest_df =project_tag_severity_latest_df
                                                  )

    # Generate Metric cards and evolution chart
    cards_metric_project = generate_metric_cards(project_metric_latest_df)
    fig_metric_evolution = metric_evolution(project_metric_df)

    # Layout structure
    layout = dbc.Row([
        dbc.Col([
            
            # Row containing project score and report date
            dbc.Row(
                [
                    # Col for the Project Score
                    dbc.Col([
                        html.Div(
                            [
                                html.H3([dbc.Badge(project_max_severity_str, id="project_max_severity", color=severity_color_mapping[project_max_severity], text_color="dark", className="me-1")], style={"display": "inline-block"}),
                                html.I(className="bi bi-info-circle-fill me-2", id="target_info", style={'display': 'inline-block', 'margin-left':'5px', 'font-size': 20}),
                                dbc.Tooltip(
                                    "Highest severity returned by all of the latest checks ran on this project.",
                                    target="target_info",
                                    style={"font-size": 13}
                                )
                            ],
                            style={"font-size": "24px", "font-weight": "bold"},
                        ),
                        display_severity_counts(project_severity_latest_df),
                    ],
                        width=6,  # Adjust the width for alignment
                    ),
                    
                    # Col for the Report Date
                    dbc.Col(
                        html.Div(
                            [
                                html.Span("Last report date: ", style={"font-weight": "bold"}),
                                html.Span(most_recent_timestamp_str, id="report_date"),
                            ],
                            style={"font-size": "20px", "text-align": "right"},
                        ),
                        width=6,  # Adjust width as needed
                    ),
                ],
                className="align-items-center",  # Ensures vertical alignment
                style= {"margin-bottom": "20px"}
            ),
            
            # Project Severity evolution
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Project Severity Levels evolution over time", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_project_severity_evolution), 
                        ]),
                    ], className="mb-4"),
                ], md=8),
                
                # Add the helper div next to the graph
                dbc.Col([
                    html.Div([
                        single_project_helper_content
                    ], style={
                        "background-color": "#d9e6ed", 
                        "color": "#205678", 
                        "border-radius": "8px", 
                        "padding": "15px", 
                        "font-size": "12px",
                        "height": "450.29px",
                        'overflow': 'hidden',  
                        'maxWidth': '100%', 
                        'wordWrap': 'break-word',
                    }),
                ], md=4),
            ]),
            
            # Checks summary
            html.H3("Checks summary", className="display-6", style={"padding": "10px", "font-size": "24px"}),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Severity level count by tag (last run)", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_project_severity_by_tag), 
                        ]),
                    ], className="mb-4"),
                ], md=4),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Evolution of max severity level by tag", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_project_max_severity_evolution)
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
            html.H3("Metrics summary", className="display-6", style={"padding": "10px", "font-size": "24px"}),
            html.P("Metrics below are computed during the last run", style={"padding": "10px", "font-style": "italic"}),
            
            html.Div(cards_metric_project, style={"width": "100%"}),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Metrics evolution over time", style={"font-size": 20}),
                        dbc.CardBody([
                            dcc.Graph(figure=fig_metric_evolution), 
                        ]),
                    ], className="mb-4"),
                ], md=8),
            ]),
        ], style=styles["content_page"])
    ], style=styles["content_page_row"])

    return layout
