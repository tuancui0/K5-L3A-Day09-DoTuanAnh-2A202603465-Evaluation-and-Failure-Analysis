"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

from collections.abc import Sequence
from math import comb

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    if len(human) != len(judge):
        raise ValueError("human and judge must have the same length")
    cm = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
    for h, j in zip(human, judge):
        if j == POS:
            cm["tp" if h == POS else "fp"] += 1
        else:
            cm["fn" if h == POS else "tn"] += 1
    return cm


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    cm = confusion(human, judge)
    p = cm["tp"] / (cm["tp"] + cm["fp"]) if cm["tp"] + cm["fp"] else 0.0
    r = cm["tp"] / (cm["tp"] + cm["fn"]) if cm["tp"] + cm["fn"] else 0.0
    return p, r


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    cm = confusion(human, judge)
    n = sum(cm.values())
    if n == 0:
        raise ValueError("kappa undefined for empty input")
    p_o = (cm["tp"] + cm["tn"]) / n
    p_e = ((cm["tp"] + cm["fp"]) * (cm["tp"] + cm["fn"]) + (cm["fn"] + cm["tn"]) * (cm["fp"] + cm["tn"])) / (n * n)
    if p_e == 1:
        raise ValueError("kappa undefined: chance agreement is 1 (constant labels)")
    return (p_o - p_e) / (1 - p_e)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    denom = sensitivity + specificity - 1
    if denom <= 0:
        raise ValueError("judge no better than chance (sensitivity + specificity <= 1): cannot correct")
    return min(1.0, max(0.0, (observed_rate + specificity - 1) / denom))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    import numpy as np
    from scipy import stats as sps

    x, y = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if x.shape != y.shape or x.size == 0:
        raise ValueError("a and b must be non-empty and the same length")
    if np.array_equal(x, y):
        return (0.0, 0.0, 0.0)

    def diff_mean(u, v, axis=-1):
        return np.mean(u - v, axis=axis)

    res = sps.bootstrap((x, y), diff_mean, paired=True, vectorized=True, n_resamples=n_resamples,
                        confidence_level=confidence, method="percentile", rng=np.random.default_rng(rng))
    return (float(np.mean(x) - np.mean(y)), float(res.confidence_interval.low), float(res.confidence_interval.high))


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    if k > n or k < 1 or not 0 <= c <= n:
        raise ValueError("need 1 <= k <= n and 0 <= c <= n")
    return 1.0 - comb(n - c, k) / comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    if k > n or k < 1 or not 0 <= c <= n:
        raise ValueError("need 1 <= k <= n and 0 <= c <= n")
    return comb(c, k) / comb(n, k)
