import requests
from datetime import datetime
import logging
import time
from typing import Dict, List, Optional, Any
from app.models import SubnetAPY, get_db
from app.config import TAO_API_BASE, TAO_APP_API_KEY, TAO_API_RATE_LIMIT
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import random
import pandas as pd
from sqlalchemy import desc
import plotly.express as px
from app.utils import fetch_combined_subnet_data

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for TAO.app API requests."""
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.interval = 60.0 / requests_per_minute
        self.last_request_time = 0.0

    def wait(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.interval:
            sleep_time = self.interval - time_since_last_request
            # Add small random jitter to prevent thundering herd
            sleep_time += random.uniform(0, 0.1)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

# Create a session with retry logic
session = requests.Session()
retry_strategy = Retry(
    total=TAO_API_RATE_LIMIT["max_retries"],
    backoff_factor=TAO_API_RATE_LIMIT["initial_retry_delay"],
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

# Initialize rate limiter
rate_limiter = RateLimiter(TAO_API_RATE_LIMIT["requests_per_minute"])

def fetch_alpha_apy(netuid: int) -> Dict:
    """
    Fetch APY data for a specific subnet from TAO.app API with rate limiting and retries.
    
    Args:
        netuid: The subnet ID to fetch APY for
        
    Returns:
        Dict containing APY data
        
    Raises:
        requests.exceptions.RequestException: If API request fails after retries
    """
    url = f"{TAO_API_BASE}/api/beta/apy/alpha"
    params = {"netuid": netuid}
    headers = {"X-API-Key": TAO_APP_API_KEY}
    
    # Wait for rate limit
    rate_limiter.wait()
    
    try:
        response = session.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Log the raw response for debugging
        logger.debug(f"Raw API response for netuid {netuid}: {data}")
        
        # Extract APY from the response
        # The API returns a list of validators in data['data']
        # Each validator has an alpha_apy field
        if 'data' in data and isinstance(data['data'], list):
            validators = data['data']
            if validators:
                # Calculate average APY from all validators
                total_apy = 0
                count = 0
                for validator in validators:
                    if 'alpha_apy' in validator and validator['alpha_apy'] is not None:
                        total_apy += float(validator['alpha_apy'])
                        count += 1
                
                if count > 0:
                    avg_apy = total_apy / count
                    data['apy'] = round(avg_apy, 2)  # Round to 2 decimal places
                    logger.info(f"Calculated average APY for netuid {netuid}: {data['apy']}%")
                    
                    # Also store validator-specific APY data
                    data['validator_apys'] = [{
                        'hotkey': v.get('hotkey'),
                        'validator_name': v.get('validator_name', ''),
                        'alpha_apy': v.get('alpha_apy'),
                        'alpha_stake': v.get('alpha_stake'),
                        'nominated_stake': v.get('nominated_stake'),
                        'vtrust': v.get('vtrust')
                    } for v in validators if 'alpha_apy' in v]
                else:
                    logger.warning(f"No valid APY values found in response for netuid {netuid}")
                    data['apy'] = None
                    data['validator_apys'] = []
            else:
                logger.warning(f"No validator data found for netuid {netuid}")
                data['apy'] = None
                data['validator_apys'] = []
        else:
            logger.warning(f"Unexpected API response format for netuid {netuid}")
            data['apy'] = None
            data['validator_apys'] = []
        
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching APY data for netuid {netuid}: {str(e)}")
        raise

def store_alpha_apy(netuid: int) -> Optional[SubnetAPY]:
    """
    Fetch and store APY data for a specific subnet.
    
    Args:
        netuid: The subnet ID to fetch and store APY for
        
    Returns:
        SubnetAPY record if successful, None if failed
        
    Raises:
        Exception: If database operation fails
    """
    try:
        # Fetch data
        data = fetch_alpha_apy(netuid)
        
        # Store in database
        db_session = get_db()
        with db_session as db:
            record = SubnetAPY(
                netuid=netuid,
                data=data,
                recorded_at=datetime.utcnow()
            )
            db.add(record)
            db.commit()
            
            # Log success with APY value
            apy_value = data.get('apy', 'N/A')
            logger.info(
                f"Stored APY data for netuid {netuid}: "
                f"APY={apy_value}%, "
                f"recorded_at={record.recorded_at}"
            )
            return record
            
    except Exception as e:
        logger.error(f"Error storing APY data for netuid {netuid}: {str(e)}")
        raise

def process_batch(netuids: List[int]) -> Dict[int, bool]:
    """
    Process a batch of netuids with rate limiting.
    
    Args:
        netuids: List of netuids to process
        
    Returns:
        Dict mapping netuid to success status (True/False)
    """
    results = {}
    for netuid in netuids:
        try:
            store_alpha_apy(netuid)
            results[netuid] = True
        except Exception as e:
            logger.error(f"Failed to process netuid {netuid}: {str(e)}")
            results[netuid] = False
    return results

def store_all_subnet_apy(start_netuid: int = 1, end_netuid: int = 64) -> Dict[int, bool]:
    """
    Fetch and store APY data for a range of subnets using batched processing.
    
    Args:
        start_netuid: First subnet ID to process (inclusive)
        end_netuid: Last subnet ID to process (inclusive)
        
    Returns:
        Dict mapping netuid to success status (True/False)
    """
    all_results = {}
    netuids = list(range(start_netuid, end_netuid + 1))
    batch_size = TAO_API_RATE_LIMIT["batch_size"]
    
    # Process in batches
    for i in range(0, len(netuids), batch_size):
        batch = netuids[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} of {(len(netuids) + batch_size - 1)//batch_size}")
        
        # Process batch
        batch_results = process_batch(batch)
        all_results.update(batch_results)
        
        # Wait between batches if not the last batch
        if i + batch_size < len(netuids):
            logger.info(f"Waiting {TAO_API_RATE_LIMIT['batch_delay']} seconds before next batch...")
            time.sleep(TAO_API_RATE_LIMIT["batch_delay"])
    
    # Log summary
    success_count = sum(1 for success in all_results.values() if success)
    logger.info(
        f"APY data collection complete. "
        f"Success: {success_count}/{len(all_results)} subnets"
    )
    
    return all_results

def get_latest_apy():
    """Get the latest APY records for each subnet."""
    db_session = get_db()
    with db_session as db:
        return db.query(SubnetAPY).order_by(desc(SubnetAPY.recorded_at)).all()

def load_latest_apy_df():
    """Load the latest APY data into a pandas DataFrame with additional metrics aggregated from all validators."""
    records = get_latest_apy()
    if not records:
        return pd.DataFrame()

    # Flatten all validator APYs into a DataFrame
    rows = []
    for r in records:
        netuid = r.netuid
        recorded_at = r.recorded_at
        validator_apys = r.data.get('validator_apys', [])
        for v in validator_apys:
            if v.get('alpha_apy') is not None:
                rows.append({
                    'netuid': netuid,
                    'recorded_at': recorded_at,
                    'alpha_apy': float(v['alpha_apy'])
                })

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame()

    # Group by subnet and calculate stats
    metrics = df.groupby('netuid').agg(
        min_apy=('alpha_apy', 'min'),
        max_apy=('alpha_apy', 'max'),
        mean_apy=('alpha_apy', 'mean'),
        median_apy=('alpha_apy', 'median'),
        std_apy=('alpha_apy', 'std'),
        validator_count=('alpha_apy', 'count'),
        recorded_at=('recorded_at', 'max')
    ).reset_index()

    return metrics

def load_all_validator_apy_df():
    """Return a DataFrame with all validator APYs, one row per validator per subnet."""
    records = get_latest_apy()
    rows = []
    for r in records:
        netuid = r.netuid
        recorded_at = r.recorded_at
        validator_apys = r.data.get('validator_apys', [])
        for v in validator_apys:
            if v.get('alpha_apy') is not None:
                # Set validator_name to 'No-name' if missing or empty
                name = v.get('validator_name')
                if not name or str(name).strip() == '':
                    name = 'No-name'
                rows.append({
                    'netuid': netuid,
                    'recorded_at': recorded_at,
                    'alpha_apy': float(v['alpha_apy']),
                    'vtrust': v.get('vtrust'),
                    'validator_name': name,
                    'hotkey': v.get('hotkey', 'Unknown'),
                    'alpha_stake': v.get('alpha_stake', 0),
                    'nominated_stake': v.get('nominated_stake', 0)
                })
    df = pd.DataFrame(rows)
    return df

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

def prepare_validator_distribution_data():
    """
    Prepares validator distribution data for visualization, including:
    - APY data for all validators
    - Rank and earning status within each subnet
    - Subnet information (name, market cap)
    
    Returns:
        pd.DataFrame: Processed data with all required fields for visualization
    """
    try:
        # Get validator APY data
        validator_df = load_all_validator_apy_df()
        if validator_df.empty:
            return pd.DataFrame()
        # Ensure all missing/empty validator names are set to 'No-name'
        validator_df['validator_name'] = validator_df['validator_name'].fillna('No-name')
        validator_df.loc[validator_df['validator_name'].str.strip() == '', 'validator_name'] = 'No-name'
        # Add total_stake column
        validator_df['alpha_stake'] = pd.to_numeric(validator_df['alpha_stake'], errors='coerce').fillna(0)
        validator_df['nominated_stake'] = pd.to_numeric(validator_df['nominated_stake'], errors='coerce').fillna(0)
        validator_df['total_stake'] = validator_df['alpha_stake'] + validator_df['nominated_stake']
        # Get subnet info
        subnet_info = fetch_combined_subnet_data()
        if subnet_info.empty:
            return pd.DataFrame()
        # Select required columns and handle missing subnet names
        subnet_info = subnet_info[["netuid", "subnet_name_screener", "market_cap_tao"]].copy()
        subnet_info['subnet_name_screener'] = subnet_info['subnet_name_screener'].fillna(
            subnet_info['netuid'].astype(str) + " (Unnamed)"
        )
        # Handle missing vtrust values by setting them to 0
        validator_df['vtrust'] = validator_df['vtrust'].fillna(0)
        # Sort by vtrust (desc), total_stake (desc), hotkey (asc) within each subnet
        validator_df = validator_df.sort_values(['netuid', 'vtrust', 'total_stake', 'hotkey'], ascending=[True, False, False, True])
        # Assign rank (1-based, unique within subnet)
        validator_df['rank'] = validator_df.groupby('netuid').cumcount() + 1
        # Mark only the first 64 as is_earning per subnet
        validator_df['is_earning'] = validator_df.groupby('netuid').cumcount() < 64
        # Handle missing APY values
        validator_df['alpha_apy'] = validator_df['alpha_apy'].fillna(0)
        # Join with subnet info
        merged_df = pd.merge(
            validator_df, 
            subnet_info, 
            on='netuid', 
            how='left'
        )
        # Handle any remaining missing values
        merged_df['market_cap_tao'] = merged_df['market_cap_tao'].fillna(0)
        merged_df['validator_name'] = merged_df['validator_name'].fillna('No-name')
        merged_df.loc[merged_df['validator_name'].str.strip() == '', 'validator_name'] = 'No-name'
        # Add subnet-level statistics
        subnet_stats = merged_df.groupby('netuid').agg({
            'alpha_apy': ['mean', 'count'],
            'is_earning': 'sum'
        }).reset_index()
        subnet_stats.columns = ['netuid', 'subnet_mean_apy', 'validator_count', 'earning_count']
        # Join subnet stats back to main dataframe
        merged_df = pd.merge(merged_df, subnet_stats, on='netuid', how='left')
        return merged_df
    except Exception as e:
        print(f"Error preparing validator distribution data: {str(e)}")
        return pd.DataFrame()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run initial data collection
    results = store_all_subnet_apy()
    
    # Print summary
    success_count = sum(1 for success in results.values() if success)
    print(f"\nAPY Data Collection Summary:")
    print(f"Successfully processed: {success_count}/{len(results)} subnets")
    
    # Show latest records
    print("\nLatest APY Records:")
    for record in get_latest_apy():
        print(f"Netuid {record['netuid']}: {record['apy']}% (recorded at {record['recorded_at']})") 