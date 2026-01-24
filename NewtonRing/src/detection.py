# -*- coding: utf-8 -*-
"""
Newton rings detection:
1) Estimate center (Hough or gradient-based)
2) Compute radial intensity profile by sampling many angles
3) Find dark ring radii (local minima) from the profile
4) Save diagnostic figures
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from dataclasses import dataclass

import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks


@dataclass
class CenterResult:
    x: float
    y: float
    method: str
    score: float


def _center_by_hough(gray: np.ndarray, cfg: Dict[str, Any]) -> Optional[CenterResult]:
    # Hough on edges can be unstable for Newton rings; we use it mainly as a fallback.
    dp = float(cfg.get("hough_dp", 1))
    min_dist = float(cfg.get("hough_min_dist", 50))
    param1 = float(cfg.get("hough_param1", 50))
    param2 = float(cfg.get("hough_param2", 30))

    # Use a broad radius range, letting OpenCV guess.
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=dp,
        minDist=min_dist,
        param1=param1,
        param2=param2,
        minRadius=0,
        maxRadius=0,
    )
    if circles is None:
        return None
    circles = np.squeeze(circles, axis=0)
    # Choose the largest circle as it often corresponds to outer ring boundary.
    idx = int(np.argmax(circles[:, 2]))
    x, y, r = circles[idx]
    return CenterResult(float(x), float(y), "hough", float(r))


def _center_by_gradient(gray: np.ndarray, cfg: Dict[str, Any]) -> Optional[CenterResult]:
    """
    Gradient-based center estimation:
    - Compute edges
    - Fit circle center by minimizing radial variance of edge pixels
    Practical approach: use image moments of edge magnitude (robust, fast).
    """
    t1 = float(cfg.get("canny_threshold1", 50))
    t2 = float(cfg.get("canny_threshold2", 150))
    edges = cv2.Canny(gray, t1, t2, L2gradient=True)

    # Use distance transform to focus on strong edges (rings)
    ys, xs = np.nonzero(edges)
    if len(xs) < 200:
        return None

    # Weighted centroid using gradient magnitude
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.magnitude(gx, gy)

    w = mag[ys, xs]
    w = np.clip(w, 1e-6, None)
    x0 = float(np.sum(xs * w) / np.sum(w))
    y0 = float(np.sum(ys * w) / np.sum(w))

    # score: inverse of weighted spread (larger is better)
    spread = float(np.sqrt(np.average((xs - x0) ** 2 + (ys - y0) ** 2, weights=w)))
    score = 1.0 / (spread + 1e-6)
    return CenterResult(x0, y0, "gradient", score)


def estimate_center(gray: np.ndarray, cfg: Dict[str, Any]) -> CenterResult:
    method = str(cfg.get("center_detection_method", "gradient")).lower()
    if method == "hough":
        res = _center_by_hough(gray, cfg)
        if res:
            return res
        res = _center_by_gradient(gray, cfg)
        if res:
            return res
    else:
        res = _center_by_gradient(gray, cfg)
        if res:
            return res
        res = _center_by_hough(gray, cfg)
        if res:
            return res
    # fallback: image center
    h, w = gray.shape[:2]
    return CenterResult(w / 2.0, h / 2.0, "fallback_center", 0.0)


def radial_profile(gray: np.ndarray, cx: float, cy: float, num_angles: int = 720, max_radius: Optional[int] = None) -> np.ndarray:
    """
    Average intensity over angles for each radius (0..max_radius-1).
    This is robust for circular fringes.
    """
    h, w = gray.shape[:2]
    if max_radius is None:
        max_radius = int(min(cx, cy, w - cx, h - cy))
    max_radius = int(max(10, max_radius))

    angles = np.linspace(0, 2 * np.pi, num_angles, endpoint=False).astype(np.float32)
    rs = np.arange(max_radius, dtype=np.float32)

    # Create sampling grid: (num_angles, max_radius)
    xs = cx + np.cos(angles)[:, None] * rs[None, :]
    ys = cy + np.sin(angles)[:, None] * rs[None, :]

    # Sample by bilinear interpolation
    prof = cv2.remap(
        gray.astype(np.float32),
        xs.astype(np.float32),
        ys.astype(np.float32),
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REFLECT,
    )
    return prof.mean(axis=0)  # (max_radius,)


def find_dark_rings(profile: np.ndarray, cfg: Dict[str, Any]) -> np.ndarray:
    """
    Find local minima positions from radial intensity profile.
    Newton rings dark fringes correspond to minima in intensity.
    """
    # Smooth by moving average
    win = int(cfg.get("profile_smooth_window", 9))
    if win < 3:
        win = 3
    if win % 2 == 0:
        win += 1
    kernel = np.ones(win, dtype=np.float32) / win
    smooth = np.convolve(profile, kernel, mode="same")

    # Find peaks in inverted signal (minima)
    inv = smooth.max() - smooth
    prominence = float(cfg.get("minima_prominence", 3.0))
    distance = int(cfg.get("minima_distance", 8))

    peaks, props = find_peaks(inv, prominence=prominence, distance=distance)

    # Remove peaks near origin (often center artifact)
    min_r = int(cfg.get("min_radius_px", 10))
    peaks = peaks[peaks >= min_r]

    return peaks.astype(int), smooth


def _save_overlay(gray: np.ndarray, cx: float, cy: float, radii_px: np.ndarray, out_path: str):
    img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    cv2.circle(img, (int(round(cx)), int(round(cy))), 5, (0, 255, 0), -1)
    for r in radii_px:
        cv2.circle(img, (int(round(cx)), int(round(cy))), int(r), (255, 0, 0), 1)
    cv2.imwrite(out_path, img)


def _save_profile_plot(profile: np.ndarray, smooth: np.ndarray, minima: np.ndarray, out_path: str):
    plt.figure(figsize=(9, 4), dpi=200)
    plt.plot(profile, label="raw")
    plt.plot(smooth, label="smoothed")
    plt.scatter(minima, smooth[minima], marker="x", label="dark rings (minima)")
    plt.xlabel("Radius (pixel)")
    plt.ylabel("Mean intensity")
    plt.title("Radial intensity profile")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()


def detect_newton_rings(
    gray: np.ndarray,
    detection_cfg: Dict[str, Any],
    calculation_cfg: Dict[str, Any],
    outdir: str,
    basename: str,
    logger=None,
) -> Dict[str, Any]:
    os.makedirs(outdir, exist_ok=True)
    fig_dir = os.path.join(outdir, "figures")
    os.makedirs(fig_dir, exist_ok=True)

    center = estimate_center(gray, detection_cfg)
    if logger:
        logger.info("Center estimated by %s: (%.2f, %.2f)", center.method, center.x, center.y)

    num_angles = int(detection_cfg.get("profile_num_angles", 720))
    max_radius_px = detection_cfg.get("max_radius_px")
    if max_radius_px is not None:
        max_radius_px = int(max_radius_px)

    profile = radial_profile(gray, center.x, center.y, num_angles=num_angles, max_radius=max_radius_px)
    minima, smooth = find_dark_rings(profile, detection_cfg)

    # Enforce min/max ring count
    min_rings = int(calculation_cfg.get("min_rings", 5))
    max_rings = int(calculation_cfg.get("max_rings", 30))
    if len(minima) < min_rings:
        return {"success": False, "message": f"Detected rings ({len(minima)}) < min_rings ({min_rings}). Try tuning config."}

    minima = minima[:max_rings]

    pixel_to_mm = float(calculation_cfg.get("pixel_to_mm", 0.01))
    radii_mm = minima * pixel_to_mm

    overlay_path = os.path.join(fig_dir, f"{basename}_rings_overlay.png")
    profile_path = os.path.join(fig_dir, f"{basename}_radial_profile.png")
    _save_overlay(gray, center.x, center.y, minima, overlay_path)
    _save_profile_plot(profile, smooth, minima, profile_path)

    return {
        "success": True,
        "center": {"x": center.x, "y": center.y, "method": center.method, "score": center.score},
        "radii_px": minima.tolist(),
        "radii_mm": radii_mm.tolist(),
        "overlay_figure": overlay_path,
        "profile_figure": profile_path,
    }
