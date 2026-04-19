# polymarket-strategist

A living repo for a repeatable Polymarket scanning strategy.

## Mission
Build a prediction-market process that is:
- explicit
- measurable
- updated from mistakes
- committed continuously
- run every 2 hours

Every cycle should:
1. scan markets
2. update open picks
3. calculate expected return correctly
4. generate a chart and written report
5. commit changes when there is something new or notable

## What this repo stores
- strategy rules
- research notes on what works
- mistakes log
- raw picks data
- daily/rolling reports
- expected return chart

## Core principle
No pick gets added unless it is positive expected value on the side we would actually buy.

## Cadence
- run every 2 hours via cron
- update `reports/latest.md`
- update `data/picks.json`
- update `reports/expected_return_chart.png`

## Current status
The original scanner had an EV bug on `NO` picks. This repo exists to make the process explicit and auditable so that kind of mistake gets caught fast and documented.
