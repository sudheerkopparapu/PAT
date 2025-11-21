# Components
from dash import dcc, html
import dash_table
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import json
import random
import copy
from typing import List, Union

from project_advisor.pat_logging import logger

from project_advisor.report.full_pat_report.config import configs
from project_advisor.report.full_pat_report.style import (styles, font_family, base_colors, severity_color_mapping)
from project_advisor.report.full_pat_report.tools import (format_md_links, truncate_text, truncate_text_in_object)

# Load constants
severity_name_mapping = configs["severity_name_mapping"]

# Helper explanation content
single_project_helper_content = dcc.Markdown('''
###### Severity Levels Guide

Each severity level represents the importance and potential impact of a given check, ranging from informational to critical requirements for deployment.

| Level | Name       | Summary |
|-------|------------|---------|
| 0     | **OK**     | Check passes. No issues. |
| 1     | **LOWEST** | Minor recommendation. No impact. |
| 2     | **LOW**    | Low risk. Might affect performance if ignored. |
| 3     | **MEDIUM** | Some performance impact. Should fix. |
| 4     | **HIGH**   | Serious performance risk. Not blocking. |
| 5     | **CRITICAL** | Must fix before deployment. Blocking issue. |

*Note : A project severity is be the highest severity level from all the checks ran on it*

###### Usage Recommendation

- You can deep dive in any checks with high severity in the **Check recommendations**.
- Teams should regularly review issues with severity levels **≥ 3** to maintain product stability and performance.
- While **LOWEST (1)** and **LOW (2)** may seem negligible, addressing them early promotes long-term code health and maintainability.
''', mathjax=True)


#####################################################
################# CHART HELPER TOOLS ################
#####################################################

def get_severity_name_to_color_mapping() -> dict:
    """
    Load config and style mappings to create a severity_name_to_color_mapping
    """
    severity_name_mapping = configs["severity_name_mapping"]
    return {severity_name_mapping[i]: color for i, color in severity_color_mapping.items() if i in severity_name_mapping}

def get_severity_icon(severity : int) -> dbc.Badge:
    """
    Return a standardized dash component representing the severity level.
    """
    return dbc.Badge(severity_name_mapping.get(severity, "NONE"),
                     color = severity_color_mapping.get(severity, "gray"), 
                     text_color= severity_color_mapping.get(severity, "gray"), 
                     className="me-1")


def format_name(name : str) -> str:
    """
    Unifed assessment name formatter.
    """
    name = name.replace("_", " ")
    name = name.replace("number", "#")
    name = name.replace("nbr", "#")
    name = name.title()
    return name

#####################################################
#################### CHARTS #########################
#####################################################

def display_severity_counts(df : pd.DataFrame) -> html.Div:
    """
    Display the severity counts for each level.
    input df columns : tags + [severities]
    """
    nbr_critical = df[5].iloc[0]
    nbr_high = df[4].iloc[0]
    nbr_medium = df[3].iloc[0]
    nbr_low = df[2].iloc[0]
    nbr_lowest = df[1].iloc[0]
    nbr_ok = df[0].iloc[0]
    nbr_not_applicable = df[-1].iloc[0] # Should be zero as filtered on data loading.
    
    severity_levels = []
    
    for severity in range(5, -1, -1):
        severity_levels.append(get_severity_icon(severity))
        severity_levels.append(f" {df[severity].iloc[0]}    ")
    
    return html.Div(severity_levels, style={"display": "inline-block"})
    

def severity_level_evolution(df : pd.DataFrame, 
                             title : str = "Evolution of severity over time", 
                             severity_col = "severity") -> px.bar:
    """
    Displays an evolution of the severity levels over time for a given set of historical severity levels
    input df columns : PAT Check report schema
    """
    logger.info(f"Building severity_level_evolution")
    df["severity_count"] = 1
    df = df.groupby(["timestamp", severity_col])['severity_count'].sum().reset_index()
    df.sort_values(["timestamp",severity_col], inplace = True)
    df[severity_col] = df[severity_col].map(severity_name_mapping)

    severity_name_to_color_mapping = get_severity_name_to_color_mapping()

    fig = px.bar(df, 
                 x="timestamp", 
                 y="severity_count", 
                 color=severity_col, 
                 color_discrete_map = severity_name_to_color_mapping,
                 title="")
    fig.update_layout(xaxis_type='category') # For equally space timestamps
    return fig


def severity_by_tag(df : pd.DataFrame) -> px.bar:
    """
    Build a horizontal stacked bar chart for severities by tags
    input df columns : tags + [severities] + count
    """
    logger.info(f"Building severity_by_tag")

    severity_levels = list(severity_name_mapping.keys())
    severity_levels.sort()
    max_count = df['count'].max()
    df = pd.melt(
        df,
        id_vars=['tags'],       # Columns to keep
        value_vars=severity_levels,  # Columns to melt
        var_name='severity_level',           # Name for the "key" column
        value_name='severity_count'          # Name for the "value" column
    )
    df["severity"] = df['severity_level'].map(severity_name_mapping)
    tags = df['tags'].unique()
    
    fig = px.bar(
        df, 
        x='severity_count', 
        y='tags', 
        orientation='h', 
        title=None,
        text='severity_count',  # Display project scores inside the bars
        color = "severity_level",
        color_discrete_map = severity_color_mapping,
    )

    fig.update_layout(
        xaxis=dict(
            title='Severity Levels', 
            showgrid=True, 
            gridcolor='LightGray', 
            range=[0, max_count], 
            showticklabels=False,  
            showticksuffix='none' 
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor='LightGray',
            tickvals=tags, 
            ticktext=[f'{tag} ' for tag in tags],  # Add space to the right of the category ticks
            title=''  
        ),
        plot_bgcolor='white',
        showlegend=False,
        font=dict(family=font_family, size=14),
        height=300,
        margin=dict(l=0, r=10, t=10, b=10),
        hovermode=False
    )
    return fig


def max_severity_by_tag_evolution(df : pd.DataFrame) -> px.line:
    """
    Build project score by category
    input df : [project/instance]_tag_severity_df 
    input df columns : timestamp + tags + [severity] + max_severity
    """
    logger.info(f"Build max_severity_by_tag_evolution")
    
    unique_levels = list(severity_name_mapping.keys())

    fig = px.line(df, x="timestamp", y="max_severity", color='tags', markers=True)
    fig.update_layout(
        yaxis=dict(
            showgrid=True, 
            gridcolor='LightGray',
            tickvals= unique_levels, 
            ticktext=[severity_name_mapping[l] for l in unique_levels],  # Add space to the right of the category ticks
            title=''  
        ),
        plot_bgcolor='white',
        font=dict(family=font_family, size=14),
        height=300,
        margin=dict(l=0, r=10, t=10, b=10),
    )
    return fig


def create_latest_severity_change_table(severity_change_df : pd.DataFrame) -> dash_table.DataTable:
    """
    Create severity_change_table
    Input columns : check_name, serverity_previous, severity_current, severity_change
    """
    logger.info(f"Building create_latest_severity_change_table")
    severity_change_df["severity_previous"] = severity_change_df["severity_previous"].map(severity_name_mapping)
    severity_change_df["severity_current"] = severity_change_df["severity_current"].map(severity_name_mapping)
    table_severity_change = dash_table.DataTable(
        columns=[{"name": format_name(i), "id": i} for i in severity_change_df.columns],
        data=severity_change_df.to_dict('records'),
        style_cell={'textAlign': 'left', 'padding': '5px', 'font-family': font_family},
        style_as_list_view=True,
        style_header={
            'backgroundColor': 'white',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {
                    'filter_query': '{severity_change} < 0'
                },
                'backgroundColor': 'lightgreen',
                'color': 'black'
            },
            {
                'if': {
                    'filter_query': '{severity_change} > 0'
                },
                'backgroundColor': 'lightcoral',
                'color': 'white'
            }
        ],
    )
    return table_severity_change


def create_check_reco_accordion(check_latest_df : pd.DataFrame, tag_severity_latest_df : pd.DataFrame) -> dbc.Accordion: 
    """
    Create check reco accordion (for project or instance)
    input df : [project/instance]_check_latest_df & [project/instance]_tag_severity_latest_df
    """
    logger.info(f"Building create_check_reco_accordion")
    
    #categories = check_reco_df.groupby('check_category')
    accordion_items = []
    for tag_idx, tag_row in tag_severity_latest_df.iterrows():
        
        max_severity = tag_row["max_severity"]
        tag_name = tag_row["tags"]

        # Add
        tag_header = html.Div([f"{format_name(tag_name).upper()}  ", # Adding space
                                         get_severity_icon(max_severity)]
                                        , style={"display": "inline-block"})


        # Create a list of individual checks within the category
        checks = []
        for _, check_row in check_latest_df.iterrows():
            if tag_name in check_row['tags']:
                check_severity = check_row['severity']
                check_name = check_row['check_name']
                check_message = check_row['message']
                check_message_truncated = check_message
                try:
                    check_result = json.loads(check_row['result_data'])
                except:
                    check_result = {
                        "description" : "Error loading description",
                        "run_result" : "Error loading the run_result"
                    }
                run_result_truncated = truncate_text_in_object(check_result['run_result'], cut_indicator = "...See dataset report for more info.")
                # Add icon for category severity
                check_header = html.Div([f"{format_name(check_name)}  ", # Adding space
                                         get_severity_icon(check_severity)]
                                        , style={"display": "inline-block"})
                
                check_style = {
                    'color': 'black',
                    'padding': '10px',
                    'border': '1px solid #ddd'
                }
           
                # If the check failed, display it with the recommendation
                check_content = html.Div([
                        html.P(f"Description: {check_result['description']}") if check_result['description'] else None,
                        html.P(recursive_pretty_print(f"Message: {check_message_truncated}")) if check_message else None,
                        html.P(f"Additional details:") if check_severity > 0 else None,
                        html.P(recursive_pretty_print(run_result_truncated)) if check_severity > 0  else None,
                    ], 
                    style=check_style
                )

                checks.append(dbc.AccordionItem(
                    check_content,
                    title=check_header,
                    item_id=f"check-{check_name}",
                    style=check_style,
                ))

        # Add category as an accordion item
        accordion_items.append(dbc.AccordionItem(
            checks,
            title=tag_header,
            item_id=f"tag_name-{tag_name}"
        ))
    return dbc.Accordion(
        accordion_items,
        always_open=True, # Keep accordion categories open to see checks easily
        flush=True,
        start_collapsed=True
    )



def recursive_pretty_print(data : Union[str, dict], path : list = []):
    """
    Attempt to display a dict with html best effort.
    """
    res = []
    if isinstance(data , dict):
        for key in data.keys():
            path_copy = copy.deepcopy(path)
            path_copy.append(key)
            res.extend(recursive_pretty_print( data[key], path_copy))
    else:
        data_str = str(data)
        path_str = ""
        break_str = ""
        if len(path)>0:
            path_str = f"{' / '.join(path)} : "
            break_str = "<br>"

        if isinstance(data, str):
            data_str = data_str.replace("\n", "<br>")
            data_str = format_md_links(data_str)
            res.append(html.Div(
                            dcc.Markdown(f"{path_str}{break_str}{data_str}", 
                                         dangerously_allow_html = True,  
                                         link_target="_blank"
                                        )
                            )
                      )
        else:
            res.append(html.P(f"{path_str}{data_str}"))
    return res 


def build_hist_card(metric_name : str, df: pd.DataFrame) -> dbc.Card:
    """
    Build a hist card fora metric
    """
    logger.debug(f"building histogram for metric : {metric_name}")
    fig = px.histogram(df, 
                       x="metric_value", 
                       labels= {"metric_value" : format_name(metric_name)},
                       width= 500, 
                       height= 300,
                       )
    fig.update_layout(yaxis_title="project count") 
    fig.update_layout(bargap=0.1)


    return dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4(format_name(metric_name), className="card-title"),
                            html.Div(
                                dcc.Graph(figure=fig)
                            )    
                        ],
                        style = {"text-align": "center"}
                    ),
                ],
                style={
                        "width": "36rem",
                        "height": "25rem",
                        "margin-left": "10px",
                        "margin-top" : "10px",
                        "display" :"inline-block",
                        "vertical-align": "top"
                      },
)

def build_agg_metric_card(metric_name : str, metric_value :int) -> dbc.Card:
    """
    build_agg_metric_card
    """
    logger.info(f"Building numerical metrics card for metric : {metric_name}")
    return dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4(format_name(metric_name), className="card-title"),
                            html.Div(
                                html.H1(
                                    metric_value,
                                    className="card-text"
                                    )
                            )    
                        ],
                        style = {"text-align": "center"}
                   ),
                ],
                style={ "width": "18rem",
                        "height": "10rem",
                        "margin-left": "10px",
                        "margin-top" : "10px",
                        "display" :"inline-block",
                        "vertical-align": "top"
                      },
)

def build_severities_by_tag_cards(df: pd.DataFrame) -> List[dbc.Card]:
    """
    df input : filtered project_tag_severity_latest_df
    """
    logger.info(f"Building build_severities_by_tag_cards")

    df = df.reset_index() 
    df = pd.melt(
        df,
        id_vars=['tags'],       # Columns to keep
        value_vars=[-1, 0,1,2,4,5],  # Columns to melt
        var_name='severity_level',           # Name for the "key" column
        value_name='severity_count'          # Name for the "value" column
    )
    df = df.groupby(['tags', 'severity_level'], as_index=False)['severity_count'].sum()
    df = df[df["severity_count"] >0]
    df["severity"] = df['severity_level'].map(severity_name_mapping)
  
    tag_severities_cards = []
    for tag in set(df["tags"]):   
        fig = px.pie(df[df["tags"] == tag], 
                 names = "severity",
                 values = "severity_count",
                 color = 'severity_level',
                 color_discrete_map= severity_color_mapping,
                 width= 250, 
                 height= 250,
                )
        fig.update_layout(showlegend=False,
                          uniformtext_minsize=10, 
                          uniformtext_mode='hide')
        
        tag_severities_cards.append(
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            html.H4(tag, className="card-title"),
                            html.Div(
                                dcc.Graph(figure=fig)
                            )    
                        ],style = {"text-align": "center"}
                    ),
                ],
                style={
                        "width": "20rem",
                        "height": "20rem",
                        "margin-left": "10px",
                        "margin-top" : "10px",
                        "display" :"inline-block",
                        "vertical-align": "top"
                     },
            )
        )
    return tag_severities_cards

def generate_metric_cards(df_metrics : pd.DataFrame) -> List[dbc.Card]:
    """
    Building generic metric cards
    """
    logger.info(f"Building generic metric cards")
    
    cards_per_row = 6
    rows = []

    # Split the dataframe into chunks of 5 rows
    for i in range(0, len(df_metrics), cards_per_row):
        row_cards = []

        for _, metric in df_metrics.iloc[i:i + cards_per_row].iterrows():
            metric_value = str(int(float(metric['metric_value']))) if metric['metric_type'] == 'INT' else metric['metric_value']
            metric_metadata = json.loads(metric['result_data'])
            metric_unit = metric_metadata.get("metric_unit")
            
            # Case where metric has a unit
            if metric_unit:
                metric_value = f"{metric_value} {metric_unit}"
            
            card = dbc.Card([
                dbc.CardHeader(f"{metric['metric_name'].replace('_', ' ').replace('nbr', '#').replace('percentage', '%').capitalize()}", 
                               style={"height": "70px", 'display': 'flex', "align-items": "center", 'justify-content': 'center', 'overflow': 'hidden', "font-size": "14px", 'white-space': 'wrap', 'text-overflow': 'ellipsis'}),
                dbc.CardBody(
                    [
                        html.H3(f"{metric_value}", className="card-title") ,
                        html.P(f"{metric_metadata['description'].replace('.','')}", className="card-text", style={"font-size": "12px"}),
                    ]
                )],
                style={"height": "100%", "text-align": "center"},
            )
            row_cards.append(dbc.Col(card, width=12 // cards_per_row))  # 2 units width to fit 6 cards in a row

        # Add the row to the list of rows
        rows.append(dbc.Row(row_cards, justify="start", style={"margin-bottom": "20px"}))

    return rows


def metric_evolution(df : pd.DataFrame) -> go.Figure:
    """
    Building metric evolution
    """
    logger.info(f"Building metric evolution")
    
    fig = go.Figure()

    metric_name = df['metric_name'].unique()

    # Define color palette for the categories (you can expand the palette as needed)
    colors = generate_colors(len(metric_name))

    # Loop over each unique category to create a separate line for each
    for i, metric in enumerate(metric_name):
        metric_data = df[df['metric_name'] == metric]
        
        # Add a line trace for the current category
        fig.add_trace(go.Scatter(
            x=metric_data['timestamp'],  
            y=metric_data['metric_value'], 
            mode='lines+markers',  
            name=metric.replace("nbr", "#").replace("_", " ").replace("percentage", "%").capitalize(), 
            line=dict(color=colors[i % len(colors)], width=3), 
            marker=dict(size=7) 
        ))

    # Update the layout of the chart with titles, gridlines, and overall design
    fig.update_layout(
        title=None,
        xaxis=dict(title=None, showgrid=True, gridcolor='LightGray', tickformat='%b %d, %Y\n%H:%M:%S'),
        yaxis=dict(title='Metric value', showgrid=True, gridcolor='LightGray'),
        plot_bgcolor='white',  
        legend=dict(
                font=dict(
                    size=12 
                )
            ),
        hovermode='x unified',  
        showlegend=True,  
        height=300,
        font=dict(family=font_family, size=14),
        margin=dict(l=10, r=10, t=10, b=10)
    )

    # Add hover template for better readability
    fig.update_traces(
        hovertemplate='Date: %{x}<br>Metric value: %{y}', 
        selector=dict(type='scatter')  
    )

    return fig
            
    
def generate_colors(num_categories):
    """
    If number of categories is less than or equal to the number of base colors, just return the base colors
    """
    if num_categories <= len(base_colors):
        return base_colors[:num_categories]
    
    # If number of categories exceeds base colors, generate more colors by randomizing shades
    generated_colors = base_colors.copy()
    while len(generated_colors) < num_categories:
        # Randomly lighten or darken an existing color slightly to create more variety
        new_color = random.choice(base_colors)
        # Modify the color a little bit to create a variation (change brightness or saturation)
        # Adjust the RGB values slightly
        new_color_variation = lighten_or_darken_color(new_color, random.uniform(-0.2, 0.2))
        generated_colors.append(new_color_variation)
    
    return generated_colors[:num_categories]


# Helper function to lighten or darken a color
def lighten_or_darken_color(color, factor):
    # Convert hex color to RGB
    color = color.lstrip('#')
    r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
    
    # Adjust the color by factor (-1 to 1 where negative darkens, positive lightens)
    r = int(max(min(r * (1 + factor), 255), 0))
    g = int(max(min(g * (1 + factor), 255), 0))
    b = int(max(min(b * (1 + factor), 255), 0))
    
    # Convert back to hex
    return f'#{r:02x}{g:02x}{b:02x}'






