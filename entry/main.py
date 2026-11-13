import sys
import json
import math

# Standard normal quantiles for [0.05, 0.25, 0.5, 0.75, 0.95]
Z_SCORES = [
    -1.6448536269514722,
    -0.6744897501960817,
    0.0,
    0.6744897501960817,
    1.6448536269514722
]

def sigma_emp(prices):
    """Estimate robust volatility from the last 480 minute price moves."""
    # Compute all price changes
    if len(prices) < 2:
        return 0.0025
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    # Take the last 480 changes (or as many as available)
    changes = changes[-480:]
    n = len(changes)
    # If fewer than 30 points, return floor value
    if n < 30:
        return 0.0025
    # Compute 95th percentile of absolute changes
    abs_changes = [abs(c) for c in changes]
    abs_changes_sorted = sorted(abs_changes)
    # 95th percentile index (using ceiling method)
    idx = int(math.ceil(0.95 * n)) - 1
    if idx >= n:
        idx = n - 1
    p95 = abs_changes_sorted[idx]
    # Clip changes at 1.5 * p95
    clip_val = 1.5 * p95
    clipped = [max(min(c, clip_val), -clip_val) for c in changes]
    # Sample standard deviation of clipped changes
    mean_clipped = sum(clipped) / n
    variance = sum((c - mean_clipped) ** 2 for c in clipped) / (n - 1)
    std = math.sqrt(variance)
    # Floor at 0.001
    std = max(std, 0.001)
    # Shrink toward 0.0025 with weight n/(n+100)
    weight = n / (n + 100)
    sigma = weight * std + (1 - weight) * 0.0025
    # Multiply by 1.1
    sigma *= 1.1
    # Clamp to [0.0005, 0.08]
    sigma = max(min(sigma, 0.08), 0.0005)
    return sigma

def predict_market(prices):
    """Return 240x5 quantile predictions for a single market."""
    current_price = prices[-1]
    sigma = sigma_emp(prices)
    predictions = []
    for h in range(1, 241):  # 1 to 240 minutes ahead
        spread = sigma * (h ** 0.35)
        minute_preds = []
        for z in Z_SCORES:
            pred = current_price + spread * z
            # Clip to [0, 1]
            pred = max(min(pred, 1.0), 0.0)
            minute_preds.append(pred)
        predictions.append(minute_preds)
    return predictions

def main():
    # Read input from stdin or file
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    # Parse markets: expect list of dicts with "id" and "prices", or dict with "markets" key
    markets = []  # list of (id, prices)
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and "id" in item and "prices" in item:
                markets.append((item["id"], item["prices"]))
    elif isinstance(data, dict) and "markets" in data:
        for item in data["markets"]:
            if isinstance(item, dict) and "id" in item and "prices" in item:
                markets.append((item["id"], item["prices"]))
    elif isinstance(data, dict) and "id" in data and "prices" in data:
        markets.append((data["id"], data["prices"]))

    forecasts = []
    for market_id, prices in markets:
        if len(prices) == 0:
            # No prices, produce flat predictions at 0.0? But spec doesn't define. Use 0.0.
            current_price = 0.0
        else:
            current_price = prices[-1]
        # If not enough prices for any changes, sigma_emp will return 0.0025 (since n<30)
        preds = predict_market(prices)
        forecasts.append({"id": market_id, "q": preds})

    # Output as JSON object with "forecasts" key
    json.dump({"forecasts": forecasts}, sys.stdout)

if __name__ == "__main__":
    main()
