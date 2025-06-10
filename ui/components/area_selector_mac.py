import os
import subprocess
import tempfile
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPixmap, QImage
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
            
            # 检测系统缩放因子
            dpi_scale = 1.0
            try:
                # 在macOS上，可以通过比较截图尺寸与报告的屏幕尺寸来估计缩放因子
                result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], capture_output=True, text=True)
                output = result.stdout
                if 'Retina' in output:
                    dpi_scale = 2.0
                    logger.info("检测到屏幕类型: Retina显示屏, 设置DPI缩放因子: 2.0")
                else:
                    logger.info("检测到屏幕类型: 标准分辨率, 设置DPI缩放因子: 1.0")
            except:
                logger.warning("无法检测DPI缩放因子，使用默认值: 1.0")
                
            # 使用screencapture命令进行截图，交互式
            result = subprocess.run([
                'screencapture',
                '-i',  # 交互式
                '-s',  # 选择区域
                temp_filename
            ], check=False)
            
            # 检查是否取消了截图
            if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0:
                # 使用CV2读取截图
                img = cv2.imread(temp_filename)
                if img is None:
                    logger.error("无法读取截图文件")
                    return None, None, None
                
                # 获取截图尺寸
                height, width, _ = img.shape
                
                # 创建原始截图的永久副本
                logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
                captures_dir = os.path.join(logs_dir, "captures")
                os.makedirs(captures_dir, exist_ok=True)
                
                # 创建带时间戳的文件名
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                original_capture_path = os.path.join(captures_dir, f"original_capture_{timestamp}.png")
                
                # 复制截图
                shutil.copy2(temp_filename, original_capture_path)
                logger.info(f"原始截图已永久保存到: {original_capture_path}")
                
                # 保存路径到类变量
                MacScreenCaptureSelector.original_capture_path = original_capture_path
                
                # 创建一个标记图像，用于调试
                marked_img = img.copy()
                
                # 估计区域在全屏的位置
                # 由于我们没有原始屏幕坐标，需要创建一个合理的估计
                # 重要修复：截图本身就是用户选择的区域，x和y坐标应该基于屏幕中心计算
                # 在没有确切坐标时，让我们使用屏幕中心减去截图尺寸的一半作为估计
                center_x = screen_width // 2
                center_y = screen_height // 2
                
                # 计算区域的估计位置（以屏幕中心为基准点）
                x = center_x - (width // 2)
                y = center_y - (height // 2)
                
                # 实际情况下，要从最近的用户鼠标位置获取更准确的坐标
                # 这里我们可以通过分析系统截图工具的行为，尝试获取更准确的坐标
                # 例如，分析截图的内容特征来匹配原始屏幕上的位置
                
                # 保存调试用的标记图像
                debug_capture_path = os.path.join(captures_dir, f"debug_capture_{timestamp}.png")
                cv2.imwrite(debug_capture_path, marked_img)
                logger.info(f"调试用标记图像已保存到: {debug_capture_path}")
                logger.info(f"自动设置区域位置: X={x}, Y={y}, 宽={width}, 高={height}")
                
                # 转换为RGB格式显示
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # 创建QImage和QPixmap
                bytes_per_line = 3 * width
                q_img = QImage(img_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(q_img)
                
                # 创建QRect
                rect = QRect(x, y, width, height)
                
                # 清理临时文件
                try:
                    os.remove(temp_filename)
                except:
                    pass
                    
                # 显示确认对话框
                dialog = QDialog()
                dialog.setWindowTitle("确认选择区域")
                dialog.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
                dialog.setFixedSize(500, 400)
                
                layout = QVBoxLayout()
                
                # 添加提示标签
                hint_label = QLabel("您已选择以下屏幕区域，请确认:")
                hint_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(hint_label)
                
                # 创建预览标签
                preview_label = QLabel()
                preview_label.setAlignment(Qt.AlignCenter)
                preview_label.setFixedSize(450, 300)
                
                # 缩放图像以适应预览区域
                scaled_pixmap = pixmap.scaled(
                    preview_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                preview_label.setPixmap(scaled_pixmap)
                layout.addWidget(preview_label)
                
                # 添加坐标信息
                coords_label = QLabel(f"X: {x}, Y: {y}, 宽: {width}, 高: {height}")
                coords_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(coords_label)
                
                # 添加按钮区域
                button_layout = QHBoxLayout()
                
                # 确认按钮
                confirm_button = QPushButton("确认使用此区域")
                confirm_button.setMinimumWidth(150)
                button_layout.addWidget(confirm_button)
                
                # 取消按钮
                cancel_button = QPushButton("取消")
                cancel_button.setMinimumWidth(120)
                button_layout.addWidget(cancel_button)
                
                layout.addLayout(button_layout)
                dialog.setLayout(layout)
                
                # 设置是否已确认的变量
                confirmed = [False]
                
                def on_confirm():
                    confirmed[0] = True
                    dialog.close()
                    
                def on_cancel():
                    dialog.close()
                    
                confirm_button.clicked.connect(on_confirm)
                cancel_button.clicked.connect(on_cancel)
                
                dialog.exec_()
                
                if confirmed[0]:
                    return rect, pixmap, original_capture_path
                else:
                    return None, None, None
            else:
                logger.warning("用户取消了区域选择")
                return None, None, None
        except Exception as e:
            logger.error(f"选择区域失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None, None
    
