import dash
from dash import html, dcc, page_container
import dash_bootstrap_components as dbc

def get_layout():
    # Tesla-inspired dark theme colors
    SIDEBAR_STYLE = {
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "250px",
        "padding": "2rem 1rem",
        "background-color": "#111",
        "color": "white",
        "z-index": "1000",
        "transition": "transform 0.3s ease-in-out",
        "transform": "translateX(-250px)"  # Start hidden on mobile
    }

    CONTENT_STYLE = {
        "margin-left": "0",  # Start with no margin on mobile
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
        "min-height": "100vh",
        "transition": "margin-left 0.3s ease-in-out",
        "position": "relative",  # Add relative positioning
        "z-index": "1"  # Lower z-index than sidebar
    }

    # Backdrop for mobile
    backdrop = html.Div(
        id="sidebar-backdrop",
        style={
            "position": "fixed",
            "top": 0,
            "left": 0,
            "right": 0,
            "bottom": 0,
            "backgroundColor": "rgba(0, 0, 0, 0.5)",
            "zIndex": "999",
            "display": "none",
            "transition": "opacity 0.3s ease-in-out"
        }
    )

    # Mobile navigation toggle
    toggle_button = dbc.Button(
        html.I(className="fas fa-bars"),
        id="sidebar-toggle",
        color="dark",
        className="d-md-none",
        style={
            'position': 'fixed',
            'top': '10px',
            'left': '10px',
            'zIndex': '1001',
            'backgroundColor': '#111',
            'color': 'white',
            'border': 'none',
            'padding': '10px 15px',
            'borderRadius': '5px',
            'cursor': 'pointer',
            'display': 'none'  # Hidden by default, shown on mobile
        }
    )

    # Sidebar with Tesla-inspired styling
    sidebar = html.Div(
        [
            html.H2("Bittensor", className="display-6", style={"color": "white", "padding": "1rem"}),
            html.Hr(style={"border-color": "#333"}),
            html.Nav([
                dcc.Link(
                    "Overview",
                    href="/dashboard/",
                    className="nav-link",
                    style={"color": "white", "padding": "0.5rem 1rem", "margin": "0.2rem 0"}
                ),
                dcc.Link(
                    "Fundamentals",
                    href="/dashboard/fundamentals",
                    className="nav-link",
                    style={"color": "white", "padding": "0.5rem 1rem", "margin": "0.2rem 0"}
                ),
            ], className="nav flex-column"),
        ],
        style=SIDEBAR_STYLE,
        id="sidebar"
    )

    # Main content area
    content = html.Div(
        children=[page_container],
        style=CONTENT_STYLE,
        id="page-content"
    )

    # Store for tracking sidebar state
    sidebar_state_store = dcc.Store(id='sidebar-state', data={'is_open': False})  # Start closed on mobile

    # Add Font Awesome for icons
    font_awesome_link = html.Link(
        rel="stylesheet",
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"
    )

    return html.Div([
        dcc.Location(id="url"),
        backdrop,
        toggle_button,
        sidebar,
        content,
        sidebar_state_store,
        font_awesome_link
    ]) 