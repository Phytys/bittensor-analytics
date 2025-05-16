
import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from config import (
    TAO_API_BASE,
    TAO_APP_API_KEY,
    TAO_APP_RATE_LIMIT_SECONDS,
    ENABLE_RATE_LIMITING
)

load_dotenv()
HEADERS = {"X-API-Key": TAO_APP_API_KEY}

def rate_limited_fetch(endpoint: str, params: dict = None):
    """
    Universal wrapper for GET requests to TAO.app API with optional rate limiting.
    """
    url = f"{TAO_API_BASE}{endpoint}"

    if ENABLE_RATE_LIMITING:
        time.sleep(TAO_APP_RATE_LIMIT_SECONDS)

    response = requests.get(url, headers=HEADERS, params=params or {})

    if response.status_code != 200:
        raise requests.HTTPError(
            f"API Error {response.status_code}: {response.text}",
            response=response
        )

    return response.json()

def fetch_subnet_info():
    data = rate_limited_fetch("/api/beta/analytics/subnets/info")
    return pd.DataFrame(data)
