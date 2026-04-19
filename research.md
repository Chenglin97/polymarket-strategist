# research.md

## What seems to work for other prediction-market participants

This is the initial research baseline, not gospel.

### 1. Specialization beats generic forecasting
Prediction markets aggregate public information fast. The easiest way to lose money is to have broad opinions on everything.
The only plausible edge is in narrow domains where:
- you understand the news flow
- you understand how the market overreacts or underreacts
- you can estimate base rates better than the crowd

### 2. Positive EV matters more than hit rate
A high win rate can still lose money if you keep buying overpriced contracts.
This is the exact bug the old scanner had on NO picks.
So the process must optimize for:
- expected value
- expected ROI
- sizing discipline
not just accuracy.

### 3. Calibration matters
A forecaster who says 70% should be right about 70% of the time over many similar cases.
We need to compare:
- predicted probability buckets
- realized outcomes
This is better than bragging about 1 or 2 correct calls.

### 4. Base rates first, narratives second
The crowd often gets excited by narratives.
Useful pattern:
1. ask the base rate
2. ask what must happen for this market to resolve YES
3. compare that path to real timing constraints

### 5. Fractional Kelly is safer than full Kelly
Even with edge, model error is huge.
So if we ever trade real money:
- use fractional Kelly
- keep position sizes small
- survive variance

### 6. Abstention is a feature
If the scanner finds only 1 real edge in 2000 markets, that is good.
It means it is filtering instead of hallucinating conviction.

## Initial external reference themes
- prediction markets work by aggregating dispersed information
- market prices move fast, so edge is rare
- bankroll/risk sizing matters when edge is real

## Current conclusion
Our edge, if any, will come from:
- AI market specialization
- strict EV filtering
- careful postmortems
- consistency in logging and review
