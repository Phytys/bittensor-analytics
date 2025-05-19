import requests
from datetime import datetime
import logging
import time
from typing import Dict, List, Optional, Any
from app.models import SubnetAPY, get_db
from app.config import TAO_API_BASE, TAO_APP_API_KEY, TAO_API_RATE_LIMIT
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import random

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

def get_latest_apy(netuid: Optional[int] = None) -> List[Dict]:
    """
    Get the latest APY record(s) from the database.
    
    Args:
        netuid: Optional subnet ID to filter by
        
    Returns:
        List of dicts containing latest APY data
    """
    db_session = get_db()
    with db_session as db:
        query = db.query(SubnetAPY)
        
        if netuid is not None:
            query = query.filter(SubnetAPY.netuid == netuid)
        
        # Get latest record per netuid
        latest_records = []
        for record in query.order_by(SubnetAPY.recorded_at.desc()).all():
            latest_records.append({
                'netuid': record.netuid,
                'apy': record.data.get('apy'),
                'recorded_at': record.recorded_at,
                'raw_data': record.data
            })
        
        return latest_records

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