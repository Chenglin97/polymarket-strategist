# mistakes.md

## 2026-04-19
### Mistake: wrong EV logic for NO picks
The old scanner compared belief against `yes_price` even when taking the NO side.
That created fake edges and allowed negative-EV picks into the book.

Example failures:
- Anthropic market cap between $400B-$600B: scanner liked NO, but the NO side was priced around 0.99, so our 0.95 belief was actually negative EV.
- ByteDance second-best coding model: NO looked "obvious", but at effectively 1.00 price it was still a bad trade.

### Fix
- compute `chosen_side_price`
- compute `expected_profit = belief - chosen_side_price`
- reject picks with expected_profit <= 0.05
- reject picks with expected_roi <= 0.20

### Lesson
Feeling right is not enough. The side has to be cheap enough to buy.
