import sys
import os
import traceback
import time
import threading
import platform
from typing import Dict, Any, Optional, List, Callable
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal
from loguru import logger

class ErrorHandler(QObject):
    """全局错误处理器，处理应用程序中的异常，特别关注Mac M系列芯片特有的错误"""
    
    # 信号
    error_occurred = pyqtSignal(str, str, str)  # 错误类型, 错误消息, 错误堆栈
    error_recovered = pyqtSignal(str, str)  # 错误类型, 恢复消息
    
    # 错误模式
    MODE_SILENT = "silent"  # 静默模式，仅记录日志
    MODE_NOTIFY = "notify"  # 通知模式，记录日志并通过信号通知
    MODE_RECOVER = "recover"  # 恢复模式，尝试自动恢复
    MODE_CRITICAL = "critical"  # 严重模式，可能需要重启应用
    
    # Mac M4特定错误标识
    MAC_M4_ERROR_KEYS = [
        'apple', 'm1', 'm2', 'm3', 'm4', 'silicon', 'arm64', 
        'metal', 'rosetta', 'darwin'
    ]
    
    def __init__(self):
        """初始化错误处理器"""
        super().__init__()
        
        # 记录系统信息
        self.is_mac = platform.system() == "Darwin"
        self.is_apple_silicon = False
        self.mac_model = ""
        
        # 错误计数器
        self.error_counts = {}  # {error_type: count}
        
        # 最近的错误
        self.recent_errors = []  # [(timestamp, error_type, error_msg)]
        self.max_recent_errors = 20
        
        # 检查Mac M系列芯片
        if self.is_mac:
            self._check_mac_silicon()
        
        # 设置全局异常处理器
        sys.excepthook = self.global_exception_handler
        
        logger.info("全局错误处理器已初始化")
        if self.is_apple_silicon:
            logger.info(f"已启用Apple Silicon ({self.mac_model}) 错误处理优化")
    
    def _check_mac_silicon(self):
        """检查Mac是否使用Apple Silicon芯片"""
        try:
            # 检查处理器架构
            if platform.machine() == 'arm64':
                self.is_apple_silicon = True
                
                # 尝试获取更详细的芯片信息
                try:
                    from config.mac_compatibility import MacCompatibility
                    mac_compat = MacCompatibility()
                    chip_info = mac_compat.get_chip_info()
                    self.mac_model = chip_info.get('model', '')
                except:
                    # 如果无法导入兼容性模块，使用系统命令获取芯片信息
                    try:
                        import subprocess
                        result = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string']).decode('utf-8').strip()
                        if 'Apple' in result:
                            self.mac_model = result.split(' ')[-1]  # 提取型号部分
                    except:
                        pass
        except Exception as e:
            logger.warning(f"检查Apple Silicon状态失败: {e}")
    
    def global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """全局异常处理函数
        
        Args:
            exc_type: 异常类型
            exc_value: 异常值
            exc_traceback: 异常堆栈
        """
        # 生成堆栈跟踪字符串
        stack_trace = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # 记录异常
        logger.error(f"未捕获的异常: {exc_type.__name__}: {exc_value}")
        logger.error(stack_trace)
        
        # 增加错误计数
        error_type = exc_type.__name__
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # 添加到最近错误列表
        self.recent_errors.append((time.time(), error_type, str(exc_value)))
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
        
        # 尝试寻找解决方案
        solution = self._find_solution(error_type, str(exc_value), stack_trace)
        
        # 如果有解决方案，尝试执行
        if solution and "action" in solution and solution["action"]:
            try:
                solution["action"]()
                if "recovery_message" in solution:
                    logger.info(f"错误自动恢复: {solution['recovery_message']}")
                    self.error_recovered.emit(error_type, solution['recovery_message'])
            except Exception as e:
                logger.error(f"执行错误恢复操作失败: {e}")
        
        # 发送错误信号
        self.error_occurred.emit(error_type, str(exc_value), stack_trace)
    
    def handle_error(self, error_type: str, error_msg: str, mode: str = MODE_NOTIFY) -> Dict[str, Any]:
        """处理特定错误
        
        Args:
            error_type: 错误类型
            error_msg: 错误消息
            mode: 处理模式
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        # 记录错误
        logger.error(f"处理错误: {error_type}: {error_msg} (模式: {mode})")
        
        # 增加错误计数
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # 添加到最近错误列表
        self.recent_errors.append((time.time(), error_type, error_msg))
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
        
        # 获取解决方案
        solution = self._find_solution(error_type, error_msg, "")
        
        # 根据不同模式处理
        result = {
            "error_type": error_type,
            "error_msg": error_msg,
            "mode": mode,
            "solution": solution,
            "handled": False
        }
        
        if mode == self.MODE_SILENT:
            # 只记录，不执行任何操作
            result["handled"] = True
            
        elif mode == self.MODE_NOTIFY:
            # 通知但不自动恢复
            self.error_occurred.emit(error_type, error_msg, "")
            result["handled"] = True
            
        elif mode == self.MODE_RECOVER and solution and "action" in solution and solution["action"]:
            # 尝试自动恢复
            try:
                solution["action"]()
                if "recovery_message" in solution:
                    logger.info(f"错误自动恢复: {solution['recovery_message']}")
                    self.error_recovered.emit(error_type, solution['recovery_message'])
                result["handled"] = True
            except Exception as e:
                logger.error(f"执行错误恢复操作失败: {e}")
                result["recovery_error"] = str(e)
                
        elif mode == self.MODE_CRITICAL:
            # 严重错误，通知并可能需要重启
            self.error_occurred.emit(error_type, error_msg, "")
            if solution and solution.get("restart_required", False):
                result["restart_required"] = True
            result["handled"] = True
        
        return result
    
    def _find_solution(self, error_type: str, error_msg: str, stack_trace: str) -> Optional[Dict[str, Any]]:
        """寻找错误解决方案
        
        Args:
            error_type: 错误类型
            error_msg: 错误消息
            stack_trace: 错误堆栈
            
        Returns:
            Optional[Dict[str, Any]]: 解决方案，如果没有则返回None
        """
        # 预定义的解决方案
        solutions = []
        
        # Mac M系列芯片特定错误
        if self.is_apple_silicon:
            solutions.extend(self._get_apple_silicon_solutions())
        
        # 通用错误解决方案
        solutions.extend(self._get_common_solutions())
        
        # 查找匹配的解决方案
        for solution in solutions:
            # 检查错误类型匹配
            if "error_type" in solution and solution["error_type"] != error_type:
                continue
                
            # 检查错误消息模式匹配
            if "error_pattern" in solution:
                pattern = solution["error_pattern"]
                if pattern not in error_msg:
                    continue
            
            # 找到匹配的解决方案
            return solution
        
        # 没有找到匹配的解决方案
        return None
    
    def _get_apple_silicon_solutions(self) -> List[Dict[str, Any]]:
        """获取Apple Silicon特定的错误解决方案
        
        Returns:
            List[Dict[str, Any]]: 解决方案列表
        """
        return [
            {
                "error_type": "RuntimeError",
                "error_pattern": "Metal.framework",
                "solution": "Metal框架问题，可能与GPU加速相关。尝试禁用GPU加速或更新驱动。",
                "action": lambda: os.environ.update({"DISABLE_METAL": "1"}),
                "recovery_message": "已禁用Metal框架，将使用CPU模式",
                "restart_required": False,
                "is_mac_specific": True
            },
            {
                "error_type": "ImportError",
                "error_pattern": "arm64",
                "solution": "导入库失败，可能是非ARM64原生库。尝试使用pip重新安装该库的arm64版本。",
                "restart_required": True,
                "is_mac_specific": True
            },
            {
                "error_type": "ValueError",
                "error_pattern": "CoreML",
                "solution": "CoreML模型错误，可能是模型与当前芯片不兼容。尝试更新模型或切换到通用模型。",
                "restart_required": False,
                "is_mac_specific": True
            },
            {
                "error_type": "RuntimeError",
                "error_pattern": "libtesseract",
                "solution": "Tesseract库加载错误，可能需要重新安装ARM64版本的Tesseract。",
                "restart_required": True,
                "is_mac_specific": True
            }
        ]
    
    def _get_common_solutions(self) -> List[Dict[str, Any]]:
        """获取通用错误解决方案
        
        Returns:
            List[Dict[str, Any]]: 解决方案列表
        """
        return [
            {
                "error_type": "PermissionError",
                "solution": "权限错误，可能需要提升权限或检查文件权限设置。",
                "restart_required": False
            },
            {
                "error_type": "FileNotFoundError",
                "solution": "文件未找到，请检查文件路径是否正确。",
                "restart_required": False
            },
            {
                "error_type": "ImportError",
                "solution": "导入库失败，可能需要安装缺失的依赖。",
                "restart_required": True
            },
            {
                "error_type": "MemoryError",
                "solution": "内存不足，尝试关闭其他应用程序或增加系统虚拟内存。",
                "action": self._clear_memory_cache,
                "recovery_message": "已清理内存缓存",
                "restart_required": False
            }
        ]
    
    def _clear_memory_cache(self):
        """清理内存缓存"""
        import gc
        gc.collect()
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计信息
        
        Returns:
            Dict[str, Any]: 错误统计信息
        """
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_counts": self.error_counts.copy(),
            "recent_errors": self.recent_errors.copy()
        }


# 全局单例
_instance = None

def get_error_handler() -> ErrorHandler:
    """获取错误处理器单例"""
    global _instance
    if _instance is None:
        _instance = ErrorHandler()
    return _instance 