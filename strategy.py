# strategy.py
# Indicator-based quick analysis and fallback confidence scoring.
import statistics
import math

def compute_simple_indicators(prices):
    if not prices or len(prices) < 6:
        return None
    last = prices[-1]
    prev = prices[-2]
    diff = last - prev
    returns = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    vol = statistics.pstdev(returns) if len(returns) > 1 else 0.0
    n_long = min(len(prices), 20)
    sma_short = sum(prices[-5:]) / 5
    sma_long = sum(prices[-n_long:]) / n_long
    # basic momentum: average of last 3 returns
    momentum = sum(returns[-3:]) / 3 if len(returns) >= 3 else returns[-1]
    return {
        "last": last,
        "prev": prev,
        "diff": diff,
        "vol": vol,
        "sma_short": sma_short,
        "sma_long": sma_long,
        "momentum": momentum
    }

def base_confidence(ind):
    if ind is None:
        return 0
    score = 50
    # momentum/diff contribution
    score += min(25, abs(ind["diff"]) * 40)
    # trend alignment
    if ind["sma_short"] > ind["sma_long"]:
        score += 10
    else:
        score -= 5
    # volatility adds confidence up to a point
    score += min(10, ind["vol"] * 100)
    # momentum sign increases confidence
    if abs(ind["momentum"]) > 0:
        score += min(5, abs(ind["momentum"]) * 50)
    score = max(0, min(100, int(score)))
    return score

def direction_from_ind(ind):
    if ind is None:
        return "NEUTRAL"
    if ind["diff"] > 0:
        return "CALL"
    elif ind["diff"] < 0:
        return "PUT"
    return "NEUTRAL"
