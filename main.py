import requests
import json
from datetime import datetime, timedelta, timezone
import os

# Endpoints for CLOB API
CLOB_MARKETS_URL = "https://clob.polymarket.com/markets"
CLOB_MARKET_URL = "https://clob.polymarket.com/market/{}"  # expects market_id
CLOB_PRICES_HISTORY_URL = "https://clob.polymarket.com/prices-history"

HISTORY_DIR = "market_histories"
os.makedirs(HISTORY_DIR, exist_ok=True)

# Only select markets in the last year to download
ONE_YEAR_AGO = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=365)
# Only select markets in the last month to download
ONE_MONTH_AGO = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(days=30)

# Use cursor-based pagination for /markets endpoint
next_cursor = ""

while True:
    params = {
        "next_cursor": next_cursor,
    }

    #print(f"Fetching markets with next_cursor '{next_cursor}'...")
    resp = requests.get(CLOB_MARKETS_URL, params=params)
    resp.raise_for_status()
    data = resp.json()
    #print(f"Response: {json.dumps(data, ensure_ascii=False)} ... [truncated]")
    markets = data.get("markets") or data.get("data") or data
    if not markets:
        print("No more markets to fetch.")
        break

    for market in markets:
        if isinstance(market, dict):
            # Try all plausible end date fields, prioritizing 'end_date_iso' as in the example
            end_date_iso = (
                market.get("end_date_iso") or
                market.get("end_date") or
                market.get("resolved_at") or
                market.get("close_time")
            )
            if not end_date_iso:
                continue
            try:
                end_date = datetime.fromisoformat(str(end_date_iso).replace('Z', '+00:00'))
            except Exception:
                continue
            if end_date < ONE_MONTH_AGO:
                continue

            slug = market.get("market_slug") or market.get("slug")
            tokens = market.get("tokens")
            if slug and tokens:
                for token in tokens:
                    token_id = token.get("token_id")
                    if not token_id or not str(token_id).strip():
                        continue
                    prices_params = {"market": token_id, "interval": "max", "fidelity": "1"}
                    prices_resp = requests.get(CLOB_PRICES_HISTORY_URL, params=prices_params)
                    print(f"Fetching prices for token_id {token_id} in market {slug}...")
                    print(f"Prices response: {json.dumps(prices_resp.json(), ensure_ascii=False)}")
                    prices_resp.raise_for_status()
                    prices_data = prices_resp.json()
                    if prices_data.get("history"):
                        safe_slug = str(slug).replace('/', '_').replace(' ', '_')
                        history_path = os.path.join(HISTORY_DIR, f"{safe_slug}_{token_id}.json")
                        with open(history_path, "w") as hist_f:
                            json.dump(prices_data, hist_f, ensure_ascii=False, indent=2)
    # Handle cursor-based pagination
    next_cursor = data.get("next_cursor")
    if not next_cursor or next_cursor == "LTE=":
        break