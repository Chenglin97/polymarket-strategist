#!/usr/bin/env python3
"""
Daily market scanner — finds mispriced markets and logs paper picks.
Focuses on tech/AI, crypto, and data-driven domains where I have an edge.

Important strategy rule:
Only add picks with *positive expected value on the side I would actually buy*.
That means for YES picks, compare my belief to YES market price.
For NO picks, compare my belief to NO market price (1 - yes_price).
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
from tracker import load_picks, add_pick, save_picks, check_resolutions, fetch

PICKS_FILE = os.path.join(os.path.dirname(__file__), "picks.json")

MIN_EXPECTED_PROFIT = 0.015
MIN_EXPECTED_ROI = 0.05
MIN_VOLUME = 20
MAX_NEW_PICKS_PER_RUN = 8

def get_all_markets():
    all_markets = []
    for offset in range(0, 2000, 100):
        try:
            m = fetch(f"https://gamma-api.polymarket.com/markets?limit=100&active=true&closed=false&order=volume&ascending=false&offset={offset}")
            batch = m if isinstance(m, list) else m.get("markets", [])
            if not batch:
                break
            all_markets.extend(batch)
        except Exception:
            break
    return all_markets

def analyze_market(market):
    """
    Returns (my_pick, my_confidence, reasoning) or None if no edge.
    my_confidence is the probability that the picked side wins.
    """
    q = market.get("question", "").lower()
    try:
        prices = json.loads(market.get("outcomePrices", "[0,0]"))
        yes_p = float(prices[0])
        no_p = float(prices[1])
    except:
        return None

    # Skip only truly near-certain markets
    if yes_p > 0.98 or yes_p < 0.02:
        return None

    # Looser volume floor for paper trading, we want faster learning
    vol = float(market.get("volume", 0))
    if vol < MIN_VOLUME:
        return None

    # === TECH / AI MARKETS ===
    ai_keywords = ["openai", "gpt", "claude", "anthropic", "gemini", "deepseek",
                   "llama", "mistral", "ai model", "llm", "model release", "benchmark",
                   "github", "open source", "hugging face", "bytedance", "xai", "grok",
                   "meta", "google ai", "agi", "coding model"]

    if any(k in q for k in ai_keywords):
        leadership_terms = ["#1", "number one", "best", "top", "second best", "2nd best", "sota", "state of the art"]
        release_terms = ["release", "launch", "ship", "announce", "roll out"]

        # Generic AI leadership claims: usually better as NO, there are too many strong competitors.
        if any(term in q for term in leadership_terms) and 0.12 < yes_p < 0.88:
            no_conf = min(max(0.70 + yes_p * 0.20, 0.72), 0.88)
            return ("no", no_conf,
                    f"Leadership claims in AI are fragile and crowded. Market YES at {yes_p:.0%} still looks too optimistic versus how quickly rankings shift.")

        # Generic release/launch claims: undervalued launches can be worth small YES bets.
        if any(term in q for term in release_terms) and yes_p < 0.22:
            yes_conf = min(max(yes_p + 0.10, yes_p * 1.8), 0.42)
            return ("yes", yes_conf,
                    f"Launch markets are often underpriced when frontier labs are shipping fast. Market YES at {yes_p:.0%} looks a bit too low.")

        # Gemini release markets - Google has been releasing fast
        if ("gemini" in q and "release" in q) or ("gemini" in q and "launch" in q):
            if yes_p < 0.15:
                return ("yes", min(yes_p * 2.5, 0.40),
                        f"Google's Gemini release velocity is high. Market at {yes_p:.0%} seems low given recent acceleration.")

        # DeepSeek/#1 model claims - highly competitive market, hard to be #1
        if "deepseek" in q and ("#1" in q or "best" in q or "top" in q):
            if yes_p > 0.15:
                return ("no", 0.85,
                        f"Being definitively #1 in AI is hard to hold. DeepSeek is strong but not consistently #1.")

        # ByteDance #1 claim
        if "bytedance" in q and ("#1" in q or "best" in q):
            if yes_p > 0.10:
                return ("no", 0.88,
                        f"ByteDance has strong models but #1 coding/AI is dominated by OpenAI/Anthropic.")

        # Anthropic IPO by 2027 - unlikely given current trajectory
        if "anthropic" in q and "ipo" in q and "2027" in q:
            if yes_p > 0.25:
                return ("no", 0.75,
                        f"Anthropic IPO by 2027 is unlikely given they just raised at $61.5B valuation and are not profitable.")

    # === CRYPTO MARKETS ===
    btc_keywords = ["bitcoin", "btc"]
    eth_keywords = ["ethereum", "eth"]

    if any(k in q for k in btc_keywords):
        # BTC price level markets - compare to current price
        # BTC is currently around $74,674 (Apr 16 2026)
        btc_current = 74674

        if "$150,000" in market.get("question","") or "150k" in q:
            if yes_p > 0.05:
                return ("no", 0.96, f"BTC at ~${btc_current:,}. Reaching $150K in near term is highly unlikely.")

        if "$100,000" in market.get("question","") or "100k" in q:
            # $100K from $74K = +34%, possible in 1-3 months but uncertain
            if "april" in q and yes_p > 0.20:
                return ("no", 0.80, f"BTC at ~${btc_current:,}. Reaching $100K in April requires +34% in <2 weeks.")
            if "may" in q and yes_p > 0.30:
                return ("no", 0.70, f"BTC at ~${btc_current:,}. $100K in May requires significant rally.")

        if "$85,000" in market.get("question","") or "85k" in q:
            if "april" in q and yes_p > 0.15:
                return ("no", 0.75, f"BTC at ~${btc_current:,}. $85K in April requires +13.8% with downtrend visible.")

        if "$80,000" in market.get("question","") or "80k" in q:
            if "april" in q and 0.25 < yes_p < 0.50:
                return ("yes", 0.40, f"BTC at ~${btc_current:,}. $80K is +7.1% - possible but not certain. Slight yes edge.")

    # === GEOPOLITICS - only where I have clear data ===
    if "fed" in q and ("interest rate" in q or "rates" in q):
        if "50 bps" in q and "decrease" in q:
            if yes_p > 0.05:
                return ("no", 0.97, "Fed cutting 50bps is highly unlikely given current inflation data and Fed signals.")
        if "25 bps" in q and "increase" in q:
            if yes_p > 0.05:
                return ("no", 0.96, "Fed hiking 25bps is very unlikely - they are in pause/cut mode.")

    return None

def run():
    data = load_picks()

    # Check for resolutions first
    resolved = check_resolutions(data)
    if resolved:
        print(f"Resolved {resolved} picks")

    # Get all markets and analyze
    print("Fetching markets...")
    markets = get_all_markets()
    print(f"Analyzing {len(markets)} markets...")

    candidates = []
    existing_ids = {p["market_id"] for p in data["picks"]}
    for market in markets:
        result = analyze_market(market)
        if result is None:
            continue
        if market.get("id") in existing_ids:
            continue

        my_pick, my_confidence, reasoning = result
        try:
            prices = json.loads(market.get("outcomePrices", "[0,0]"))
            yes_p = float(prices[0])
        except:
            continue

        side_price = yes_p if my_pick == "yes" else 1 - yes_p
        expected_profit = my_confidence - side_price
        expected_roi = expected_profit / side_price if side_price > 0 else 0

        if expected_profit <= MIN_EXPECTED_PROFIT:
            continue
        if expected_roi <= MIN_EXPECTED_ROI:
            continue

        q = market.get("question", "")
        category = "tech/ai" if any(k in q.lower() for k in ["ai","gpt","gemini","deepseek","anthropic","llm","model","openai","claude"]) else \
                   "crypto" if any(k in q.lower() for k in ["bitcoin","btc","ethereum","eth","crypto"]) else \
                   "macro"

        candidates.append({
            "market": market,
            "question": q,
            "my_pick": my_pick,
            "my_confidence": my_confidence,
            "yes_p": yes_p,
            "reasoning": reasoning,
            "category": category,
            "expected_profit": expected_profit,
            "expected_roi": expected_roi,
            "sort_key": (expected_profit, expected_roi)
        })

    candidates.sort(key=lambda c: c["sort_key"], reverse=True)

    new_picks = 0
    for c in candidates[:MAX_NEW_PICKS_PER_RUN]:
        added = add_pick(
            data,
            c["market"]["id"],
            c["question"],
            c["my_pick"],
            c["my_confidence"],
            c["yes_p"],
            c["reasoning"],
            c["category"],
        )
        if added:
            new_picks += 1
            side_price = c["yes_p"] if c["my_pick"] == "yes" else 1 - c["yes_p"]
            print(f"  NEW PICK: {c['my_pick'].upper()} | belief {c['my_confidence']:.0%} vs paid {side_price:.0%} | EV {c['expected_profit']:.2f} | {c['question'][:65]}")

    save_picks(data)

    # Print summary
    pending = [p for p in data["picks"] if p["status"] == "pending"]
    correct = [p for p in data["picks"] if p["status"] == "correct"]
    wrong = [p for p in data["picks"] if p["status"] == "wrong"]
    total_resolved = len(correct) + len(wrong)

    print(f"\n=== Summary ===")
    print(f"New picks this run: {new_picks}")
    print(f"Total picks: {len(data['picks'])} ({len(pending)} pending)")
    if total_resolved > 0:
        print(f"Accuracy: {len(correct)}/{total_resolved} = {len(correct)/total_resolved*100:.1f}%")
    print(f"Resolved this run: {resolved}")

    # Show top positive-EV pending picks under the corrected strategy
    def pending_ev(p):
        if "expected_profit" in p:
            return p["expected_profit"]
        yes = float(p["market_yes_price"])
        side_price = yes if p["my_pick"] == "yes" else 1 - yes
        return float(p["my_confidence"]) - side_price

    top = sorted(pending, key=pending_ev, reverse=True)[:5]
    if top:
        print(f"\nTop pending picks by expected profit:")
        for p in top:
            print(f"  {p['my_pick'].upper()} ev:{pending_ev(p):.2f} | {p['question'][:65]}")

if __name__ == "__main__":
    run()
