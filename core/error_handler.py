import sys
import os
import traceback
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal
from loguru import logger

class ErrorHandler(QObject):
    """全局错误处理器，用于处理和管理应用程序异常"""
    
    # 信号
    error_occurred = pyqtSignal(str, str, str)  # 错误信号 (类型, 消息, 详情)
    error_handled = pyqtSignal(str, bool)       # 错误处理信号 (错误ID, 是否成功)
    
    # 错误级别
    LEVEL_INFO = 'info'
    LEVEL_WARNING = 'warning'
    LEVEL_ERROR = 'error'
    LEVEL_CRITICAL = 'critical'
    
    # Mac M4特定错误标识
    MAC_M4_ERROR_KEYS = [
        'apple', 'm1', 'm2', 'm3', 'm4', 'silicon', 'arm64', 
        'metal', 'rosetta', 'darwin'
    ]
    
    def __init__(self):
        """初始化错误处理器"""
        super().__init__()
        
        # 错误记录
        self.error_records = {}
        
        # 常见错误模式及解决方案
        self.error_patterns = {
            'ModuleNotFoundError': {
                'solution': "缺少依赖模块，请运行 'pip install -r requirements.txt' 安装所需依赖。",
                'restart_required': False
            },
            'PermissionError': {
                'solution': "权限不足，请检查应用程序权限设置。在macOS上，请确保已授予屏幕录制和辅助功能权限。",
                'restart_required': True
            },
            'RuntimeError: Tesseract OCR未安装或配置错误': {
                'solution': "未检测到Tesseract OCR，请使用 'brew install tesseract' 安装。",
                'restart_required': True
            },
            'TypeError': {
                'solution': "类型错误，可能是由于版本不兼容导致。请检查依赖版本是否符合要求。",
                'restart_required': False
            },
            'QtCore.QTimer': {
                'solution': "Qt定时器错误，可能是由于并发操作导致。尝试减少并发监控任务数量。",
                'restart_required': False
            },
            'Metal.framework': {
                'solution': "Metal图形库错误，这是macOS特定问题。请更新系统和图形驱动。",
                'restart_required': True,
                'is_mac_specific': True
            },
            'arm64': {
                'solution': "Apple Silicon架构特定错误，请确保使用兼容的原生库版本。",
                'restart_required': False,
                'is_mac_specific': True
            }
        }
        
        # 自动恢复处理器
        self.recovery_handlers = {}
        
        # 设置全局异常钩子
        self.original_excepthook = sys.excepthook
        sys.excepthook = self.global_exception_handler
    
    def global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """全局未捕获异常处理器"""
        # 获取异常信息
        error_msg = str(exc_value)
        error_type = exc_type.__name__
        error_traceback = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # 生成错误ID
        error_id = f"{error_type}_{int(time.time())}"
        
        # 记录错误
        self.record_error(error_id, error_type, error_msg, error_traceback)
        
        # 日志记录
        logger.error(f"未捕获的异常 [{error_id}]: {error_type}: {error_msg}")
        logger.debug(f"错误堆栈跟踪: {error_traceback}")
        
        # 发送错误信号
        try:
            self.error_occurred.emit(error_type, error_msg, error_traceback)
        except:
            pass
        
        # 尝试处理错误
        handled = self.handle_error(error_id, error_type, error_msg, error_traceback)
        
        # 如果无法处理，调用原始异常处理器
        if not handled:
            self.original_excepthook(exc_type, exc_value, exc_traceback)
    
    def record_error(self, error_id: str, error_type: str, message: str, traceback_text: str) -> None:
        """记录错误信息"""
        self.error_records[error_id] = {
            'type': error_type,
            'message': message,
            'traceback': traceback_text,
            'timestamp': time.time(),
            'handled': False,
            'solution_applied': None
        }
    
    def handle_error(self, error_id: str, error_type: str, message: str, 
                    traceback_text: str) -> bool:
        """处理错误，尝试应用解决方案
        
        Args:
            error_id: 错误ID
            error_type: 错误类型
            message: 错误消息
            traceback_text: 错误堆栈跟踪
            
        Returns:
            bool: 是否成功处理
        """
        # 检查是否有匹配的错误模式
        solution = self._find_solution(error_type, message, traceback_text)
        
        if solution:
            # 更新错误记录
            if error_id in self.error_records:
                self.error_records[error_id]['handled'] = True
                self.error_records[error_id]['solution_applied'] = solution
            
            # 应用自动恢复处理器(如果有)
            if error_type in self.recovery_handlers:
                try:
                    recovery_thread = threading.Thread(
                        target=self.recovery_handlers[error_type],
                        args=(error_id, message, solution)
                    )
                    recovery_thread.daemon = True
                    recovery_thread.start()
                    return True
                except Exception as e:
                    logger.error(f"恢复处理失败: {e}")
            
            # 显示错误对话框
            self._show_error_dialog(error_type, message, solution)
            return True
            
        return False
    
    def _find_solution(self, error_type: str, message: str, traceback_text: str) -> Optional[Dict[str, Any]]:
        """查找匹配的解决方案"""
        # 直接匹配错误类型
        if error_type in self.error_patterns:
            return self.error_patterns[error_type]
        
        # 匹配错误消息中的关键模式
        for pattern, solution in self.error_patterns.items():
            if pattern in message or pattern in traceback_text:
                return solution
        
        # 检查是否为Mac M4特定错误
        for key in self.MAC_M4_ERROR_KEYS:
            if (key.lower() in message.lower() or 
                key.lower() in traceback_text.lower()):
                
                # 查找是否有匹配此Mac特定错误的解决方案
                for pattern, solution in self.error_patterns.items():
                    if solution.get('is_mac_specific', False) and (
                        pattern in message or pattern in traceback_text
                    ):
                        return solution
                
                # 如果没有找到特定解决方案，返回通用Mac解决方案
                return {
                    'solution': "这可能是Mac M系列芯片兼容性问题。请确保使用原生ARM64版本的库和最新版本的Tesseract OCR。",
                    'restart_required': False,
                    'is_mac_specific': True
                }
                
        return None
    
    def _show_error_dialog(self, error_type: str, message: str, solution: Dict[str, Any]) -> None:
        """显示错误对话框"""
        try:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle(f"应用程序错误 - {error_type}")
            msg_box.setText(f"发生错误: {message}")
            msg_box.setInformativeText(f"建议解决方案:\n{solution['solution']}")
            
            if solution.get('restart_required', False):
                msg_box.setInformativeText(
                    f"{msg_box.informativeText()}\n\n应用程序需要重启才能解决此问题。"
                )
            
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()
        except:
            # 如果无法显示图形界面对话框，则打印到控制台
            print(f"\n错误: {error_type}: {message}")
            print(f"建议解决方案: {solution['solution']}")
            if solution.get('restart_required', False):
                print("应用程序需要重启才能解决此问题。")
    
    def register_recovery_handler(self, error_type: str, handler: Callable) -> None:
        """注册错误恢复处理器
        
        Args:
            error_type: 错误类型
            handler: 处理函数，接受(error_id, message, solution)参数
        """
        self.recovery_handlers[error_type] = handler
    
    def add_error_pattern(self, pattern: str, solution: str, 
                         restart_required: bool = False, 
                         is_mac_specific: bool = False) -> None:
        """添加自定义错误模式和解决方案
        
        Args:
            pattern: 错误模式关键词
            solution: 解决方案描述
            restart_required: 是否需要重启应用程序
            is_mac_specific: 是否为Mac特定问题
        """
        self.error_patterns[pattern] = {
            'solution': solution,
            'restart_required': restart_required,
            'is_mac_specific': is_mac_specific
        }
    
    def get_error_history(self) -> List[Dict[str, Any]]:
        """获取错误历史记录"""
        return [
            {
                'id': error_id,
                'type': record['type'],
                'message': record['message'],
                'timestamp': record['timestamp'],
                'handled': record['handled']
            }
            for error_id, record in self.error_records.items()
        ]
    
    def clear_error_history(self) -> None:
        """清除错误历史记录"""
        self.error_records = {}
    
    def restore_original_excepthook(self) -> None:
        """恢复原始异常处理钩子"""
        sys.excepthook = self.original_excepthook


# 全局单例
_instance = None

def get_error_handler() -> ErrorHandler:
    """获取错误处理器单例"""
    global _instance
    if _instance is None:
        _instance = ErrorHandler()
    return _instance 