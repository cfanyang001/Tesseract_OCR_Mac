import os
import subprocess
import tempfile
from PyQt5.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QLabel, QInputDialog, QPushButton, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPixmap, QImage
from loguru import logger


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
            import pyautogui
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
            
            # 改进的位置设置对话框
            manual_position_dialog = QDialog()
            manual_position_dialog.setWindowTitle("设置区域位置")
            manual_position_dialog.setMinimumWidth(400)
            manual_position_dialog.setMinimumHeight(300)
            
            mp_layout = QVBoxLayout()
            
            mp_title = QLabel("您已选择了屏幕区域:")
            mp_title.setAlignment(Qt.AlignCenter)
            mp_layout.addWidget(mp_title)
            
            # 显示所选区域的图像
            mp_preview = QLabel()
            mp_preview.setAlignment(Qt.AlignCenter)
            mp_preview.setMinimumSize(320, 240)
            mp_preview.setStyleSheet("border: 1px solid #333;")
            
            if width > 300 or height > 200:
                scaled = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                mp_preview.setPixmap(scaled)
            else:
                mp_preview.setPixmap(pixmap)
            mp_layout.addWidget(mp_preview)
            
            mp_info = QLabel(f"图像尺寸: {width}x{height} 像素")
            mp_info.setAlignment(Qt.AlignCenter)
            mp_layout.addWidget(mp_info)
            
            mp_question = QLabel("请选择如何设置这个区域在屏幕上的位置:")
            mp_question.setAlignment(Qt.AlignCenter)
            mp_layout.addWidget(mp_question)
            
            mp_buttons = QHBoxLayout()
            
            mp_center = QPushButton("屏幕中央")
            mp_mouse = QPushButton("鼠标位置")
            mp_manual = QPushButton("手动设置")
            
            mp_buttons.addWidget(mp_center)
            mp_buttons.addWidget(mp_mouse)
            mp_buttons.addWidget(mp_manual)
            
            mp_layout.addLayout(mp_buttons)
            
            manual_position_dialog.setLayout(mp_layout)
            
            position_result = {'method': 'center'}
            
            def on_mp_center():
                position_result['method'] = 'center'
                manual_position_dialog.accept()
                
            def on_mp_mouse():
                position_result['method'] = 'mouse'
                manual_position_dialog.accept()
                
            def on_mp_manual():
                position_result['method'] = 'manual'
                manual_position_dialog.accept()
                
            mp_center.clicked.connect(on_mp_center)
            mp_mouse.clicked.connect(on_mp_mouse)
            mp_manual.clicked.connect(on_mp_manual)
            
            manual_position_dialog.exec_()
            
            # 根据用户选择计算坐标
            if position_result['method'] == 'center':
                # 放在屏幕中央
                x = max(0, (screen_width - width) // 2)
                y = max(0, (screen_height - height) // 2)
                logger.info("使用屏幕中心策略计算坐标")
            elif position_result['method'] == 'mouse':
                # 使用当前鼠标位置
                current_x, current_y = pyautogui.position()
                x = max(0, current_x - width // 2)
                y = max(0, current_y - height // 2)
                logger.info("使用鼠标位置策略计算坐标")
            else:
                # 手动设置
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
            x = min(x, screen_width - width)
            y = min(y, screen_height - height)
            
            # 创建区域
            rect = QRect(x, y, width, height)
            
            # 创建确认对话框，同时显示预览图和坐标
            confirm_dialog = QDialog()
            confirm_dialog.setWindowTitle("确认区域")
            confirm_dialog.setMinimumWidth(400)
            confirm_dialog.setMinimumHeight(400)
            
            layout = QVBoxLayout()
            
            # 添加区域坐标信息（明确显示）
            coord_label = QLabel(f"计算的区域位置: X={x}, Y={y}, 宽={width}, 高={height}")
            coord_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(coord_label)
            
            # 添加区域预览标题
            preview_title = QLabel("区域预览图像:")
            preview_title.setAlignment(Qt.AlignCenter)
            layout.addWidget(preview_title)
            
            # 添加预览图像
            preview_label = QLabel()
            preview_label.setAlignment(Qt.AlignCenter)
            preview_label.setMinimumSize(320, 240)
            preview_label.setStyleSheet("border: 1px solid #333;")
            
            if width > 300 or height > 200:
                # 缩放大图像以适应对话框
                scaled_pixmap = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                preview_label.setPixmap(scaled_pixmap)
            else:
                preview_label.setPixmap(pixmap)
            layout.addWidget(preview_label)
            
            # 显示图像大小信息
            size_label = QLabel(f"图像大小: {pixmap.width()}x{pixmap.height()} 像素")
            size_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(size_label)
            
            # 提示信息
            info_label = QLabel("请确认这个区域位置。点击\"确认\"使用当前设置，或点击其他按钮进行调整。")
            info_label.setWordWrap(True)
            info_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(info_label)
            
            # 按钮布局
            btn_layout = QHBoxLayout()
            
            adjust_btn = QPushButton("调整坐标")
            verify_btn = QPushButton("验证区域")
            confirm_btn = QPushButton("确认")
            
            btn_layout.addWidget(adjust_btn)
            btn_layout.addWidget(verify_btn)
            btn_layout.addWidget(confirm_btn)
            
            # 设置默认按钮
            confirm_btn.setDefault(True)
            
            # 将按钮布局添加到主布局
            layout.addLayout(btn_layout)
            
            confirm_dialog.setLayout(layout)
            
            # 连接按钮信号
            result = {'action': 'confirm', 'rect': rect}
            
            def on_adjust():
                result['action'] = 'adjust'
                confirm_dialog.accept()
            
            def on_verify():
                result['action'] = 'verify'
                confirm_dialog.accept()
                
            def on_confirm():
                result['action'] = 'confirm'
                confirm_dialog.accept()
            
            adjust_btn.clicked.connect(on_adjust)
            verify_btn.clicked.connect(on_verify)
            confirm_btn.clicked.connect(on_confirm)
            
            # 显示对话框
            confirm_dialog.exec_()
            
            # 处理用户选择
            if result['action'] == 'adjust':
                # 用户选择手动调整坐标
                x, ok1 = QInputDialog.getInt(None, "调整X坐标", "请输入区域的X坐标:", rect.x(), 0, screen_width - rect.width(), 1)
                if not ok1:
                    x = rect.x()
                
                y, ok2 = QInputDialog.getInt(None, "调整Y坐标", "请输入区域的Y坐标:", rect.y(), 0, screen_height - rect.height(), 1)
                if not ok2:
                    y = rect.y()
                
                # 更新区域
                rect = QRect(x, y, rect.width(), rect.height())
                
                # 再次确认调整后的区域
                adjust_dialog = QDialog()
                adjust_dialog.setWindowTitle("确认调整后的区域")
                adjust_dialog.setMinimumWidth(400)
                adjust_dialog.setMinimumHeight(300)
                
                a_layout = QVBoxLayout()
                
                # 显示调整后的坐标
                a_coord_label = QLabel(f"调整后的区域位置: X={rect.x()}, Y={rect.y()}, 宽={rect.width()}, 高={rect.height()}")
                a_coord_label.setAlignment(Qt.AlignCenter)
                a_layout.addWidget(a_coord_label)
                
                # 显示原始截图
                a_label = QLabel("原始区域内容:")
                a_label.setAlignment(Qt.AlignCenter)
                a_layout.addWidget(a_label)
                
                a_preview = QLabel()
                a_preview.setAlignment(Qt.AlignCenter)
                a_preview.setMinimumSize(320, 240)
                a_preview.setStyleSheet("border: 1px solid #333;")
                
                if pixmap.width() > 300 or pixmap.height() > 200:
                    scaled = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    a_preview.setPixmap(scaled)
                else:
                    a_preview.setPixmap(pixmap)
                a_layout.addWidget(a_preview)
                
                # 显示位置指南
                a_guide = QLabel("您可以使用以下信息帮助定位:\n"
                                "1. 在屏幕上查找上图所示的内容\n"
                                "2. 调整坐标使其位于正确位置")
                a_guide.setWordWrap(True)
                a_guide.setAlignment(Qt.AlignCenter)
                a_layout.addWidget(a_guide)
                
                a_buttons = QHBoxLayout()
                a_retry = QPushButton("重新调整")
                a_confirm = QPushButton("确认使用")
                
                a_buttons.addWidget(a_retry)
                a_buttons.addWidget(a_confirm)
                
                a_layout.addLayout(a_buttons)
                adjust_dialog.setLayout(a_layout)
                
                # 设置默认按钮
                a_confirm.setDefault(True)
                
                a_result = {'confirmed': False}
                
                def on_a_retry():
                    a_result['confirmed'] = False
                    adjust_dialog.accept()
                    
                def on_a_confirm():
                    a_result['confirmed'] = True
                    adjust_dialog.accept()
                    
                a_retry.clicked.connect(on_a_retry)
                a_confirm.clicked.connect(on_a_confirm)
                
                adjust_dialog.exec_()
                
                if not a_result['confirmed']:
                    # 用户不满意，重新调整
                    return MacScreenCaptureSelector.select_area()
            
            elif result['action'] == 'verify':
                # 用户选择验证区域 - 创建简化的位置指示器
                verify_dialog = QDialog()
                verify_dialog.setWindowTitle("验证区域")
                verify_dialog.setMinimumWidth(500)
                verify_dialog.setMinimumHeight(400)
                
                v_layout = QVBoxLayout()
                
                # 显示验证区域的坐标信息
                v_coord_label = QLabel(f"当前区域位置: X={rect.x()}, Y={rect.y()}, 宽={rect.width()}, 高={rect.height()}")
                v_coord_label.setAlignment(Qt.AlignCenter)
                v_layout.addWidget(v_coord_label)
                
                # 创建一个图片标签说明区域位置
                v_guide_label = QLabel("当前区域实时预览:")
                v_guide_label.setAlignment(Qt.AlignCenter)
                v_layout.addWidget(v_guide_label)
                
                # 创建一个屏幕位置指示图
                # 这里我们使用一个简单的示意图显示选定区域在屏幕上的位置
                position_preview = QLabel()
                position_preview.setAlignment(Qt.AlignCenter)
                position_preview.setMinimumSize(400, 200)
                position_preview.setStyleSheet("background-color: #333; border: 1px solid #555;")
                
                # 创建一个简单的屏幕示意图和区域指示
                # 这里仅创建QLabel，实际实现中可以使用QPainter绘制更详细的示意图
                pos_info = QLabel(f"区域位于屏幕的:\n"
                                 f"水平位置: {rect.x() / screen_width * 100:.1f}% 处\n"
                                 f"垂直位置: {rect.y() / screen_height * 100:.1f}% 处")
                pos_info.setAlignment(Qt.AlignCenter)
                pos_info.setStyleSheet("color: white; background: none; border: none;")
                
                # 为position_preview创建一个布局以放置pos_info
                pos_layout = QVBoxLayout(position_preview)
                pos_layout.addWidget(pos_info)
                
                v_layout.addWidget(position_preview)
                
                # 显示原始图像
                v_label = QLabel("您选择的区域内容:")
                v_label.setAlignment(Qt.AlignCenter)
                v_layout.addWidget(v_label)
                
                v_preview = QLabel()
                v_preview.setAlignment(Qt.AlignCenter)
                v_preview.setMinimumSize(320, 240)
                v_preview.setStyleSheet("border: 1px solid #333;")
                
                if pixmap.width() > 300 or pixmap.height() > 200:
                    scaled = pixmap.scaled(300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    v_preview.setPixmap(scaled)
                else:
                    v_preview.setPixmap(pixmap)
                v_layout.addWidget(v_preview)
                
                # 显示大小信息
                v_size_label = QLabel(f"预览图像大小: {pixmap.width()}x{pixmap.height()} 像素")
                v_size_label.setAlignment(Qt.AlignCenter)
                v_layout.addWidget(v_size_label)
                
                v_buttons = QHBoxLayout()
                v_retry = QPushButton("重新选择")
                v_adjust = QPushButton("调整坐标")
                v_confirm = QPushButton("确认使用")
                
                v_buttons.addWidget(v_retry)
                v_buttons.addWidget(v_adjust)
                v_buttons.addWidget(v_confirm)
                
                v_layout.addLayout(v_buttons)
                verify_dialog.setLayout(v_layout)
                
                # 设置默认按钮
                v_confirm.setDefault(True)
                
                v_result = {'action': 'confirm'}
                
                def on_v_retry():
                    v_result['action'] = 'retry'
                    verify_dialog.accept()
                    
                def on_v_adjust():
                    v_result['action'] = 'adjust'
                    verify_dialog.accept()
                    
                def on_v_confirm():
                    v_result['action'] = 'confirm'
                    verify_dialog.accept()
                    
                v_retry.clicked.connect(on_v_retry)
                v_adjust.clicked.connect(on_v_adjust)
                v_confirm.clicked.connect(on_v_confirm)
                
                verify_dialog.exec_()
                
                if v_result['action'] == 'retry':
                    # 用户选择重新选择区域
                    return MacScreenCaptureSelector.select_area()
                elif v_result['action'] == 'adjust':
                    # 用户选择调整坐标
                    x, ok1 = QInputDialog.getInt(None, "调整X坐标", "请输入区域的X坐标:", rect.x(), 0, screen_width - rect.width(), 1)
                    if not ok1:
                        x = rect.x()
                    
                    y, ok2 = QInputDialog.getInt(None, "调整Y坐标", "请输入区域的Y坐标:", rect.y(), 0, screen_height - rect.height(), 1)
                    if not ok2:
                        y = rect.y()
                    
                    # 更新区域
                    rect = QRect(x, y, rect.width(), rect.height())
            
            logger.info(f"最终选择区域: {rect}, 临时文件: {temp_filename}")
            
            return rect, pixmap, temp_filename
        
        except Exception as e:
            logger.error(f"区域选择失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None, None
    
