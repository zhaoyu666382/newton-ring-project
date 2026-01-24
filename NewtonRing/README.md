# NewtonRing - 牛顿环自动测量系统（图片法）

本项目实现「拍照/导入图片 → 自动识别牛顿环 → 自动提取暗纹半径 → 线性拟合 r²-n → 自动生成 Word 实验报告」的完整闭环。

> 说明：本仓库中 `main.py` / `preprocess.py` / `detection.py` / `calculation.py` / `report_gen.py` 已补全为可运行版本，并优化了圆心定位与环半径提取流程。

---

## 1. 环境安装（Windows + Python 3.10）

**⚠️ 注意：不要使用 `requirements.txt`，请按照下面依赖逐行安装**

建议先在终端中切换到 Python 3.10 环境，或者使用你自己的 Python 3.10 路径：

```powershell
# 升级 pip / setuptools / wheel
python -m pip install --upgrade pip setuptools wheel

# 依赖逐行安装
python -m pip install numpy==1.24.3 --only-binary=:all:
python -m pip install scipy==1.11.2
python -m pip install pandas==2.0.3
python -m pip install pillow==10.0.0
python -m pip install opencv-python==4.8.1.78
python -m pip install matplotlib==3.7.2
python -m pip install python-docx==1.1.0
python -m pip install PyYAML==6.0.1
```

> 💡 小提示：
>
> * 每条命令执行完成后确认没有报错
> * 使用 `python` 或 `python3`，保证是 **Python 3.10**

---

## 2. 运行方式

假设你在项目根目录（包含 `NewtonRing/` 文件夹）：

### 2.1 处理单张图片并生成报告（推荐）

```powershell
python NewtonRing/main.py --image NewtonRing/data/raw/your_image.jpg --config NewtonRing/config.yaml
```

* `--image`：图片路径，从 **当前目录**算起
* `--config`：配置文件路径，通常是 `NewtonRing/config.yaml`
* 运行后，结果会输出到 `output/` 目录

---

### 2.2 指定输出目录

```powershell
python NewtonRing/main.py --image NewtonRing/data/raw/your_image.jpg --config NewtonRing/config.yaml --outdir NewtonRing/output
```

---

### 2.3 仅检测与拟合，不生成报告

```powershell
python NewtonRing/main.py --image NewtonRing/data/raw/your_image.jpg --config NewtonRing/config.yaml --no-report
```

---

### 2.4 测试其他图片

例如另一张 synthetic 图片：

```powershell
python NewtonRing/main.py --image NewtonRing/data/raw/synthetic.png --config NewtonRing/config.yaml
```

> ⚠️ 如果检测环数过少或失败，可通过修改 `config.yaml` 中的 `min_rings`、`threshold`、`min_radius` / `max_radius` 调整参数。

---

## 3. 输出内容（output/）

* `figures/*_rings_overlay.png`：检测到的圆心与暗纹半径可视化叠加图
* `figures/*_radial_profile.png`：径向平均灰度曲线 + 暗纹峰/谷标注
* `figures/*_fit_r2_n.png`：r²-n 拟合图（用于报告）
* `reports/*_NewtonRing_Report.docx`：自动生成的实验报告

---

## 4. 关键配置说明（config.yaml）

* `calculation.pixel_to_mm`：像素到毫米的标定系数（**必须正确标定，否则 R 结果无意义**）
* `calculation.wavelength`：光源波长（nm）
* `calculation.min_rings`：最少需要检测到的暗环数
* `detection.center_detection_method`：圆心定位方式：`hough` 或 `gradient`
* `detection.profile_num_angles`：径向曲线采样角度数（越大越稳健，但慢）

---

## 5. 项目结构

* `src/preprocess.py`：预处理（去噪、对比度增强）
* `src/detection.py`：圆心定位、极坐标展开、径向曲线、暗纹半径提取
* `src/calculation.py`：r²-n 拟合与曲率半径 R 计算
* `src/report_gen.py`：Word 报告生成（自动插入图表与表格）
