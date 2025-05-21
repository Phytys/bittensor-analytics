import dash
from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
from app.subnet_metrics import load_latest_apy_df, load_all_validator_apy_df
import pandas as pd
import plotly.express as px
from app import cache

# Register the page
dash.register_page(
    __name__,
    path="/fundamentals",  # This makes it available at /dashboard/fundamentals
    name="Subnet Metrics",
    title="Subnet Metrics"
)

@cache.memoize(timeout=600)  # Cache for 10 minutes
def get_fundamentals_data():
    """Load and cache the latest APY data."""
    return load_latest_apy_df()

def get_validator_apy_df():
    records = get_fundamentals_data()
    rows = []
    for r in records:
        netuid = r['netuid']
        recorded_at = r['recorded_at']
        # If you have access to the validator_apys list:
        for v in r.get('validator_apys', []):
            if v.get('alpha_apy') is not None:
                rows.append({
                    'netuid': netuid,
                    'recorded_at': recorded_at,
                    'alpha_apy': float(v['alpha_apy'])
                })
    return pd.DataFrame(rows)

def layout():
    df = get_fundamentals_data()
    
    if df.empty:
        return html.Div([
            html.H1("Subnet Metrics", className="mb-4"),
            dbc.Alert(
                "No metrics data available. Please wait for data collection to complete.",
                color="warning",
                className="mt-3"
            )
        ])

    # Filter out extreme APY values
    apy_col = 'mean_apy'
    apy_threshold = 500
    filtered_df = df[df[apy_col] < apy_threshold].copy()
    filtered_out = df[df[apy_col] >= apy_threshold]
    filtered_subnets = filtered_out['netuid'].tolist()

    # Tagline for the whole page
    page_tagline = html.Div(
        "This dashboard reveals how intelligence is rewarded across Bittensor's subnets. "
        "We show where validators thrive — and where incentives break down.",
        style={
            "backgroundColor": "#f3e5f5",
            "padding": "12px 18px",
            "marginBottom": "10px",
            "borderLeft": "5px solid #8e24aa",
            "color": "#4a148c",
            "fontWeight": "500",
        }
    )

    # Tagline for the chart
    chart_tagline = html.Div(
        "Boxplot shows the range of APY (Annual Percentage Yield) earned by validators in each subnet. "
        "APY reflects the annualized return for staking with a validator. Wider boxes mean more variation in rewards among validators within a subnet. "
        "You can zoom and pan on the graph for a closer look.",
        style={
            "color": "#1976d2",
            "fontWeight": "500",
            "marginBottom": "8px",
            "fontSize": "1.05rem"
        }
    )

    return html.Div([
        html.H1("Subnet Metrics", className="mb-4"),
        page_tagline,
        html.Hr(style={"margin": "18px 0 18px 0", "borderTop": "2px solid #e0e0e0"}),
        dcc.Checklist(
            options=[{"label": "Log scale y-axis", "value": "log"}],
            value=[],
            id="log-scale-toggle",
            style={"marginBottom": "10px"}
        ),
        chart_tagline,
        dcc.Loading(
            type='circle',
            children=html.Div([
                html.H3("📦 Placeholder"),
                dcc.Graph(id='apy-boxplot'),
            ])
        ),
        html.Div(
            f"Filtered out {len(filtered_subnets)} subnet(s) with mean APY >= {apy_threshold}%: {filtered_subnets if filtered_subnets else 'None'}",
            style={
                "backgroundColor": "#fff3cd",
                "color": "#856404",
                "padding": "10px 16px",
                "marginTop": "10px",
                "borderLeft": "5px solid #ffe082",
                "fontSize": "0.98rem"
            }
        ),
        dbc.Alert(
            "Data is fetched periodically and stored in the database. This table shows the latest cached values.",
            color="info",
            className="mb-4"
        ),
        dbc.Card([
            dbc.CardBody([
                dash_table.DataTable(
                    columns=[{"name": col, "id": col} for col in df.columns],
                    data=df.to_dict("records"),
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
                            'if': {'column_id': 'mean_apy', 'filter_query': '{mean_apy} > 100'},
                            'backgroundColor': '#ffcdd2',  # Light red
                            'color': 'black'
                        },
                        {
                            'if': {'column_id': 'std_apy', 'filter_query': '{std_apy} > 30'},
                            'backgroundColor': '#fff9c4',  # Light yellow
                            'color': 'black'
                        }
                    ],
                    page_size=20,
                )
            ])
        ])
    ])

# Dash callback for log scale toggle and boxplot
dash.callback(
    dash.Output('apy-boxplot', 'figure'),
    dash.Input('log-scale-toggle', 'value')
)(
    lambda log_value: _build_apy_boxplot(log_value)
)

def _build_apy_boxplot(log_value):
    df = load_all_validator_apy_df()
    apy_threshold = 500
    # Remove zero APY rows
    df = df[df['alpha_apy'] > 0]
    # Only keep subnets with at least one nonzero APY
    valid_subnets = df['netuid'].unique()
    filtered_df = df[(df['alpha_apy'] < apy_threshold) & (df['netuid'].isin(valid_subnets))].copy()
    fig = px.box(
        filtered_df,
        x='netuid',
        y='alpha_apy',
        points='all',
        title='Validator APY Distribution by Subnet',
        labels={
            'netuid': 'Subnet ID',
            'alpha_apy': 'Validator APY (%)',
        },
        template='plotly_white',
        log_y='log' in log_value,
    )
    fig.update_layout(height=600, margin=dict(t=50, b=40, l=50, r=50))
    return fig 