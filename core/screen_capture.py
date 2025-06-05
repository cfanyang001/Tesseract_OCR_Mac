import os
import numpy as np
import cv2
import pyautogui
from PIL import Image
from typing import Dict, Any, Optional, Tuple, List
from PyQt5.QtCore import QRect
from loguru import logger


class ScreenCapture:
    """屏幕捕获模块，用于捕获屏幕指定区域的图像"""
    
    def __init__(self):
        """初始化屏幕捕获器"""
        # 获取屏幕尺寸
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"屏幕尺寸: {self.screen_width}x{self.screen_height}")
        
        # 默认配置
        self.config = {
            'scale_factor': 1.0,     # 缩放因子
            'format': 'RGB',         # 图像格式 (RGB, BGR, GRAY)
            'quality': 95,           # JPEG质量 (1-100)
        }
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """设置配置"""
        self.config.update(config)
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.config.copy()
    
    def capture_screen(self) -> np.ndarray:
        """捕获整个屏幕"""
        try:
            # 使用pyautogui捕获屏幕
            screenshot = pyautogui.screenshot()
            
            # 转换为numpy数组
            image = np.array(screenshot)
            
            # 根据配置进行格式转换
            image = self._convert_format(image)
            
            logger.debug(f"屏幕捕获成功: {image.shape}")
            return image
        
        except Exception as e:
            logger.error(f"屏幕捕获失败: {e}")
            # 返回空图像
            return np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
    
    def capture_area(self, rect: QRect) -> np.ndarray:
        """捕获指定区域
        
        Args:
            rect: 区域矩形
            
        Returns:
            np.ndarray: 区域图像
        """
        try:
            # 获取区域坐标
            x, y, width, height = rect.x(), rect.y(), rect.width(), rect.height()
            
            # 确保坐标在屏幕范围内
            x = max(0, min(x, self.screen_width - 1))
            y = max(0, min(y, self.screen_height - 1))
            width = max(1, min(width, self.screen_width - x))
            height = max(1, min(height, self.screen_height - y))
            
            logger.debug(f"捕获区域: x={x}, y={y}, width={width}, height={height}")
            
            # 使用pyautogui捕获区域
            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            
            # 打印图像信息
            logger.debug(f"截图尺寸: {screenshot.width}x{screenshot.height}")
            
            # 转换为numpy数组
            image = np.array(screenshot)
            logger.debug(f"numpy数组形状: {image.shape}")
            
            # 确保图像有效
            if image.size == 0 or not (height > 0 and width > 0):
                logger.error("捕获到的图像无效")
                return np.zeros((height, width, 3), dtype=np.uint8)
            
            # 根据配置进行格式转换
            image = self._convert_format(image)
            
            # 根据配置进行缩放
            if self.config['scale_factor'] != 1.0:
                image = self._scale_image(image, self.config['scale_factor'])
            
            logger.debug(f"最终图像尺寸: {image.shape}")
            return image
        
        except Exception as e:
            logger.error(f"区域捕获失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # 返回空图像
            return np.zeros((height, width, 3), dtype=np.uint8)
    
    def capture_window(self, window_title: str) -> Tuple[np.ndarray, QRect]:
        """捕获指定窗口
        
        Args:
            window_title: 窗口标题
            
        Returns:
            Tuple[np.ndarray, QRect]: 窗口图像和区域
        """
        try:
            # 在macOS上，我们需要使用其他方法获取窗口位置
            # 这里使用简化的方法，实际项目中可能需要更复杂的实现
            
            # 临时方案：捕获整个屏幕，然后让用户手动选择区域
            logger.warning("窗口捕获在macOS上不直接支持，请使用区域捕获")
            
            # 返回整个屏幕和全屏区域
            image = self.capture_screen()
            rect = QRect(0, 0, self.screen_width, self.screen_height)
            
            return image, rect
        
        except Exception as e:
            logger.error(f"窗口捕获失败: {e}")
            # 返回空图像和空区域
            return np.zeros((100, 100, 3), dtype=np.uint8), QRect(0, 0, 100, 100)
    
    def _convert_format(self, image: np.ndarray) -> np.ndarray:
        """转换图像格式"""
        if self.config['format'] == 'BGR':
            return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        elif self.config['format'] == 'GRAY':
            return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:  # RGB
            return image
    
    def _scale_image(self, image: np.ndarray, scale_factor: float) -> np.ndarray:
        """缩放图像"""
        if scale_factor == 1.0:
            return image
        
        height, width = image.shape[:2]
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    def save_image(self, image: np.ndarray, file_path: str) -> bool:
        """保存图像到文件
        
        Args:
            image: 图像数组
            file_path: 文件路径
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # 保存图像
            success = cv2.imwrite(
                file_path, 
                image if self.config['format'] == 'BGR' else cv2.cvtColor(image, cv2.COLOR_RGB2BGR),
                [cv2.IMWRITE_JPEG_QUALITY, self.config['quality']]
            )
            
            if success:
                logger.debug(f"图像保存成功: {file_path}")
            else:
                logger.error(f"图像保存失败: {file_path}")
            
            return success
        
        except Exception as e:
            logger.error(f"图像保存失败: {e}")
            return False
