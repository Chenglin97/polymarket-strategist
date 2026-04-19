#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
CRON_LINE="0 */2 * * * cd $ROOT && /usr/bin/python3 $ROOT/run_cycle.py >> $ROOT/reports/cron.log 2>&1"
( crontab -l 2>/dev/null | grep -v 'polymarket-strategist/run_cycle.py' ; echo "$CRON_LINE" ) | crontab -
echo "Installed cron: $CRON_LINE"
