#!/usr/bin/env python3
"""
gex_fetcher.py — GEX Data Fetcher (Railway edition)
Pulls Classic GEX data from GexBot API and saves gex-data.json.
Config is driven entirely by environment variables.
"""

import json
import os
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


# ── Config from environment ────────────────────────────────────────────────────
API_KEY  = os.environ["GEXBOT_API_KEY"]
BASE_URL = os.environ.get("GEXBOT_BASE_URL", "https://api.gexbot.com")
DATA_DIR = os.environ.get("DATA_DIR", "/tmp/brief")

BASELINE_TICKERS = [
    "SPX", "NDX", "VIX",
    "SPY", "QQQ", "IWM",
    "ES_SPX", "NQ_NDX",
    "USO", "GLD", "TLT",
]

EXTRA_TICKERS = [
    "NVDA", "AAPL", "TSLA", "META", "AMD", "MU",
]

AGGREGATION_PERIOD = os.environ.get("GEX_PERIOD", "full")
GREEKS = ["delta", "gamma"]

HEADERS = {"User-Agent": "MorningBrief-Railway/1.0", "Accept": "application/json"}

# ── Helpers ────────────────────────────────────────────────────────────────────

def api_get(url):
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        print(f"  [ERROR] HTTP {e.code} for {url}")
    except URLError as e:
        print(f"  [ERROR] Connection failed: {e.reason}")
    except Exception as e:
        print(f"  [ERROR] {e}")
    return None


def get_available_tickers():
    data = api_get(f"{BASE_URL}/tickers")
    if not data:
        return set()
    supported = set()
    for cat in ["stocks", "indexes", "futures"]:
        supported.update(data.get(cat, []))
    return supported


def get_classic_gex(ticker):
    return api_get(f"{BASE_URL}/{ticker}/classic/{AGGREGATION_PERIOD}?key={API_KEY}")


def get_greeks(ticker, greek):
    return api_get(f"{BASE_URL}/{ticker}/state/{greek}?key={API_KEY}")


# ── Main ───────────────────────────────────────────────────────────────────────

def run():
    print(f"[gex_fetcher] Starting — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    os.makedirs(DATA_DIR, exist_ok=True)

    all_tickers = list(dict.fromkeys(BASELINE_TICKERS + EXTRA_TICKERS))
    available   = get_available_tickers()
    valid       = [t for t in all_tickers if not available or t in available]

    output = {
        "generated_at":       datetime.now().isoformat(),
        "aggregation_period": AGGREGATION_PERIOD,
        "endpoint":           "classic",
        "tickers":            {},
    }

    for ticker in valid:
        print(f"  Fetching {ticker}...")
        entry = {"classic_gex": None, "greeks": {}}

        gex = get_classic_gex(ticker)
        if gex:
            entry["classic_gex"] = gex
            print(f"    ✓ spot={gex.get('spot')}  flip={gex.get('zero_gamma')}  "
                  f"call_wall={gex.get('major_pos_oi')}  put_wall={gex.get('major_neg_oi')}")
        else:
            print(f"    ✗ GEX failed")

        for greek in GREEKS:
            data = get_greeks(ticker, greek)
            if data:
                entry["greeks"][greek] = data

        output["tickers"][ticker] = entry

    out_path = os.path.join(DATA_DIR, "gex-data.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[gex_fetcher] ✓ Saved {out_path} ({len(valid)} tickers)")
    return out_path


if __name__ == "__main__":
    run()
