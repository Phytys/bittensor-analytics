import requests
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import TAO_API_BASE, TAO_APP_API_KEY, DATABASE_URI, CACHE_DEFAULT_TIMEOUT

# SQLAlchemy setup
engine = create_engine(DATABASE_URI, connect_args={'check_same_thread': False})
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
Base.metadata.create_all(bind=engine)

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
