# -*- coding: utf-8 -*-
"""
Generate a Word report (.docx) with:
- Basic info
- Data table (n, r, r^2)
- Figures (overlay, radial profile, r^2-n fit)
- Results and conclusion

Font requirements:
- Use SimSun (宋体) for East Asian text (set via run._element.rPr.rFonts)
"""

from __future__ import annotations

from typing import Dict, Any
from pathlib import Path
import os
import numpy as np
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml.ns import qn


def _set_run_font(run, font_name: str = "SimSun", font_size_pt: int = 12, bold: bool = False):
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
    run.font.size = Pt(font_size_pt)
    run.bold = bold


def _set_paragraph_font(paragraph, font_name: str = "SimSun", font_size_pt: int = 12):
    for run in paragraph.runs:
        _set_run_font(run, font_name=font_name, font_size_pt=font_size_pt)


def _make_fit_plot(fit: Dict[str, Any], out_path: str):
    n = np.asarray(fit["n"], dtype=float)
    r2 = np.asarray(fit["r2_mm2"], dtype=float)
    slope = float(fit["slope"])
    intercept = float(fit["intercept"])

    plt.figure(figsize=(8, 5), dpi=300)
    plt.scatter(n, r2, s=45, label="data")
    plt.plot(n, slope * n + intercept, linewidth=2, label=f"fit: r^2={slope:.4f} n + {intercept:.4f}")
    plt.xlabel("Ring index n")
    plt.ylabel("r^2 (mm^2)")
    plt.title("Newton rings: r^2 vs n")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    os.makedirs(Path(out_path).parent, exist_ok=True)
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()


def generate_word_report(
    outdir: str,
    basename: str,
    det: Dict[str, Any],
    fit: Dict[str, Any],
    report_cfg: Dict[str, Any] | None = None,
    logger=None,
) -> str:
    report_cfg = report_cfg or {}
    outdir = Path(outdir)
    rep_dir = outdir / "reports"
    fig_dir = outdir / "figures"
    rep_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    fit_fig = str(fig_dir / f"{basename}_fit_r2_n.png")
    _make_fit_plot(fit, fit_fig)

    doc = Document()

    # Title
    title = doc.add_paragraph()
    run = title.add_run("牛顿环实验报告（自动生成）")
    _set_run_font(run, font_size_pt=18, bold=True)
    title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    # Info line
    info = doc.add_paragraph()
    run = info.add_run(f"样本：{basename}    圆心方法：{det['center']['method']}    R = {fit['R_mm']:.2f} mm")
    _set_run_font(run, font_size_pt=10)
    info.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

    doc.add_paragraph()

    # Principle
    h = doc.add_paragraph()
    _set_run_font(h.add_run("一、实验原理"), font_size_pt=14, bold=True)
    p = doc.add_paragraph(
        "牛顿环为平凸透镜与平玻璃间空气薄膜形成的等厚干涉条纹。对反射暗纹近似满足 r^2 = n λ R + b，"
        "其中 r 为暗纹半径，n 为级数，λ 为波长，R 为透镜曲率半径，b 吸收中心间隙等系统项。"
        "通过对 r^2-n 进行线性拟合得到斜率 k=λR，从而 R=k/λ。"
    )
    _set_paragraph_font(p, font_size_pt=11)

    # Equipment
    h = doc.add_paragraph()
    _set_run_font(h.add_run("二、实验装置与软件"), font_size_pt=14, bold=True)
    eq = doc.add_paragraph("牛顿环仪、单色光源（钠灯/等效单色光）、相机/电子目镜、计算机（Python + OpenCV）。")
    _set_paragraph_font(eq, font_size_pt=11)

    # Data
    h = doc.add_paragraph()
    _set_run_font(h.add_run("三、数据处理与结果"), font_size_pt=14, bold=True)

    table = doc.add_table(rows=1, cols=3)
    hdr = table.rows[0].cells
    hdr[0].text = "n"
    hdr[1].text = "r (mm)"
    hdr[2].text = "r^2 (mm^2)"
    for cell in hdr:
        for p in cell.paragraphs:
            _set_paragraph_font(p, font_size_pt=10)

    for n, r, r2 in zip(fit["n"], fit["r_mm"], fit["r2_mm2"]):
        row = table.add_row().cells
        row[0].text = f"{int(n)}"
        row[1].text = f"{float(r):.4f}"
        row[2].text = f"{float(r2):.4f}"
        for cell in row:
            for p in cell.paragraphs:
                _set_paragraph_font(p, font_size_pt=10)

    doc.add_paragraph()

    res = doc.add_paragraph()
    run = res.add_run(
        f"线性拟合：r^2 = ({fit['slope']:.6f}) n + ({fit['intercept']:.6f})，"
        f"R = {fit['R_mm']:.2f} ± {fit['R_se_mm']:.2f} mm，拟合优度 R² = {fit['r_squared']:.4f}。"
    )
    _set_run_font(run, font_size_pt=11)

    # Figures
    h = doc.add_paragraph()
    _set_run_font(h.add_run("四、图像与拟合图"), font_size_pt=14, bold=True)

    def add_fig(caption: str, path: str, width_cm: float = 15.5):
        if not os.path.exists(path):
            return
        cap = doc.add_paragraph()
        _set_run_font(cap.add_run(caption), font_size_pt=11, bold=True)
        pic_p = doc.add_paragraph()
        pic_p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        run = pic_p.add_run()
        run.add_picture(path, width=Cm(width_cm))

    add_fig("图1：暗纹半径识别叠加图", det.get("overlay_figure", ""), width_cm=15.5)
    add_fig("图2：径向灰度曲线与暗纹位置", det.get("profile_figure", ""), width_cm=15.5)
    add_fig("图3：r²-n 拟合图", fit_fig, width_cm=15.5)

    # Conclusion
    h = doc.add_paragraph()
    _set_run_font(h.add_run("五、结论"), font_size_pt=14, bold=True)
    concl = doc.add_paragraph(
        f"本次基于图像法自动提取牛顿环暗纹半径，并进行 r²-n 线性拟合，得到透镜曲率半径 "
        f"R = {fit['R_mm']:.2f} mm（不确定度约 {fit['R_se_mm']:.2f} mm）。"
        "后续可通过更精确的像素标定、光源波长校准与多次测量取平均进一步降低误差。"
    )
    _set_paragraph_font(concl, font_size_pt=11)

    out_path = rep_dir / f"{basename}_NewtonRing_Report.docx"
    doc.save(str(out_path))
    if logger:
        logger.info("Word report generated: %s", out_path)
    return str(out_path)
