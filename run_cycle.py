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

# sync source strategy scripts from workspace version for now
WORKSPACE_PRED = Path('/home/chenglin/.openclaw/workspace/prediction')
for name in ['scan_and_pick.py', 'tracker.py', 'report_expected_return.py']:
    src = WORKSPACE_PRED / name
    dst = ROOT / name
    if src.exists():
        dst.write_text(src.read_text())

# seed picks file if missing
src_picks = WORKSPACE_PRED / 'picks.json'
dst_picks = DATA / 'picks.json'
if not dst_picks.exists() and src_picks.exists():
    dst_picks.write_text(src_picks.read_text())

# patch script-local expected files by running from repo root with cwd and env symlink strategy
# easiest is copy current data file into local expected location before run and back after
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
    f"- invalid legacy picks: {summary.get('invalid_strategy_pending_count')}\n"
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

print(latest.read_text())
