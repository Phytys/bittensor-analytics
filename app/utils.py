import requests
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, Text, DateTime, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import TAO_API_BASE, TAO_APP_API_KEY, DATABASE_URI, CACHE_DEFAULT_TIMEOUT
from app.models import SubnetAPY, get_db
from typing import List

# SQLAlchemy setup
connect_args = {'check_same_thread': False} if DATABASE_URI.startswith('sqlite') else {}
engine = create_engine(DATABASE_URI, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class SubnetInfoCache(Base):
    __tablename__ = 'subnet_info'
    netuid = Column(Integer, primary_key=True, index=True)
    data = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)

class SubnetScreenerCache(Base):
    __tablename__ = 'subnet_screener'
    netuid = Column(Integer, primary_key=True, index=True)
    data = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine, checkfirst=True)

HEADERS = {"X-API-Key": TAO_APP_API_KEY}

def fetch_and_cache_json(endpoint: str, cache_model):
    """
    Fetch JSON from TAO.app API and cache in SQL database for CACHE_DEFAULT_TIMEOUT seconds.
    """
    session = SessionLocal()
    cutoff = datetime.utcnow() - timedelta(seconds=CACHE_DEFAULT_TIMEOUT)
    # Check cache
    recent = session.query(cache_model).filter(cache_model.updated_at > cutoff).all()
    if recent:
        data = [eval(rec.data) for rec in recent]
    else:
        url = f"{TAO_API_BASE}{endpoint}"
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        data = resp.json()
        # Refresh cache
        session.query(cache_model).delete()
        for item in data:
            rec = cache_model(netuid=item['netuid'], data=str(item), updated_at=datetime.utcnow())
            session.add(rec)
        session.commit()
    session.close()
    return data

def fetch_combined_subnet_data():
    """Fetch and merge subnet_info and subnet_screener data."""
    info_list = fetch_and_cache_json('/api/beta/analytics/subnets/info', SubnetInfoCache)
    screener_list = fetch_and_cache_json('/api/beta/subnet_screener', SubnetScreenerCache)
    df_info = pd.DataFrame(info_list)
    df_scr = pd.DataFrame(screener_list)
    merged_df = pd.merge(df_info, df_scr, on='netuid', how='outer', suffixes=('_info', '_screener'))
    return merged_df

def load_latest_apy_df() -> pd.DataFrame:
    """
    Load the most recent APY data for each subnet into a pandas DataFrame.
    
    Returns:
        pd.DataFrame: DataFrame containing the latest APY data with columns:
            - netuid: Subnet ID
            - recorded_at: Timestamp of the record
            - apy: Average APY for the subnet
            - validator_count: Number of validators
            - min_apy: Minimum validator APY
            - max_apy: Maximum validator APY
            - mean_apy: Mean validator APY
            - median_apy: Median validator APY
            - std_apy: Standard deviation of validator APYs
    """
    db_session = get_db()
    with db_session as db:
        # Get the most recent record for each subnet
        latest_records = []
        for netuid in range(1, 64):  # Assuming subnets 1-63
            latest = db.query(SubnetAPY).filter(
                SubnetAPY.netuid == netuid
            ).order_by(desc(SubnetAPY.recorded_at)).first()
            
            if latest:
                record = {
                    'netuid': latest.netuid,
                    'recorded_at': latest.recorded_at,
                    'apy': latest.data.get('apy'),  # Overall subnet APY
                }
                
                # Add validator-specific stats if available
                validator_apys = latest.data.get('validator_apys', [])
                if validator_apys:
                    apys = [float(v['alpha_apy']) for v in validator_apys 
                           if v.get('alpha_apy') is not None and float(v['alpha_apy']) > 0]
                    if apys:
                        record.update({
                            'validator_count': len(validator_apys),
                            'min_apy': min(apys),
                            'max_apy': max(apys),
                            'mean_apy': sum(apys) / len(apys),
                            'median_apy': pd.Series(apys).median(),
                            'std_apy': pd.Series(apys).std() if len(apys) > 1 else 0
                        })
                
                latest_records.append(record)
        
        df = pd.DataFrame(latest_records)
        if not df.empty:
            # Sort by netuid and ensure datetime column is properly formatted
            df = df.sort_values('netuid')
            df['recorded_at'] = pd.to_datetime(df['recorded_at'])
            
            # Round numeric columns to 2 decimal places
            numeric_cols = ['apy', 'min_apy', 'max_apy', 'mean_apy', 'median_apy', 'std_apy']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = df[col].round(2)
        
        return df

def get_cached_netuids() -> List[int]:
    """
    Get a sorted list of all netuids from the cached subnet info.
    This is more efficient than querying the API directly since we already cache this data.
    
    Returns:
        List[int]: Sorted list of active subnet IDs
    """
    with get_db() as db:
        netuids = [row.netuid for row in db.query(SubnetInfoCache).all()]
        return sorted(netuids)
