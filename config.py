
import os
from dotenv import load_dotenv

load_dotenv()

# === API Keys ===
TAO_APP_API_KEY = os.getenv("TAO_APP_API_KEY")

# === API Base URL ===
TAO_API_BASE = "https://api.tao.app"

# === Rate Limiting Settings ===
ENABLE_RATE_LIMITING = True       # Toggle on/off
TAO_APP_RATE_LIMIT_PER_MIN = 10
TAO_APP_RATE_LIMIT_SECONDS = 60 / TAO_APP_RATE_LIMIT_PER_MIN  # Delay between requests

# === Optional: Scoring Weights ===
SUBNET_SCORING_WEIGHTS = {
    "tao_in": 0.20,
    "net_volume_tao": 0.15,
    "tao_sustainability_ratio": 0.15,
    "pnl_trend": 0.10,
    "price_7d": 0.10,
    "github_activity": 0.10,
    "stake_decentralization": 0.10,
    "alpha_apy": 0.10,
}
