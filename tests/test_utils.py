import logging
from app.utils import load_latest_apy_df
import pandas as pd

def test_load_latest_apy():
    """Test the load_latest_apy_df function."""
    print("\n🧪 Testing load_latest_apy_df()")
    print("=============================")
    
    # Load the data
    df = load_latest_apy_df()
    
    # Basic DataFrame info
    print("\nDataFrame Info:")
    print("--------------")
    print(f"Shape: {df.shape}")
    print(f"\nColumns: {df.columns.tolist()}")
    
    # Sample data
    print("\nFirst 5 rows:")
    print("------------")
    print(df.head().to_string())
    
    # Data quality checks
    print("\nData Quality Checks:")
    print("------------------")
    print(f"Missing values:\n{df.isnull().sum()}")
    print(f"\nData types:\n{df.dtypes}")
    
    # APY statistics
    print("\nAPY Statistics:")
    print("-------------")
    apy_cols = [col for col in df.columns if 'apy' in col]
    print(df[apy_cols].describe().round(2))
    
    # Validator coverage
    print("\nValidator Coverage:")
    print("-----------------")
    if 'validator_count' in df.columns:
        print(f"Total validators: {df['validator_count'].sum()}")
        print(f"Average validators per subnet: {df['validator_count'].mean():.1f}")
        print(f"Min validators: {df['validator_count'].min()}")
        print(f"Max validators: {df['validator_count'].max()}")
    
    # Timestamp check
    print("\nTimestamp Check:")
    print("--------------")
    print(f"Most recent record: {df['recorded_at'].max()}")
    print(f"Oldest record: {df['recorded_at'].min()}")
    print(f"Time span: {df['recorded_at'].max() - df['recorded_at'].min()}")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Run the test
    test_load_latest_apy() 