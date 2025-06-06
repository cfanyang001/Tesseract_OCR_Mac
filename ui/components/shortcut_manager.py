from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QKeySequence, QShortcut

import platform
from typing import Dict, Any, List, Callable, Optional, Tuple
from loguru import logger

class ShortcutAction:
    """快捷键动作"""
    
    def __init__(self, name: str, description: str, key_sequence: str, 
                callback: Callable, enabled: bool = True):
        """初始化快捷键动作
        
        Args:
            name: 动作名称（唯一标识）
            description: 动作描述
            key_sequence: 快捷键序列，如 "Ctrl+S"
            callback: 回调函数
            enabled: 是否启用
        """
        self.name = name
        self.description = description
        self.key_sequence = key_sequence
        self.callback = callback
        self.enabled = enabled
        self.shortcut = None  # 实际的QShortcut对象，由管理器设置


class ShortcutManager(QObject):
    """快捷键管理器，用于管理全局快捷键"""
    
    # 信号
    shortcut_triggered = pyqtSignal(str)  # 快捷键触发信号 (动作名称)
    
    # 预定义的平台特有快捷键
    PLATFORM_SHORTCUTS = {
        "darwin": {  # macOS
            "save": "Ctrl+S",
            "open": "Ctrl+O",
            "new": "Ctrl+N",
            "close": "Ctrl+W",
            "quit": "Ctrl+Q",
            "copy": "Ctrl+C",
            "paste": "Ctrl+V",
            "cut": "Ctrl+X",
            "select_all": "Ctrl+A",
            "find": "Ctrl+F",
            "help": "F1"
        },
        "win32": {  # Windows
            "save": "Ctrl+S",
            "open": "Ctrl+O",
            "new": "Ctrl+N",
            "close": "Alt+F4",
            "quit": "Ctrl+Q",
            "copy": "Ctrl+C",
            "paste": "Ctrl+V",
            "cut": "Ctrl+X",
            "select_all": "Ctrl+A",
            "find": "Ctrl+F",
            "help": "F1"
        },
        "linux": {  # Linux
            "save": "Ctrl+S",
            "open": "Ctrl+O",
            "new": "Ctrl+N",
            "close": "Ctrl+W",
            "quit": "Ctrl+Q",
            "copy": "Ctrl+C",
            "paste": "Ctrl+V",
            "cut": "Ctrl+X",
            "select_all": "Ctrl+A",
            "find": "Ctrl+F",
            "help": "F1"
        }
    }
    
    def __init__(self, parent=None):
        """初始化快捷键管理器
        
        Args:
            parent: 父对象，通常是主窗口
        """
        super().__init__(parent)
        
        self.shortcuts = {}  # {name: ShortcutAction}
        self.platform = platform.system().lower()
        
        # 对于macOS，特殊处理Command键
        if self.platform == "darwin":
            # 标准方式: Qt会自动将Ctrl映射到macOS的Command键
            pass
    
    def register_shortcut(self, name: str, description: str, key_sequence: str, 
                         callback: Callable, enabled: bool = True) -> bool:
        """注册快捷键
        
        Args:
            name: 动作名称（唯一标识）
            description: 动作描述
            key_sequence: 快捷键序列，如 "Ctrl+S"
            callback: 回调函数
            enabled: 是否启用
            
        Returns:
            bool: 是否注册成功
        """
        try:
            # 检查名称是否已存在
            if name in self.shortcuts:
                logger.warning(f"快捷键 '{name}' 已存在，将被覆盖")
            
            # 创建动作
            action = ShortcutAction(name, description, key_sequence, callback, enabled)
            
            # 保存动作
            self.shortcuts[name] = action
            
            # 如果有父窗口，创建QShortcut
            if self.parent():
                self._create_shortcut(action)
            
            logger.debug(f"注册快捷键: {name} - {key_sequence}")
            return True
            
        except Exception as e:
            logger.error(f"注册快捷键失败: {e}")
            return False
    
    def register_app_shortcuts(self, parent) -> None:
        """注册应用程序标准快捷键
        
        Args:
            parent: 父窗口
        """
        try:
            # 获取当前平台的快捷键
            platform_keys = self.PLATFORM_SHORTCUTS.get(
                self.platform, self.PLATFORM_SHORTCUTS["win32"]
            )
            
            # 根据Apple Silicon优化
            is_apple_silicon = False
            if self.platform == "darwin":
                try:
                    import platform as plt
                    is_apple_silicon = plt.machine() == 'arm64'
                except:
                    pass
                    
            # 注册标准快捷键
            self.register_shortcut(
                "start_monitor", 
                "开始监控", 
                "F5", 
                lambda: self.shortcut_triggered.emit("start_monitor")
            )
            
            self.register_shortcut(
                "stop_monitor", 
                "停止监控", 
                "Shift+F5", 
                lambda: self.shortcut_triggered.emit("stop_monitor")
            )
            
            self.register_shortcut(
                "capture_screen", 
                "捕获屏幕", 
                "F6", 
                lambda: self.shortcut_triggered.emit("capture_screen")
            )
            
            self.register_shortcut(
                "save_config", 
                "保存配置", 
                platform_keys["save"], 
                lambda: self.shortcut_triggered.emit("save_config")
            )
            
            self.register_shortcut(
                "open_config", 
                "打开配置", 
                platform_keys["open"], 
                lambda: self.shortcut_triggered.emit("open_config")
            )
            
            self.register_shortcut(
                "show_settings", 
                "显示设置", 
                "F9", 
                lambda: self.shortcut_triggered.emit("show_settings")
            )
            
            self.register_shortcut(
                "refresh_ocr", 
                "刷新OCR识别", 
                "F10", 
                lambda: self.shortcut_triggered.emit("refresh_ocr")
            )
            
            # 根据平台添加特殊快捷键
            if self.platform == "darwin":
                # macOS特有快捷键
                if is_apple_silicon:
                    # M系列芯片特有的优化快捷键
                    self.register_shortcut(
                        "optimize_performance", 
                        "优化性能", 
                        "Ctrl+Shift+P", 
                        lambda: self.shortcut_triggered.emit("optimize_performance")
                    )
                
                # 添加macOS特有的任务管理快捷键
                self.register_shortcut(
                    "task_manager", 
                    "任务管理", 
                    "Ctrl+Shift+T", 
                    lambda: self.shortcut_triggered.emit("task_manager")
                )
            elif self.platform == "win32":
                # Windows特有快捷键
                self.register_shortcut(
                    "task_manager", 
                    "任务管理", 
                    "Ctrl+Shift+T", 
                    lambda: self.shortcut_triggered.emit("task_manager")
                )
            
            logger.info(f"已注册标准应用程序快捷键 ({len(self.shortcuts)}个)")
            
        except Exception as e:
            logger.error(f"注册标准快捷键失败: {e}")
    
    def apply_shortcuts(self, parent) -> None:
        """应用所有快捷键到指定窗口
        
        Args:
            parent: 父窗口
        """
        try:
            # 保存父窗口引用
            self.setParent(parent)
            
            # 为所有动作创建QShortcut
            for action in self.shortcuts.values():
                self._create_shortcut(action)
                
            logger.debug(f"已应用快捷键到窗口 ({len(self.shortcuts)}个)")
            
        except Exception as e:
            logger.error(f"应用快捷键失败: {e}")
    
    def _create_shortcut(self, action: ShortcutAction) -> None:
        """为动作创建QShortcut
        
        Args:
            action: 快捷键动作
        """
        if not self.parent():
            return
            
        # 创建QShortcut
        shortcut = QShortcut(QKeySequence(action.key_sequence), self.parent())
        
        # 设置回调
        shortcut.activated.connect(action.callback)
        
        # 设置启用状态
        shortcut.setEnabled(action.enabled)
        
        # 保存QShortcut引用
        action.shortcut = shortcut
    
    def enable_shortcut(self, name: str, enabled: bool = True) -> bool:
        """启用或禁用快捷键
        
        Args:
            name: 动作名称
            enabled: 是否启用
            
        Returns:
            bool: 是否成功
        """
        try:
            if name not in self.shortcuts:
                logger.warning(f"快捷键 '{name}' 不存在")
                return False
                
            action = self.shortcuts[name]
            action.enabled = enabled
            
            if action.shortcut:
                action.shortcut.setEnabled(enabled)
                
            return True
            
        except Exception as e:
            logger.error(f"设置快捷键状态失败: {e}")
            return False
    
    def get_shortcut_info(self, name: str = None) -> Dict[str, Any]:
        """获取快捷键信息
        
        Args:
            name: 动作名称，为None时返回所有快捷键信息
            
        Returns:
            Dict[str, Any]: 快捷键信息
        """
        try:
            if name:
                if name not in self.shortcuts:
                    return {}
                    
                action = self.shortcuts[name]
                return {
                    "name": action.name,
                    "description": action.description,
                    "key_sequence": action.key_sequence,
                    "enabled": action.enabled
                }
            else:
                result = {}
                for name, action in self.shortcuts.items():
                    result[name] = {
                        "name": action.name,
                        "description": action.description,
                        "key_sequence": action.key_sequence,
                        "enabled": action.enabled
                    }
                return result
                
        except Exception as e:
            logger.error(f"获取快捷键信息失败: {e}")
            return {}
    
    def get_shortcut_help(self) -> List[Dict[str, str]]:
        """获取快捷键帮助信息，用于显示在帮助对话框中
        
        Returns:
            List[Dict[str, str]]: 快捷键帮助信息列表
        """
        try:
            result = []
            for name, action in self.shortcuts.items():
                if action.enabled:
                    result.append({
                        "name": action.name,
                        "description": action.description,
                        "key_sequence": action.key_sequence
                    })
            
            # 按快捷键名称排序
            result.sort(key=lambda x: x["description"])
            return result
            
        except Exception as e:
            logger.error(f"获取快捷键帮助信息失败: {e}")
            return []


# 全局单例
_instance = None

def get_shortcut_manager() -> ShortcutManager:
    """获取快捷键管理器单例"""
    global _instance
    if _instance is None:
        _instance = ShortcutManager()
    return _instance 