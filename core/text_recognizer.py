import time
import threading
from typing import Dict, Any, Optional, Tuple, List, Callable
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
    
    def __init__(self):
        """初始化文本识别器"""
        super().__init__()
        
        # 创建OCR处理器和屏幕捕获器
        try:
            self.ocr_processor = OCRProcessor()
            self.screen_capture = ScreenCapture()
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
            'result_cache_size': 10     # 结果缓存大小
        }
        
        # 状态
        self._running = False           # 是否正在运行
        self._thread = None             # 识别线程
        self._stop_event = threading.Event()  # 停止事件
        self._result_cache = []         # 结果缓存
        self._last_text = ""            # 上次识别的文本
        self._last_capture_time = 0     # 上次捕获时间
    
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
    
    def recognize_area(self, rect: QRect) -> Tuple[str, Dict[str, Any]]:
        """识别指定区域的文本
        
        Args:
            rect: 区域矩形
            
        Returns:
            Tuple[str, Dict[str, Any]]: 识别的文本和详细信息
        """
        try:
            # 捕获屏幕区域
            image = self.screen_capture.capture_area(rect)
            
            # 预处理图像
            processed_image = preprocess_for_ocr(image, self.config['preprocessing_steps'])
            
            # OCR识别
            text, details = self.ocr_processor.recognize_text(processed_image)
            
            # 规范化文本
            if self.config['normalize_text']:
                text = normalize_text(text, not self.config['case_sensitive'])
            
            # 更新缓存
            self._update_cache(text, details)
            
            # 更新状态
            self._last_text = text
            self._last_capture_time = time.time()
            
            logger.debug(f"文本识别成功: {len(text)} 字符")
            return text, details
        
        except Exception as e:
            logger.error(f"文本识别失败: {e}")
            self.error_occurred.emit(str(e))
            return "", {}
    
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
        self._result_cache = []
        self._last_text = ""
    
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
                        error_count = 0  # 重置错误计数，给系统恢复的机会
                        
                        # 暂停稍长时间让系统恢复
                        time.sleep(2.0)
                    
                finally:
                    # 无论成功或失败，等待下一次识别
                    self._stop_event.wait(self.config['refresh_rate'] / 1000)
        
        except Exception as e:
            logger.error(f"连续识别线程异常: {e}")
            self.error_occurred.emit(str(e))
            # 不要立即设置_running为False，以便可以尝试恢复
            
            # 尝试恢复线程运行
            time.sleep(1.0)
            if not self._stop_event.is_set():
                logger.info("尝试恢复连续识别线程...")
                try:
                    # 递归调用，重新启动识别循环
                    self._continuous_recognition_thread(rect)
                except Exception as restart_error:
                    logger.error(f"恢复连续识别线程失败: {restart_error}")
                    self._running = False
    
    def _update_cache(self, text: str, details: Dict[str, Any]) -> None:
        """更新结果缓存
        
        Args:
            text: 识别的文本
            details: 详细信息
        """
        # 添加到缓存
        self._result_cache.append({
            'text': text,
            'details': details,
            'timestamp': time.time()
        })
        
        # 限制缓存大小
        if len(self._result_cache) > self.config['result_cache_size']:
            self._result_cache = self._result_cache[-self.config['result_cache_size']:] 