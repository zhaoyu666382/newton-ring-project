#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Newton Ring Auto Measurement System
Entry point: CLI for processing Newton rings images and generating a report.

Usage examples:
  python main.py --image data/raw/sample.jpg
  python main.py --image data/raw/sample.jpg --config config.yaml --outdir output
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import yaml

from src.utils import setup_logger, ensure_dir, get_timestamp
from src.preprocess import preprocess_image
from src.detection import detect_newton_rings
from src.calculation import fit_radius_squared_vs_n
from src.report_gen import generate_word_report


def load_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Newton Ring auto measurement (image -> radii -> fit -> Word report).")
    ap.add_argument("--image", type=str, required=True, help="Input image path (jpg/png/bmp).")
    ap.add_argument("--config", type=str, default="config.yaml", help="Config yaml path.")
    ap.add_argument("--outdir", type=str, default="output", help="Output directory.")
    ap.add_argument("--no-report", action="store_true", help="Only run detection+fit, do not generate Word report.")
    ap.add_argument("--debug", action="store_true", help="Enable debug logging.")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    cfg = load_config(Path(args.config))

    outdir = Path(args.outdir)
    ensure_dir(str(outdir))
    ts = get_timestamp()

    log_dir = Path(cfg.get("logging", {}).get("log_dir", "output/logs"))
    ensure_dir(str(log_dir))
    log_file = None
    if cfg.get("logging", {}).get("save_to_file", True):
        log_file = str(log_dir / f"run_{ts}.log")

    level = "DEBUG" if args.debug else cfg.get("logging", {}).get("level", "INFO")
    import logging
    logger = setup_logger("NewtonRing", log_file=log_file, level=getattr(logging, level, logging.INFO))

    image_path = Path(args.image)
    if not image_path.exists():
        logger.error("Image not found: %s", image_path)
        return 2

    logger.info("Loading image: %s", image_path)
    img_bgr, img_gray = preprocess_image(
        str(image_path),
        preprocessing_cfg=cfg.get("preprocessing", {}),
        return_intermediates=False,
    )

    logger.info("Detecting rings...")
    det = detect_newton_rings(
        img_gray,
        detection_cfg=cfg.get("detection", {}),
        calculation_cfg=cfg.get("calculation", {}),
        outdir=str(outdir),
        basename=image_path.stem,
        logger=logger,
    )

    if not det["success"]:
        logger.error("Detection failed: %s", det.get("message", "unknown"))
        return 3

    logger.info("Fitting r^2 vs n ...")
    fit = fit_radius_squared_vs_n(
        radii_mm=det["radii_mm"],
        wavelength_nm=float(cfg.get("calculation", {}).get("wavelength", 589.3)),
        ring_index_start=int(cfg.get("calculation", {}).get("ring_index_start", 1)),
    )

    logger.info("Fit result: slope=%.6f mm^2/idx, R=%.3f mm", fit["slope"], fit["R_mm"])

    if args.no_report:
        logger.info("Done (report disabled). Outputs are in: %s", outdir)
        return 0

    logger.info("Generating Word report...")
    report_cfg = cfg.get("report", {})
    report_path = generate_word_report(
        outdir=str(outdir),
        basename=image_path.stem,
        det=det,
        fit=fit,
        report_cfg=report_cfg,
        logger=logger,
    )

    logger.info("Report saved: %s", report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
