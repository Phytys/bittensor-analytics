from dash import Dash, html, dcc, dash_table, Input, Output
import plotly.express as px
import pandas as pd
from app.logic import compute_basic_subnet_score
from app.utils import fetch_combined_subnet_data

def init_dashboard(server, cache):
    app = Dash(
        __name__,
        server=server,
        url_base_pathname='/dashboard/',
        suppress_callback_exceptions=True
    )

    app.title = "Subnet Dashboard"

    @cache.memoize()
    def load_subnet_data():
        df = fetch_combined_subnet_data()
        df = compute_basic_subnet_score(df)
        return df

    app.layout = html.Div([
        html.H1("Bittensor Subnet Analytics", style={"textAlign": "center"}),
        html.Div([
            html.Label("Select metric to visualize:"),
            dcc.Dropdown(
                id='metric-selector',
                options=[
                    {'label': 'Score', 'value': 'score'},
                    {'label': 'TAO In', 'value': 'tao_in_screener'},
                    {'label': 'Market Cap (TAO)', 'value': 'market_cap_proxy'},
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

    @app.callback(
        Output('subnet-bar-chart', 'figure'),
        Output('subnet-table', 'columns'),
        Output('subnet-table', 'data'),
        Input('metric-selector', 'value')
    )
    def update_dashboard(selected_metric):
        df = load_subnet_data()
        df_sorted = df.sort_values(by=selected_metric, ascending=False)
        fig = px.bar(
            df_sorted.head(15),
            x='subnet_name_screener',
            y=selected_metric,
            title=f"Top 15 Subnets by {selected_metric.replace('_', ' ').title()}",
            labels={selected_metric: selected_metric.replace('_', ' ').title()},
            hover_data=['netuid', 'tao_in_screener', 'market_cap_proxy', 'price_screener', 'score']
        )
        table_columns = [{"name": col, "id": col} for col in df_sorted.columns]
        table_data = df_sorted.to_dict("records")
        return fig, table_columns, table_data

    return app
