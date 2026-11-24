"""
Pure Python implementation of Bjontegaard Delta (BD) metric calculation.
Reference: ITU-T VCEG-M33 / ITU-T VCEG-AI11 (G. Bjontegaard, 2001).
Calculates BD-Rate (%) and BD-VMAF (score delta) between two Rate-Distortion curves.
Zero external dependencies (uses standard math and matrix solving).
"""

import math
from typing import List, Tuple, Optional


def _solve_linear_system(A: List[List[float]], b: List[float]) -> List[float]:
    """Solve Ax = b using Gaussian elimination with partial pivoting."""
    n = len(b)
    # Augmented matrix
    M = [A[i][:] + [b[i]] for i in range(n)]

    for i in range(n):
        # Pivot
        max_row = i
        for k in range(i + 1, n):
            if abs(M[k][i]) > abs(M[max_row][i]):
                max_row = k
        M[i], M[max_row] = M[max_row], M[i]

        pivot = M[i][i]
        if abs(pivot) < 1e-12:
            raise ValueError("Singular matrix in polynomial fitting")

        for j in range(i, n + 1):
            M[i][j] /= pivot

        for k in range(n):
            if k != i:
                factor = M[k][i]
                for j in range(i, n + 1):
                    M[k][j] -= factor * M[i][j]

    return [M[i][n] for i in range(n)]


def polyfit_1d(x: List[float], y: List[float], degree: int = 3) -> List[float]:
    """
    Fits a polynomial y = c0 + c1*x + c2*x^2 + ... + cd*x^d.
    Returns coefficients [c0, c1, ..., cd].
    """
    if len(x) != len(y):
        raise ValueError("x and y must have equal length")
    if len(x) <= degree:
        degree = max(1, len(x) - 1)

    m = degree + 1
    # Build normal equations: (X^T * X) c = X^T * y
    # X^T * X is size m x m, where entry (j, k) is sum(x^(j+k))
    # X^T * y is size m, where entry j is sum(y * x^j)
    A = [[0.0] * m for _ in range(m)]
    b = [0.0] * m

    for j in range(m):
        for k in range(m):
            A[j][k] = sum(xi ** (j + k) for xi in x)
        b[j] = sum(yi * (xi ** j) for xi, yi in zip(x, y))

    try:
        return _solve_linear_system(A, b)
    except ValueError:
        # Fallback to linear fit if cubic matrix is ill-conditioned
        if degree > 1:
            return polyfit_1d(x, y, degree=1)
        raise


def polyval(coeffs: List[float], x: float) -> float:
    """Evaluate polynomial with coefficients [c0, c1, c2, ...] at x."""
    res = 0.0
    for i, c in enumerate(coeffs):
        res += c * (x ** i)
    return res


def polyint_definite(coeffs: List[float], low: float, high: float) -> float:
    """Definite integral of polynomial from low to high."""
    res = 0.0
    for i, c in enumerate(coeffs):
        power = i + 1
        res += (c / power) * ((high ** power) - (low ** power))
    return res


def calculate_bd_rate(
    rate1: List[float],
    metric1: List[float],
    rate2: List[float],
    metric2: List[float],
    degree: int = 3,
) -> Optional[float]:
    """
    Calculates Bjontegaard Delta Rate (BD-Rate) in percent.
    rate1, metric1: Reference curve (e.g. H.264), rates in kbps, metric in VMAF (0-100).
    rate2, metric2: Test curve (e.g. AV1 or HEVC).

    Returns:
        BD-Rate as percentage savings/increase.
        E.g., -45.2 means rate2 requires 45.2% less bitrate at equal VMAF.
    """
    if len(rate1) < 2 or len(rate2) < 2:
        return None

    # Sort curves by metric
    pts1 = sorted(zip(metric1, rate1), key=lambda p: p[0])
    pts2 = sorted(zip(metric2, rate2), key=lambda p: p[0])

    m1_vals = [p[0] for p in pts1]
    log_r1_vals = [math.log(max(1e-5, p[1])) for p in pts1]

    m2_vals = [p[0] for p in pts2]
    log_r2_vals = [math.log(max(1e-5, p[1])) for p in pts2]

    # Overlapping metric interval
    low = max(min(m1_vals), min(m2_vals))
    high = min(max(m1_vals), max(m2_vals))

    if high <= low:
        # Non-overlapping range, extrapolate slight overlap or return direct ratio
        low = min(max(min(m1_vals), min(m2_vals)), 50.0)
        high = max(min(max(m1_vals), max(m2_vals)), 95.0)
        if high <= low:
            return None

    # Fit log(rate) as function of metric (VMAF): log(R) = f(VMAF)
    d1 = min(degree, len(pts1) - 1)
    d2 = min(degree, len(pts2) - 1)

    coeffs1 = polyfit_1d(m1_vals, log_r1_vals, degree=d1)
    coeffs2 = polyfit_1d(m2_vals, log_r2_vals, degree=d2)

    int1 = polyint_definite(coeffs1, low, high)
    int2 = polyint_definite(coeffs2, low, high)

    avg_log_diff = (int2 - int1) / (high - low)
    bd_rate_pct = (math.exp(avg_log_diff) - 1.0) * 100.0

    return round(bd_rate_pct, 2)


def calculate_bd_vmaf(
    rate1: List[float],
    metric1: List[float],
    rate2: List[float],
    metric2: List[float],
    degree: int = 3,
) -> Optional[float]:
    """
    Calculates Bjontegaard Delta VMAF (BD-VMAF / BD-PSNR).
    Returns average VMAF score delta at equal bitrate.
    Positive value means rate2 has higher quality at equal bitrate.
    """
    if len(rate1) < 2 or len(rate2) < 2:
        return None

    pts1 = sorted(zip(rate1, metric1), key=lambda p: p[0])
    pts2 = sorted(zip(rate2, metric2), key=lambda p: p[0])

    log_r1_vals = [math.log(max(1e-5, p[0])) for p in pts1]
    m1_vals = [p[1] for p in pts1]

    log_r2_vals = [math.log(max(1e-5, p[0])) for p in pts2]
    m2_vals = [p[1] for p in pts2]

    low = max(min(log_r1_vals), min(log_r2_vals))
    high = min(max(log_r1_vals), max(log_r2_vals))

    if high <= low:
        return None

    d1 = min(degree, len(pts1) - 1)
    d2 = min(degree, len(pts2) - 1)

    coeffs1 = polyfit_1d(log_r1_vals, m1_vals, degree=d1)
    coeffs2 = polyfit_1d(log_r2_vals, m2_vals, degree=d2)

    int1 = polyint_definite(coeffs1, low, high)
    int2 = polyint_definite(coeffs2, low, high)

    avg_metric_diff = (int2 - int1) / (high - low)
    return round(avg_metric_diff, 2)
