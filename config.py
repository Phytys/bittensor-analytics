import os
from dotenv import load_dotenv

load_dotenv()

# === API Keys ===
TAO_APP_API_KEY = os.getenv("TAO_APP_API_KEY")

# === API Base URL ===
TAO_API_BASE = "https://api.tao.app"

# === Caching Configuration ===
CACHE_TYPE = os.getenv("CACHE_TYPE", "filesystem")  # Options: 'filesystem', 'redis', etc.
CACHE_DIR = os.getenv("CACHE_DIR", "./cache")       # Used if CACHE_TYPE == 'filesystem'
CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "300"))  # in seconds

# === Database Configuration ===
# Using SQLite for simplicity; can switch via DATABASE_URI env var (e.g., Postgres on Heroku)
DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///tao_cache.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# === Rate Limiting (disabled with caching) ===
ENABLE_RATE_LIMITING = False
TAO_APP_RATE_LIMIT_PER_MIN = 10
TAO_APP_RATE_LIMIT_SECONDS = 60 / TAO_APP_RATE_LIMIT_PER_MIN

# === Scoring Weights ===
SUBNET_SCORING_WEIGHTS = {
    "tao_in": 0.20,
    "norm_price": 0.10,
    "price_7d_pct_change": 0.10,
    "has_github": 0.05,
    "has_website": 0.05,
}
