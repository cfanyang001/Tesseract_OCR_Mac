from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QSettings
from PyQt5.QtGui import QColor, QPalette

import os
import platform
import json
from typing import Dict, Any, List, Optional
from loguru import logger

class ThemeManager(QObject):
    """主题管理器，提供应用程序主题和样式设置"""
    
    # 主题变更信号
    theme_changed = pyqtSignal(str)  # 主题名称
    
    # 预定义主题
    THEME_LIGHT = "light"
    THEME_DARK = "dark"
    THEME_SYSTEM = "system"
    THEME_CUSTOM = "custom"
    
    def __init__(self):
        """初始化主题管理器"""
        super().__init__()
        
        # 当前主题
        self.current_theme = self.THEME_LIGHT
        
        # 主题定义
        self.themes = {
            self.THEME_LIGHT: self._get_light_theme(),
            self.THEME_DARK: self._get_dark_theme()
        }
        
        # 自定义主题
        self.custom_theme = {}
        
        # 系统信息
        self.is_mac = platform.system() == "Darwin"
        self.is_apple_silicon = False
        
        if self.is_mac:
            try:
                if platform.machine() == 'arm64':
                    self.is_apple_silicon = True
            except:
                pass
        
        # 加载保存的主题设置
        self._load_theme_settings()
    
    def _get_light_theme(self) -> Dict[str, Any]:
        """获取浅色主题定义
        
        Returns:
            Dict[str, Any]: 主题定义
        """
        return {
            "name": self.THEME_LIGHT,
            "display_name": "浅色主题",
            "colors": {
                "primary": "#4A86E8",
                "secondary": "#6C757D",
                "success": "#28A745",
                "warning": "#FFC107",
                "danger": "#DC3545",
                "info": "#17A2B8",
                "light": "#F8F9FA",
                "dark": "#343A40",
                "text": "#212529",
                "text_secondary": "#6C757D",
                "background": "#FFFFFF",
                "background_secondary": "#F8F9FA",
                "border": "#DEE2E6"
            },
            "style_sheet": """
                QMainWindow, QDialog {
                    background-color: #FFFFFF;
                }
                
                QWidget {
                    color: #212529;
                }
                
                QTabWidget::pane {
                    border: 1px solid #DEE2E6;
                    background-color: #FFFFFF;
                }
                
                QTabBar::tab {
                    background-color: #F8F9FA;
                    color: #212529;
                    border: 1px solid #DEE2E6;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                
                QTabBar::tab:selected {
                    background-color: #FFFFFF;
                    border-bottom-color: #FFFFFF;
                }
                
                QPushButton {
                    background-color: #4A86E8;
                    color: #FFFFFF;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                
                QPushButton:hover {
                    background-color: #3A76D8;
                }
                
                QPushButton:pressed {
                    background-color: #2A66C8;
                }
                
                QPushButton:disabled {
                    background-color: #CCCCCC;
                    color: #666666;
                }
                
                QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {
                    border: 1px solid #DEE2E6;
                    background-color: #FFFFFF;
                    color: #212529;
                    padding: 4px;
                    border-radius: 4px;
                }
                
                QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus {
                    border: 1px solid #4A86E8;
                }
                
                QLabel {
                    color: #212529;
                }
                
                QStatusBar {
                    background-color: #F8F9FA;
                    color: #212529;
                    border-top: 1px solid #DEE2E6;
                }
                
                QMenuBar {
                    background-color: #F8F9FA;
                    color: #212529;
                    border-bottom: 1px solid #DEE2E6;
                }
                
                QMenuBar::item {
                    background-color: transparent;
                    padding: 4px 8px;
                }
                
                QMenuBar::item:selected {
                    background-color: #E9ECEF;
                }
                
                QMenu {
                    background-color: #FFFFFF;
                    color: #212529;
                    border: 1px solid #DEE2E6;
                }
                
                QMenu::item {
                    padding: 4px 24px 4px 8px;
                }
                
                QMenu::item:selected {
                    background-color: #E9ECEF;
                }
                
                QToolBar {
                    background-color: #F8F9FA;
                    border: 1px solid #DEE2E6;
                    spacing: 3px;
                }
                
                QProgressBar {
                    border: 1px solid #DEE2E6;
                    background-color: #F8F9FA;
                    text-align: center;
                    color: #212529;
                    border-radius: 4px;
                }
                
                QProgressBar::chunk {
                    background-color: #4A86E8;
                    border-radius: 3px;
                }
            """
        }
    
    def _get_dark_theme(self) -> Dict[str, Any]:
        """获取深色主题定义
        
        Returns:
            Dict[str, Any]: 主题定义
        """
        return {
            "name": self.THEME_DARK,
            "display_name": "深色主题",
            "colors": {
                "primary": "#4A86E8",
                "secondary": "#6C757D",
                "success": "#28A745",
                "warning": "#FFC107",
                "danger": "#DC3545",
                "info": "#17A2B8",
                "light": "#F8F9FA",
                "dark": "#343A40",
                "text": "#F8F9FA",
                "text_secondary": "#ADB5BD",
                "background": "#212529",
                "background_secondary": "#343A40",
                "border": "#495057"
            },
            "style_sheet": """
                QMainWindow, QDialog {
                    background-color: #212529;
                }
                
                QWidget {
                    color: #F8F9FA;
                }
                
                QTabWidget::pane {
                    border: 1px solid #495057;
                    background-color: #212529;
                }
                
                QTabBar::tab {
                    background-color: #343A40;
                    color: #F8F9FA;
                    border: 1px solid #495057;
                    padding: 8px 16px;
                    margin-right: 2px;
                }
                
                QTabBar::tab:selected {
                    background-color: #212529;
                    border-bottom-color: #212529;
                }
                
                QPushButton {
                    background-color: #4A86E8;
                    color: #FFFFFF;
                    border: none;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                
                QPushButton:hover {
                    background-color: #3A76D8;
                }
                
                QPushButton:pressed {
                    background-color: #2A66C8;
                }
                
                QPushButton:disabled {
                    background-color: #495057;
                    color: #ADB5BD;
                }
                
                QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {
                    border: 1px solid #495057;
                    background-color: #343A40;
                    color: #F8F9FA;
                    padding: 4px;
                    border-radius: 4px;
                }
                
                QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus {
                    border: 1px solid #4A86E8;
                }
                
                QLabel {
                    color: #F8F9FA;
                }
                
                QStatusBar {
                    background-color: #343A40;
                    color: #F8F9FA;
                    border-top: 1px solid #495057;
                }
                
                QMenuBar {
                    background-color: #343A40;
                    color: #F8F9FA;
                    border-bottom: 1px solid #495057;
                }
                
                QMenuBar::item {
                    background-color: transparent;
                    padding: 4px 8px;
                }
                
                QMenuBar::item:selected {
                    background-color: #495057;
                }
                
                QMenu {
                    background-color: #343A40;
                    color: #F8F9FA;
                    border: 1px solid #495057;
                }
                
                QMenu::item {
                    padding: 4px 24px 4px 8px;
                }
                
                QMenu::item:selected {
                    background-color: #495057;
                }
                
                QToolBar {
                    background-color: #343A40;
                    border: 1px solid #495057;
                    spacing: 3px;
                }
                
                QProgressBar {
                    border: 1px solid #495057;
                    background-color: #343A40;
                    text-align: center;
                    color: #F8F9FA;
                    border-radius: 4px;
                }
                
                QProgressBar::chunk {
                    background-color: #4A86E8;
                    border-radius: 3px;
                }
            """
        }
    
    def _load_theme_settings(self):
        """从设置中加载主题"""
        try:
            settings = QSettings()
            
            # 读取主题名称
            theme_name = settings.value("theme/name", self.THEME_LIGHT)
            
            # 加载主题
            self.set_theme(theme_name)
            
            # 如果是自定义主题，读取自定义设置
            if theme_name == self.THEME_CUSTOM:
                custom_theme_str = settings.value("theme/custom", "{}")
                try:
                    custom_theme = json.loads(custom_theme_str)
                    self.custom_theme = custom_theme
                except:
                    logger.warning("无法解析自定义主题设置")
                    self.custom_theme = {}
                
        except Exception as e:
            logger.error(f"加载主题设置失败: {e}")
            # 使用默认浅色主题
            self.current_theme = self.THEME_LIGHT
    
    def _save_theme_settings(self):
        """保存主题设置"""
        try:
            settings = QSettings()
            
            # 保存主题名称
            settings.setValue("theme/name", self.current_theme)
            
            # 如果是自定义主题，保存自定义设置
            if self.current_theme == self.THEME_CUSTOM and self.custom_theme:
                custom_theme_str = json.dumps(self.custom_theme)
                settings.setValue("theme/custom", custom_theme_str)
                
        except Exception as e:
            logger.error(f"保存主题设置失败: {e}")
    
    def get_current_theme(self) -> str:
        """获取当前主题名称
        
        Returns:
            str: 主题名称
        """
        return self.current_theme
    
    def get_available_themes(self) -> List[Dict[str, str]]:
        """获取可用的主题列表
        
        Returns:
            List[Dict[str, str]]: 主题列表，每个主题包含name和display_name
        """
        result = []
        for name, theme in self.themes.items():
            result.append({
                "name": name,
                "display_name": theme.get("display_name", name)
            })
        
        return result
    
    def get_theme_colors(self, theme_name: Optional[str] = None) -> Dict[str, str]:
        """获取主题颜色
        
        Args:
            theme_name: 主题名称，为None时使用当前主题
            
        Returns:
            Dict[str, str]: 颜色定义
        """
        if theme_name is None:
            theme_name = self.current_theme
            
        theme = self.themes.get(theme_name)
        if theme:
            return theme.get("colors", {})
        
        return {}
    
    def set_theme(self, theme_name: str) -> bool:
        """设置当前主题
        
        Args:
            theme_name: 主题名称
            
        Returns:
            bool: 是否设置成功
        """
        if theme_name == self.THEME_SYSTEM:
            # 根据系统主题设置浅色或深色主题
            theme_name = self._detect_system_theme()
        
        if theme_name not in self.themes and theme_name != self.THEME_CUSTOM:
            logger.warning(f"未知的主题名称: {theme_name}")
            return False
        
        # 记录当前主题
        self.current_theme = theme_name
        
        # 应用主题
        self._apply_theme()
        
        # 保存设置
        self._save_theme_settings()
        
        # 发送主题变更信号
        self.theme_changed.emit(theme_name)
        
        return True
    
    def set_custom_theme(self, custom_theme: Dict[str, Any]) -> bool:
        """设置自定义主题
        
        Args:
            custom_theme: 自定义主题定义
            
        Returns:
            bool: 是否设置成功
        """
        try:
            # 保存自定义主题
            self.custom_theme = custom_theme
            
            # 设置当前主题为自定义主题
            self.current_theme = self.THEME_CUSTOM
            
            # 应用主题
            self._apply_theme()
            
            # 保存设置
            self._save_theme_settings()
            
            # 发送主题变更信号
            self.theme_changed.emit(self.THEME_CUSTOM)
            
            return True
            
        except Exception as e:
            logger.error(f"设置自定义主题失败: {e}")
            return False
    
    def _detect_system_theme(self) -> str:
        """检测系统主题
        
        Returns:
            str: 主题名称
        """
        # TODO: 实现系统主题检测
        # 这里简化处理，始终返回浅色主题
        return self.THEME_LIGHT
    
    def _apply_theme(self):
        """应用主题到应用程序"""
        app = QApplication.instance()
        if not app:
            logger.warning("无法获取QApplication实例")
            return
        
        # 获取样式表
        style_sheet = self._get_theme_style_sheet()
        
        # 应用样式表
        app.setStyleSheet(style_sheet)
    
    def _get_theme_style_sheet(self) -> str:
        """获取主题样式表
        
        Returns:
            str: 样式表
        """
        if self.current_theme == self.THEME_CUSTOM:
            return self.custom_theme.get("style_sheet", "")
            
        theme = self.themes.get(self.current_theme)
        if theme:
            return theme.get("style_sheet", "")
            
        return ""


# 全局单例
_instance = None

def get_theme_manager() -> ThemeManager:
    """获取主题管理器单例"""
    global _instance
    if _instance is None:
        _instance = ThemeManager()
    return _instance 