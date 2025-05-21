import dash
from dash import html, dcc, dash_table, Input, Output
import plotly.express as px
import pandas as pd
from app.utils import fetch_combined_subnet_data
from app.logic import compute_basic_subnet_score
import dash_bootstrap_components as dbc
from app import cache

# Register the page
dash.register_page(
    __name__,
    path="/",  # This makes it the default page at /dashboard/
    name="Overview",
    title="Overview"
)

def layout():
    return html.Div([
        html.H1("Subnet Overview", className="mb-4"),
        
        # Metric selector in a card
        dbc.Card([
            dbc.CardBody([
                html.Label("Select metric to visualize:", className="mb-2"),
                dcc.Dropdown(
                    id='metric-selector',
                    options=[
                        {'label': 'Score', 'value': 'score'},
                        {'label': 'TAO In', 'value': 'tao_in_screener'},
                        {'label': 'Market Cap (TAO)', 'value': 'market_cap_tao'},
                        {'label': '7d Price % Change', 'value': 'price_7d_pct_change'}
                    ],
                    value='score',
                    style={'width': '100%'}
                )
            ])
        ], className="mb-4"),
        
        # Bar chart in a card
        dbc.Card([
            dbc.CardBody([
                dcc.Graph(id='subnet-bar-chart')
            ])
        ], className="mb-4"),
        
        # Data table in a card
        dbc.Card([
            dbc.CardBody([
                html.H2("Subnet Table", className="h4 mb-3"),
                dash_table.DataTable(
                    id='subnet-table',
                    columns=[],
                    data=[],
                    sort_action='native',
                    filter_action='native',
                    page_size=15,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'whiteSpace': 'normal',
                        'height': 'auto'
                    },
                    style_header={
                        'backgroundColor': '#111',
                        'color': 'white',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        }
                    ]
                )
            ])
        ])
    ])

@dash.callback(
    Output('subnet-bar-chart', 'figure'),
    Output('subnet-table', 'columns'),
    Output('subnet-table', 'data'),
    Input('metric-selector', 'value')
)
@cache.memoize(timeout=600)  # Cache for 10 minutes
def update_dashboard(selected_metric):
    df = fetch_combined_subnet_data()
    df = compute_basic_subnet_score(df)
    df_sorted = df.sort_values(by=selected_metric, ascending=False)
    
    # Create bar chart with Tesla-inspired styling
    fig = px.bar(
        df_sorted.head(15),
        x='subnet_name_screener',
        y=selected_metric,
        title=f"Top 15 Subnets by {selected_metric.replace('_', ' ').title()}",
        labels={
            'subnet_name_screener': 'Subnet',
            selected_metric: selected_metric.replace('_', ' ').title()
        },
        hover_data=['netuid', 'market_cap_tao', 'alpha_circ', 'price_screener', 'score']
    )
    
    # Update layout for Tesla-inspired styling
    fig.update_layout(
        template='plotly_white',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Inter, sans-serif"),
        title_font=dict(size=20),
        xaxis=dict(
            title_font=dict(size=14),
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            title_font=dict(size=14),
            tickfont=dict(size=12)
        ),
        margin=dict(t=60, l=60, r=30, b=60)
    )
    
    # Update bar colors
    fig.update_traces(
        marker_color='#111',
        marker_line_color='#111',
        marker_line_width=1.5,
        opacity=0.8
    )
    
    # Prepare table data
    table_columns = [{"name": col, "id": col} for col in df_sorted.columns]
    table_data = df_sorted.to_dict("records")
    
    return fig, table_columns, table_data 