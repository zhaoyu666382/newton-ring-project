# -*- coding: utf-8 -*-
"""
Image preprocessing for Newton rings.

- Read image
- Convert to grayscale
- Denoise (Gaussian/Bilateral)
- Enhance contrast (CLAHE)
"""

from __future__ import annotations

from typing import Dict, Tuple, Any
import cv2
import numpy as np


def preprocess_image(
    image_path: str,
    preprocessing_cfg: Dict[str, Any] | None = None,
    return_intermediates: bool = False,
) -> Tuple[np.ndarray, np.ndarray] | Tuple[np.ndarray, np.ndarray, Dict[str, np.ndarray]]:
    cfg = preprocessing_cfg or {}
    k = int(cfg.get("gaussian_kernel_size", 5))
    if k % 2 == 0:
        k += 1

    img_bgr = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise ValueError(f"Failed to read image: {image_path}")

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    inter = {"gray": gray.copy()}

    # Gaussian blur
    gray_blur = cv2.GaussianBlur(gray, (k, k), 0)
    inter["gaussian"] = gray_blur.copy()

    # Bilateral filter (edge-preserving)
    d = int(cfg.get("bilateral_d", 9))
    sigma_color = float(cfg.get("bilateral_sigma_color", 75))
    sigma_space = float(cfg.get("bilateral_sigma_space", 75))
    gray_bi = cv2.bilateralFilter(gray_blur, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)
    inter["bilateral"] = gray_bi.copy()

    # CLAHE enhance
    clip = float(cfg.get("clahe_clip_limit", 2.0))
    grid = int(cfg.get("clahe_grid_size", 8))
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(grid, grid))
    gray_eq = clahe.apply(gray_bi)
    inter["clahe"] = gray_eq.copy()

    if return_intermediates:
        return img_bgr, gray_eq, inter
    return img_bgr, gray_eq
