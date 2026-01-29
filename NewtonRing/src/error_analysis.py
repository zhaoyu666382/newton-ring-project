# -*- coding: utf-8 -*-
"""
Error analysis for Newton rings measurement.

Given fit result (from src/calculation.py), compute:
- residuals of r^2 (mm^2)
- goodness metrics
- if reference R is provided: abs/rel error for R

Also generate diagnostic plots:
- residual plot (n vs residual in mm^2)
- R comparison bar plot (R_meas vs R_ref)

Units:
- R in mm
- residuals in mm^2
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import os
import numpy as np
import matplotlib.pyplot as plt


def analyze_error(
    fit: Dict[str, Any],
    reference_R_mm: Optional[float] = None,
    thresholds: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Parameters
    ----------
    fit:
        output dict from src/calculation.fit_radius_squared_vs_n()
        must include: n, r2_mm2, slope, intercept, R_mm, r_squared
    reference_R_mm:
        reference curvature radius in mm (optional)
    thresholds:
        optional dict with keys like:
        - min_r_squared (default 0.98)
        - max_rel_error (default None)

    Returns
    -------
    error_result dict:
        - measured_R_mm
        - reference_R_mm
        - abs_error_mm, rel_error
        - residuals_mm2 list and summary stats
        - flags: pass_fit_quality, pass_error (if ref exists), overall_pass
    """
    thresholds = thresholds or {}
    min_r2 = float(thresholds.get("min_r_squared", 0.98))
    max_rel_error = thresholds.get("max_rel_error", None)
    if max_rel_error is not None:
        max_rel_error = float(max_rel_error)

    n = np.asarray(fit["n"], dtype=float)
    r2 = np.asarray(fit["r2_mm2"], dtype=float)
    slope = float(fit["slope"])
    intercept = float(fit["intercept"])

    # residuals of r^2
    r2_pred = slope * n + intercept
    residuals = r2 - r2_pred

    residual_mean = float(np.mean(residuals)) if residuals.size else 0.0
    residual_std = float(np.std(residuals, ddof=1)) if residuals.size >= 2 else 0.0
    residual_max_abs = float(np.max(np.abs(residuals))) if residuals.size else 0.0

    measured_R_mm = float(fit["R_mm"])
    r_squared = float(fit.get("r_squared", 0.0))

    # pass/fail by fit quality
    pass_fit_quality = bool(r_squared >= min_r2)

    # errors if reference exists
    abs_error_mm = None
    rel_error = None
    pass_error = None
    if reference_R_mm is not None and np.isfinite(reference_R_mm) and reference_R_mm != 0:
        reference_R_mm = float(reference_R_mm)
        abs_error_mm = float(abs(measured_R_mm - reference_R_mm))
        rel_error = float(abs_error_mm / abs(reference_R_mm))
        if max_rel_error is not None:
            pass_error = bool(rel_error <= max_rel_error)
        else:
            pass_error = True  # no threshold => don't fail it
    else:
        reference_R_mm = None

    overall_pass = pass_fit_quality and (pass_error if pass_error is not None else True)

    return {
        "measured_R_mm": measured_R_mm,
        "reference_R_mm": reference_R_mm,
        "abs_error_mm": abs_error_mm,
        "rel_error": rel_error,
        "r_squared": r_squared,
        "thresholds": {
            "min_r_squared": min_r2,
            "max_rel_error": max_rel_error,
        },
        "residuals_mm2": residuals.tolist(),
        "residual_stats": {
            "mean_mm2": residual_mean,
            "std_mm2": residual_std,
            "max_abs_mm2": residual_max_abs,
        },
        "flags": {
            "pass_fit_quality": pass_fit_quality,
            "pass_error": pass_error,
            "overall_pass": overall_pass,
        },
    }


def save_residual_plot(
    fit: Dict[str, Any],
    err: Dict[str, Any],
    out_path: str,
    dpi: int = 200,
) -> str:
    """Save residual plot: n vs residual(r^2)."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    n = np.asarray(fit["n"], dtype=float)
    residuals = np.asarray(err["residuals_mm2"], dtype=float)

    plt.figure()
    plt.axhline(0.0, linewidth=1)
    plt.plot(n, residuals, marker="o", linestyle="-")
    plt.xlabel("Ring index n")
    plt.ylabel("Residual of r^2 (mm^2)")
    plt.title("Residual Plot (r^2 - fitted)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=dpi)
    plt.close()
    return out_path


def save_R_comparison_plot(
    err: Dict[str, Any],
    out_path: str,
    dpi: int = 200,
) -> Optional[str]:
    """Save R comparison bar plot if reference exists."""
    if err.get("reference_R_mm") is None:
        return None

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    R_meas = float(err["measured_R_mm"])
    R_ref = float(err["reference_R_mm"])

    plt.figure()
    plt.bar(["Measured R", "Reference R"], [R_meas, R_ref])
    plt.ylabel("R (mm)")
    plt.title("R Comparison")
    plt.tight_layout()
    plt.savefig(out_path, dpi=dpi)
    plt.close()
    return out_path
