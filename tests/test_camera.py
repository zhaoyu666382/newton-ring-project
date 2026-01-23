"""
摄像头测试程序 - 牛顿环项目
功能：
1. 检测可用摄像头
2. 实时显示摄像头画面
3. 拍照保存功能
4. 图像质量检测（清晰度、对比度）
5. 基础图像处理演示

使用说明：
- 按 's' 键保存当前帧
- 按 'q' 键退出
- 按 'g' 键切换灰度/彩色模式
- 按 'e' 键显示边缘检测
- 按 'c' 键显示清晰度和对比度指标
"""

import cv2
import numpy as np
import os
from datetime import datetime


class CameraTest:
    """摄像头测试类"""
    
    def __init__(self, camera_id=0, save_dir='data/raw'):
        """
        初始化摄像头
        
        参数:
            camera_id: 摄像头编号，0表示默认摄像头
            save_dir: 图片保存目录
        """
        self.camera_id = camera_id
        self.save_dir = save_dir
        self.cap = None
        self.gray_mode = False
        self.edge_mode = False
        
        # 创建保存目录
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            print(f"✅ 创建保存目录: {save_dir}")
    
    def detect_cameras(self):
        """检测所有可用的摄像头"""
        print("\n🔍 检测可用摄像头...")
        available_cameras = []
        
        # 尝试前10个摄像头ID
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    available_cameras.append(i)
                    h, w = frame.shape[:2]
                    print(f"  ✅ 摄像头 {i}: 分辨率 {w}x{h}")
                cap.release()
        
        if not available_cameras:
            print("  ❌ 未检测到可用摄像头")
        else:
            print(f"\n共检测到 {len(available_cameras)} 个摄像头")
        
        return available_cameras
    
    def open_camera(self):
        """打开摄像头"""
        print(f"\n📷 尝试打开摄像头 {self.camera_id}...")
        self.cap = cv2.VideoCapture(self.camera_id)
        
        if not self.cap.isOpened():
            print(f"❌ 无法打开摄像头 {self.camera_id}")
            return False
        
        # 获取摄像头参数
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        
        print(f"✅ 摄像头已打开")
        print(f"   分辨率: {width}x{height}")
        print(f"   帧率: {fps} FPS")
        
        return True
    
    def calculate_sharpness(self, image):
        """
        计算图像清晰度（使用拉普拉斯方差）
        
        参数:
            image: 输入图像（BGR或灰度）
        返回:
            清晰度分数（越高越清晰）
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 计算拉普拉斯算子的方差
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        
        return sharpness
    
    def calculate_contrast(self, image):
        """
        计算图像对比度（标准差）
        
        参数:
            image: 输入图像（BGR或灰度）
        返回:
            对比度分数
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        contrast = gray.std()
        return contrast
    
    def process_frame(self, frame):
        """
        处理帧图像
        
        参数:
            frame: 原始帧
        返回:
            处理后的帧
        """
        if self.gray_mode:
            # 灰度模式
            processed = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
        elif self.edge_mode:
            # 边缘检测模式
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            processed = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        else:
            processed = frame.copy()
        
        return processed
    
    def add_info_overlay(self, frame, sharpness, contrast):
        """
        在画面上叠加信息
        
        参数:
            frame: 输入帧
            sharpness: 清晰度
            contrast: 对比度
        """
        # 创建半透明背景
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # 绘制信息面板
        cv2.rectangle(overlay, (10, 10), (300, 120), (0, 0, 0), -1)
        frame_with_overlay = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        # 添加文字信息
        font = cv2.FONT_HERSHEY_SIMPLEX
        y_offset = 35
        
        # 清晰度
        sharpness_text = f"Sharpness: {sharpness:.1f}"
        if sharpness > 100:
            color = (0, 255, 0)  # 绿色 - 清晰
            status = "Clear"
        elif sharpness > 50:
            color = (0, 255, 255)  # 黄色 - 一般
            status = "Moderate"
        else:
            color = (0, 0, 255)  # 红色 - 模糊
            status = "Blurry"
        
        cv2.putText(frame_with_overlay, sharpness_text, (20, y_offset), 
                    font, 0.6, color, 2)
        cv2.putText(frame_with_overlay, f"Status: {status}", (20, y_offset + 25),
                    font, 0.5, color, 1)
        
        # 对比度
        contrast_text = f"Contrast: {contrast:.1f}"
        cv2.putText(frame_with_overlay, contrast_text, (20, y_offset + 55),
                    font, 0.6, (255, 255, 255), 2)
        
        return frame_with_overlay
    
    def save_frame(self, frame):
        """
        保存当前帧
        
        参数:
            frame: 要保存的帧
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"capture_{timestamp}.jpg"
        filepath = os.path.join(self.save_dir, filename)
        
        cv2.imwrite(filepath, frame)
        print(f"✅ 图片已保存: {filepath}")
        
        return filepath
    
    def run(self):
        """运行摄像头测试"""
        if not self.open_camera():
            return
        
        print("\n" + "="*60)
        print("摄像头测试运行中...")
        print("="*60)
        print("操作说明:")
        print("  [s] - 保存当前帧")
        print("  [g] - 切换灰度/彩色模式")
        print("  [e] - 切换边缘检测模式")
        print("  [c] - 显示/隐藏质量指标")
        print("  [q] 或 [ESC] - 退出程序")
        print("  或直接关闭窗口")
        print("="*60)
        
        show_metrics = False
        frame_count = 0
        
        try:
            while True:
                ret, frame = self.cap.read()
                
                if not ret:
                    print("❌ 无法读取摄像头画面")
                    break
                
                frame_count += 1
                
                # 处理帧
                processed_frame = self.process_frame(frame)
                
                # 计算图像质量指标
                if show_metrics or frame_count % 10 == 0:  # 每10帧计算一次
                    sharpness = self.calculate_sharpness(frame)
                    contrast = self.calculate_contrast(frame)
                
                # 叠加信息
                if show_metrics:
                    display_frame = self.add_info_overlay(processed_frame, sharpness, contrast)
                else:
                    display_frame = processed_frame
                
                # 显示画面
                cv2.imshow('Newton Ring - Camera Test', display_frame)
                
                # 按键处理（增加超时以便响应更快）
                key = cv2.waitKey(1) & 0xFF
                
                # 检查窗口是否被关闭
                try:
                    if cv2.getWindowProperty('Newton Ring - Camera Test', cv2.WND_PROP_VISIBLE) < 1:
                        print("\n👋 窗口已关闭，退出程序")
                        break
                except:
                    # 窗口已被关闭
                    print("\n👋 窗口已关闭，退出程序")
                    break
                
                if key == ord('q') or key == 27:  # q键或ESC键
                    print("\n👋 退出程序")
                    break
                elif key == ord('s'):
                    self.save_frame(frame)
                elif key == ord('g'):
                    self.gray_mode = not self.gray_mode
                    self.edge_mode = False
                    mode = "灰度" if self.gray_mode else "彩色"
                    print(f"🔄 切换到{mode}模式")
                elif key == ord('e'):
                    self.edge_mode = not self.edge_mode
                    self.gray_mode = False
                    mode = "边缘检测" if self.edge_mode else "正常"
                    print(f"🔄 切换到{mode}模式")
                elif key == ord('c'):
                    show_metrics = not show_metrics
                    status = "显示" if show_metrics else "隐藏"
                    print(f"🔄 {status}质量指标")
        
        except KeyboardInterrupt:
            print("\n👋 用户中断，退出程序")
        
        finally:
            # 确保资源被释放
            if self.cap is not None:
                self.cap.release()
            cv2.destroyAllWindows()
            # 多次调用确保窗口完全关闭
            cv2.waitKey(1)
            print("✅ 资源已释放")


def main():
    """主函数"""
    print("="*60)
    print("牛顿环项目 - 摄像头测试程序")
    print("="*60)
    
    # 创建测试对象
    camera_test = CameraTest(camera_id=0, save_dir='data/raw')
    
    # 检测可用摄像头
    available = camera_test.detect_cameras()
    
    if available:
        # 询问用户选择摄像头
        if len(available) > 1:
            print(f"\n检测到多个摄像头: {available}")
            try:
                choice = int(input("请选择摄像头ID (直接回车使用0): ") or "0")
                if choice in available:
                    camera_test.camera_id = choice
                else:
                    print(f"⚠️  无效选择，使用默认摄像头 0")
            except ValueError:
                print(f"⚠️  无效输入，使用默认摄像头 0")
        
        # 运行测试
        camera_test.run()
    else:
        print("\n❌ 未找到可用摄像头，请检查:")
        print("   1. 摄像头是否正确连接")
        print("   2. 摄像头驱动是否安装")
        print("   3. 其他程序是否占用摄像头")
        print("   4. 尝试重启电脑")


if __name__ == "__main__":
    main()