import time
import threading
from typing import Dict, Any, Optional, Tuple, List, Callable, Union
from PyQt5.QtCore import QRect, QObject, pyqtSignal

from core.ocr_processor import OCRProcessor
from core.screen_capture import ScreenCapture
from core.utils.image_processing import preprocess_for_ocr
from core.utils.text_processing import clean_text, normalize_text
from loguru import logger


class TextRecognizer(QObject):
    """文本识别模块，结合屏幕捕获和OCR处理"""
    
    # 信号
    text_recognized = pyqtSignal(str, dict)  # 文本识别信号 (文本, 详细信息)
    error_occurred = pyqtSignal(str)         # 错误信号
    
    def __init__(self, ocr_processor=None, screen_capture=None):
        """初始化文本识别器
        
        Args:
            ocr_processor: OCR处理器实例，如果为None则创建新实例
            screen_capture: 屏幕捕获器实例，如果为None则创建新实例
        """
        super().__init__()
        
        # 创建OCR处理器和屏幕捕获器
        try:
            self.ocr_processor = ocr_processor if ocr_processor else OCRProcessor()
            self.screen_capture = screen_capture if screen_capture else ScreenCapture()
            logger.info("文本识别器初始化成功")
        except Exception as e:
            logger.error(f"文本识别器初始化失败: {e}")
            raise
        
        # 默认配置
        self.config = {
            'refresh_rate': 1000,       # 刷新频率 (毫秒)
            'preprocessing_steps': [    # 预处理步骤
                'resize', 'denoise', 'binarize', 'remove_noise'
            ],
            'normalize_text': True,     # 是否规范化文本
            'case_sensitive': False,    # 是否区分大小写
            'continuous_mode': False,   # 是否连续识别
            'result_cache_size': 10,    # 结果缓存大小
            'use_cache': True,          # 是否使用缓存
            'cache_ttl': 1.0,           # 缓存有效期(秒)
            'min_confidence': 50,       # 最低置信度
            'adaptive_refresh': True,   # 自适应刷新率
            'min_refresh_rate': 200,    # 最小刷新率(毫秒)
            'max_refresh_rate': 2000    # 最大刷新率(毫秒)
        }
        
        # 状态
        self._running = False           # 是否正在运行
        self._thread = None             # 识别线程
        self._stop_event = threading.Event()  # 停止事件
        self._result_cache = []         # 结果缓存
        self._last_text = ""            # 上次识别的文本
        self._last_capture_time = 0     # 上次捕获时间
        
        # 缓存
        self._text_cache = {}           # 文本缓存 {区域哈希: (文本, 详情, 时间戳)}
        self._lock = threading.RLock()  # 线程锁
        
        # 性能监控
        self._performance_metrics = {
            'avg_recognition_time': 0,  # 平均识别时间
            'recognition_count': 0,     # 识别次数
            'cache_hit_count': 0,       # 缓存命中次数
            'error_count': 0,           # 错误次数
            'current_refresh_rate': self.config['refresh_rate']  # 当前刷新率
        }
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """设置配置"""
        self.config.update(config)
        
        # 更新OCR处理器配置
        if 'ocr' in config:
            self.ocr_processor.set_config(config['ocr'])
        
        # 更新屏幕捕获器配置
        if 'capture' in config:
            self.screen_capture.set_config(config['capture'])
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.config.copy()
    
    def _get_area_hash(self, rect: QRect) -> str:
        """获取区域哈希，用于缓存键"""
        return f"{rect.x()}_{rect.y()}_{rect.width()}_{rect.height()}"
    
    def _get_from_cache(self, rect: QRect) -> Optional[Tuple[str, Dict[str, Any]]]:
        """从缓存获取文本识别结果"""
        if not self.config['use_cache']:
            return None
            
        area_hash = self._get_area_hash(rect)
        
        with self._lock:
            if area_hash in self._text_cache:
                text, details, timestamp = self._text_cache[area_hash]
                if time.time() - timestamp <= self.config['cache_ttl']:
                    self._performance_metrics['cache_hit_count'] += 1
                    logger.debug(f"使用缓存的文本识别结果: {area_hash}")
                    return text, details
        return None
    
    def _add_to_cache(self, rect: QRect, text: str, details: Dict[str, Any]) -> None:
        """添加文本识别结果到缓存"""
        if not self.config['use_cache']:
            return
            
        area_hash = self._get_area_hash(rect)
        
        with self._lock:
            self._text_cache[area_hash] = (text, details, time.time())
            
            # 清理过期缓存
            self._clean_cache()
    
    def _clean_cache(self) -> None:
        """清理过期缓存"""
        now = time.time()
        with self._lock:
            expired_keys = [
                k for k, (_, _, t) in self._text_cache.items()
                if now - t > self.config['cache_ttl']
            ]
            
            for key in expired_keys:
                if key in self._text_cache:
                    del self._text_cache[key]
    
    def recognize_area(self, rect: QRect) -> Tuple[str, Dict[str, Any]]:
        """识别指定区域的文本
        
        Args:
            rect: 区域矩形
            
        Returns:
            Tuple[str, Dict[str, Any]]: 识别的文本和详细信息
        """
        try:
            start_time = time.time()
            
            # 获取精确的区域坐标 - 使用原始传入的坐标
            x, y, width, height = rect.x(), rect.y(), rect.width(), rect.height()
            logger.info(f"文本识别: 使用精确区域坐标 x={x}, y={y}, width={width}, height={height}")
            
            # 直接使用系统命令进行截图，避免使用屏幕捕获器的中间处理
            try:
                import tempfile
                import subprocess
                import cv2
                import os
                
                # 创建临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                    temp_filename = temp_file.name
                
                logger.debug(f"文本识别: 使用系统命令直接截图，保存到 {temp_filename}")
                
                # 使用screencapture命令捕获精确区域
                result = subprocess.run([
                    'screencapture',
                    '-x',  # 无声
                    '-R', f"{x},{y},{width},{height}",  # 区域格式：x,y,width,height
                    temp_filename
                ], check=True)
                
                # 检查文件是否存在和有效
                if not os.path.exists(temp_filename) or os.path.getsize(temp_filename) == 0:
                    raise Exception("系统截图命令未能创建有效的图像文件")
                    
                # 读取图像
                image = cv2.imread(temp_filename)
                
                # 转换为RGB格式
                if image is not None:
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    logger.debug(f"文本识别: 系统命令截图成功，图像大小: {image.shape}")
                else:
                    raise Exception("无法读取截图文件")
                
                # 检查图像尺寸是否与请求区域一致
                if image.shape[1] != width or image.shape[0] != height:
                    logger.warning(f"文本识别: 图像尺寸({image.shape[1]}x{image.shape[0]})与请求区域尺寸({width}x{height})不匹配，调整大小")
                    image = cv2.resize(image, (width, height))
                
                # 删除临时文件
                try:
                    os.remove(temp_filename)
                except Exception as e:
                    logger.warning(f"删除临时文件失败: {e}")
                
            except Exception as e:
                logger.warning(f"使用系统命令截图失败: {e}，尝试使用屏幕捕获器")
                # 如果系统命令失败，回退到屏幕捕获器
                # 配置屏幕捕获器，禁用缓存和HiDPI补偿
                original_config = self.screen_capture.get_config()
                capture_config = original_config.copy()
                capture_config['use_cache'] = False
                capture_config['throttle'] = False
                capture_config['compensate_dpi'] = False
                self.screen_capture.set_config(capture_config)
                
                # 捕获指定区域
                image = self.screen_capture.capture_area(rect)
                
                # 恢复原始配置
                self.screen_capture.set_config(original_config)
            
            # 预处理图像
            processed_image = preprocess_for_ocr(image, self.config['preprocessing_steps'])
            
            # OCR识别
            text, details = self.ocr_processor.recognize_text(processed_image)
            
            # 检查置信度
            if details['confidence'] < self.config['min_confidence']:
                logger.debug(f"识别置信度过低: {details['confidence']}%，低于阈值 {self.config['min_confidence']}%")
                # 如果置信度过低，可以尝试使用不同的预处理方法
                if 'binarize' not in self.config['preprocessing_steps']:
                    # 尝试添加二值化处理
                    enhanced_steps = self.config['preprocessing_steps'] + ['binarize']
                    processed_image = preprocess_for_ocr(image, enhanced_steps)
                    text, details = self.ocr_processor.recognize_text(processed_image)
            
            # 规范化文本
            if self.config['normalize_text']:
                text = normalize_text(text, not self.config['case_sensitive'])
            
            # 更新缓存
            self._update_cache(text, details)
            
            # 不使用缓存，避免区域偏移问题
            # 更新状态
            self._last_text = text
            self._last_capture_time = time.time()
            
            # 更新性能指标
            recognition_time = time.time() - start_time
            self._update_performance_metrics(recognition_time)
            
            # 添加区域信息到结果中
            details['rect'] = {
                'x': x,
                'y': y,
                'width': width,
                'height': height
            }
            
            logger.debug(f"文本识别成功: {len(text)} 字符，区域: ({x},{y},{width},{height})，耗时: {recognition_time:.3f}秒")
            return text, details
        
        except Exception as e:
            logger.error(f"文本识别失败: {e}")
            self._performance_metrics['error_count'] += 1
            self.error_occurred.emit(str(e))
            return "", {}
    
    def _update_performance_metrics(self, recognition_time: float) -> None:
        """更新性能指标"""
        with self._lock:
            # 更新平均识别时间
            count = self._performance_metrics['recognition_count']
            avg_time = self._performance_metrics['avg_recognition_time']
            
            if count == 0:
                self._performance_metrics['avg_recognition_time'] = recognition_time
            else:
                # 使用加权平均，更重视最近的识别时间
                self._performance_metrics['avg_recognition_time'] = (
                    avg_time * 0.7 + recognition_time * 0.3
                )
            
            self._performance_metrics['recognition_count'] += 1
            
            # 自适应刷新率
            if self.config['adaptive_refresh']:
                self._adjust_refresh_rate()
    
    def _adjust_refresh_rate(self) -> None:
        """自适应调整刷新率"""
        avg_time = self._performance_metrics['avg_recognition_time']
        
        # 根据平均识别时间调整刷新率
        # 识别时间越长，刷新率越低，以减少资源使用
        if avg_time > 0.5:  # 如果识别时间超过0.5秒
            new_rate = min(
                self.config['max_refresh_rate'],
                int(self._performance_metrics['current_refresh_rate'] * 1.2)
            )
        elif avg_time < 0.1:  # 如果识别时间小于0.1秒
            new_rate = max(
                self.config['min_refresh_rate'],
                int(self._performance_metrics['current_refresh_rate'] * 0.8)
            )
        else:
            return  # 保持当前刷新率
        
        # 更新刷新率
        self._performance_metrics['current_refresh_rate'] = new_rate
        logger.debug(f"自适应调整刷新率: {new_rate}毫秒")
    
    def start_continuous_recognition(self, rect: QRect) -> None:
        """开始连续识别
        
        Args:
            rect: 区域矩形
        """
        if self._running:
            logger.warning("连续识别已经在运行")
            return
        
        # 设置连续模式
        self.config['continuous_mode'] = True
        
        # 重置停止事件
        self._stop_event.clear()
        
        # 设置运行状态
        self._running = True
        
        # 创建并启动识别线程
        self._thread = threading.Thread(
            target=self._continuous_recognition_thread,
            args=(rect,),
            daemon=True
        )
        self._thread.start()
        
        logger.info("连续识别已启动")
    
    def stop_continuous_recognition(self) -> None:
        """停止连续识别"""
        if not self._running:
            logger.warning("连续识别未在运行")
            return
        
        # 设置停止事件
        self._stop_event.set()
        
        # 等待线程结束
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        
        # 设置运行状态
        self._running = False
        
        logger.info("连续识别已停止")
    
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running
    
    def get_last_text(self) -> str:
        """获取上次识别的文本"""
        return self._last_text
    
    def get_result_cache(self) -> List[Dict[str, Any]]:
        """获取结果缓存"""
        return self._result_cache.copy()
    
    def clear_cache(self) -> None:
        """清空缓存"""
        with self._lock:
            self._result_cache = []
            self._last_text = ""
            self._text_cache = {}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self._performance_metrics.copy()
    
    def _continuous_recognition_thread(self, rect: QRect) -> None:
        """连续识别线程
        
        Args:
            rect: 区域矩形
        """
        error_count = 0
        max_errors = 5  # 允许的最大连续错误次数
        
        try:
            while not self._stop_event.is_set():
                try:
                    # 识别文本
                    text, details = self.recognize_area(rect)
                    
                    # 发送信号
                    if text:
                        self.text_recognized.emit(text, details)
                    
                    # 重置错误计数
                    error_count = 0
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"连续识别过程中发生错误 ({error_count}/{max_errors}): {e}")
                    
                    # 如果连续错误太多，发出警告但继续运行
                    if error_count >= max_errors:
                        error_msg = f"连续识别过程中发生多次错误: {e}"
                        logger.warning(error_msg)
                        self.error_occurred.emit(error_msg)
                        error_count = 0  # 重置错误计数，避免持续发送警告
                
                # 等待下一次识别
                # 使用自适应刷新率
                refresh_rate = self._performance_metrics['current_refresh_rate'] / 1000.0
                if not self._stop_event.wait(refresh_rate):
                    continue
                else:
                    break
        
        except Exception as e:
            logger.error(f"连续识别线程异常: {e}")
            self.error_occurred.emit(str(e))
            self._running = False
    
    def _update_cache(self, text: str, details: Dict[str, Any]) -> None:
        """更新结果缓存
        
        Args:
            text: 识别的文本
            details: 详细信息
        """
        # 创建缓存条目
        cache_entry = {
            'text': text,
            'details': details,
            'timestamp': time.time()
        }
        
        # 添加到缓存
        with self._lock:
            self._result_cache.insert(0, cache_entry)
            
            # 限制缓存大小
            if len(self._result_cache) > self.config['result_cache_size']:
                self._result_cache = self._result_cache[:self.config['result_cache_size']] 