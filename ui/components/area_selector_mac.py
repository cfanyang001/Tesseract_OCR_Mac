import os
import subprocess
import tempfile
from PyQt5.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QLabel, QInputDialog
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
            
            # 获取鼠标当前位置作为参考点
            try:
                mouse_x, mouse_y = pyautogui.position()
                logger.info(f"当前鼠标位置: {mouse_x}, {mouse_y}")
            except:
                mouse_x, mouse_y = 0, 0
                logger.warning("无法获取鼠标位置，将使用默认坐标(0,0)")
            
            # 记录截图前的时间戳
            import time
            start_time = time.time()
            
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
            
            # 获取截图后的鼠标位置，作为区域的中心点
            end_mouse_x, end_mouse_y = pyautogui.position()
            logger.info(f"截图后鼠标位置: {end_mouse_x}, {end_mouse_y}")
            
            # 计算截图区域的坐标 - 假设鼠标位置在选择区域的中心附近
            # 这是一个近似值，但比让用户手动输入更方便
            x = max(0, end_mouse_x - width // 2)
            y = max(0, end_mouse_y - height // 2)
            
            # 确保坐标在屏幕范围内
            x = min(x, screen_width - width)
            y = min(y, screen_height - height)
            
            # 创建区域
            rect = QRect(x, y, width, height)
            
            # 显示确认对话框，让用户确认或调整坐标
            msg_box = QMessageBox()
            msg_box.setWindowTitle("区域选择")
            msg_box.setText(f"已自动确定区域坐标:\nX: {x}, Y: {y}, 宽: {width}, 高: {height}")
            msg_box.setInformativeText("是否需要手动调整坐标？")
            adjust_button = msg_box.addButton("调整坐标", QMessageBox.ActionRole)
            ok_button = msg_box.addButton("确认", QMessageBox.AcceptRole)
            msg_box.setDefaultButton(ok_button)
            
            msg_box.exec_()
            
            if msg_box.clickedButton() == adjust_button:
                # 用户选择手动调整坐标
                x, ok1 = QInputDialog.getInt(None, "调整X坐标", "请输入区域的X坐标:", x, 0, screen_width - width, 1)
                if not ok1:
                    x = 0
                
                y, ok2 = QInputDialog.getInt(None, "调整Y坐标", "请输入区域的Y坐标:", y, 0, screen_height - height, 1)
                if not ok2:
                    y = 0
                
                # 更新区域
                rect = QRect(x, y, width, height)
            
            logger.info(f"选择区域成功: {rect}, 临时文件: {temp_filename}")
            
            return rect, pixmap, temp_filename
            
        except Exception as e:
            logger.error(f"区域选择失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None, None
    
    @staticmethod
    def capture_rect(rect):
        """根据给定的QRect捕获屏幕区域，返回QPixmap"""
        if not rect or not rect.isValid():
            logger.error("无效的区域参数")
            return None, None
        
        try:
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_filename = temp_file.name
            temp_file.close()
            
            # 使用screencapture命令截取指定区域
            x = rect.x()
            y = rect.y()
            width = rect.width()
            height = rect.height()
            
            # 获取屏幕尺寸
            import pyautogui
            screen_width, screen_height = pyautogui.size()
            logger.debug(f"屏幕尺寸: {screen_width}x{screen_height}")
            
            # 确保坐标和尺寸有效，并且在屏幕范围内
            x = max(0, min(x, screen_width - 1))
            y = max(0, min(y, screen_height - 1))
            width = max(1, min(width, screen_width - x))
            height = max(1, min(height, screen_height - y))
                
            logger.info(f"尝试截取区域: x={x}, y={y}, w={width}, h={height}")
            
            # 使用精确的区域坐标
            region_spec = f"{x},{y},{width},{height}"
            logger.debug(f"使用区域参数: {region_spec}")
            
            # 执行截图命令
            try:
                result = subprocess.run([
                    'screencapture',
                    '-R', region_spec,
                    '-x',  # 不发出声音
                    temp_filename
                ], check=True, capture_output=True)
                
                # 输出命令执行结果
                if result.stderr:
                    stderr_output = result.stderr.decode('utf-8', errors='ignore')
                    logger.debug(f"截图命令输出: {stderr_output}")
                    
                    # 如果有错误信息，可能是坐标问题
                    if stderr_output and "Invalid" in stderr_output:
                        logger.warning(f"截图命令报告无效参数: {stderr_output}")
            except subprocess.CalledProcessError as e:
                logger.error(f"截图命令执行失败: {e}")
                # 尝试使用pyautogui作为备选方案
                try:
                    logger.info(f"尝试使用pyautogui截图: {x},{y},{width},{height}")
                    screenshot = pyautogui.screenshot(region=(x, y, width, height))
                    screenshot.save(temp_filename)
                    logger.info(f"pyautogui截图成功: {screenshot.width}x{screenshot.height}")
                except Exception as pag_error:
                    logger.error(f"pyautogui截图失败: {pag_error}")
                    return None, None
            
            # 检查文件是否有效
            if not os.path.exists(temp_filename):
                logger.error("截图文件未创建")
                return None, None
                
            if os.path.getsize(temp_filename) == 0:
                logger.error("截图文件为空")
                try:
                    os.remove(temp_filename)
                except Exception as e:
                    logger.error(f"删除空截图文件失败: {e}")
                
                # 尝试使用pyautogui作为备选方案
                try:
                    logger.info(f"尝试使用pyautogui截图(备选): {x},{y},{width},{height}")
                    screenshot = pyautogui.screenshot(region=(x, y, width, height))
                    screenshot.save(temp_filename)
                    logger.info(f"pyautogui备选截图成功: {screenshot.width}x{screenshot.height}")
                except Exception as pag_error:
                    logger.error(f"pyautogui备选截图失败: {pag_error}")
                    return None, None
            
            # 加载截图
            pixmap = QPixmap(temp_filename)
            if pixmap.isNull():
                logger.error("截图加载失败")
                try:
                    os.remove(temp_filename)
                except Exception as e:
                    logger.error(f"删除无效截图文件失败: {e}")
                return None, None
            
            logger.info(f"截图成功: {pixmap.width()}x{pixmap.height()}")
            
            return pixmap, temp_filename
            
        except Exception as e:
            logger.error(f"区域截图失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None 