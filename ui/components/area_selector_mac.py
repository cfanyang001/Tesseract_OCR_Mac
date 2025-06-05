import os
import subprocess
import tempfile
from PyQt5.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QLabel
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
            # 注意：系统截图工具不提供位置信息，只有大小信息
            width = pixmap.width()
            height = pixmap.height()
            
            # 简化处理，使用固定坐标
            x = 0
            y = 0
            
            # 创建区域
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
            
            logger.debug(f"截取区域: x={x}, y={y}, w={width}, h={height}")
            
            # 使用精确的区域坐标
            region_spec = f"{x},{y},{width},{height}"
            logger.debug(f"使用区域参数: {region_spec}")
            
            # 执行截图命令
            result = subprocess.run([
                'screencapture',
                '-R', region_spec,
                '-x',  # 不发出声音
                temp_filename
            ], check=True, capture_output=True)
            
            # 输出命令执行结果
            if result.stderr:
                logger.debug(f"截图命令输出: {result.stderr.decode('utf-8', errors='ignore')}")
            
            # 检查文件是否有效
            if not os.path.exists(temp_filename):
                logger.error("截图文件未创建")
                return None, None
                
            if os.path.getsize(temp_filename) == 0:
                logger.error("截图文件为空")
                try:
                    os.remove(temp_filename)
                except:
                    pass
                return None, None
            
            # 加载截图
            pixmap = QPixmap(temp_filename)
            if pixmap.isNull():
                logger.error("截图加载失败")
                try:
                    os.remove(temp_filename)
                except:
                    pass
                return None, None
            
            logger.debug(f"截图成功: {pixmap.width()}x{pixmap.height()}")
            
            return pixmap, temp_filename
            
        except Exception as e:
            logger.error(f"区域截图失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None 