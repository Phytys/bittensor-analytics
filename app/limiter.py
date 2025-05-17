from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.config import ENABLE_RATE_LIMITING, RATE_LIMITS

# Initialize rate limiter with in-memory storage
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    enabled=ENABLE_RATE_LIMITING,
    default_limits=[RATE_LIMITS["default"]]
) 