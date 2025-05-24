import dash
from dash import html, dcc, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
from app.subnet_metrics import load_latest_apy_df, load_all_validator_apy_df, prepare_validator_distribution_data
from app.utils import fetch_combined_subnet_data, fetch_and_cache_json, load_cache_df, SubnetInfoCache, SubnetScreenerCache
import pandas as pd
import plotly.express as px
from app import cache
import numpy as np
import plotly.graph_objs as go
import sqlalchemy
from sqlalchemy.orm import Session
from app.utils import SessionLocal
import app.coingecko as coingecko

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

    # --- SCATTER PLOT: Subnet APY vs Market Cap ---
    scatter_section = dbc.Card([
        dbc.CardBody([
            html.H3("Subnet APY vs TAO Market Cap", className="mb-3", style={"fontWeight": 600}),
            html.Div([
                html.Span("ⓘ", id="scatter-info-tooltip", style={"cursor": "pointer", "color": "#888", "fontSize": "1.1em", "marginLeft": "8px"}),
            ]),
            dbc.Tooltip(
                "Shows the relationship between subnet mean APY and TAO market cap. Dot color: 7d price change (green=up, red=down, yellow=neutral). Dot size: 1m price change. APY is annualized validator yield. Market cap is total TAO in subnet × price. Outliers filtered. Use log scale for better comparison.",
                target="scatter-info-tooltip",
                placement="right",
                style={"whiteSpace": "pre-line", "maxWidth": "350px"}
            ),
            html.Div(
                "Each dot is a subnet. X-axis: TAO market cap. Y-axis: mean validator APY. Dot color: 7d price change. Dot size: 1m price change. Use log scale for wide ranges.",
                style={"color": "#1976d2", "fontWeight": "500", "marginBottom": "8px", "fontSize": "1.05rem"}
            ),
            dbc.Row([
                dbc.Col([
                    dcc.Checklist(
                        id='scatter-log-x-toggle',
                        options=[{'label': 'Log X-Axis (Market Cap)', 'value': 'log_x'}],
                        value=[],
                        inline=True,
                        className="mb-2"
                    ),
                ], width=4),
                dbc.Col([
                    dcc.Checklist(
                        id='scatter-log-y-toggle',
                        options=[{'label': 'Log Y-Axis (APY)', 'value': 'log_y'}],
                        value=[],
                        inline=True,
                        className="mb-2"
                    ),
                ], width=4),
                dbc.Col([
                    dcc.Checklist(
                        id='scatter-label-toggle',
                        options=[{'label': 'Show NetUID Labels', 'value': 'show_labels'}],
                        value=[],
                        inline=True,
                        className="mb-2"
                    ),
                ], width=4),
            ], className="mb-3"),
            dcc.Graph(id="subnet-scatter", config={"displayModeBar": False}),
            html.Div(id="scatter-info-strip"),
            html.Div(id="scatter-last-updated")
        ])
    ], className="mb-4 shadow-sm", style={"borderRadius": "12px"})

    # --- DUAL EMISSIONS EFFICIENCY CHART SECTION ---
    emissions_efficiency_dual_section = dbc.Card([
        dbc.CardBody([
            html.H3("% of TAO Emitted to Subnet Reward Pool vs Subnet Market Cap", className="mb-3", style={"fontWeight": 600}),
            html.Div([
                html.Span("ⓘ", id="emissions-header-tooltip", style={"cursor": "pointer", "color": "#888", "fontSize": "1.1em", "marginLeft": "8px"}),
            ]),
            dbc.Tooltip(
                "Each dot is a subnet. X-axis: market cap. Y-axis: % of TAO emitted to the subnet's reward pool per block (protocol emission rate). Dot size: TAO in pool. Dot color: mean validator APY. Use log scale for wide ranges.",
                target="emissions-header-tooltip",
                placement="right",
                style={"whiteSpace": "pre-line", "maxWidth": "350px"}
            ),
            html.Div(
                "This metric shows the protocol-level percentage of the subnet's TAO pool that is emitted as new rewards to the subnet's reward pool per block.",
                style={"color": "#1976d2", "fontWeight": "500", "marginBottom": "8px", "fontSize": "1.05rem"}
            ),
            dbc.Row([
                dbc.Col([], width=6),
                dbc.Col([
                    html.Label("Market Cap Axis:"),
                    dcc.Dropdown(
                        id='emissions-xaxis-dropdown',
                        options=[
                            {'label': 'Market Cap (TAO)', 'value': 'market_cap_tao'},
                            {'label': 'Market Cap (USD)', 'value': 'market_cap_usd'},
                        ],
                        value='market_cap_tao',
                        clearable=False,
                        style={"width": "100%"},
                        className="mb-2"
                    )
                ], width=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dcc.Checklist(
                        id='emissions-label-toggle',
                        options=[{'label': 'Show NetUID Labels', 'value': 'show_labels'}],
                        value=[],
                        inline=True,
                        className="mb-2"
                    ),
                ], width=12),
            ], className="mb-3"),
            dbc.Button([
                "More info ", html.Span("ℹ️")
            ], id="emissions-info-collapse-toggle", color="dark", style={"marginBottom": "0.5rem", "fontSize": "1.05rem"}),
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody([
                        html.Div([
                            html.B("% of TAO Emitted to Subnet Reward Pool:"),
                            " The protocol-level percentage of the subnet's TAO pool that is emitted as new rewards to the subnet's reward pool per block. This is not the same as validator APY, which depends on how rewards are distributed within the subnet.",
                            html.Br(), html.Br(),
                            html.B("Bubble color:"),
                            " Encodes the mean APY (%) for the top 64 validators in the subnet.",
                            html.Br(),
                            html.B("Bubble size:"),
                            " Shows the TAO in pool for each subnet.",
                            html.Br(), html.Br(),
                            html.B("What this doesn't tell you:"),
                            html.Ul([
                                html.Li("% of TAO emitted to the subnet's reward pool does not reflect how many validators are actually earning or their individual APY."),
                            ], style={"marginBottom": 0})
                        ], style={"fontSize": "1.01rem"})
                    ]),
                    style={"backgroundColor": "#f8f9fa", "border": "1px solid #bdbdbd"}
                ),
                id="emissions-info-collapse",
                is_open=False
            ),
            dcc.Graph(id='emissions-efficiency-dual-plot', config={"displayModeBar": False}),
            html.Div(id='emissions-efficiency-dual-info'),
            html.Div(id='emissions-last-updated')
        ])
    ], className="mb-4 shadow-sm", style={"borderRadius": "12px"})

    # --- VALIDATOR DISTRIBUTION SECTION ---
    validator_distribution_section = dbc.Card([
        dbc.CardBody([
            html.H3("Validator Distribution Across Subnets", className="mb-3", style={"fontWeight": 600}),
            html.Div([
                html.Span("ⓘ", id="validator-dist-tooltip", style={"cursor": "pointer", "color": "#888", "fontSize": "1.1em", "marginLeft": "8px"}),
            ]),
            dbc.Tooltip(
                "Shows the distribution of validator APYs across subnets. Top 64 by vTrust are considered earning. Org color-coding and filters help highlight concentration. Hover for full validator stats.",
                target="validator-dist-tooltip",
                placement="right",
                style={"whiteSpace": "pre-line", "maxWidth": "350px"}
            ),
            html.Div(
                "Each dot is a validator. X-axis: subnet (netuid). Y-axis: validator APY. Dot color: org or earning status. Use filters to highlight top orgs or top 64.",
                style={"color": "#1976d2", "fontWeight": "500", "marginBottom": "8px", "fontSize": "1.05rem"}
            ),
            dbc.Row([
                dbc.Col([
                    html.Label("Select Validator:", style={"marginRight": "10px"}),
                    dcc.Dropdown(
                        id='validator-selector',
                        options=[],  # Will be populated in callback
                        value=None,
                        clearable=True,
                        style={"width": "100%"},
                        className="mb-2"
                    )
                ], width=6),
                dbc.Col([
                    dcc.Checklist(
                        id='validator-filters',
                        options=[
                            {'label': 'Show only Top 64', 'value': 'top64'},
                            {'label': 'Show only Top 10 Validator Orgs', 'value': 'top10orgs'},
                            {'label': 'Log scale Y-axis', 'value': 'log_y'}
                        ],
                        value=[],
                        inline=True,
                        className="mb-2"
                    )
                ], width=6)
            ], className="mb-3"),
            dcc.Graph(id='validator-distribution-plot', config={"displayModeBar": False}),
            html.Div(id='validator-distribution-info'),
            html.Div(id='validator-dist-last-updated')
        ])
    ], className="mb-4 shadow-sm", style={"borderRadius": "12px"})

    # --- DATA TABLE SECTION ---
    data_table_section = dbc.Card([
        dbc.CardBody([
            html.H3("Subnet Metrics Data Table", className="mb-3", style={"fontWeight": 600}),
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
                    "height": "auto",
                    "fontFamily": "Inter, sans-serif"
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
    ], className="mb-4 shadow-sm", style={"borderRadius": "12px"})

    return html.Div([
        html.H1("Subnet Metrics", className="mb-4", style={"fontWeight": 700}),
        page_tagline,
        html.Hr(style={"margin": "18px 0 18px 0", "borderTop": "2px solid #e0e0e0"}),
        scatter_section,
        emissions_efficiency_dual_section,
        validator_distribution_section,
        data_table_section
    ], style={"fontFamily": "Inter, sans-serif"})

# --- CALLBACK FOR SCATTER PLOT LOG SCALE ---
@dash.callback(
    Output("subnet-scatter", "figure"),
    Output("scatter-info-strip", "children"),
    Output("scatter-last-updated", "children"),
    Input("scatter-log-x-toggle", "value"),
    Input("scatter-log-y-toggle", "value"),
    Input("scatter-label-toggle", "value")
)
def update_subnet_scatter(log_x_toggle, log_y_toggle, label_toggle):
    # Load cached/DB data only
    apy_df = load_latest_apy_df()
    screener_df = fetch_combined_subnet_data()
    # Use 'netuid', 'market_cap_tao', 'subnet_name', 'validator_count', 'price_7d_pct_change', 'price_1m_pct_change' from screener_df
    # Use 'netuid', 'mean_apy' from apy_df (rename to subnet_apy for clarity)
    apy_df = apy_df.rename(columns={"mean_apy": "subnet_apy"})
    merged = pd.merge(apy_df, screener_df, on="netuid", how="inner")
    # Ensure subnet_name exists, fallback to subnet_name_screener, then netuid
    if "subnet_name" not in merged.columns and "subnet_name_screener" in merged.columns:
        merged["subnet_name"] = merged["subnet_name_screener"]
    elif "subnet_name" in merged.columns and "subnet_name_screener" in merged.columns:
        merged["subnet_name"] = merged["subnet_name"].fillna(merged["subnet_name_screener"])
    if "subnet_name" not in merged.columns:
        merged["subnet_name"] = merged["netuid"].astype(str)
    # Drop rows with missing/zero market cap or APY
    merged = merged[(merged["market_cap_tao"].notnull()) & (merged["market_cap_tao"] > 0) & (merged["subnet_apy"].notnull()) & (merged["subnet_apy"] > 0)]
    # Filter out only the extreme APY outlier (e.g., subnet_apy > 1000)
    apy_outlier_threshold = 1000
    filtered = merged[merged["subnet_apy"] <= apy_outlier_threshold]
    filtered_out = merged[merged["subnet_apy"] > apy_outlier_threshold]
    filtered_netuids = filtered_out["netuid"].tolist()
    # Add netuid labels if toggled
    text_labels = filtered["netuid"].astype(str) if 'show_labels' in label_toggle else None
    # Prepare color and size columns
    color_col = 'price_7d_pct_change'
    size_col = np.abs(filtered['price_1m_pct_change']).clip(lower=5)
    # Prepare hovertemplate
    hovertemplate = (
        'NetUID: %{customdata[0]}<br>'
        'Subnet: %{customdata[1]}<br>'
        'APY: %{customdata[4]:,.2f}%<br>'
        'Market Cap (TAO): %{customdata[2]:,.0f}<br>'
        '7d Price Change: %{customdata[5]:+.2f}%<br>'
        '1m Price Change: %{customdata[6]:+.2f}%<extra></extra>'
    )
    fig = px.scatter(
        filtered,
        x="market_cap_tao",
        y="subnet_apy",
        size=size_col,
        color=color_col,
        hover_data=["netuid", "subnet_name", "market_cap_tao", "validator_count", "subnet_apy", "price_7d_pct_change", "price_1m_pct_change"],
        labels={
            "market_cap_tao": "Market Cap (TAO)",
            "subnet_apy": "Subnet Mean APY (%)",
            "price_7d_pct_change": "7d Price Change (%)",
            "price_1m_pct_change": "1m Price Change (%)"
        },
        title="Subnet APY vs Market Cap (TAO)",
        template="plotly_white",
        log_x='log_x' in log_x_toggle,
        log_y='log_y' in log_y_toggle,
        text=text_labels,
        color_continuous_scale=px.colors.diverging.RdYlGn,
        range_color=[-50, 50],
        size_max=40
    )
    fig.update_traces(marker_line_color='#222', marker_line_width=1.5)
    # Add reference line at 100% APY
    fig.add_hline(y=100, line_dash="dash", line_color="#888", annotation_text="100% APY", annotation_position="top left")
    # Dynamically set y-axis range for log scale
    if 'log_y' in log_y_toggle and not filtered.empty:
        min_y = max(filtered['subnet_apy'].min(), 1e-2)  # Avoid log(0)
        max_y = filtered['subnet_apy'].max()
        fig.update_yaxes(type='log', range=[np.log10(min_y), np.log10(max_y)], title_text='Subnet Mean APY (%)')
    else:
        fig.update_yaxes(type='linear', title_text='Subnet Mean APY (%)')
    fig.update_layout(height=600, margin=dict(t=50, b=40, l=50, r=50), font=dict(family="Inter, sans-serif"))
    fig.update_traces(hovertemplate=hovertemplate, textposition='top center')
    # Info strip: filtered out and number visualized
    num_visualized = filtered.shape[0]
    num_subnets = filtered["netuid"].nunique()
    last_update = filtered.iloc[0]['recorded_at'] if not filtered.empty else "N/A"
    info_strip = html.Div([
        html.Div(
            f"Filtered out {len(filtered_netuids)} subnet(s) with APY > {apy_outlier_threshold}%: {filtered_netuids if filtered_netuids else 'None'}",
            style={
                "backgroundColor": "#fff3cd",
                "color": "#856404",
                "padding": "10px 16px",
                "marginTop": "10px",
                "borderLeft": "5px solid #ffe082",
                "fontSize": "0.98rem"
            }
        ),
        html.Div(
            f"Visualized {num_subnets} subnet(s) on the chart.",
            style={
                "backgroundColor": "#e3f2fd",
                "color": "#1565c0",
                "padding": "8px 16px",
                "marginTop": "6px",
                "borderLeft": "5px solid #90caf9",
                "fontSize": "0.98rem"
            }
        )
    ])
    last_updated_strip = html.Div(
        f"Last updated: {last_update}",
        style={
            "backgroundColor": "#e8f5e9",
            "color": "#2e7d32",
            "padding": "8px 16px",
            "marginTop": "6px",
            "borderLeft": "5px solid #81c784",
            "fontSize": "0.98rem"
        }
    )
    return fig, info_strip, last_updated_strip 

# --- CALLBACKS FOR VALIDATOR DISTRIBUTION ---
@dash.callback(
    Output('validator-selector', 'options'),
    Input('validator-selector', 'value')  # Dummy input to trigger on load
)
def update_validator_options(_):
    df = prepare_validator_distribution_data()
    if df.empty:
        return []
    # Get unique validator names, sorted alphabetically, ensure 'No-name' is present if any
    validators = sorted(df['validator_name'].unique())
    return [{'label': name, 'value': name} for name in validators]

@dash.callback(
    Output('validator-distribution-plot', 'figure'),
    Output('validator-distribution-info', 'children'),
    Output('validator-dist-last-updated', 'children'),
    Input('validator-selector', 'value'),
    Input('validator-filters', 'value')
)
def update_validator_distribution(selected_validator, filters):
    print("\n=== Validator Distribution Callback ===")
    print(f"Selected validator: {selected_validator}")
    print(f"Active filters: {filters}")
    
    df = prepare_validator_distribution_data()
    print(f"\nDataFrame shape: {df.shape}")
    
    if df.empty:
        print("No data available for plotting")
        return {}, html.Div("No validator data available")
    
    # Filter out extreme APY outliers
    apy_threshold = 1000
    filtered_df = df[(df['alpha_apy'] <= apy_threshold) & (df['alpha_apy'] > 0)].copy()  # Remove APY=0
    filtered_out = df[df['alpha_apy'] > apy_threshold]
    filtered_netuids = filtered_out['netuid'].unique().tolist()
    
    use_log_scale = 'log_y' in filters
    show_top64 = 'top64' in filters
    show_top10orgs = 'top10orgs' in filters
    
    # Ensure netuid is numeric for x-axis
    filtered_df['netuid'] = pd.to_numeric(filtered_df['netuid'], errors='coerce')
    filtered_df = filtered_df.sort_values('netuid')
    
    # Apply Top 64 filter: only show is_earning==True if checked
    if show_top64:
        filtered_df = filtered_df[filtered_df['is_earning']]
    
    # Apply Top 10 Validator Orgs filter
    color_discrete_map = None
    if show_top10orgs:
        # Compute top 10 orgs by total stake
        org_stake = filtered_df.groupby('validator_name')['total_stake'].sum().sort_values(ascending=False)
        top10_names = org_stake.head(10).index.tolist()
        filtered_df = filtered_df[filtered_df['validator_name'].isin(top10_names)]
        # Assign a color to each org
        palette = px.colors.qualitative.Plotly + px.colors.qualitative.D3 + px.colors.qualitative.Set1
        color_discrete_map = {name: palette[i % len(palette)] for i, name in enumerate(top10_names)}
    
    # Split data for traces
    hovertemplate = (
        'NetUID: %{customdata[0]}<br>'
        'Subnet: %{customdata[1]}<br>'
        'APY: %{customdata[4]}%<br>'
        'TAO in Pool: %{customdata[6]}<br>'
        'Price: $%{customdata[3]}<br>'
        'Market Cap (TAO): %{customdata[2]}<br>'
        'Market Cap (USD): $%{customdata[3]}<br>'
        'Emission %: %{customdata[4]}<br>'
        '<extra></extra>'
    )
    traces = []
    if show_top10orgs:
        # One trace per org, colored
        for i, name in enumerate(top10_names):
            org_mask = filtered_df['validator_name'] == name
            if org_mask.any():
                traces.append({
                    'x': filtered_df.loc[org_mask, 'netuid'],
                    'y': filtered_df.loc[org_mask, 'alpha_apy'],
                    'mode': 'markers',
                    'marker': {'size': 9, 'color': color_discrete_map[name], 'opacity': 0.85},
                    'name': name,
                    'text': filtered_df.loc[org_mask, 'subnet_name_screener'],
                    'customdata': filtered_df.loc[org_mask, ['netuid', 'subnet_name_screener', 'validator_name', 'alpha_apy', 'rank', 'alpha_stake', 'nominated_stake', 'total_stake']].values,
                    'hovertemplate': hovertemplate
                })
        # Highlight selected validator if any
        if selected_validator and selected_validator in top10_names:
            selected_mask = filtered_df['validator_name'] == selected_validator
            if selected_mask.any():
                traces.append({
                    'x': filtered_df.loc[selected_mask, 'netuid'],
                    'y': filtered_df.loc[selected_mask, 'alpha_apy'],
                    'mode': 'markers',
                    'marker': {'size': 14, 'color': color_discrete_map[selected_validator], 'line': {'width': 2, 'color': 'black'}, 'opacity': 1.0},
                    'name': f"{selected_validator} (Selected)",
                    'text': filtered_df.loc[selected_mask, 'subnet_name_screener'],
                    'customdata': filtered_df.loc[selected_mask, ['netuid', 'subnet_name_screener', 'validator_name', 'alpha_apy', 'rank', 'alpha_stake', 'nominated_stake', 'total_stake']].values,
                    'hovertemplate': hovertemplate
                })
    else:
        if selected_validator:
            selected_mask = filtered_df['validator_name'] == selected_validator
        else:
            selected_mask = pd.Series([False]*len(filtered_df), index=filtered_df.index)
        if selected_validator and selected_mask.any():
            traces.append({
                'x': filtered_df.loc[selected_mask, 'netuid'],
                'y': filtered_df.loc[selected_mask, 'alpha_apy'],
                'mode': 'markers',
                'marker': {'size': 12, 'color': '#d32f2f', 'line': {'width': 2, 'color': 'black'}, 'opacity': 1.0},
                'name': f"{selected_validator}",
                'text': filtered_df.loc[selected_mask, 'subnet_name_screener'],
                'customdata': filtered_df.loc[selected_mask, ['netuid', 'subnet_name_screener', 'validator_name', 'alpha_apy', 'rank', 'alpha_stake', 'nominated_stake', 'total_stake']].values,
                'hovertemplate': hovertemplate
            })
        # All other (non-selected) validators
        other_mask = ~selected_mask
        if other_mask.any():
            traces.append({
                'x': filtered_df.loc[other_mask, 'netuid'],
                'y': filtered_df.loc[other_mask, 'alpha_apy'],
                'mode': 'markers',
                'marker': {'size': 8 if show_top64 else 7, 'color': '#1976d2', 'opacity': 0.9 if show_top64 else 0.7},
                'name': 'Top 64' if show_top64 else 'All Validators',
                'text': filtered_df.loc[other_mask, 'subnet_name_screener'],
                'customdata': filtered_df.loc[other_mask, ['netuid', 'subnet_name_screener', 'validator_name', 'alpha_apy', 'rank', 'alpha_stake', 'nominated_stake', 'total_stake']].values,
                'hovertemplate': hovertemplate
            })
    # Always get the full set of netuids for x-axis ordering
    all_netuids = df['netuid'].drop_duplicates().sort_values().astype(str).tolist()
    
    fig = go.Figure()
    for t in traces:
        fig.add_trace(go.Scatter(**t))
    fig.update_layout(
        title='Validator APY Distribution Across Subnets',
        xaxis_title='NetUID (Subnet Number)',
        yaxis_title='Validator APY (%)',
        height=600,
        margin=dict(t=50, b=40, l=50, r=50),
        showlegend=True,
        xaxis=dict(type='category', categoryorder='array', categoryarray=all_netuids),
    )
    if use_log_scale:
        fig.update_yaxes(type='log')
    # Info strip
    last_update = filtered_df['recorded_at'].iloc[0] if 'recorded_at' in filtered_df.columns and not filtered_df.empty else "N/A"
    total_validators = len(filtered_df)
    total_subnets = filtered_df['netuid'].nunique()
    earning_validators = filtered_df['is_earning'].sum()
    info_strip = html.Div([
        html.Div(
            f"Showing {total_validators} validators across {total_subnets} subnets ({earning_validators} earning)",
            style={
                "backgroundColor": "#e3f2fd",
                "color": "#1565c0",
                "padding": "8px 16px",
                "marginTop": "6px",
                "borderLeft": "5px solid #90caf9",
                "fontSize": "0.98rem"
            }
        ),
        html.Div(
            f"Filtered out {len(filtered_netuids)} subnet(s) with APY > {apy_threshold}%: {filtered_netuids if filtered_netuids else 'None'}",
            style={
                "backgroundColor": "#fff3cd",
                "color": "#856404",
                "padding": "8px 16px",
                "marginTop": "6px",
                "borderLeft": "5px solid #ffe082",
                "fontSize": "0.98rem"
            }
        )
    ])
    last_updated_strip = html.Div(
        f"Last updated: {last_update}",
        style={
            "backgroundColor": "#e8f5e9",
            "color": "#2e7d32",
            "padding": "8px 16px",
            "marginTop": "6px",
            "borderLeft": "5px solid #81c784",
            "fontSize": "0.98rem"
        }
    )
    return fig, info_strip, last_updated_strip 

# --- CALLBACK FOR DUAL EMISSIONS EFFICIENCY CHART ---
@dash.callback(
    Output('emissions-efficiency-dual-plot', 'figure'),
    Output('emissions-efficiency-dual-info', 'children'),
    Output('emissions-last-updated', 'children'),
    Input('emissions-label-toggle', 'value')
)
def update_emissions_efficiency_dual_plot(label_toggle):
    # Ensure defaults if dropdowns are not initialized
    df = load_emission_data()
    # Get global TAO price (USD)
    global_tao_price, _ = coingecko.get_latest_tao_price()
    if global_tao_price is None:
        global_tao_price = 0.0
    # Compute market cap USD using global TAO price and market_cap_tao
    df['market_cap_usd'] = df['market_cap_tao'] * global_tao_price
    # Merge in mean_apy for top 64 validators per subnet
    apy_df = load_latest_apy_df()
    if 'mean_apy' in apy_df.columns:
        df = pd.merge(df, apy_df[['netuid', 'mean_apy']], on='netuid', how='left')
    else:
        df['mean_apy'] = None
    df = df[df['market_cap_tao'].notnull() & df['market_cap_tao'] > 0].copy()
    # Prepare custom_data for hover: round only for display
    df['market_cap_usd_disp'] = df['market_cap_usd'].round(2)
    df['emissions_per_tao_disp'] = df['emissions_per_tao'].round(2)
    df['market_cap_tao_disp'] = df['market_cap_tao'].round(2)
    df['emission_pct_disp'] = df['emission_pct'].round(2)
    df['tao_in_disp'] = df['tao_in'].round(2)
    df['mean_apy_disp'] = df['mean_apy'].round(2) if 'mean_apy' in df.columns else None
    # Cap mean_apy for color scale at 200%
    apy_color_cap = 200
    df['mean_apy_capped'] = df['mean_apy'].clip(upper=apy_color_cap)
    color_col = 'mean_apy_capped'
    # Human-friendly axis labels
    axis_labels = {
        'market_cap_tao': 'Subnet Market Cap (TAO)',
        'emission_pct': '% of TAO Emitted to Subnet Reward Pool (per block)',
        'mean_apy': 'Mean APY (%)'
    }
    # Enhanced hovertemplate with formatting
    hovertemplate = (
        'NetUID: %{customdata[0]}<br>'
        'Subnet: %{customdata[1]}<br>'
        'Mean APY: %{customdata[7]:,.0f}%<br>'
        'TAO in Pool: %{customdata[6]:,.0f}<br>'
        'Market Cap (TAO): %{customdata[2]:,.0f}<br>'
        'Market Cap (USD): $%{customdata[3]:,.0f}<br>'
        'Emission %: %{customdata[4]:.2f}<br>'
        '<extra></extra>'
    )
    text_labels = df['netuid'].astype(str) if 'show_labels' in label_toggle else None
    fig = px.scatter(
        df,
        x='market_cap_tao',
        y='emission_pct',
        size='tao_in',
        color=color_col,
        custom_data=[
            df['netuid'],
            df['subnet_name'],
            df['market_cap_tao_disp'],
            df['market_cap_usd_disp'],
            df['emission_pct_disp'],
            df['emissions_per_tao_disp'],
            df['tao_in_disp'],
            df['mean_apy_disp'],
        ],
        title=f"{axis_labels['emission_pct']} vs {axis_labels['market_cap_tao']}",
        template='plotly_white',
        text=text_labels,
        labels=axis_labels,
        color_continuous_scale=px.colors.sequential.Viridis,
        range_color=[0, apy_color_cap],
        color_continuous_midpoint=apy_color_cap/2
    )
    # Set colorbar label
    fig.update_coloraxes(colorbar_title='Mean APY (%)')
    fig.update_traces(hovertemplate=hovertemplate, textposition='top center')
    fig.update_layout(height=600, margin=dict(t=50, b=40, l=50, r=50))
    # Info strip: just show number of subnets visualized
    num_subnets = df['netuid'].nunique()
    info_strip = html.Div([
        html.Div(
            f"Visualized {num_subnets} subnet(s) on the chart.",
            style={
                "backgroundColor": "#e3f2fd",
                "color": "#1565c0",
                "padding": "8px 16px",
                "marginTop": "6px",
                "borderLeft": "5px solid #90caf9",
                "fontSize": "0.98rem"
            }
        )
    ])
    # Get latest cache update time from both caches
    session = SessionLocal()
    info_time = session.query(sqlalchemy.func.max(SubnetInfoCache.updated_at)).scalar()
    screener_time = session.query(sqlalchemy.func.max(SubnetScreenerCache.updated_at)).scalar()
    session.close()
    last_update = max([t for t in [info_time, screener_time] if t is not None], default=None)
    if last_update is not None:
        last_update = str(last_update)
    else:
        last_update = "N/A"
    last_updated_strip = html.Div(
        f"Last updated: {last_update}",
        style={
            "backgroundColor": "#e8f5e9",
            "color": "#2e7d32",
            "padding": "8px 16px",
            "marginTop": "6px",
            "borderLeft": "5px solid #81c784",
            "fontSize": "0.98rem"
        }
    )
    return fig, info_strip, last_updated_strip

def load_emission_data():
    # Define fields and types for each cache
    info_fields = ['netuid', 'tao_in']
    screener_fields = ['netuid', 'subnet_name', 'market_cap_tao', 'price', 'emission_pct']
    info_dtypes = {'netuid': int, 'tao_in': float}
    screener_dtypes = {'netuid': int, 'market_cap_tao': float, 'price': float, 'emission_pct': float}
    # Load from cache
    info = load_cache_df(SubnetInfoCache, fields=info_fields, dtypes=info_dtypes)
    screener = load_cache_df(SubnetScreenerCache, fields=screener_fields, dtypes=screener_dtypes)
    merged = pd.merge(info, screener, on='netuid', how='inner')
    merged['market_cap_usd'] = merged['market_cap_tao'] * merged['price']
    merged['emissions_per_tao'] = merged['emission_pct'] / merged['tao_in'].replace(0, np.nan)
    return merged 

# Add callback to toggle the collapse
@dash.callback(
    Output("emissions-info-collapse", "is_open"),
    Input("emissions-info-collapse-toggle", "n_clicks"),
    State("emissions-info-collapse", "is_open"),
)
def toggle_emissions_info_collapse(n, is_open):
    if n:
        return not is_open
    return is_open 