import sys
import numpy as np
import cv2
import matplotlib.pyplot as plt
from docx import Document
from PIL import Image
import scipy
import pandas as pd

print("=" * 50)
print("环境检查报告")
print("=" * 50)
print(f"Python版本: {sys.version}")
print(f"NumPy版本: {np.__version__}")
print(f"OpenCV版本: {cv2.__version__}")
print(f"Matplotlib版本: {plt.matplotlib.__version__}")
print(f"python-docx已安装: OK")
print(f"Pillow版本: {Image.__version__}")
print(f"SciPy版本: {scipy.__version__}")
print(f"Pandas版本: {pd.__version__}")
print("=" * 50)
print("✅ 所有依赖包安装成功！")