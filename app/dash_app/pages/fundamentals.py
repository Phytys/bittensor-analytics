import dash
from dash import html, dash_table
import dash_bootstrap_components as dbc
from app.fundamentals import load_latest_apy_df
import pandas as pd
from app import cache

# Register the page
dash.register_page(
    __name__,
    path="/fundamentals",  # This makes it available at /dashboard/fundamentals
    name="Fundamentals",
    title="Fundamentals"
)

@cache.memoize(timeout=600)  # Cache for 10 minutes
def get_fundamentals_data():
    """Load and cache the latest APY data."""
    return load_latest_apy_df()

def layout():
    df = get_fundamentals_data()
    
    if df.empty:
        return html.Div([
            html.H1("Subnet Fundamentals", className="mb-4"),
            dbc.Alert(
                "No fundamentals data available. Please wait for data collection to complete.",
                color="warning",
                className="mt-3"
            )
        ])
    
    # Select and rename columns for display
    display_cols = {
        'netuid': 'Subnet ID',
        'validator_count': 'Validators',
        'min_apy': 'Min APY (%)',
        'max_apy': 'Max APY (%)',
        'mean_apy': 'Mean APY (%)',
        'median_apy': 'Median APY (%)',
        'std_apy': 'Std Dev (%)',
        'recorded_at': 'Last Updated'
    }
    
    df_display = df[display_cols.keys()].copy()
    df_display.columns = display_cols.values()
    
    # Format datetime
    df_display['Last Updated'] = pd.to_datetime(df_display['Last Updated']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Sort by Mean APY
    df_display = df_display.sort_values('Mean APY (%)', ascending=False)
    
    return html.Div([
        html.H1("Subnet Fundamentals", className="mb-4"),
        
        # Info alert
        dbc.Alert(
            "Data is fetched periodically and stored in the database. This table shows the latest cached values.",
            color="info",
            className="mb-4"
        ),
        
        # APY table in a card
        dbc.Card([
            dbc.CardBody([
                dash_table.DataTable(
                    columns=[{"name": col, "id": col} for col in df_display.columns],
                    data=df_display.to_dict("records"),
                    sort_action="native",
                    filter_action="native",
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "textAlign": "left",
                        "padding": "10px",
                        "whiteSpace": "normal",
                        "height": "auto"
                    },
                    style_header={
                        "backgroundColor": "#111",
                        "color": "white",
                        "fontWeight": "bold"
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        },
                        {
                            'if': {'column_id': 'Mean APY (%)', 'filter_query': '{Mean APY (%)} > 100'},
                            'backgroundColor': '#ffcdd2',  # Light red
                            'color': 'black'
                        },
                        {
                            'if': {'column_id': 'Std Dev (%)', 'filter_query': '{Std Dev (%)} > 30'},
                            'backgroundColor': '#fff9c4',  # Light yellow
                            'color': 'black'
                        }
                    ],
                    page_size=20,
                )
            ])
        ])
    ]) 