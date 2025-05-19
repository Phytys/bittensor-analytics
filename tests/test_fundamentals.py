import logging
import os
from sqlalchemy import inspect
from app.fundamentals import store_all_subnet_apy, get_latest_apy
from app.models import get_db, SubnetAPY, init_db, Base, engine
from datetime import datetime, timedelta
import pandas as pd

def setup_logging():
    """Configure detailed logging for testing."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Also log to file for review
    file_handler = logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'apy_collection_test.log'))
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    file_handler.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(file_handler)

def setup_database():
    """Initialize database tables."""
    print("\n🗄️  Initializing database...")
    
    # Drop all tables first to ensure clean state
    Base.metadata.drop_all(bind=engine)
    print("✅ Dropped existing tables")
    
    # Create tables
    init_db()
    print("✅ Created new tables")
    
    # Verify tables exist
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"📋 Available tables: {', '.join(tables)}")
    
    if 'subnet_apy' not in tables:
        raise RuntimeError("Failed to create subnet_apy table!")

def verify_data_quality():
    """Verify the quality of collected APY data."""
    db_session = get_db()
    with db_session as db:
        # Get all records from last 5 minutes
        recent = db.query(SubnetAPY).filter(
            SubnetAPY.recorded_at >= datetime.utcnow() - timedelta(minutes=5)
        ).all()
        
        if not recent:
            print("❌ No recent records found!")
            return False
            
        # Convert to DataFrame for analysis
        records = []
        validator_stats = []  # Track individual validator stats
        
        for r in recent:
            record = {
                'netuid': r.netuid,
                'apy': r.data.get('apy'),
                'recorded_at': r.recorded_at,
                'validator_count': len(r.data.get('validator_apys', [])),
            }
            
            # Add validator-specific stats if available
            validator_apys = r.data.get('validator_apys', [])
            if validator_apys:
                # Filter out None values and convert to float, excluding zeros
                apys = [float(v['alpha_apy']) for v in validator_apys 
                       if v.get('alpha_apy') is not None and float(v['alpha_apy']) > 0]
                if apys:
                    record.update({
                        'min_apy': min(apys),
                        'max_apy': max(apys),
                        'avg_apy': sum(apys) / len(apys),
                        'std_apy': pd.Series(apys).std() if len(apys) > 1 else 0,
                        'median_apy': pd.Series(apys).median()
                    })
                    
                    # Add individual validator stats
                    for v in validator_apys:
                        if v.get('alpha_apy') is not None:
                            alpha_apy = float(v['alpha_apy'])
                            if alpha_apy > 0:  # Only include positive APYs
                                validator_stats.append({
                                    'netuid': r.netuid,
                                    'validator_name': v.get('validator_name', 'Unknown'),
                                    'hotkey': v.get('hotkey', '')[:8] + '...',  # Truncate for readability
                                    'alpha_apy': alpha_apy,
                                    'alpha_stake': float(v.get('alpha_stake', 0)),
                                    'nominated_stake': float(v.get('nominated_stake', 0)),
                                    'vtrust': float(v.get('vtrust', 0))
                                })
            
            records.append(record)
        
        df = pd.DataFrame(records)
        validator_df = pd.DataFrame(validator_stats) if validator_stats else None
        
        # Basic statistics
        print("\n📊 Data Quality Report:")
        print(f"Total records: {len(df)}")
        print(f"Unique subnets: {df['netuid'].nunique()}")
        
        if 'validator_count' in df.columns:
            print(f"\nValidator Coverage:")
            print(f"Average validators per subnet: {df['validator_count'].mean():.1f}")
            print(f"Min validators: {df['validator_count'].min()}")
            print(f"Max validators: {df['validator_count'].max()}")
        
        print("\nAPY Statistics:")
        if 'apy' in df.columns:
            print("\nOverall APY per subnet:")
            print(df['apy'].describe())
        
        if all(col in df.columns for col in ['min_apy', 'max_apy', 'avg_apy', 'std_apy', 'median_apy']):
            print("\nValidator-specific APY per subnet:")
            print("Minimum APY (excluding zeros):")
            print(df['min_apy'].describe())
            print("\nMaximum APY:")
            print(df['max_apy'].describe())
            print("\nAverage APY:")
            print(df['avg_apy'].describe())
            print("\nMedian APY:")
            print(df['median_apy'].describe())
            print("\nStandard Deviation:")
            print(df['std_apy'].describe())
        
        if validator_df is not None:
            print("\nTop 5 Validators by APY:")
            top_validators = validator_df.nlargest(5, 'alpha_apy')
            print(top_validators[['netuid', 'validator_name', 'alpha_apy', 'alpha_stake', 'vtrust']].to_string())
            
            print("\nBottom 5 Validators by APY:")
            bottom_validators = validator_df.nsmallest(5, 'alpha_apy')
            print(bottom_validators[['netuid', 'validator_name', 'alpha_apy', 'alpha_stake', 'vtrust']].to_string())
            
            print("\nValidator APY Distribution:")
            print(validator_df['alpha_apy'].describe())
            
            # Check for potential outliers using IQR method
            q1 = validator_df['alpha_apy'].quantile(0.25)
            q3 = validator_df['alpha_apy'].quantile(0.75)
            iqr = q3 - q1
            outliers = validator_df[
                (validator_df['alpha_apy'] < q1 - 1.5 * iqr) |
                (validator_df['alpha_apy'] > q3 + 1.5 * iqr)
            ]
            if not outliers.empty:
                print("\n⚠️ Potential APY outliers detected:")
                print(outliers[['netuid', 'validator_name', 'alpha_apy', 'vtrust']].to_string())
            
            # Check for extreme APY values
            extreme_apy = validator_df[validator_df['alpha_apy'] > 200]  # APY > 200% is extreme
            if not extreme_apy.empty:
                print("\n⚠️ Warning: Found extremely high APY values (>200%):")
                print(extreme_apy[['netuid', 'validator_name', 'alpha_apy', 'vtrust']].to_string())
            
            # Analyze correlation between APY and stake
            correlation = validator_df['alpha_apy'].corr(validator_df['alpha_stake'])
            print(f"\nCorrelation between APY and stake: {correlation:.3f}")
            
            # Analyze correlation between APY and trust
            correlation = validator_df['alpha_apy'].corr(validator_df['vtrust'])
            print(f"Correlation between APY and trust: {correlation:.3f}")
        
        # Check for missing or invalid data
        missing_apy = df[df['apy'].isna()]
        if not missing_apy.empty:
            print("\n⚠️ Warning: Found records with missing APY:")
            print(missing_apy[['netuid', 'recorded_at']])
        
        # Check for reasonable APY values
        unreasonable = df[(df['apy'] < 0) | (df['apy'] > 1000)]  # APY > 1000% is probably wrong
        if not unreasonable.empty:
            print("\n⚠️ Warning: Found potentially unreasonable APY values:")
            print(unreasonable[['netuid', 'apy', 'recorded_at']])
        
        return True

def test_small_batch():
    """Test APY collection with a small batch of subnets."""
    print("\n🧪 Testing APY Collection")
    print("=========================")
    
    # Test with just 3 subnets first
    test_netuids = [1, 2, 3]  # Start with a small batch
    print(f"\nTesting with subnets: {test_netuids}")
    
    # Run collection
    results = store_all_subnet_apy(
        start_netuid=min(test_netuids),
        end_netuid=max(test_netuids)
    )
    
    # Print results
    success_count = sum(1 for success in results.values() if success)
    print(f"\n✅ Collection Results:")
    print(f"Successfully processed: {success_count}/{len(results)} subnets")
    
    # Show latest records
    print("\n📈 Latest APY Records:")
    for record in get_latest_apy():
        if record['netuid'] in test_netuids:
            print(f"Netuid {record['netuid']}: {record['apy']}% (recorded at {record['recorded_at']})")
    
    return success_count == len(test_netuids)

def main():
    """Run the test suite."""
    setup_logging()
    setup_database()  # Initialize database before running tests
    
    print("🚀 Starting APY Collection Test")
    print("==============================")
    
    # Test small batch first
    if test_small_batch():
        print("\n✅ Small batch test successful!")
        
        # Verify data quality
        print("\n🔍 Verifying data quality...")
        if verify_data_quality():
            print("\n✅ Data quality checks passed!")
            
            # If everything looks good, ask before running full collection
            response = input("\nWould you like to run the full collection now? (y/n): ")
            if response.lower() == 'y':
                print("\n🔄 Running full collection...")
                results = store_all_subnet_apy()
                success_count = sum(1 for success in results.values() if success)
                print(f"\n✅ Full collection complete: {success_count}/{len(results)} subnets successful")
        else:
            print("\n❌ Data quality checks failed!")
    else:
        print("\n❌ Small batch test failed!")

if __name__ == "__main__":
    main() 