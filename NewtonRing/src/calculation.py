# -*- coding: utf-8 -*-
"""
Physical calculation for Newton rings.

We fit: r^2 = k * n + b
Then: k = λ * R  (for reflected light dark rings when d0 offset absorbed by b)
=> R = k / λ

Units:
- r in mm => r^2 in mm^2
- λ in nm, convert to mm: λ_mm = λ_nm * 1e-6
"""

from __future__ import annotations

from typing import Dict, List, Any
import numpy as np


def fit_radius_squared_vs_n(
    radii_mm: List[float],
    wavelength_nm: float = 589.3,
    ring_index_start: int = 1,
) -> Dict[str, Any]:
    radii_mm = np.asarray(radii_mm, dtype=float)
    n = np.arange(ring_index_start, ring_index_start + len(radii_mm), dtype=float)
    r2 = radii_mm ** 2

    # Linear least squares fit
    # r2 = slope * n + intercept
    slope, intercept = np.polyfit(n, r2, 1)

    # Compute fit quality and uncertainty
    r2_pred = slope * n + intercept
    residuals = r2 - r2_pred
    dof = max(1, len(n) - 2)
    sigma2 = np.sum(residuals ** 2) / dof

    Sxx = np.sum((n - n.mean()) ** 2)
    slope_se = float(np.sqrt(sigma2 / Sxx)) if Sxx > 0 else float("nan")
    intercept_se = float(np.sqrt(sigma2 * (1.0 / len(n) + (n.mean() ** 2) / Sxx))) if Sxx > 0 else float("nan")

    ss_tot = np.sum((r2 - r2.mean()) ** 2)
    r_squared = float(1 - np.sum(residuals ** 2) / ss_tot) if ss_tot > 0 else 0.0

    # Convert wavelength
    wavelength_mm = wavelength_nm * 1e-6
    R_mm = float(slope / wavelength_mm)
    R_se_mm = float(slope_se / wavelength_mm) if np.isfinite(slope_se) else float("nan")

    return {
        "n": n.tolist(),
        "r_mm": radii_mm.tolist(),
        "r2_mm2": r2.tolist(),
        "slope": float(slope),
        "intercept": float(intercept),
        "slope_se": slope_se,
        "intercept_se": intercept_se,
        "R_mm": R_mm,
        "R_se_mm": R_se_mm,
        "r_squared": r_squared,
    }
