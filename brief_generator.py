#!/usr/bin/env python3
"""
brief_generator.py — AI Research Agent (Railway edition)
Uses the Anthropic API with web_search to research today's market and
produce a brief-data-YYYY-MM-DD.json file for brief_builder to consume.
"""

import anthropic
import json
import os
import re
from datetime import datetime, date


DATA_DIR = os.environ.get("DATA_DIR", "/tmp/brief")
MODEL    = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# ── GEX summary helper ─────────────────────────────────────────────────────────

def _summarize_gex(gex_path: str) -> str:
    """Extract key levels from gex-data.json into a compact text block."""
    if not os.path.exists(gex_path):
        return "GEX data unavailable."

    with open(gex_path) as f:
        gex = json.load(f)

    lines = [f"GEX data as of: {gex.get('generated_at', 'unknown')}"]
    key_tickers = ["SPX", "SPY", "QQQ", "IWM", "NDX", "USO", "GLD", "TLT",
                   "NVDA", "AAPL", "TSLA", "META", "AMD", "MU"]
    futures_map  = {"ES_SPX": "ES", "NQ_NDX": "NQ"}

    for t in key_tickers + list(futures_map.keys()):
        entry = gex.get("tickers", {}).get(t, {})
        g = entry.get("classic_gex")
        if not g:
            continue
        display = futures_map.get(t, t)
        lines.append(
            f"{display}: spot={g.get('spot')}  gamma_flip={g.get('zero_gamma')}  "
            f"call_wall(oi)={g.get('major_pos_oi')}  put_wall(oi)={g.get('major_neg_oi')}  "
            f"sum_gex_oi={g.get('sum_gex_oi')}"
        )
    return "\n".join(lines)


# ── JSON extraction ────────────────────────────────────────────────────────────

def _extract_json(content: list) -> str:
    """Pull the JSON object out of Claude's response content blocks."""
    full_text = ""
    for block in content:
        if hasattr(block, "text"):
            full_text += block.text

    # Strip markdown fences if present
    clean = re.sub(r"^```(?:json)?\s*", "", full_text.strip(), flags=re.MULTILINE)
    clean = re.sub(r"\s*```$", "", clean.strip(), flags=re.MULTILINE)

    # Find first { ... } block
    start = clean.find("{")
    end   = clean.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in response. Raw:\n{full_text[:500]}")

    json_str = clean[start:end+1]
    json.loads(json_str)  # validate
    return json_str


# ── System prompt ──────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a post-market research agent generating a daily brief for Sharif,
an active options and futures trader. Your job is to research today's market session using
web searches and return a single, valid JSON object — nothing else.

Rules:
- Search for real, current data — never fabricate prices or percentages
- Focus on what actually MOVED markets today (intraday drivers, reversals, volume)
- All "implication" fields must be specific and actionable with real tickers and levels
- Frame GEX levels as tomorrow's key levels (this is a post-market brief)
- Return ONLY the JSON object. No explanation, no markdown fences, no commentary.
- Include 3-5 macro_cards, 3-5 geopolitical items, 6-8 setups, 2-4 earnings entries
"""

# ── User prompt template ───────────────────────────────────────────────────────

def _build_prompt(today: str, gex_summary: str) -> str:
    return f"""Today is {today}. Generate the post-market brief JSON for today's US equity session.

{gex_summary}

Search for:
1. S&P 500, Nasdaq, Dow, Russell 2000, VIX closing prices and % changes
2. DXY, 10Y yield, WTI crude, Brent crude, gold, bitcoin closing prices
3. What drove today's session — intraday moves, key reversals, breadth, volume leaders
4. Top macro news: Fed, geopolitics, economic data releases, how the market reacted
5. Today's AMC earnings results and tomorrow's BMO earnings to watch
6. Sector performance: which sectors led/lagged today
7. Economic calendar: upcoming releases this week and next (time, consensus, prior)
8. Active geopolitical situations impacting markets

Return a JSON object with EXACTLY this structure — use real data from your searches:

{{
  "date": "{today}",
  "date_display": "<Weekday, Month D, YYYY>",
  "headline": "<punchy headline summarizing today's session and dominant theme>",
  "subtitle": "<one sentence bridging today's action to tomorrow's setup>",
  "exec_summary": "<3-4 sentence HTML paragraph using <strong> for key figures. Recap session drivers, key takeaway, tomorrow's GEX levels and catalysts.>",

  "market_snapshot": [
    {{"label": "S&P 500",   "value": "X,XXX",   "change": "X.XX%", "direction": "up|down"}},
    {{"label": "Nasdaq",    "value": "XX,XXX",  "change": "X.XX%", "direction": "up|down"}},
    {{"label": "Dow Jones", "value": "XX,XXX",  "change": "X.XX%", "direction": "up|down"}},
    {{"label": "VIX",       "value": "XX.XX",   "change": "X.XX%", "direction": "up|down"}},
    {{"label": "WTI Crude", "value": "$XX.XX",  "change": "X.XX%", "direction": "up|down"}},
    {{"label": "Gold",      "value": "$X,XXX",  "change": "X.XX%", "direction": "up|down"}},
    {{"label": "DXY",       "value": "XXX.XX",  "change": "X.XX%", "direction": "up|down"}},
    {{"label": "10Y Yield", "value": "X.XXX%",  "change": "X bps", "direction": "up|down"}},
    {{"label": "Bitcoin",   "value": "$XX,XXX", "change": "X.XX%", "direction": "up|down"}},
    {{"label": "Brent",     "value": "$XX.XX",  "change": "X.XX%", "direction": "up|down"}}
  ],

  "sector_rotation": [
    {{"ticker": "XLE",  "name": "Energy",             "color": "#f59e0b", "tail": [[r1,m1],[r2,m2],[r3,m3],[r4,m4],[r5,m5]]}},
    {{"ticker": "XLI",  "name": "Industrials",         "color": "#10b981", "tail": [[r1,m1],[r2,m2],[r3,m3],[r4,m4],[r5,m5]]}},
    {{"ticker": "XLF",  "name": "Financials",          "color": "#818cf8", "tail": [[r1,m1],[r2,m2],[r3,m3],[r4,m4],[r5,m5]]}},
    {{"ticker": "XLV",  "name": "Health Care",         "color": "#a78bfa", "tail": [[r1,m1],[r2,m2],[r3,m3],[r4,m4],[r5,m5]]}},
    {{"ticker": "XLB",  "name": "Materials",           "color": "#fb923c", "tail": [[r1,m1],[r2,m2],[r3,m3],[r4,m4],[r5,m5]]}},
    {{"ticker": "XLP",  "name": "Consumer Staples",    "color": "#34d399", "tail": [[r1,m1],[r2,m2],[r3,m3],[r4,m4],[r5,m5]]}},
    {{"ticker": "XLU",  "name": "Utilities",           "color": "#67e8f9", "tail": [[r1,m1],[r2,m2],[r3,m3],[r4,m4],[r5,m5]]}},
    {{"ticker": "XLC",  "name": "Communication Svcs",  "color": "#fbbf24", "tail": [[r1,m1],[r2,m2],[r3,m3],[r4,m4],[r5,m5]]}},
    {{"ticker": "XLY",  "name": "Consumer Disc",       "color": "#f87171", "tail": [[r1,m1],[r2,m2],[r3,m3],[r4,m4],[r5,m5]]}},
    {{"ticker": "XLK",  "name": "Technology",          "color": "#ef4444", "tail": [[r1,m1],[r2,m2],[r3,m3],[r4,m4],[r5,m5]]}},
    {{"ticker": "XLRE", "name": "Real Estate",         "color": "#94a3b8", "tail": [[r1,m1],[r2,m2],[r3,m3],[r4,m4],[r5,m5]]}}
  ],

  "macro_cards": [
    {{
      "priority": "critical|important|monitor",
      "title": "Card title",
      "body": "2-3 sentences on what happened and how the market reacted.",
      "implication": "Specific actionable trade idea with real tickers and levels for tomorrow."
    }}
  ],

  "calendar": [
    {{
      "date": "Mon 3/16",
      "event": "Event name",
      "detail": "Time ET and brief description with actual/consensus/prior",
      "impact": "high|med|low"
    }}
  ],

  "geopolitical": [
    {{
      "status": "active|escalating|ongoing",
      "status_label": "Display label",
      "title": "Region / Conflict",
      "body": "2-3 sentence situation summary.",
      "watch": "What to monitor and market implications with specific tickers."
    }}
  ],

  "setups": [
    {{
      "ticker": "TICKER / ALT",
      "name": "Full name",
      "notes": "2-3 sentence setup with specific levels. Reference GEX call wall / put wall / gamma flip where relevant."
    }}
  ],

  "earnings": [
    {{
      "ticker": "TICKER",
      "timing": "AMC|BMO",
      "day": "Weekday, Month D",
      "why": "For AMC (today): what the numbers showed and the stock's reaction. For BMO (tomorrow): why it matters and what to watch.",
      "catalyst": false
    }},
    {{
      "ticker": "NON-EARNINGS CATALYST LABEL",
      "timing": "",
      "day": "Date and event name",
      "why": "Explanation of major non-earnings catalyst for tomorrow or this week.",
      "catalyst": true
    }}
  ]
}}

Remember: rs_ratio > 100 = outperforming SPY, rs_momentum > 100 = RS is accelerating.
Quadrants: Leading (>100, >100), Weakening (>100, <100), Lagging (<100, <100), Improving (<100, >100).
Estimate sector tail values from today's relative performance data. Oldest point first, current point last.

Return ONLY the JSON. No other text."""


# ── Main ───────────────────────────────────────────────────────────────────────

def run(today: str | None = None) -> str:
    today = today or date.today().strftime("%Y-%m-%d")
    print(f"[brief_generator] Starting research for {today}...")

    gex_path    = os.path.join(DATA_DIR, "gex-data.json")
    gex_summary = _summarize_gex(gex_path)
    print(f"[brief_generator] GEX summary:\n{gex_summary}\n")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    messages = [{"role": "user", "content": _build_prompt(today, gex_summary)}]

    print(f"[brief_generator] Calling {MODEL} with web_search tool...")
    response = client.messages.create(
        model=MODEL,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 20,
        }],
        messages=messages,
    )

    # If the model stopped to use tools, keep going until end_turn
    while response.stop_reason == "tool_use":
        tool_uses   = [b for b in response.content if b.type == "tool_use"]
        tool_results = []
        for tu in tool_uses:
            print(f"[brief_generator]   🔍 web_search: {tu.input.get('query', '')[:80]}")
            tool_results.append({
                "type":       "tool_result",
                "tool_use_id": tu.id,
                "content":    tu.output if hasattr(tu, "output") else "",
            })

        messages = messages + [
            {"role": "assistant", "content": response.content},
            {"role": "user",      "content": tool_results},
        ]
        response = client.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=[{
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 20,
            }],
            messages=messages,
        )

    print(f"[brief_generator] Response received (stop_reason={response.stop_reason})")

    json_str  = _extract_json(response.content)
    out_path  = os.path.join(DATA_DIR, f"brief-data-{today}.json")
    with open(out_path, "w") as f:
        f.write(json_str)

    print(f"[brief_generator] ✓ Saved {out_path}")
    return out_path


if __name__ == "__main__":
    run()
