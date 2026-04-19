#!/usr/bin/env python3
import json
import os
from pathlib import Path
from urllib import parse, request

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT / 'local'
CHAT_FILE = LOCAL / 'telegram_chat_id.txt'
SUMMARY_FILE = ROOT / 'reports' / 'expected_return_summary.json'


def load_token():
    cfg = Path.home() / '.openclaw' / 'openclaw.json'
    data = json.loads(cfg.read_text())
    return data['channels']['telegram']['botToken']


def load_chat_id():
    return CHAT_FILE.read_text().strip()


def build_message():
    summary = json.loads(SUMMARY_FILE.read_text())
    top = summary.get('top_pending_by_ev', [])
    lines = [
        'polymarket strategist',
        f"pending EV total: {summary.get('pending_expected_profit_total')}",
        f"positive-only EV: {summary.get('pending_expected_profit_positive_only')}",
        f"realized profit: {summary.get('realized_profit_total')}",
        f"pending picks: {summary.get('pending_count')} (valid: {summary.get('valid_strategy_pending_count')}, invalid legacy: {summary.get('invalid_strategy_pending_count')})",
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
    print(json.dumps(send(build_message())))
