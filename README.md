# NVIDIA CEO Price Forecaster

Entry for make.fun bounty [polymarket-nvidia-ceo-forecast-01](https://make.fun/bounty/polymarket-nvidia-ceo-forecast-01).

Forecasts the Yes price of each of the 24 markets of Polymarket's "Next CEO of NVIDIA?" event for every minute of the next 4 hours, as five quantiles (5/25/50/75/95%).

## Model
Per-market empirical volatility with a sub-diffusive spread:

- sigma: robust (95%-clipped) standard deviation of the last 480 one-minute moves, shrunk toward the 0.0025 baseline with weight n/(n+100), scaled by 1.1
- Spread grows as h^0.35 (sub-diffusive; prices mean-revert on this horizon)
- q_tau = clamp(x + z_tau * sigma * h^0.35, 0, 1)

Deterministic, standard library only, no network. Runs in ~0.3 s per case.

Practice pinball loss: 0.2843 (house baseline: 0.3636).
