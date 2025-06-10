import os
import subprocess
import tempfile
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPixmap
from loguru import logger
import pyautogui
import shutil
import cv2
import datetime


class MacScreenCaptureSelector:
    """Mac系统专用的屏幕区域选择器，使用系统原生截图工具"""
    
    # 添加一个类变量来保存原始截图
    original_capture_path = None
    
    @staticmethod
    def select_area():
        """使用macOS系统截图工具选择区域，返回QRect和QPixmap"""
        try:
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_filename = temp_file.name
            temp_file.close()
            
            # 使用系统截图工具，交互式选择
            logger.info("启动系统截图工具，请选择区域")
            
            # 获取屏幕尺寸
            screen_width, screen_height = pyautogui.size()
            logger.info(f"屏幕尺寸: {screen_width}x{screen_height}")
            
            # 获取当前鼠标位置作为参考点
            mouse_x, mouse_y = pyautogui.position()
            
            # 运行截图命令
            subprocess.run([
                'screencapture', 
                '-i',   # 交互式
                '-s',   # 选择模式
                '-x',   # 不发出声音
                temp_filename
            ], check=True)
            
            # 检查文件是否存在和有效
            if not os.path.exists(temp_filename) or os.path.getsize(temp_filename) == 0:
                logger.warning("未选择区域或截图被取消")
                try:
                    os.remove(temp_filename)
                except:
                    pass
                return None, None, None
            
            # 加载截图
            pixmap = QPixmap(temp_filename)
            if pixmap.isNull():
                logger.error("截图加载失败")
                try:
                    os.remove(temp_filename)
                except:
                    pass
                return None, None, None
            
            # 获取区域信息
            width = pixmap.width()
            height = pixmap.height()
            
            # 自动计算一个合理的起始坐标位置
            # 策略：尝试以鼠标为中心，但确保不超出屏幕边界
            x = max(0, min(mouse_x - width // 2, screen_width - width))
            y = max(0, min(mouse_y - height // 2, screen_height - height))
            
            # 为用户显示确认对话框
            info_dialog = QDialog()
            info_dialog.setWindowTitle("区域选择完成")
            info_dialog.setMinimumWidth(400)
            info_dialog.setMinimumHeight(300)
            
            layout = QVBoxLayout()
            
            # 标题
            title = QLabel("您已选择了屏幕区域:")
            title.setAlignment(Qt.AlignCenter)
            layout.addWidget(title)
            
            # 显示所选区域的图像
            preview = QLabel()
            preview.setAlignment(Qt.AlignCenter)
            preview.setMinimumSize(320, 240)
            preview.setStyleSheet("border: 1px solid #333;")
            
            if width > 300 or height > 200:
                scaled = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                preview.setPixmap(scaled)
            else:
                preview.setPixmap(pixmap)
            layout.addWidget(preview)
            
            # 显示图像尺寸信息
            size_label = QLabel(f"图像尺寸: {width}x{height} 像素")
            size_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(size_label)
            
            # 提示说明
            hint_label = QLabel("系统将自动设置合适的区域位置，您无需手动输入坐标")
            hint_label.setStyleSheet("color: gray; font-style: italic;")
            hint_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(hint_label)
            
            # 确认按钮
            confirm_btn = QPushButton("确认使用此区域")
            confirm_btn.setMinimumHeight(40)
            layout.addWidget(confirm_btn)
            
            info_dialog.setLayout(layout)
            
            # 记录用户选择
            confirmed = {'ok': False}
            
            def on_confirm():
                confirmed['ok'] = True
                info_dialog.accept()
            
            confirm_btn.clicked.connect(on_confirm)
            
            info_dialog.exec_()
            
            # 如果用户取消，终止操作
            if not confirmed['ok']:
                try:
                    os.remove(temp_filename)
                except:
                    pass
                return None, None, None
            
            # 创建区域
            rect = QRect(x, y, width, height)
            
            # 创建永久保存的副本，用于后续OCR操作
            permanent_dir = os.path.join(os.getcwd(), "logs/captures")
            os.makedirs(permanent_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            permanent_path = os.path.join(permanent_dir, f"original_capture_{timestamp}.png")
            
            # 复制原始截图到永久位置
            shutil.copy2(temp_filename, permanent_path)
            logger.info(f"原始截图已永久保存到: {permanent_path}")
            
            # 保存原始截图路径到类变量
            MacScreenCaptureSelector.original_capture_path = permanent_path
            
            # 添加调试标记到图像
            try:
                # 读取截图
                debug_image = cv2.imread(permanent_path)
                if debug_image is not None:
                    # 在图像上添加指示位置和内容的标记
                    cv2.rectangle(debug_image, (0, 0), (width-1, height-1), (0, 0, 255), 2)
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(debug_image, f"选定区域", (10, 30), font, 1, (0, 0, 255), 2)
                    cv2.putText(debug_image, f"尺寸:{width}x{height}", (10, 70), font, 0.7, (0, 0, 255), 2)
                    
                    # 保存带标记的图像
                    debug_path = os.path.join(permanent_dir, f"debug_capture_{timestamp}.png")
                    cv2.imwrite(debug_path, debug_image)
                    logger.info(f"调试用标记图像已保存到: {debug_path}")
            except Exception as debug_error:
                logger.warning(f"创建调试图像失败: {debug_error}")
            
            logger.info(f"自动设置区域位置: X={x}, Y={y}, 宽={width}, 高={height}")
            
            return rect, pixmap, permanent_path
            
        except Exception as e:
            logger.error(f"区域选择失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            try:
                os.remove(temp_filename)
            except:
                pass
            return None, None, None
    
