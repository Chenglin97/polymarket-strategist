# strategy.md

## Goal
Find a small number of repeatable positive-EV opportunities, not a large number of opinions.

## What counts as a valid edge
For a binary market:
- YES side market price = `yes_price`
- NO side market price = `1 - yes_price`
- our belief on chosen side = `q`
- expected profit per 1 contract = `q - chosen_side_price`

We only take a pick if:
1. expected profit > 0.05
2. expected ROI > 0.20
3. liquidity is not obviously dead
4. thesis is explainable in plain English
5. market is inside domains where we might actually have edge

## Domain focus
### Tier 1
- AI model releases
- AI vendor/product milestones
- public AI company/product events

### Tier 2
- BTC/ETH major threshold markets with short windows
- Fed/rates only when market pricing is obviously disconnected from public signals

### Avoid
- sports
- celebrity gossip
- thin politics edge with no proprietary insight
- novelty markets where we are just guessing

## Sizing
For now this is paper trading.
When we go live, default to fractional Kelly, probably 0.1x to 0.25x Kelly, because model error is the real risk.

## What the scanner should do each run
1. fetch lots of active markets
2. resolve existing picks if closed
3. score markets only in target domains
4. reject any negative-EV pick
5. generate daily chart and report
6. log mistakes and weird cases

## What proves the strategy works
Not one lucky hit.
Need:
- 30-50 resolved picks minimum
- calibration check, not just accuracy
- realized PnL compared with expected PnL
- category-level breakdown
- abstention discipline (most markets should be skipped)

## Failure modes to watch
- confusing probability edge with tradable edge
- taking NO at 0.99 because it feels "safe"
- overfitting to headlines
- too-small sample size
- fake precision in confidence scores
