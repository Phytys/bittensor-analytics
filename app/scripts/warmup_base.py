from datetime import datetime, timedelta
import time
from app.utils import get_db, get_cached_netuids

__all__ = ['run_warmup']

def run_warmup(fetch_fn, model_class, name="metric", min_age_hours=6, sleep_sec=6):
    """
    Generic warmup function to collect data for all subnets.
    Uses cached subnet info to determine which subnets to process.
    
    Args:
        fetch_fn: Function that fetches data for a subnet (takes netuid as arg)
        model_class: SQLAlchemy model class to store the data
        name: Name of the metric for logging
        min_age_hours: Skip subnets with data newer than this
        sleep_sec: Seconds to sleep between requests
    """
    now = datetime.utcnow()
    netuids = get_cached_netuids()
    print(f"[{name.upper()}] 🔍 Found {len(netuids)} active subnets")
    
    with get_db() as db:
        for netuid in netuids:
            recent = db.query(model_class).filter(
                model_class.netuid == netuid,
                model_class.recorded_at > now - timedelta(hours=min_age_hours)
            ).first()
            if recent:
                print(f"[{name.upper()}] ✅ Skipping netuid={netuid} (cached)")
                continue

            try:
                data = fetch_fn(netuid)
                record = model_class(netuid=netuid, data=data)
                db.add(record)
                db.commit()
                print(f"[{name.upper()}] ✅ Stored for netuid={netuid}")
            except Exception as e:
                print(f"[{name.upper()}] ❌ Failed for netuid={netuid}: {e}")
            time.sleep(sleep_sec)
