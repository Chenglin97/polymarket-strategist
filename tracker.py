#!/usr/bin/env python3
"""
Polymarket Paper Trading Tracker
Fetches markets, logs my predictions, tracks outcomes.
Run daily to update picks and check resolutions.
"""
import json, os, time, urllib.request
from datetime import datetime, timezone

TRACKER_FILE = os.path.join(os.path.dirname(__file__), "picks.json")
POLYMARKET_API = "https://gamma-api.polymarket.com"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def load_picks():
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE) as f:
            return json.load(f)
    return {"picks": [], "stats": {"total": 0, "correct": 0, "pending": 0}}

def save_picks(data):
    with open(TRACKER_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_markets(limit=200):
    markets = fetch(f"{POLYMARKET_API}/markets?limit={limit}&active=true&closed=false&order=volume&ascending=false")
    return markets if isinstance(markets, list) else markets.get("markets", [])

def check_resolutions(data):
    """Check if any pending picks have resolved."""
    updated = 0
    for pick in data["picks"]:
        if pick["status"] != "pending":
            continue
        try:
            market = fetch(f"{POLYMARKET_API}/markets/{pick['market_id']}")
            prices = json.loads(market.get("outcomePrices", "[0,0]"))
            yes_p = float(prices[0])
            closed = market.get("closed", False)
            if closed:
                # Resolved: yes_p ~1.0 means yes won, ~0.0 means no won
                resolved_yes = yes_p > 0.95
                my_pick_yes = pick["my_pick"] == "yes"
                pick["status"] = "correct" if resolved_yes == my_pick_yes else "wrong"
                pick["resolved_at"] = datetime.now(timezone.utc).isoformat()
                pick["final_yes_price"] = yes_p
                updated += 1
                data["stats"]["total"] += 1
                if pick["status"] == "correct":
                    data["stats"]["correct"] += 1
        except Exception as e:
            pass
    return updated

def add_pick(data, market_id, question, my_pick, my_confidence, market_yes_price, reasoning, category):
    """Add a new paper trade pick."""
    # Don't double-pick
    for p in data["picks"]:
        if p["market_id"] == market_id:
            return False
    selected_side_price = market_yes_price if my_pick == "yes" else 1 - market_yes_price
    expected_profit = my_confidence - selected_side_price
    expected_roi = expected_profit / selected_side_price if selected_side_price > 0 else None
    data["picks"].append({
        "market_id": market_id,
        "question": question,
        "my_pick": my_pick,
        "my_confidence": my_confidence,
        "market_yes_price": market_yes_price,
        "selected_side_price": selected_side_price,
        "expected_profit": expected_profit,
        "expected_roi": expected_roi,
        "edge": expected_profit,
        "reasoning": reasoning,
        "category": category,
        "picked_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "resolved_at": None,
        "final_yes_price": None
    })
    data["stats"]["pending"] = sum(1 for p in data["picks"] if p["status"] == "pending")
    return True

if __name__ == "__main__":
    data = load_picks()
    resolved = check_resolutions(data)
    save_picks(data)
    
    stats = data["stats"]
    pending = sum(1 for p in data["picks"] if p["status"] == "pending")
    correct = sum(1 for p in data["picks"] if p["status"] == "correct")
    wrong = sum(1 for p in data["picks"] if p["status"] == "wrong")
    total_resolved = correct + wrong
    
    print(f"=== Polymarket Paper Tracker ===")
    print(f"Total picks: {len(data['picks'])}")
    print(f"Pending: {pending}")
    print(f"Resolved: {total_resolved} ({correct} correct, {wrong} wrong)")
    if total_resolved > 0:
        print(f"Accuracy: {correct/total_resolved*100:.1f}%")
    print(f"Resolved this run: {resolved}")
    print(f"\nRecent picks:")
    for p in sorted(data["picks"], key=lambda x: x["picked_at"], reverse=True)[:10]:
        edge_str = f"+{p['edge']:.2f}" if p["my_pick"] == "yes" and p["my_confidence"] > p["market_yes_price"] else f"{p['edge']:.2f}"
        print(f"  [{p['status']}] {p['my_pick'].upper()} | edge:{edge_str} | {p['question'][:60]}")
