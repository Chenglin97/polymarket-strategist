#!/usr/bin/env python3
import json
from pathlib import Path
from urllib import parse, request

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT / 'local'
CHAT_FILE = LOCAL / 'telegram_chat_id.txt'
SUMMARY_FILE = ROOT / 'reports' / 'expected_return_summary.json'
RUN_SUMMARY_FILE = ROOT / 'reports' / 'run_summary.json'
STATE_FILE = LOCAL / 'last_sent_summary.json'


def load_token():
    cfg = Path.home() / '.openclaw' / 'openclaw.json'
    data = json.loads(cfg.read_text())
    return data['channels']['telegram']['botToken']


def load_chat_id():
    return CHAT_FILE.read_text().strip()


def load_summary():
    return json.loads(SUMMARY_FILE.read_text())


def load_run_summary():
    if RUN_SUMMARY_FILE.exists():
        return json.loads(RUN_SUMMARY_FILE.read_text())
    return {}


def stable_view(summary):
    return {
        'pending_expected_profit_total': summary.get('pending_expected_profit_total'),
        'pending_expected_profit_positive_only': summary.get('pending_expected_profit_positive_only'),
        'realized_profit_total': summary.get('realized_profit_total'),
        'sim_realized_bankroll': summary.get('sim_realized_bankroll'),
        'sim_pending_ev_dollars': summary.get('sim_pending_ev_dollars'),
        'sim_bankroll_plus_pending_ev': summary.get('sim_bankroll_plus_pending_ev'),
        'pending_count': summary.get('pending_count'),
        'valid_strategy_pending_count': summary.get('valid_strategy_pending_count'),
        'invalid_strategy_pending_count': summary.get('invalid_strategy_pending_count'),
        'legacy_invalid_count': summary.get('legacy_invalid_count'),
        'top_pending_by_ev': summary.get('top_pending_by_ev', [])[:1],
    }


def build_message(summary, run_summary, previous):
    top = summary.get('top_pending_by_ev', [])
    same = previous == stable_view(summary)
    if same:
        lines = [
            'polymarket strategist',
            'no material change this cycle',
            f"new this run: {run_summary.get('new_picks_this_run')} | closed this run: {run_summary.get('resolved_this_run')}",
            f"total: {run_summary.get('total_picks')} | pending: {run_summary.get('pending_count')} | closed: {run_summary.get('resolved_count')}",
            f"positive-only EV: {summary.get('pending_expected_profit_positive_only')}",
            f"sim bankroll: {summary.get('sim_realized_bankroll')} + EV {summary.get('sim_pending_ev_dollars')} = {summary.get('sim_bankroll_plus_pending_ev')}",
        ]
    else:
        lines = [
            'polymarket strategist',
            f"new this run: {run_summary.get('new_picks_this_run')} | closed this run: {run_summary.get('resolved_this_run')}",
            f"total: {run_summary.get('total_picks')} | pending: {run_summary.get('pending_count')} | closed: {run_summary.get('resolved_count')}",
            f"pending EV total: {summary.get('pending_expected_profit_total')}",
            f"positive-only EV: {summary.get('pending_expected_profit_positive_only')}",
            f"realized profit: {summary.get('realized_profit_total')}",
            f"sim bankroll: {summary.get('sim_realized_bankroll')} + EV {summary.get('sim_pending_ev_dollars')} = {summary.get('sim_bankroll_plus_pending_ev')}",
        ]
    if top:
        best = top[0]
        lines.append(f"best current edge: {best['pick'].upper()} | ev {best['expected_profit']:.4f} | {best['question'][:90]}")
    return '\n'.join(lines)


def send(msg):
    token = load_token()
    chat_id = load_chat_id()
    payload = parse.urlencode({'chat_id': chat_id, 'text': msg}).encode()
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    req = request.Request(url, data=payload, method='POST')
    with request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


if __name__ == '__main__':
    if not CHAT_FILE.exists() or not SUMMARY_FILE.exists():
        raise SystemExit(0)
    summary = load_summary()
    run_summary = load_run_summary()
    previous = None
    if STATE_FILE.exists():
        previous = json.loads(STATE_FILE.read_text())
    print(json.dumps(send(build_message(summary, run_summary, previous))))
    LOCAL.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(stable_view(summary), indent=2))
