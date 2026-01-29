# NewtonRing —— 牛顿环自动测量与误差分析系统（图片法）

本项目基于图像处理与物理模型，实现牛顿环实验从**图像输入 → 自动测量 → 结果拟合 → 误差分析 → 实验报告生成**的完整自动化流程，适用于大学物理实验或相关课程设计。

系统支持**单张图片自动处理**，可输出曲率半径测量结果，并自动生成包含图表与误差分析的 **Word 实验报告**。

---

## ✨ 功能概览

**完整实验闭环：**

1. 📷 导入或拍摄牛顿环图像
2. 🧠 自动识别牛顿环圆心与暗纹
3. 📏 自动提取暗环半径
4. 📈 对 ( r^2 - n ) 进行线性拟合，计算曲率半径 ( R )
5. 📊 **误差分析（新增）**

   * r² 拟合残差分析
   * 曲率半径绝对 / 相对误差计算（可选参考值）
   * 残差图与 R 对比图自动生成
6. 📝 自动生成 Word 实验报告（含图表与分析结论）

---

## 🧩 项目结构

```
NewtonRing/
├─ main.py                  # 主入口
├─ config.yaml               # 全局配置文件
├─ data/
│  └─ raw/                   # 原始实验图片
├─ output/
│  ├─ figures/               # 自动生成的图像
│  └─ reports/               # Word 实验报告
└─ src/
   ├─ preprocess.py          # 图像预处理
   ├─ detection.py           # 圆心定位 & 暗纹检测
   ├─ calculation.py         # r²-n 拟合 & R 计算
   ├─ error_analysis.py      # ⭐ 误差分析模块（新增）
   └─ report_gen.py          # Word 报告生成
```

---

## 🛠️ 环境配置（Windows + Python 3.10）

> ⚠️ **请使用 Python 3.10，不建议使用 requirements.txt**

### 1️⃣ 升级基础工具

```powershell
python -m pip install --upgrade pip setuptools wheel
```

### 2️⃣ 依赖逐行安装（推荐方式）

```powershell
python -m pip install numpy==1.24.3 --only-binary=:all:
python -m pip install scipy==1.11.2
python -m pip install pandas==2.0.3
python -m pip install pillow==10.0.0
python -m pip install opencv-python==4.8.1.78
python -m pip install matplotlib==3.7.2
python -m pip install python-docx==1.1.0
python -m pip install PyYAML==6.0.1
```

💡 **建议**：每条命令执行完成后确认无报错。

---

## ▶️ 运行方式

假设当前路径为项目根目录（包含 `NewtonRing/`）：

### 1️⃣ 标准流程（检测 + 拟合 + 报告）

```powershell
python NewtonRing/main.py --image NewtonRing/data/raw/your_image.jpg --config NewtonRing/config.yaml
```

输出内容位于 `NewtonRing/output/`。

---

### 2️⃣ 指定输出目录

```powershell
python NewtonRing/main.py --image NewtonRing/data/raw/your_image.jpg --config NewtonRing/config.yaml --outdir NewtonRing/output
```

---

### 3️⃣ 不生成 Word 报告（仅分析）

```powershell
python NewtonRing/main.py --image NewtonRing/data/raw/your_image.jpg --config NewtonRing/config.yaml --no-report
```

---

## 📊 输出结果说明（output/）

### figures/

* `*_rings_overlay.png`
  → 检测到的圆心与暗环叠加图
* `*_radial_profile.png`
  → 径向灰度曲线及暗纹标注
* `*_fit_r2_n.png`
  → ( r^2 - n ) 线性拟合图
* `*_residuals.png`
  → ⭐ r² 拟合残差图（误差分析）
* `*_R_compare.png`
  → ⭐ 测量 R 与参考 R 对比图（如提供参考值）

### reports/

* `*_NewtonRing_Report.docx`
  → 自动生成的实验报告（含误差分析章节）

---

## 📐 关键配置说明（config.yaml）

```yaml
calculation:
  pixel_to_mm: 0.0125       # 像素 → mm 标定系数（必须正确）
  wavelength: 589           # 光源波长 (nm)

detection:
  center_detection_method: hough
  profile_num_angles: 360
  min_rings: 6

error_analysis:
  enabled: true
  reference_R_mm: 1200.0    # 可选：参考曲率半径（mm）
  min_r_squared: 0.98
  max_rel_error: 0.05
```

⚠️ **注意**：

* `pixel_to_mm` 不准确会导致 R 结果无物理意义
* 误差分析模块可独立开关，适合不同实验阶段使用

---

## 📉 误差分析模块说明（新增）

系统在拟合完成后，可自动进行误差分析：

* **r² 残差分析**

  * 均值、标准差、最大残差
  * 判断半径提取稳定性
* **曲率半径误差**

  * 绝对误差 |ΔR|
  * 相对误差
* **自动生成诊断图像**

  * 残差分布图
  * R 测量值与参考值对比图

分析结果可自动写入 Word 实验报告。

---

## 🧪 两种常用误差分析用法

### 方法 A：命令行给参考值（快速测试）

```bash
python main.py --image data/raw/synthetic.png --reference-R 1200
```

单位：**mm**

---

### 方法 B：配置文件方式（最终交付推荐）

```yaml
error_analysis:
  enabled: true
  reference_R_mm: 1200.0
  min_r_squared: 0.98
  max_rel_error: 0.05
```

