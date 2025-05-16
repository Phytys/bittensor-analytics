import dash
from dash import html, dcc, dash_table, Input, Output
import pandas as pd
import plotly.express as px
from flask_caching import Cache
from config import CACHE_TYPE, CACHE_DIR, CACHE_DEFAULT_TIMEOUT
from utils import fetch_combined_subnet_data
from logic import compute_basic_subnet_score

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server

# Configure cache
cache = Cache(server, config={
    'CACHE_TYPE': CACHE_TYPE,
    'CACHE_DIR': CACHE_DIR,
    'CACHE_DEFAULT_TIMEOUT': CACHE_DEFAULT_TIMEOUT
})

@cache.memoize()
def load_subnet_data():
    df = fetch_combined_subnet_data()
    df = compute_basic_subnet_score(df)
    return df.to_json(date_format='iso', orient='split')

# Layout
app.layout = html.Div([
    html.H1("Bittensor Subnet Analytics", style={"textAlign": "center"}),
    html.Div([
        html.Label("Select metric to visualize:"),
        dcc.Dropdown(
            id='metric-selector',
            options=[
                {'label': 'Score', 'value': 'score'},
                {'label': 'TAO In', 'value': 'tao_in_screener'},
                {'label': 'Price', 'value': 'price_screener'},
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
    df = pd.read_json(load_subnet_data(), orient='split')
    print("DataFrame columns in callback:", df.columns.tolist())
    print("Selected metric:", selected_metric)
    print("First few rows of DataFrame in callback:")
    print(df.head())
    try:
        df_sorted = df.sort_values(by=selected_metric, ascending=False)
    except KeyError as e:
        print(f"Error sorting by {selected_metric}. Available columns: {df.columns.tolist()}")
        raise
    fig = px.bar(
        df_sorted.head(15),
        x='subnet_name_screener',
        y=selected_metric,
        title=f"Top 15 Subnets by {selected_metric.replace('_', ' ').title()}",
        labels={
            selected_metric: selected_metric.replace('_', ' ').title(),
            'subnet_name_screener': 'Subnet Name'
        },
        hover_data=['netuid', 'tao_in_screener', 'price_screener', 'score']
    )
    table_columns = [{"name": col, "id": col} for col in df_sorted.columns]
    table_data = df_sorted.to_dict("records")
    return fig, table_columns, table_data

if __name__ == "__main__":
    app.run(debug=True)
