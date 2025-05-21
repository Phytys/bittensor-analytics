from dash import Dash, Input, Output, State, html, no_update, callback_context
import dash_bootstrap_components as dbc
from app.dash_app.layout import get_layout
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_dashboard(server):
    """Initialize the Dash app and mount it to the Flask server."""
    app = Dash(
        __name__,
        server=server,
        url_base_pathname="/dashboard/",
        use_pages=True,
        pages_folder="pages",  # Changed to relative path
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,
            # Add custom CSS for Tesla-inspired styling
            {
                'href': 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap',
                'rel': 'stylesheet'
            }
        ],
        suppress_callback_exceptions=True
    )

    # Set app title
    app.title = "Bittensor Analytics"

    # Apply the layout
    app.layout = get_layout()

    # Add callback for sidebar toggle
    @app.callback(
        Output("sidebar", "style"),
        Output("page-content", "style"),
        Output("sidebar-state", "data"),
        Output("sidebar-backdrop", "style"),
        Input("sidebar-toggle", "n_clicks"),
        Input("sidebar-backdrop", "n_clicks"),
        State("sidebar-state", "data"),
        prevent_initial_call=True
    )
    def toggle_sidebar(n_clicks, backdrop_clicks, sidebar_state):
        logger.debug(f"Toggle callback triggered. n_clicks: {n_clicks}, backdrop_clicks: {backdrop_clicks}, sidebar_state: {sidebar_state}")
        
        if n_clicks is None and backdrop_clicks is None:
            logger.debug("No clicks detected, returning no_update")
            return no_update, no_update, no_update, no_update
        
        try:
            is_open = not sidebar_state.get('is_open', False)
            logger.debug(f"Toggling sidebar. New state: {is_open}")
            
            sidebar_style = {
                'position': 'fixed',
                'top': 0,
                'left': 0,
                'bottom': 0,
                'width': '250px',
                'backgroundColor': '#111',
                'padding': '20px',
                'zIndex': '1000',
                'transform': 'translateX(0)',
                'transition': 'transform 0.3s ease-in-out'
            }
            
            content_style = {
                'marginLeft': '250px',
                'padding': '20px',
                'transition': 'margin-left 0.3s ease-in-out',
                'position': 'relative',
                'zIndex': '1'
            }
            
            backdrop_style = {
                'position': 'fixed',
                'top': 0,
                'left': 0,
                'right': 0,
                'bottom': 0,
                'backgroundColor': 'rgba(0, 0, 0, 0.5)',
                'zIndex': '999',
                'display': 'block',
                'transition': 'opacity 0.3s ease-in-out'
            }
            
            if not is_open:
                sidebar_style['transform'] = 'translateX(-250px)'
                content_style['marginLeft'] = '0'
                backdrop_style['display'] = 'none'
            
            return sidebar_style, content_style, {'is_open': is_open}, backdrop_style
        except Exception as e:
            logger.error(f"Error in toggle_sidebar: {str(e)}")
            return no_update, no_update, no_update, no_update

    # Add custom CSS for responsive design
    app.index_string = '''
    <!DOCTYPE html>
    <html>
        <head>
            {%metas%}
            <title>{%title%}</title>
            {%favicon%}
            {%css%}
            <style>
                /* Mobile styles */
                @media (max-width: 768px) {
                    #sidebar {
                        transform: translateX(-250px);
                    }
                    #page-content {
                        margin-left: 0 !important;
                    }
                    #sidebar-toggle {
                        display: block !important;
                        opacity: 1 !important;
                        visibility: visible !important;
                    }
                }
                
                /* Desktop styles */
                @media (min-width: 769px) {
                    #sidebar {
                        transform: translateX(0) !important;
                    }
                    #sidebar-toggle {
                        display: none !important;
                    }
                    #sidebar-backdrop {
                        display: none !important;
                    }
                    #page-content {
                        margin-left: 250px !important;
                    }
                }
                
                /* General styles */
                body {
                    font-family: 'Inter', sans-serif;
                    overflow-x: hidden;
                }
                
                .nav-link {
                    color: rgba(255, 255, 255, 0.8) !important;
                    transition: color 0.3s ease;
                }
                
                .nav-link:hover {
                    color: white !important;
                }
                
                .nav-link.active {
                    color: white !important;
                    background-color: rgba(255, 255, 255, 0.1) !important;
                }

                #sidebar-toggle {
                    transition: opacity 0.3s ease;
                }

                #sidebar-toggle:hover {
                    opacity: 0.8;
                }

                #sidebar {
                    will-change: transform;
                }

                #page-content {
                    will-change: margin-left;
                }

                #sidebar-backdrop {
                    will-change: opacity;
                }

                /* Ensure content is above the background but below the sidebar */
                .dash-table-container,
                .js-plotly-plot {
                    position: relative;
                    z-index: 1;
                }
            </style>
        </head>
        <body>
            {%app_entry%}
            <footer>
                {%config%}
                {%scripts%}
                {%renderer%}
            </footer>
        </body>
    </html>
    '''

    return app 