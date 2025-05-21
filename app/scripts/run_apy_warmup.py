#!/usr/bin/env python3
"""
Script to run APY warmup, can be used both locally and on Heroku.
For Heroku: heroku run python -m app.scripts.run_apy_warmup
For local: python -m app.scripts.run_apy_warmup
"""
import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

from app.subnet_metrics import store_all_subnet_apy

def main():
    """Run the APY warmup script."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Check if we're running on Heroku
    if not os.environ.get('DYNO'):
        logger.warning("Not running on Heroku - this is fine for local testing")

    try:
        logger.info("🚀 Starting APY data collection...")
        results = store_all_subnet_apy()
        success_count = sum(1 for success in results.values() if success)
        logger.info(f"✨ APY data collection complete. Success: {success_count}/{len(results)} subnets")
        return True
    except Exception as e:
        logger.error(f"❌ Error during APY data collection: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
