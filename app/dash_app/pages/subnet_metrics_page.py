import dash
from dash import html, dcc, dash_table, Input, Output
import dash_bootstrap_components as dbc
from app.subnet_metrics import load_latest_apy_df, load_all_validator_apy_df, prepare_validator_distribution_data
from app.utils import fetch_combined_subnet_data
import pandas as pd
import plotly.express as px
from app import cache
import numpy as np
import plotly.graph_objs as go

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
    apy_threshold = 1000
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

    # --- SCATTER PLOT: Subnet APY vs Market Cap ---
    scatter_section = [
        html.H3("\ud83d\udcc8 Subnet APY vs TAO Market Cap", style={"marginTop": "40px"}),
        dcc.Checklist(
            id='scatter-log-x-toggle',
            options=[{'label': 'Log X-Axis (Market Cap)', 'value': 'log_x'}],
            value=[],
            inline=True,
            style={"marginBottom": "8px"}
        ),
        dcc.Checklist(
            id='scatter-log-y-toggle',
            options=[{'label': 'Log Y-Axis (APY)', 'value': 'log_y'}],
            value=[],
            inline=True,
            style={"marginBottom": "8px"}
        ),
        dcc.Checklist(
            id='scatter-label-toggle',
            options=[{'label': 'Show NetUID Labels', 'value': 'show_labels'}],
            value=[],
            inline=True,
            style={"marginBottom": "15px"}
        ),
        dcc.Graph(id="subnet-scatter"),
        html.Div(id="scatter-info-strip")
    ]

    # --- VALIDATOR DISTRIBUTION SECTION ---
    validator_distribution_section = [
        html.H3("👥 Validator Distribution Across Subnets", style={"marginTop": "40px"}),
        html.Div(
            "This chart shows how validators are distributed across subnets, with APY as the key metric. "
            "Each dot represents a validator, with earning validators (top 64 by vtrust) shown more prominently. "
            "Select a validator to highlight their positions across subnets.",
            style={
                "color": "#1976d2",
                "fontWeight": "500",
                "marginBottom": "15px",
                "fontSize": "1.05rem"
            }
        ),
        dbc.Row([
            dbc.Col([
                html.Label("Select Validator:", style={"marginRight": "10px"}),
                dcc.Dropdown(
                    id='validator-selector',
                    options=[],  # Will be populated in callback
                    value=None,
                    clearable=True,
                    style={"width": "100%"}
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
                    inline=True
                )
            ], width=6)
        ], style={"marginBottom": "15px"}),
        dcc.Graph(id='validator-distribution-plot'),
        html.Div(id='validator-distribution-info')
    ]

    # --- DATA TABLE SECTION ---
    data_table_section = [
        html.H3("Subnet Metrics Data Table", style={"marginTop": "40px"}),
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
    ]

    # --- LAST UPDATE INFO ---
    last_update = df.iloc[0]['recorded_at'] if not df.empty else "N/A"
    last_update_info = html.Div(
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

    return html.Div([
        html.H1("Subnet Metrics", className="mb-4"),
        page_tagline,
        html.Hr(style={"margin": "18px 0 18px 0", "borderTop": "2px solid #e0e0e0"}),
        html.H3("📦 Placeholder"),
        chart_tagline,
        dcc.Checklist(
            options=[{"label": "Log scale y-axis", "value": "log"}],
            value=[],
            id="log-scale-toggle",
            style={"marginBottom": "10px"}
        ),
        dcc.Loading(
            type='circle',
            children=html.Div([
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
        last_update_info,
        *scatter_section,
        *validator_distribution_section,
        *data_table_section
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
    apy_threshold = 1000
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

# --- CALLBACK FOR SCATTER PLOT LOG SCALE ---
@dash.callback(
    Output("subnet-scatter", "figure"),
    Output("scatter-info-strip", "children"),
    Input("scatter-log-x-toggle", "value"),
    Input("scatter-log-y-toggle", "value"),
    Input("scatter-label-toggle", "value")
)
def update_subnet_scatter(log_x_toggle, log_y_toggle, label_toggle):
    # Load cached/DB data only
    apy_df = load_latest_apy_df()
    screener_df = fetch_combined_subnet_data()
    # Use 'netuid', 'market_cap_tao', 'subnet_name', 'validator_count' from screener_df
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
    fig = px.scatter(
        filtered,
        x="market_cap_tao",
        y="subnet_apy",
        size="validator_count",
        hover_data=["netuid", "subnet_name", "market_cap_tao", "validator_count", "subnet_apy"],
        labels={
            "market_cap_tao": "Market Cap (TAO)",
            "subnet_apy": "Subnet Mean APY (%)",
        },
        title="Subnet APY vs Market Cap (TAO)",
        template="plotly_white",
        log_x='log_x' in log_x_toggle,
        log_y='log_y' in log_y_toggle,
        text=text_labels
    )
    # Add reference line at 100% APY
    fig.add_hline(y=100, line_dash="dash", line_color="#888", annotation_text="100% APY", annotation_position="top left")
    # Dynamically set y-axis range for log scale
    if 'log_y' in log_y_toggle and not filtered.empty:
        min_y = max(filtered['subnet_apy'].min(), 1e-2)  # Avoid log(0)
        max_y = filtered['subnet_apy'].max()
        fig.update_yaxes(type='log', range=[np.log10(min_y), np.log10(max_y)], title_text='Subnet Mean APY (%)')
    else:
        fig.update_yaxes(type='linear', title_text='Subnet Mean APY (%)')
    fig.update_layout(height=600, margin=dict(t=50, b=40, l=50, r=50))
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
        ),
        html.Div(
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
    ])
    return fig, info_strip 

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
        'NetUID: %{x}<br>'
        'Subnet: %{text}<br>'
        'APY: %{y}<br>'
        'Validator: %{customdata[2]}<br>'
        'Rank: %{customdata[4]:.0f}<br>'
        'Alpha Stake: %{customdata[5]:,.2f}<br>'
        'Nominated Stake: %{customdata[6]:,.2f}<br>'
        'Total Stake: %{customdata[7]:,.2f}<extra></extra>'
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
    last_update = filtered_df['recorded_at'].iloc[0] if not filtered_df.empty else "N/A"
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
        ),
        html.Div(
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
    ])
    return fig, info_strip 