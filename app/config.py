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

# === API Base URL ===
TAO_API_BASE = "https://api.tao.app"

# === Caching Configuration ===
CACHE_TYPE = os.getenv("CACHE_TYPE", "filesystem")  # Options: 'filesystem', 'redis', etc.
CACHE_DIR = os.getenv("CACHE_DIR", "./cache")       # Used if CACHE_TYPE == 'filesystem'
CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))  # in seconds

# === Database Configuration ===
# Handle Heroku's PostgreSQL URL format
database_url = os.getenv("DATABASE_URL", "sqlite:///tao_cache.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
DATABASE_URI = database_url
SQLALCHEMY_TRACK_MODIFICATIONS = False

# === Rate Limiting (disabled with caching) ===
ENABLE_RATE_LIMITING = False
TAO_APP_RATE_LIMIT_PER_MIN = 10
TAO_APP_RATE_LIMIT_SECONDS = 60 / TAO_APP_RATE_LIMIT_PER_MIN

# === Scoring Weights ===
SUBNET_SCORING_WEIGHTS = {
    "tao_in": 0.20,          # Liquidity weight
    "market_cap": 0.15,      # Total value weight (renamed from norm_price)
    "price_7d_pct_change": 0.10,  # Momentum weight
    "has_github": 0.05,      # Development activity weight
    "has_website": 0.05,     # Project maturity weight
}
