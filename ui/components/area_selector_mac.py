import os
import subprocess
import tempfile
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPixmap
from loguru import logger
import pyautogui


class MacScreenCaptureSelector:
    """Mac系统专用的屏幕区域选择器，使用系统原生截图工具"""
    
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
            
            # 简化的位置设置对话框
            position_dialog = QDialog()
            position_dialog.setWindowTitle("设置区域位置")
            position_dialog.setMinimumWidth(400)
            position_dialog.setMinimumHeight(300)
            
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
            
            # 显示图像尺寸
            size_info = QLabel(f"图像尺寸: {width}x{height} 像素")
            size_info.setAlignment(Qt.AlignCenter)
            layout.addWidget(size_info)
            
            # 提示信息
            prompt = QLabel("请选择如何设置这个区域在屏幕上的位置:")
            prompt.setAlignment(Qt.AlignCenter)
            layout.addWidget(prompt)
            
            # 按钮布局
            buttons = QHBoxLayout()
            
            center_btn = QPushButton("屏幕中央")
            mouse_btn = QPushButton("鼠标位置")
            manual_btn = QPushButton("手动设置")
            
            buttons.addWidget(center_btn)
            buttons.addWidget(mouse_btn)
            buttons.addWidget(manual_btn)
            
            layout.addLayout(buttons)
            
            position_dialog.setLayout(layout)
            
            # 记录用户选择
            position_method = {'method': 'center'}
            
            def on_center():
                position_method['method'] = 'center'
                position_dialog.accept()
                
            def on_mouse():
                position_method['method'] = 'mouse'
                position_dialog.accept()
                
            def on_manual():
                position_method['method'] = 'manual'
                position_dialog.accept()
                
            center_btn.clicked.connect(on_center)
            mouse_btn.clicked.connect(on_mouse)
            manual_btn.clicked.connect(on_manual)
            
            position_dialog.exec_()
            
            # 根据用户选择计算坐标
            if position_method['method'] == 'center':
                # 放在屏幕中央
                x = max(0, (screen_width - width) // 2)
                y = max(0, (screen_height - height) // 2)
                logger.info("使用屏幕中心策略计算坐标")
            elif position_method['method'] == 'mouse':
                # 使用当前鼠标位置
                current_x, current_y = pyautogui.position()
                x = max(0, current_x - width // 2)
                y = max(0, current_y - height // 2)
                logger.info("使用鼠标位置策略计算坐标")
            else:
                # 手动设置
                from PyQt5.QtWidgets import QInputDialog
                x, ok1 = QInputDialog.getInt(None, "设置X坐标", "请输入区域的X坐标:", 
                                          screen_width // 2 - width // 2, 0, screen_width - width, 1)
                if not ok1:
                    x = (screen_width - width) // 2
                
                y, ok2 = QInputDialog.getInt(None, "设置Y坐标", "请输入区域的Y坐标:", 
                                          screen_height // 2 - height // 2, 0, screen_height - height, 1)
                if not ok2:
                    y = (screen_height - height) // 2
                
                logger.info("使用手动设置坐标")
            
            # 确保坐标在屏幕范围内
            x = min(max(0, x), screen_width - width)
            y = min(max(0, y), screen_height - height)
            
            # 创建区域
            rect = QRect(x, y, width, height)
            
            # 删除临时文件
            try:
                os.remove(temp_filename)
            except Exception as e:
                logger.warning(f"无法删除临时文件: {e}")
            
            # 直接返回结果
            return rect, pixmap, temp_filename
            
        except Exception as e:
            logger.error(f"区域选择失败: {str(e)}")
            try:
                os.remove(temp_filename)
            except:
                pass
            return None, None, None
    
