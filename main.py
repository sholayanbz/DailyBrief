#!/usr/bin/env python3
"""
main.py — Daily Brief Pipeline Orchestrator
Railway runs this via cron: "python main.py"

Pipeline:
  1. gex_fetcher   → gex-data.json
  2. brief_generator → brief-data-YYYY-MM-DD.json  (Claude API + web_search)
  3. brief_builder → post-market-brief-YYYY-MM-DD.html
  4. emailer       → sends HTML email to EMAIL_TO
"""

import os
import sys
import traceback
from datetime import date, datetime

# Ensure DATA_DIR exists before any module uses it
DATA_DIR = os.environ.get("DATA_DIR", "/tmp/brief")
os.makedirs(DATA_DIR, exist_ok=True)
os.environ["DATA_DIR"] = DATA_DIR  # propagate to all modules

import gex_fetcher
import brief_generator
import brief_builder
import emailer


def log(msg: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def run():
    today = date.today().strftime("%Y-%m-%d")
    log(f"=== Daily Brief Pipeline starting — {today} ===")
    log(f"DATA_DIR={DATA_DIR}")

    # ── Step 1: Fetch GEX data ─────────────────────────────────────────────────
    log("Step 1/4 — Fetching GEX data...")
    try:
        gex_fetcher.run()
        log("Step 1 ✓")
    except Exception:
        log("Step 1 ✗ — GEX fetch failed. Continuing without fresh GEX data.")
        traceback.print_exc()

    # ── Step 2: Research & generate brief-data JSON ────────────────────────────
    log("Step 2/4 — Running AI research agent...")
    try:
        data_path = brief_generator.run(today)
        log(f"Step 2 ✓ → {data_path}")
    except Exception:
        log("Step 2 ✗ — Brief generation failed. Aborting pipeline.")
        traceback.print_exc()
        sys.exit(1)

    # ── Step 3: Build HTML ─────────────────────────────────────────────────────
    log("Step 3/4 — Building HTML brief...")
    try:
        html_path = brief_builder.run(data_path)
        log(f"Step 3 ✓ → {html_path}")
    except Exception:
        log("Step 3 ✗ — HTML build failed. Aborting pipeline.")
        traceback.print_exc()
        sys.exit(1)

    # ── Step 4: Email the brief ────────────────────────────────────────────────
    log("Step 4/4 — Sending email...")
    try:
        emailer.run(html_path)
        log("Step 4 ✓ — Brief delivered.")
    except Exception:
        log("Step 4 ✗ — Email failed. Brief was generated but not sent.")
        traceback.print_exc()
        sys.exit(1)

    log(f"=== Pipeline complete ===")


if __name__ == "__main__":
    run()
