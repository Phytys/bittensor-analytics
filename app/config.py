import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

def get_required_env(key: str, default=None):
    """Get required environment variable or raise error if not set."""
    value = os.getenv(key, default)
    if value is None:
        raise RuntimeError(f"Required environment variable {key} is not set")
    return value

# === API Keys ===
TAO_APP_API_KEY = get_required_env("TAO_APP_API_KEY")
COINGECKO_API_KEY = os.environ.get('COINGECKO_API_KEY')

# === API Base URL ===
TAO_API_BASE = "https://api.tao.app"

# === Caching Configuration ===
CACHE_TYPE = os.getenv("CACHE_TYPE", "filesystem")  # Options: 'filesystem', 'redis', etc.
CACHE_DIR = os.getenv("CACHE_DIR", "./cache")       # Used if CACHE_TYPE == 'filesystem'
CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "600"))  # in seconds

# === Rate Limiting Configuration ===
# Flask web application rate limits (for incoming HTTP requests)
ENABLE_RATE_LIMITING = True  # Always enabled in production
RATE_LIMITS = {
    "default": "60/minute",  # Default rate limit
    "blog": "30/minute",     # Blog-specific rate limit
}

# === TAO.app API Rate Limiting ===
# Controls rate limiting for outgoing requests to TAO.app API
TAO_API_RATE_LIMIT = {
    "requests_per_minute": int(os.getenv("TAO_API_REQUESTS_PER_MINUTE", "30")),  # Default: 30 requests per minute
    "initial_retry_delay": float(os.getenv("TAO_API_INITIAL_RETRY_DELAY", "1.0")),  # Initial delay in seconds
    "max_retries": int(os.getenv("TAO_API_MAX_RETRIES", "3")),  # Maximum number of retries
    "max_retry_delay": float(os.getenv("TAO_API_MAX_RETRY_DELAY", "30.0")),  # Maximum retry delay in seconds
    "batch_size": int(os.getenv("TAO_API_BATCH_SIZE", "5")),  # Number of requests to process before pausing
    "batch_delay": float(os.getenv("TAO_API_BATCH_DELAY", "2.0")),  # Delay between batches in seconds
}

# === Database Configuration ===
# Handle Heroku's PostgreSQL URL format
database_url = os.getenv("DATABASE_URL", "sqlite:///tao_cache.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
DATABASE_URI = database_url
SQLALCHEMY_TRACK_MODIFICATIONS = False

# === Scoring Weights ===
SUBNET_SCORING_WEIGHTS = {
    "tao_in": 0.20,          # Liquidity weight
    "market_cap": 0.15,      # Total value weight (renamed from norm_price)
    "price_7d_pct_change": 0.10,  # Momentum weight
    "has_github": 0.05,      # Development activity weight
    "has_website": 0.05,     # Project maturity weight
}

# === Data Retention Settings ===
# Time series data retention configuration
RETENTION_DAYS = int(os.getenv("RETENTION_DAYS", "30"))  # Days to keep time series data
MAX_ROWS_PER_NETUID = int(os.getenv("MAX_ROWS_PER_NETUID", "100"))  # Max rows per netuid
DATA_FETCH_FREQUENCIES = {
    "apy": "daily",  # APY and emissions data
    "emissions": "daily",
    "entropy": "hourly",  # Entropy and reputation data
    "reputation": "hourly",
    "metadata": "weekly"  # GitHub and other metadata
}
