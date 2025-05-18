import pandas as pd
from app.config import SUBNET_SCORING_WEIGHTS as W

def compute_basic_subnet_score(df: pd.DataFrame) -> pd.DataFrame:
    """Add 'score' column based on normalized metrics including market cap."""
    df = df.copy()
    
    # Normalize market cap using market_cap_tao
    df['norm_market_cap'] = df['market_cap_tao'] / (df['market_cap_tao'].max() + 1e-8)

    # Normalize other values
    df['norm_tao_in'] = df['tao_in_screener'] / (df['tao_in_screener'].max() + 1e-8)
    min_trend = df['price_7d_pct_change'].min()
    max_trend = df['price_7d_pct_change'].max()
    df['norm_price_trend'] = (df['price_7d_pct_change'] - min_trend) / ((max_trend - min_trend) + 1e-8)
    df['has_github'] = df['github_repo_screener'].apply(lambda x: 1 if x else 0)
    df['has_website'] = df['subnet_website_screener'].apply(lambda x: 1 if x else 0)

    # Compute score with updated market cap normalization
    df['score'] = (
        df['norm_tao_in'] * W['tao_in'] +
        df['norm_market_cap'] * W['market_cap'] +
        df['norm_price_trend'] * W['price_7d_pct_change'] +
        df['has_github'] * W['has_github'] +
        df['has_website'] * W['has_website']
    )
    return df
