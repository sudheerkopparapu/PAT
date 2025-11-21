# Callbacks
import dash
import logging
from dash.dependencies import Input, Output, State, ALL
from dash import dcc, html, ctx
from flask import request
from dash import callback_context


from project_advisor.report.full_pat_report.config import configs
from project_advisor.report.full_pat_report.style import styles
from project_advisor.report.full_pat_report.tools import (enrich_project_list,
                                                          user_is_admin,
                                                          get_user_project_keys,
                                                          
                                                         )
                                                          
from project_advisor.report.full_pat_report.tabs.single_pat_report import (generate_layout_single_pat, generate_project_details)
from project_advisor.report.full_pat_report.tabs.batch_pat_report import (generate_layout_batch_pat, generate_batch_details)
from project_advisor.report.full_pat_report.tabs.instance_pat_report import (generate_layout_instance_pat, generate_instance_details)

def get_authenticated_user_id():
    """
    get user auth info
    Note : Only callable within a callback
    """
    logging.info("get user authentication info")
    
    client = configs["client"]
    request_headers = dict(request.headers)
    auth_info = client.get_auth_info_from_browser_headers(request_headers)
    return auth_info["authIdentifier"]


def load_callbacks(app, data):
    """
    Init Callbacks
    """
    logging.info(f"Init Callbacks")
    
    # Init variables for callbacks
    client = configs["client"]
    project_check_df = data["project_check_df"]
    project_metric_df = data["project_metric_df"]
    list_pat_project_ids = data["list_pat_project_ids"]
    
    has_instance_report = data["has_instance_report"]
    
    user_to_project_df = data["user_to_project_df"]
    status_to_project = data["status_to_project"]
    tag_to_project = data["tag_to_project"]
    
    # All projects available in the report
    list_pat_projects_enriched = enrich_project_list(list_pat_project_ids)
    
    logging.info(f"All enriched projects : {len(list_pat_projects_enriched)}")
    
    # Callback to intialize webapp and setup personalization per user.
    @app.callback(
        Output('menu-user', 'children'),
        Output('layout-dropdown-container', 'children'),
        Output('layout-settings-container', 'children'),
        [Input('init-input', 'children')]
    )
    def init_webapp_display(input_value):
        """
        Load user using webapp
        """
        logging.info(f"Init webapp display")
        
        user_login = get_authenticated_user_id()
        users = client.list_users()
        user_name = next((user['displayName'] for user in users if user['login'] == user_login), "Unknown")
        logging.info(f"User with display name : {user_name} has been identified")
        
        ### Define drop down options (based on user permissions on the instance)
        project_pat_tab = {'label': 'Project Assessment Tool', 'value': 'project'} # Project Tab option (always on)
        batch_pat_tab = {'label': 'Batch Project Assessment Tool', 'value': 'batch'} # Batch Project Tab option (always on)
        
        if user_is_admin(user_login) and has_instance_report: # If instance user is admin, give access to Instance PAT.
            instance_pat_tab = {'label': 'Instance Assessment Tool', 'value': 'instance'}
        else:
            instance_pat_tab = {'label': html.Span(['Instance Assessment Tool', html.I(className="fas fa-lock", style={'margin-left': '10px'})]), 'value': 'instance', 'disabled': True}
        
        # Define drop down options
        options = [project_pat_tab, batch_pat_tab, instance_pat_tab]
        
        main_drop_down = dcc.Dropdown(
                                    id='layout-dropdown',
                                    options=options,
                                    value='project',  # Default value
                                    className='mb-3',
                                    style=styles["dropdown_style"],
                                )

        ### Define the default available settings
        # Single PAT Settings
        user_project_list = []
        if user_is_admin(user_login):
            user_project_list = list_pat_projects_enriched
        else:
            user_project_keys = get_user_project_keys(user_login, user_to_project_df)
            user_project_list = [p for p in list_pat_projects_enriched if list(p.keys())[0] in user_project_keys]
        options_project = [{'label': list(project.keys())[0], 'value': list(project.keys())[0]} for project in user_project_list]
        
        single_pat_settings = html.Div([
                    html.P("Please select a project:", style={"color": "white", "font-size": 14}),
                    dcc.Dropdown(
                        id='project-dropdown',
                        options=options_project,  
                        placeholder="Select a project",
                        className='mb-3',
                        style=styles["dropdown_style"],
                    )],
                id = "single-pat-settings",
                style = {'display': 'block'}
        )
        
        # Batch PAT Settings
        #batch_pat_settings = html.Div("Batch PAT settings - TODO", id = "batch-pat-settings", style = {'display': 'none'}) # Hide by default
        all_statuses = list(status_to_project.keys())
        options_status = [{'label': status, 'value': status} for status in all_statuses]
        all_project_tags = list(tag_to_project.keys())
        options_tag = [{'label': tag, 'value': tag} for tag in all_project_tags]
          
        batch_pat_settings = html.Div([
                    html.P("Filters for Projects to consider:", style={"color": "white", "font-size": 14}),
                    dcc.Dropdown(
                        id='project-status-dropdown',
                        value = all_statuses,
                        options=options_status,  
                        placeholder="Select project statuses",
                        className='mb-3',
                        style=styles["dropdown_style"],
                        #maxHeight = 100,
                        #optionHeight = 50,
                        multi=True
                    ),
                    dcc.Dropdown(
                        id='project-tag-dropdown',
                        value = [],
                        options=options_tag,  
                        placeholder="Select project tags (Leave empty for all)",
                        className='mb-3',
                        style=styles["dropdown_style"],
                        #maxHeight = 100,
                        #optionHeight = 50,
                        multi=True
                    )],
                id = "batch-pat-settings",
                style = {'display': 'none'}
        )
        
        # Instance PAT Settings
        instance_pat_settings = html.Div("The Instance PAT report is not configurable.", id = "instance-pat-settings", style = {'display': 'none'}) # Hide by default
        
        tab_settings = [single_pat_settings, batch_pat_settings, instance_pat_settings]
     
        return f"Hello {user_name}", main_drop_down, tab_settings 
  
    

    # Define callback to update content based on dropdown selection
    @app.callback(
        [Output('layout', 'children'),
         Output('layout-details-container', 'children'),
         Output('single-pat-settings', 'style'),
         Output('batch-pat-settings', 'style'),
         Output('instance-pat-settings', 'style'),
        ],
        [Input('layout-dropdown', 'value'),
         Input('project-dropdown', 'value'),
         Input('project-status-dropdown', 'value'),
         Input('project-tag-dropdown', 'value'),
         
         # All all extra report settings here 
        ],
        prevent_initial_call=True
    )
    def update_main_content(selected_tool, selected_project, status_filter, tag_filter):
        """
        Update main content
        """
        logging.info(f"Update main content")
        
        ctx = callback_context
        # Debugging
        #logging.info (f"ctx.triggered {ctx.triggered}")
        #logging.info (f"ctx.triggered_id {ctx.triggered_id}")
        
        ### CASE : Update Tab ###
        
        if ctx.triggered_id == "project-dropdown":
            logging.info("project-dropdown has been updated")
        elif ctx.triggered_id == "project-tag-dropdown":
            logging.info("project-tag-dropdown has been updated")
        elif ctx.triggered_id == "project-status-dropdown":
            logging.info("project-status-dropdown has been updated")
        elif ctx.triggered_id == "layout-dropdown":
            logging.info("layout-dropdown has been updated")
        else:
            logging.warning("trigger id is not recognised")
       
        # Define user project list.
        user_login = get_authenticated_user_id()
        logging.info(f"All projects in the PAT Report : {len(list_pat_project_ids)}")
        
        
        user_auth_project_list = get_user_project_keys(user_login, user_to_project_df)
        logging.info(f"All projects user has access to : {len(user_auth_project_list)}")
        
        project_in_report_user_cannot_see = set(list_pat_project_ids).difference(set(user_auth_project_list))
        logging.info(f"There are {len(project_in_report_user_cannot_see)} projects in PAT report that user cannot see")
    
        
        user_project_list = [project_key for project_key in list_pat_project_ids if project_key in user_auth_project_list]
        logging.info(f"Final nbr of projects available to users : {len(user_project_list)}")
        
        
        tab_setting_display = [{'display': 'none'},  {'display': 'none'},  {'display': 'none'}]
        
        # Determine which input triggered the callback
        if not ctx.triggered or selected_tool == 'project':
            logging.info(f"Display layout for single PAT for project {selected_project}")
            
            if selected_project in list_pat_project_ids:
                project_metadata = next(proj for proj in list_pat_projects_enriched if selected_project in proj)
            else:
                project_metadata = None
            tab_setting_display[0] = {'display': 'block'}
            
            display = generate_layout_single_pat(selected_project, data)
            details = generate_project_details(selected_project, project_metadata, styles)

        elif selected_tool == 'batch':
            logging.info(f"Display layout for Batch PAT Report")
            batch_report_settings = {}
            
            batch_report_settings["project_ids"] = user_project_list
            batch_report_settings["status_filter"] = status_filter
            batch_report_settings["tag_filter"] = tag_filter
            tab_setting_display[1] = {'display': 'block'}
            display = generate_layout_batch_pat(batch_report_settings, data)
            details = generate_batch_details(batch_report_settings, data)
        
        elif selected_tool == 'instance':
            logging.info(f"Display layout for Instance PAT Report")
            tab_setting_display[2] = {'display': 'block'}
            display = generate_layout_instance_pat(list_pat_projects_enriched, data)
            details = generate_instance_details(list_pat_projects_enriched, data)
        
        else:
            logging.info("WARNING : selected_tool is not compatible")
            display = None
            details = dash.no_update
    
        return display, details, *tab_setting_display
    