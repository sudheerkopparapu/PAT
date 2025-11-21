# style.py

# Base color palette for charts
base_colors = ['#4578fc', '#f35b05', '#00b257', '#becaf9', "#dfd1eb", "#b8e7ba", "#fccd20"]

severity_color_mapping = {
    5: "#C3B1E1",     # Pastel Purple
    4: "#f4978e",     # Pastel Red
    3: "#fec89a",     # Pastel Orange
    2: "#FFD700",     # Gold
    1: "#bde0fe",     # Pastel Blue
    0: "#9ACD32",     # Light Green
    -1: "#A9A9A9"     # DarkGray
}

# font family
font_family = "Source Sans Pro"

# Define base colors and font family
css_colors = {
    "background_color": "#f0f3f6",
    "sidebar_bg": "#221c35",
    "sidebar_header_bg": "#7dbeea",
    "sidebar_details_bg": "#343a40",
    "top_bar_bg": "white",
    "card_bg": "white",
    "footer_border": "#d1d8e0"
}

styles = {
    "page_style": {
        "font-family": font_family,
        "background-color": css_colors["background_color"],
        "padding": "0px",
        "height": "100vh",
        "max-width": "100%"
    },
    "sidebar_container": {
        "background-color": css_colors["sidebar_bg"], 
        "padding": 0,
        "position": "fixed",
        "top": 0,
        "left": 0,
        "z-index": "999",
        "width": "400px",
        "height": "100vh",
        "boxShadow": "2px 0 5px rgba(0, 0, 0, 0.3)"
    },
    "sidebar_content": {
        "height": "100vh",
        "padding": "30px"
    },
    "sidebar_header": {
        "color": "white", 
        "padding": "15px 30px",
        "font-size": "22px",
        "backgroundColor": css_colors["sidebar_header_bg"]
    },
    "sidebar_project_details": {
        "padding": "20px", 
        "background-color": css_colors["sidebar_details_bg"], 
        "border-radius": "8px",
        "overflow": "hidden",
        "text-overflow": "ellipsis",
        "white-space": "normal",
        "word-wrap": "break-word"
    },
    "sidebar_footer": {
        "padding": "20px",
        "color": "white",
        "position": "absolute",
        "bottom": "0px",
        "width": "100%",
        "display": "flex",
        "justify-content": "center",
        "text-align": "center"
    },
    "footer_content": {
        "border-top": f"1px solid {css_colors['footer_border']}",
        "color": "#fff",
        "padding": "30px",
        "width": "90%"
    },
    "dropdown_style": {
        "backgroundColor": css_colors["background_color"],
        "borderRadius": "5px",
    },
    "top_white_bar": {
        "background-color": css_colors["top_bar_bg"],
        "height": "56.39px",
        "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
        "position": "fixed",
        "top": "0",
        "left": "400px",
        "width": "calc(100% - 400px)",
        "z-index": "1000"
    },
    "content_container": {
        "margin-top": "56.39px",
        "margin-left": "400px",
        "background-color": css_colors["background_color"],
        "height": "calc(100vh - 56.39px)",
        "width": "calc(100% - 400px)",
        "overflow-x": "hidden",
        "position": "relative"
    },
    "content_page_row": {
        "--bs-gutter-x": 0,
        "margin-left": 0,
        "margin-right": 0
    },
    "content_page": {
        "margin": "20px"
    },
    "content_card": {
        "backgroundColor": css_colors["card_bg"],
        "width": "250px",
        "height": "250px",
        "borderRadius": "8px",
        "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
        "padding": "20px",
        "align-content": "center",
        "text-align": "-webkit-center"
    },
    "homepage_single_pat": {
        "backgroundColor": "#f7f9fa",
        "borderRadius": "8px",
        "font-size": "25px",
        "text-align": "center",
        "padding": "70px",
        "width": "fit-content"
    },
    "div_homepage_single_pat": {
        "height": "100vh", 
        "text-align": "-webkit-center", 
        "align-content": "center"
    },
    "colors" : {
        "GREEN" : "#ACE1AF",
        "YELLOW" : "#FFFF00",
        "RED" : "#fd5c63",
        "GRAY" : "#D3D3D3"
    }
}
