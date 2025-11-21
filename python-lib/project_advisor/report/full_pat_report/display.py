# Main display
import logging
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from project_advisor.report.full_pat_report.config import configs
from project_advisor.report.full_pat_report.style import styles

def build_layout(input_config, data):
    """
    Generate Main Layout for the whole webapp
    """
    logging.info("Generate Main Layout for the whole webapp")

    # Sidebar
    sidebar = dbc.Col([
                html.H2(html.Span([html.I(className="fa-solid fa-chart-line", style={'margin-right': '10px'}), "PAT Report"]), className="display-6", style=styles["sidebar_header"]),
                html.Div([
                    html.P("Please select the type of assessment:", style={"color": "white", "font-size": 14}), 

                    # Dropdown for Tab options
                    html.Div([dcc.Dropdown(id='layout-dropdown')],
                             id = "layout-dropdown-container"),

                    # Placeholder for the dynamic sidebar dropdown
                    html.Div([
                                html.Div([
                                        dcc.Dropdown(id = "project-dropdown")
                                    ],id = "single-pat-settings"),
                                html.Div([
                                        dcc.Dropdown(id = "project-status-dropdown"),
                                        dcc.Dropdown(id = "project-tag-dropdown")
                                    ],id = "batch-pat-settings"
                                ),
                                html.Div([],id = "instance-pat-settings")
                             ],
                             id="layout-settings-container"
                    ),

                    # Placeholder for project details
                    html.Div(id='layout-details-container')

                ], className="bg-dark", style=styles["sidebar_content"]),

                # Footer section
                html.Div([
                    html.Div([
                        html.P("Any questions or bugs to report?", style={"marginBottom": "0.5rem"}),
                        html.P("Please contact the Dataiku team", style={"marginBottom": "0"})
                    ], style=styles["footer_content"])
                ], style=styles["sidebar_footer"]),

            ], width=3, style=styles["sidebar_container"])


    # Main content
    main_content = dbc.Col([

                        # Top white bar
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Div([
                                        html.P(children=["Hello"], id="menu-user", style={"padding": "10px 20px", "font-size": 20, "color": "#495057", "margin-top": "5px"})
                                    ], className="d-flex justify-content-end"),
                                ], style=styles["top_white_bar"])
                            ])
                        ]),

                        # Main Report Layour
                        html.Div(id="layout")
        ], 
        width=9, 
        style=styles["content_container"]
    )
    
    memory = html.Div([
                    dcc.Store(id='example-id')]
    )

    # Define the layout
    main_layout =  dbc.Container([
        dbc.Row([
            sidebar,
            main_content
        ]),
        html.Div(id="init-input"), # To trigger the init callback setting up the webapp.
        memory,
    ], fluid=True, style=styles["page_style"])
    
    return main_layout