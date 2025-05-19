from dash import Dash, html, dcc, dash_table, Input, Output
import plotly.express as px
import pandas as pd
from app.logic import compute_basic_subnet_score
from app.utils import fetch_combined_subnet_data, load_latest_apy_df
from app.config import CACHE_DEFAULT_TIMEOUT

def init_dashboard(server, cache):
    app = Dash(
        __name__,
        server=server,
        url_base_pathname='/dashboard/',
        suppress_callback_exceptions=True
    )

    app.title = "Subnet Dashboard"

    @cache.memoize(timeout=CACHE_DEFAULT_TIMEOUT)
    def load_subnet_data():
        df = fetch_combined_subnet_data()
        df = compute_basic_subnet_score(df)
        return df

    @cache.memoize(timeout=CACHE_DEFAULT_TIMEOUT)
    def load_fundamentals_data():
        """Load and cache the latest APY data."""
        return load_latest_apy_df()

    def render_overview_tab():
        return html.Div([
            html.Div([
                html.Label("Select metric to visualize:"),
                dcc.Dropdown(
                    id='metric-selector',
                    options=[
                        {'label': 'Score', 'value': 'score'},
                        {'label': 'TAO In', 'value': 'tao_in_screener'},
                        {'label': 'Market Cap (TAO)', 'value': 'market_cap_tao'},
                        {'label': '7d Price % Change', 'value': 'price_7d_pct_change'}
                    ],
                    value='score',
                    style={'width': '300px'}
                )
            ], style={'padding': '20px'}),
            dcc.Graph(id='subnet-bar-chart'),
            html.H2("Subnet Table"),
            dash_table.DataTable(
                id='subnet-table',
                columns=[],
                data=[],
                sort_action='native',
                filter_action='native',
                page_size=15,
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '5px'},
                style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
            )
        ])

    def render_fundamentals_tab():
        df = load_fundamentals_data()  # Use cached version
        
        if df.empty:
            return html.Div([
                html.H3("Subnet Fundamentals – Alpha APY"),
                html.P("No fundamentals data available. Please wait for data collection to complete.")
            ])
        
        # Select and rename columns for display
        display_cols = {
            'netuid': 'Subnet ID',
            'apy': 'Subnet APY (%)',
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
            html.H3("Subnet Fundamentals – Alpha APY"),
            html.P(
                "Data is fetched periodically and stored in the database. This table shows the latest cached values.",
                style={'fontStyle': 'italic', 'color': 'gray'}
            ),
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
                    "backgroundColor": "lightgrey",
                    "fontWeight": "bold",
                    "textAlign": "center"
                },
                style_data_conditional=[
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

    app.layout = html.Div([
        html.H1("Bittensor Subnet Analytics", style={"textAlign": "center"}),
        dcc.Tabs(id="tabs", value="overview", children=[
            dcc.Tab(label="Overview", value="overview"),
            dcc.Tab(label="Fundamentals", value="fundamentals")
        ]),
        html.Div(id="tab-content")
    ])

    @app.callback(
        Output("tab-content", "children"),
        Input("tabs", "value")
    )
    def render_tab_content(tab):
        if tab == "overview":
            return render_overview_tab()
        elif tab == "fundamentals":
            return render_fundamentals_tab()

    @app.callback(
        Output('subnet-bar-chart', 'figure'),
        Output('subnet-table', 'columns'),
        Output('subnet-table', 'data'),
        Input('metric-selector', 'value')
    )
    def update_overview_tab(selected_metric):
        df = load_subnet_data()
        df_sorted = df.sort_values(by=selected_metric, ascending=False)
        fig = px.bar(
            df_sorted.head(15),
            x='subnet_name_screener',
            y=selected_metric,
            title=f"Top 15 Subnets by {selected_metric.replace('_', ' ').title()}",
            labels={selected_metric: selected_metric.replace('_', ' ').title()},
            hover_data=['netuid', 'market_cap_tao', 'alpha_circ', 'price_screener', 'score']
        )
        table_columns = [{"name": col, "id": col} for col in df_sorted.columns]
        table_data = df_sorted.to_dict("records")
        return fig, table_columns, table_data

    return app
