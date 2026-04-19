#!/usr/bin/env python3
"""
Generate a daily expected return report and chart for paper picks.

Strategy assumptions:
- One contract per pick.
- Expected profit per contract = belief_correct - market_price_paid.
- Realized profit per resolved contract = 1 - market_price_paid if correct else -market_price_paid.

Outputs:
- prediction/expected_return_history.json
- prediction/expected_return_chart.png
- prediction/expected_return_summary.json
"""
import json
import os
from datetime import datetime, timezone

import matplotlib.pyplot as plt

BASE = os.path.dirname(__file__)
PICKS_FILE = os.path.join(BASE, "picks.json")
HISTORY_FILE = os.path.join(BASE, "expected_return_history.json")
SUMMARY_FILE = os.path.join(BASE, "expected_return_summary.json")
CHART_FILE = os.path.join(BASE, "expected_return_chart.png")
STARTING_BANKROLL = 1000.0
STAKE_FRACTION = 0.05


def load_json(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default


def selected_side_price(pick):
    yes = float(pick["market_yes_price"])
    return yes if pick["my_pick"] == "yes" else 1 - yes


def expected_profit(pick):
    return float(pick["my_confidence"]) - selected_side_price(pick)


def expected_roi(pick):
    price = selected_side_price(pick)
    if price <= 0:
        return None
    return expected_profit(pick) / price


def realized_profit(pick):
    price = selected_side_price(pick)
    if pick["status"] == "correct":
        return 1 - price
    if pick["status"] == "wrong":
        return -price
    return 0.0


def simulate_bankroll(picks):
    bankroll = STARTING_BANKROLL
    pending_ev_dollars = 0.0
    resolved_count = 0

    ordered = sorted(
        [p for p in picks if p.get("status") in ("pending", "correct", "wrong")],
        key=lambda p: p.get("picked_at", "")
    )

    for pick in ordered:
        side_price = selected_side_price(pick)
        if side_price <= 0:
            continue
        stake = bankroll * STAKE_FRACTION
        shares = stake / side_price
        if pick["status"] == "correct":
            bankroll += shares * (1 - side_price)
            resolved_count += 1
        elif pick["status"] == "wrong":
            bankroll -= stake
            resolved_count += 1
        elif pick["status"] == "pending":
            pending_ev_dollars += shares * expected_profit(pick)

    return {
        "starting_bankroll": round(STARTING_BANKROLL, 2),
        "stake_fraction": STAKE_FRACTION,
        "realized_bankroll": round(bankroll, 2),
        "pending_ev_dollars": round(pending_ev_dollars, 2),
        "bankroll_plus_pending_ev": round(bankroll + pending_ev_dollars, 2),
        "resolved_positions_count": resolved_count,
    }


def summarize(data):
    picks = data.get("picks", [])
    pending = [p for p in picks if p["status"] == "pending"]
    resolved = [p for p in picks if p["status"] in ("correct", "wrong")]
    legacy_invalid = [p for p in picks if p.get("status") == "legacy_invalid"]

    pending_ev = sum(expected_profit(p) for p in pending)
    pending_ev_positive = sum(max(expected_profit(p), 0) for p in pending)
    realized_pnl = sum(realized_profit(p) for p in resolved)

    valid_strategy_pending = [p for p in pending if expected_profit(p) > 0]
    invalid_strategy_pending = [p for p in pending if expected_profit(p) <= 0]

    sim = simulate_bankroll(picks)

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_picks": len(picks),
        "pending_count": len(pending),
        "resolved_count": len(resolved),
        "win_rate": (sum(1 for p in resolved if p["status"] == "correct") / len(resolved)) if resolved else None,
        "pending_expected_profit_total": round(pending_ev, 6),
        "pending_expected_profit_positive_only": round(pending_ev_positive, 6),
        "realized_profit_total": round(realized_pnl, 6),
        "valid_strategy_pending_count": len(valid_strategy_pending),
        "invalid_strategy_pending_count": len(invalid_strategy_pending),
        "legacy_invalid_count": len(legacy_invalid),
        "sim_starting_bankroll": sim["starting_bankroll"],
        "sim_stake_fraction": sim["stake_fraction"],
        "sim_realized_bankroll": sim["realized_bankroll"],
        "sim_pending_ev_dollars": sim["pending_ev_dollars"],
        "sim_bankroll_plus_pending_ev": sim["bankroll_plus_pending_ev"],
        "sim_resolved_positions_count": sim["resolved_positions_count"],
        "top_pending_by_ev": [
            {
                "question": p["question"],
                "pick": p["my_pick"],
                "market_price_paid": round(selected_side_price(p), 6),
                "belief": round(float(p["my_confidence"]), 6),
                "expected_profit": round(expected_profit(p), 6),
                "expected_roi": round(expected_roi(p), 6) if expected_roi(p) is not None else None,
            }
            for p in sorted(pending, key=expected_profit, reverse=True)[:10]
        ],
    }
    return summary


def append_history(summary):
    history = load_json(HISTORY_FILE, [])
    today = summary["timestamp"][:10]
    point = {
        "date": today,
        "pending_expected_profit_total": summary["pending_expected_profit_total"],
        "pending_expected_profit_positive_only": summary["pending_expected_profit_positive_only"],
        "realized_profit_total": summary["realized_profit_total"],
        "pending_count": summary["pending_count"],
        "valid_strategy_pending_count": summary["valid_strategy_pending_count"],
        "invalid_strategy_pending_count": summary["invalid_strategy_pending_count"],
        "legacy_invalid_count": summary.get("legacy_invalid_count", 0),
        "sim_realized_bankroll": summary.get("sim_realized_bankroll"),
        "sim_pending_ev_dollars": summary.get("sim_pending_ev_dollars"),
        "sim_bankroll_plus_pending_ev": summary.get("sim_bankroll_plus_pending_ev"),
        "win_rate": summary["win_rate"],
    }

    replaced = False
    for i, existing in enumerate(history):
        if existing.get("date") == today:
            history[i] = point
            replaced = True
            break
    if not replaced:
        history.append(point)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
    return history


def render_chart(history):
    if not history:
        return
    dates = [h["date"] for h in history]
    pending_all = [h["pending_expected_profit_total"] for h in history]
    pending_pos = [h["pending_expected_profit_positive_only"] for h in history]
    realized = [h["realized_profit_total"] for h in history]

    plt.figure(figsize=(10, 5))
    plt.plot(dates, pending_all, marker="o", label="Pending EV (all picks)")
    plt.plot(dates, pending_pos, marker="o", label="Pending EV (positive-only picks)")
    plt.plot(dates, realized, marker="o", label="Realized PnL")
    plt.axhline(0, color="gray", linewidth=1)
    plt.title("Prediction Strategy Expected Return")
    plt.ylabel("Profit per 1-contract stake")
    plt.xlabel("Date")
    plt.xticks(rotation=30, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(CHART_FILE, dpi=160)
    plt.close()


def main():
    data = load_json(PICKS_FILE, {"picks": []})
    summary = summarize(data)
    history = append_history(summary)
    render_chart(history)
    with open(SUMMARY_FILE, "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))
    print(CHART_FILE)


if __name__ == "__main__":
    main()
