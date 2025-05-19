from sqlalchemy import Column, Integer, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from typing import Type, Optional
from app.config import DATABASE_URI, RETENTION_DAYS, MAX_ROWS_PER_NETUID
import logging

# SQLAlchemy setup
connect_args = {'check_same_thread': False} if DATABASE_URI.startswith('sqlite') else {}
engine = create_engine(DATABASE_URI, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class NetuidTimeSeries(Base):
    """Base class for all time series data models."""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    netuid = Column(Integer, index=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    data = Column(JSON)

    @classmethod
    def purge_old_records(cls, session, netuid: Optional[int] = None) -> int:
        """
        Purge old records based on retention policy.
        If netuid is provided, purges only for that netuid.
        Returns number of records deleted.
        """
        try:
            # First try time-based retention
            cutoff_date = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
            query = session.query(cls).filter(cls.recorded_at < cutoff_date)
            
            if netuid is not None:
                query = query.filter(cls.netuid == netuid)
            
            time_deleted = query.delete()
            
            # Then try row-count based retention per netuid
            if netuid is not None:
                netuids = [netuid]
            else:
                # Get all unique netuids
                netuids = [r[0] for r in session.query(cls.netuid).distinct().all()]
            
            count_deleted = 0
            for n in netuids:
                # Get count of records for this netuid
                count = session.query(cls).filter(cls.netuid == n).count()
                if count > MAX_ROWS_PER_NETUID:
                    # Get the timestamp of the record that would be kept
                    cutoff_record = session.query(cls)\
                        .filter(cls.netuid == n)\
                        .order_by(cls.recorded_at.desc())\
                        .offset(MAX_ROWS_PER_NETUID - 1)\
                        .first()
                    
                    if cutoff_record:
                        # Delete all records older than this one
                        count_deleted += session.query(cls)\
                            .filter(cls.netuid == n)\
                            .filter(cls.recorded_at < cutoff_record.recorded_at)\
                            .delete()
            
            session.commit()
            total_deleted = time_deleted + count_deleted
            logging.info(f"Purged {total_deleted} old records from {cls.__tablename__}")
            return total_deleted
            
        except Exception as e:
            session.rollback()
            logging.error(f"Error purging old records from {cls.__tablename__}: {str(e)}")
            raise

class SubnetAPY(NetuidTimeSeries):
    """Time series data for subnet APY."""
    __tablename__ = "subnet_apy"

class SubnetEmission(NetuidTimeSeries):
    """Time series data for subnet emissions."""
    __tablename__ = "subnet_emissions"

class SubnetEntropy(NetuidTimeSeries):
    """Time series data for subnet entropy."""
    __tablename__ = "subnet_entropy"

class SubnetReputation(NetuidTimeSeries):
    """Time series data for subnet reputation."""
    __tablename__ = "subnet_reputation"

# Create all tables
def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)

class DBSession:
    """Database session context manager."""
    def __init__(self):
        self.db = None

    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.db:
            self.db.close()

def get_db():
    """Get database session context manager."""
    return DBSession() 