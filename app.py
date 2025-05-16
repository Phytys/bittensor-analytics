import dash
from dash import html, dcc, dash_table
import plotly.express as px
import pandas as pd

from utils import fetch_subnet_info

# Fetch data
df = fetch_subnet_info()

# Optional: sort subnets by market cap (if available)
if "price" in df.columns and "tao_in" in df.columns:
    df["market_cap_tao"] = df["price"] * df["tao_in"]

# Columns to show in table (customize as you prefer)
columns_to_show = [
    "netuid", "subnet_name", "price", "tao_in", "alpha_in", "alpha_out",
    "market_cap_tao", "github_repo", "discord", "subnet_website"
]

# Filter and sort
df_view = df[columns_to_show].sort_values(by="market_cap_tao", ascending=False)

# Initialize Dash App
app = dash.Dash(__name__)
app.title = "Bittensor Subnet Overview"

app.layout = html.Div([
    html.H1("Bittensor Subnets Overview", style={"textAlign": "center"}),
    html.Hr(),

    html.H2("Subnet Fundamentals", style={"marginTop": "20px"}),

    dash_table.DataTable(
        columns=[{"name": col, "id": col} for col in df_view.columns],
        data=df_view.to_dict("records"),
        sort_action="native",
        filter_action="native",
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
        page_size=20,
    )
])

if __name__ == "__main__":
    app.run(debug=True)
