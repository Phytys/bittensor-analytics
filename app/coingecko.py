import requests
from datetime import datetime, timedelta
from app.utils import SessionLocal, TaoPriceHistory, Base
from app.config import COINGECKO_API_KEY
import logging

COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
TAO_ID = "bittensor"

logger = logging.getLogger(__name__)

def fetch_tao_price_from_coingecko():
    """
    Fetch the current TAO price in USD from CoinGecko.
    Returns (price, timestamp) or (None, None) on error.
    """
    url = f"{COINGECKO_API_URL}/simple/price"
    params = {
        "ids": TAO_ID,
        "vs_currencies": "usd"
    }
    headers = {
        "x-cg-pro-api-key": COINGECKO_API_KEY
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        price = data.get(TAO_ID, {}).get("usd")
        if price is not None:
            return float(price), datetime.utcnow()
    except Exception as e:
        logger.error(f"Error fetching TAO price from CoinGecko: {e}")
    return None, None

def fetch_tao_price_history_from_coingecko(days=365):
    """
    Fetch daily close TAO price for the past `days` days from CoinGecko.
    Returns a list of dicts: [{date, price_usd}]
    """
    url = f"{COINGECKO_API_URL}/coins/{TAO_ID}/market_chart"
    params = {
        "vs_currency": "usd",
        "days": days,
        "interval": "daily"
    }
    headers = {
        "x-cg-pro-api-key": COINGECKO_API_KEY
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        prices = data.get("prices", [])
        # prices: list of [timestamp_ms, price]
        result = []
        for ts, price in prices:
            date = datetime.utcfromtimestamp(ts / 1000).replace(hour=0, minute=0, second=0, microsecond=0)
            result.append({"date": date, "price_usd": float(price)})
        return result
    except Exception as e:
        logger.error(f"Error fetching TAO price history from CoinGecko: {e}")
        return []

def update_tao_price_history(days=365):
    """
    Fetch and store daily close TAO price for the past `days` days in the database.
    Skips dates already present.
    """
    session = SessionLocal()
    existing_dates = set(r.date.date() for r in session.query(TaoPriceHistory.date).all())
    history = fetch_tao_price_history_from_coingecko(days)
    new_rows = 0
    for entry in history:
        if entry["date"].date() not in existing_dates:
            row = TaoPriceHistory(
                date=entry["date"],
                price_usd=entry["price_usd"],
                source="coingecko",
                updated_at=datetime.utcnow()
            )
            session.add(row)
            new_rows += 1
    if new_rows > 0:
        session.commit()
    session.close()
    logger.info(f"Added {new_rows} new TAO price history rows.")
    return new_rows

def get_latest_tao_price():
    """
    Get the most recent TAO price from the database, or fetch from CoinGecko if not available.
    Returns (price, date).
    """
    session = SessionLocal()
    row = session.query(TaoPriceHistory).order_by(TaoPriceHistory.date.desc()).first()
    session.close()
    if row and row.price_usd is not None:
        return row.price_usd, row.date
    # Fallback: fetch from API and store
    price, ts = fetch_tao_price_from_coingecko()
    if price is not None:
        session = SessionLocal()
        row = TaoPriceHistory(
            date=ts.replace(hour=0, minute=0, second=0, microsecond=0),
            price_usd=price,
            source="coingecko",
            updated_at=datetime.utcnow()
        )
        session.add(row)
        session.commit()
        session.close()
        return price, ts
    return None, None 