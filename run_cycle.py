#!/usr/bin/env python3
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
DATA.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)

dst_picks = DATA / 'picks.json'
if not dst_picks.exists():
    dst_picks.write_text(json.dumps({"picks": [], "stats": {"total": 0, "correct": 0, "pending": 0}}, indent=2))

# repo-local run state, no more syncing from workspace
local_picks = ROOT / 'picks.json'
local_picks.write_text(dst_picks.read_text())

scan = subprocess.run(['python3', str(ROOT / 'scan_and_pick.py')], cwd=str(ROOT), capture_output=True, text=True)
report = subprocess.run(['python3', str(ROOT / 'report_expected_return.py')], cwd=str(ROOT), capture_output=True, text=True)

# sync outputs into repo structure
if local_picks.exists():
    dst_picks.write_text(local_picks.read_text())

for name in ['expected_return_history.json', 'expected_return_summary.json', 'expected_return_chart.png']:
    src = ROOT / name
    if src.exists():
        target = REPORTS / name
        if name.endswith('.png'):
            target.write_bytes(src.read_bytes())
        else:
            target.write_text(src.read_text())

summary = {}
summary_path = REPORTS / 'expected_return_summary.json'
if summary_path.exists():
    summary = json.loads(summary_path.read_text())

latest = REPORTS / 'latest.md'
now = datetime.now(timezone.utc).isoformat()
latest.write_text(
    f"# polymarket strategist\n\n"
    f"timestamp: {now}\n\n"
    f"## scan stdout\n```\n{scan.stdout.strip()}\n```\n\n"
    f"## report stdout\n```\n{report.stdout.strip()}\n```\n\n"
    f"## summary\n"
    f"- total picks: {summary.get('total_picks')}\n"
    f"- pending: {summary.get('pending_count')}\n"
    f"- resolved: {summary.get('resolved_count')}\n"
    f"- win rate: {summary.get('win_rate')}\n"
    f"- pending EV total: {summary.get('pending_expected_profit_total')}\n"
    f"- positive-only pending EV: {summary.get('pending_expected_profit_positive_only')}\n"
    f"- realized profit total: {summary.get('realized_profit_total')}\n"
    f"- valid pending picks: {summary.get('valid_strategy_pending_count')}\n"
    f"- invalid live picks: {summary.get('invalid_strategy_pending_count')}\n"
    f"- archived legacy picks: {summary.get('legacy_invalid_count')}\n"
    f"- simulated realized bankroll: {summary.get('sim_realized_bankroll')}\n"
    f"- simulated pending EV dollars: {summary.get('sim_pending_ev_dollars')}\n"
    f"- simulated bankroll plus pending EV: {summary.get('sim_bankroll_plus_pending_ev')}\n"
)

# write run-specific archive
archive = REPORTS / 'history'
archive.mkdir(exist_ok=True)
stamp = datetime.now().strftime('%Y-%m-%d-%H%M%S')
(archive / f'{stamp}.md').write_text(latest.read_text())

# auto-commit and push if there are changes
if (ROOT / '.git').exists():
    subprocess.run(['git', 'add', '.'], cwd=str(ROOT), check=False)
    status = subprocess.run(['git', 'status', '--porcelain'], cwd=str(ROOT), capture_output=True, text=True)
    if status.stdout.strip():
        subprocess.run(['git', 'commit', '-m', f'polymarket strategist cycle {stamp}'], cwd=str(ROOT), check=False)
        subprocess.run(['git', 'push'], cwd=str(ROOT), check=False)

# best-effort Telegram report for the owner
notify = ROOT / 'notify_telegram.py'
if notify.exists():
    subprocess.run(['python3', str(notify)], cwd=str(ROOT), check=False)

print(latest.read_text())
