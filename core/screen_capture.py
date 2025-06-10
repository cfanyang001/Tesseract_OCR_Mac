import os
import numpy as np
import cv2
import pyautogui
import time
import threading
from PIL import Image
from typing import Dict, Any, Optional, Tuple, List, Union
from PyQt5.QtCore import QRect
from loguru import logger


class ScreenCapture:
    """屏幕捕获模块，用于捕获屏幕指定区域的图像"""
    
    def __init__(self):
        """初始化屏幕捕获器"""
        # 获取屏幕尺寸
        self.screen_width, self.screen_height = pyautogui.size()
        logger.info(f"屏幕尺寸: {self.screen_width}x{self.screen_height}")
        
        # 检测系统缩放因子
        try:
            # 在macOS上，可以通过比较截图尺寸与报告的屏幕尺寸来估计缩放因子
            import subprocess
            # 获取屏幕信息
            result = subprocess.run(['system_profiler', 'SPDisplaysDataType'], capture_output=True, text=True)
            display_info = result.stdout
            
            # 检查是否有Retina关键字
            is_retina = 'Retina' in display_info
            
            # 设置默认缩放因子
            self.dpi_scale = 2.0 if is_retina else 1.0
            logger.info(f"检测到屏幕类型: {'Retina (HiDPI)' if is_retina else '标准分辨率'}, 设置DPI缩放因子: {self.dpi_scale}")
        except Exception as e:
            logger.warning(f"无法检测屏幕缩放因子: {e}，使用默认值1.0")
            self.dpi_scale = 1.0
        
        # 默认配置
        self.config = {
            'scale_factor': 1.0,     # 缩放因子
            'format': 'RGB',         # 图像格式 (RGB, BGR, GRAY)
            'quality': 95,           # JPEG质量 (1-100)
            'use_cache': True,       # 是否使用缓存
            'cache_ttl': 0.2,        # 缓存有效期(秒)
            'throttle': True,        # 是否启用节流
            'throttle_interval': 0.1, # 节流间隔(秒)
            'compensate_dpi': True,  # 是否补偿HiDPI显示（启用，处理坐标问题）
        }
        
        # 缓存
        self._cache = {}
        self._cache_timestamps = {}
        self._last_capture_time = {}
        
        # 线程锁，防止并发截图
        self._lock = threading.RLock()
        
        logger.info(f"屏幕捕获器初始化完成，DPI缩放: {self.dpi_scale}，默认配置: {self.config}")
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """设置配置"""
        self.config.update(config)
        
        # 如果禁用缓存，清空缓存
        if not self.config['use_cache']:
            with self._lock:
                self._cache = {}
                self._cache_timestamps = {}
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.config.copy()
    
    def _can_capture(self, key: str) -> bool:
        """检查是否可以进行新的截图（节流控制）"""
        if not self.config['throttle']:
            return True
            
        now = time.time()
        last_time = self._last_capture_time.get(key, 0)
        
        if now - last_time >= self.config['throttle_interval']:
            self._last_capture_time[key] = now
            return True
        return False
    
    def _get_from_cache(self, key: str) -> Optional[np.ndarray]:
        """从缓存获取图像"""
        if not self.config['use_cache']:
            return None
            
        with self._lock:
            # 检查缓存是否存在且未过期
            if key in self._cache and key in self._cache_timestamps:
                timestamp = self._cache_timestamps[key]
                if time.time() - timestamp <= self.config['cache_ttl']:
                    logger.debug(f"使用缓存的屏幕截图: {key}")
                    return self._cache[key].copy()  # 返回副本以避免修改缓存
        return None
    
    def _add_to_cache(self, key: str, image: np.ndarray) -> None:
        """添加图像到缓存"""
        if not self.config['use_cache']:
            return
            
        with self._lock:
            self._cache[key] = image.copy()  # 存储副本以避免外部修改
            self._cache_timestamps[key] = time.time()
    
    def capture_screen(self) -> np.ndarray:
        """捕获整个屏幕"""
        cache_key = "full_screen"
        
        try:
            # 检查缓存
            cached_image = self._get_from_cache(cache_key)
            if cached_image is not None:
                return cached_image
            
            # 节流控制
            if not self._can_capture(cache_key):
                # 如果不能截图但有缓存，返回最后的缓存（即使已过期）
                if cache_key in self._cache:
                    logger.debug("节流控制：使用上次的屏幕截图")
                    return self._cache[cache_key].copy()
                # 如果没有缓存，创建空图像
                return np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)
            
            # 使用线程锁确保一次只有一个截图操作
            with self._lock:
                # 使用pyautogui捕获屏幕
                screenshot = pyautogui.screenshot()
                
                # 转换为numpy数组
                image = np.array(screenshot)
                
                # 根据配置进行格式转换
                image = self._convert_format(image)
                
                # 添加到缓存
                self._add_to_cache(cache_key, image)
                
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
        # 获取区域坐标
        x, y, width, height = rect.x(), rect.y(), rect.width(), rect.height()
        
        # 记录原始坐标和尺寸
        logger.info(f"捕获区域原始坐标: x={x}, y={y}, width={width}, height={height}")
        
        # 保存原始尺寸，用于最终验证
        original_width = width
        original_height = height
        
        # 针对HiDPI显示进行坐标调整
        if self.config.get('compensate_dpi', True) and self.dpi_scale != 1.0:
            logger.info(f"应用HiDPI坐标调整，缩放因子: {self.dpi_scale}")
            # 在某些系统下，可能需要调整坐标以考虑DPI缩放
            x = int(x * self.dpi_scale)
            y = int(y * self.dpi_scale)
            width = int(width * self.dpi_scale)
            height = int(height * self.dpi_scale)
            logger.info(f"HiDPI调整后坐标: x={x}, y={y}, width={width}, height={height}")
        
        # 确保坐标在屏幕范围内
        x = max(0, min(x, self.screen_width - 1))
        y = max(0, min(y, self.screen_height - 1))
        width = max(1, min(width, self.screen_width - x))
        height = max(1, min(height, self.screen_height - y))
        
        # 记录调整后坐标
        logger.info(f"捕获区域最终坐标: x={x}, y={y}, width={width}, height={height}")
        
        # 创建缓存键 - 使用原始坐标创建缓存键，确保一致性
        cache_key = f"area_{rect.x()}_{rect.y()}_{rect.width()}_{rect.height()}"
        
        try:
            # 如果禁用了缓存，直接跳过缓存检查
            if not self.config['use_cache']:
                logger.debug("缓存已禁用，直接捕获屏幕区域")
            else:
                # 检查缓存
                cached_image = self._get_from_cache(cache_key)
                if cached_image is not None:
                    logger.debug(f"使用缓存的区域图像: {cache_key}")
                    # 确保缓存图像尺寸与请求的区域尺寸一致
                    if cached_image.shape[1] != original_width or cached_image.shape[0] != original_height:
                        logger.warning(f"缓存图像尺寸({cached_image.shape[1]}x{cached_image.shape[0]})与请求区域尺寸({original_width}x{original_height})不匹配，调整大小")
                        cached_image = cv2.resize(cached_image, (original_width, original_height))
                    return cached_image
            
            # 使用线程锁确保一次只有一个截图操作
            with self._lock:
                final_image = None
                
                # 优先使用系统命令 screencapture 进行截图
                try:
                    logger.debug(f"使用macOS系统命令捕获区域 x={x}, y={y}, width={width}, height={height}")
                    import tempfile
                    import subprocess
                    
                    # 创建临时文件
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                        temp_filename = temp_file.name
                    
                    # 使用screencapture命令捕获指定区域 - 使用最终调整后的坐标
                    capture_result = subprocess.run([
                        'screencapture',
                        '-x',  # 无声
                        '-R', f"{x},{y},{width},{height}",  # 区域格式：x,y,width,height
                        temp_filename
                    ], check=True, capture_output=True)
                    
                    # 检查命令是否成功执行
                    if capture_result.returncode != 0:
                        logger.warning(f"系统截图命令失败，返回代码: {capture_result.returncode}")
                        if capture_result.stderr:
                            logger.warning(f"错误输出: {capture_result.stderr.decode('utf-8', errors='ignore')}")
                        raise Exception("系统命令执行失败")
                    
                    # 检查文件是否存在和有效
                    if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0:
                        # 读取图像
                        image = cv2.imread(temp_filename)
                        
                        # 检查图像是否有效
                        if image is not None and image.size > 0:
                            logger.debug(f"系统命令截图成功，原始图像大小: {image.shape}")
                            
                            # 转换颜色空间
                            if self.config['format'] == 'RGB':
                                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                            elif self.config['format'] == 'GRAY':
                                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                                # 确保灰度图像是3通道的，便于后续处理
                                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
                            
                            # 确保图像尺寸与请求的原始区域尺寸一致
                            if image.shape[1] != original_width or image.shape[0] != original_height:
                                logger.warning(f"系统命令捕获的图像尺寸({image.shape[1]}x{image.shape[0]})与请求区域尺寸({original_width}x{original_height})不匹配，调整大小")
                                image = cv2.resize(image, (original_width, original_height))
                            
                            final_image = image
                        else:
                            logger.warning(f"无法读取系统命令创建的图像文件")
                    else:
                        logger.warning(f"系统命令未创建有效的截图文件: {temp_filename}")
                    
                    # 删除临时文件
                    try:
                        if os.path.exists(temp_filename):
                            os.remove(temp_filename)
                    except Exception as file_error:
                        logger.warning(f"删除临时文件失败: {file_error}")
                
                except Exception as e:
                    logger.warning(f"使用系统命令截图失败: {e}，尝试备用方法")
                
                # 如果系统命令失败，使用pyautogui作为备用方法
                if final_image is None:
                    try:
                        logger.debug(f"使用pyautogui捕获区域: ({x}, {y}, {width}, {height})")
                        screenshot = pyautogui.screenshot(region=(x, y, width, height))
                        
                        # 转换为numpy数组
                        image = np.array(screenshot)
                        
                        if image.size > 0:
                            logger.debug(f"pyautogui截图成功，图像大小: {image.shape}")
                            
                            # 根据配置进行格式转换
                            image = self._convert_format(image)
                            
                            # 确保图像尺寸正确
                            if image.shape[1] != original_width or image.shape[0] != original_height:
                                logger.warning(f"pyautogui捕获的图像尺寸({image.shape[1]}x{image.shape[0]})与请求区域尺寸({original_width}x{original_height})不匹配，调整大小")
                                image = cv2.resize(image, (original_width, original_height))
                            
                            final_image = image
                        else:
                            logger.warning("pyautogui返回空图像")
                    except Exception as py_error:
                        logger.error(f"pyautogui截图失败: {py_error}")
                
                # 如果所有方法都失败，返回空图像
                if final_image is None:
                    logger.error("所有屏幕捕获方法都失败，返回空图像")
                    return np.zeros((original_height, original_width, 3), dtype=np.uint8)
                
                # 根据配置进行缩放（通常不需要，因为我们已经确保尺寸正确）
                if self.config['scale_factor'] != 1.0:
                    final_image = self._scale_image(final_image, self.config['scale_factor'])
                
                # 添加到缓存 - 使用原始坐标创建的缓存键
                self._add_to_cache(cache_key, final_image)
                
                logger.debug(f"区域捕获成功，最终图像尺寸: {final_image.shape}")
                return final_image
        
        except Exception as e:
            logger.error(f"区域捕获失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 返回空图像，但确保尺寸正确
            return np.zeros((original_height, original_width, 3), dtype=np.uint8)
    
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
    
    def clear_cache(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache = {}
            self._cache_timestamps = {}
            logger.debug("屏幕捕获缓存已清空")
    
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