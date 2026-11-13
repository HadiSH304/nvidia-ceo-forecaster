#!/usr/bin/env python3
"""NVIDIA CEO price forecaster - empirical per-market volatility, subdiffusive spread.

q_tau = clamp(x + z_tau * sigma * h^0.35)
sigma = shrink(clip-robust std of last-480-minute moves, baseline 0.0025) * 1.1
"""
import json, math, os, glob

ZS = [-1.6448536269514722, -0.6744897501960817, 0.0, 0.6744897501960817, 1.6448536269514722]
QS = [0.05, 0.25, 0.5, 0.75, 0.95]

WIN = 480
CLIP_MULT = 1.5
SHRINK_N = 100
SIGMA_MULT = 1.1
EXP = 0.35

def sigma_emp(prices):
    p = prices
    w = p[-WIN:] if len(p) >= WIN else p
    if len(w) < 30:
        return 0.0025
    moves = [w[i] - w[i-1] for i in range(1, len(w))]
    am = sorted(abs(t) for t in moves)
    clip = max(am[int(0.95 * len(am))] * CLIP_MULT, 0.001)
    cm = [min(max(t, -clip), clip) for t in moves]
    mu = sum(cm) / len(cm)
    var = sum((t - mu) ** 2 for t in cm) / max(1, len(cm) - 1)
    sigma = math.sqrt(var)
    wgt = len(w) / (len(w) + SHRINK_N)
    sigma = wgt * sigma + (1 - wgt) * 0.0025
    return min(max(sigma * SIGMA_MULT, 0.0005), 0.08)

def main():
    indir = os.environ.get('MAKEFUN_INPUT_DIR', '/input')
    outdir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(outdir, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(indir, '*.in'))):
        case = json.load(open(path))
        cid = case['case']
        forecasts = []
        for m in case['markets']:
            x = m['prices'][-1]
            sig = sigma_emp(m['prices'])
            q = []
            for h in range(1, 241):
                s = sig * (h ** EXP)
                q.append([max(0.0, min(1.0, x + z * s)) for z in ZS])
            forecasts.append({'id': m['id'], 'q': q})
        with open(os.path.join(outdir, f'{cid}.out'), 'w') as f:
            json.dump({'forecasts': forecasts}, f, separators=(',', ':'))

if __name__ == '__main__':
    main()
