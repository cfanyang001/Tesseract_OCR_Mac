from PyQt5.QtCore import QObject, pyqtSlot
from loguru import logger

from config.config_manager import ConfigManager

class ConfigController(QObject):
    """配置控制器，连接配置面板和配置管理器"""
    
    def __init__(self, config_panel):
        """初始化配置控制器
        
        Args:
            config_panel: 配置面板组件
        """
        super().__init__()
        self.config_panel = config_panel
        self.config_manager = ConfigManager()
        
        # 连接信号
        self.connect_signals()
        
        # 初始化配置面板
        self.init_config_panel()
    
    def connect_signals(self):
        """连接信号"""
        # 配置面板信号
        self.config_panel.config_changed.connect(self.on_config_changed)
        self.config_panel.config_saved.connect(self.on_config_saved)
    
    def init_config_panel(self):
        """初始化配置面板"""
        try:
            # 获取所有配置名称
            config_names = self.config_manager.get_all_config_names()
            
            # 清除现有项
            self.config_panel.config_combo.clear()
            
            # 添加配置名称到下拉框
            for name in config_names:
                self.config_panel.config_combo.addItem(name)
            
            # 设置当前配置
            current_config = self.config_manager.current_config
            self.config_panel.config_combo.setCurrentText(current_config)
            
            logger.info("配置面板初始化完成")
        
        except Exception as e:
            logger.error(f"初始化配置面板失败: {e}")
    
    @pyqtSlot(str)
    def on_config_changed(self, config_name):
        """当选择的配置改变时
        
        Args:
            config_name: 配置名称
        """
        try:
            # 设置配置管理器的当前配置
            self.config_manager.set_current_config(config_name)
            
            # 更新配置面板显示
            self.update_config_display()
            
            logger.info(f"切换到配置: {config_name}")
        
        except Exception as e:
            logger.error(f"切换配置失败: {e}")
    
    @pyqtSlot(str, dict)
    def on_config_saved(self, config_name, config_data):
        """当配置保存时
        
        Args:
            config_name: 配置名称
            config_data: 配置数据
        """
        try:
            # 保存配置
            success = self.config_manager.save_config(config_name, config_data)
            
            if success:
                logger.info(f"配置 {config_name} 已保存")
            else:
                logger.error(f"保存配置 {config_name} 失败")
        
        except Exception as e:
            logger.error(f"保存配置时发生错误: {e}")
    
    def update_config_display(self):
        """更新配置面板显示"""
        # 获取当前配置
        config = self.config_manager.get_config()
        
        # 更新配置面板
        # 这里应该根据当前标签页更新配置面板
        # 简化实现，仅更新配置面板显示
        self.config_panel.update_config_display()
    
    def apply_config_to_tab(self, tab_name, tab_widget):
        """应用配置到标签页
        
        Args:
            tab_name: 标签页名称
            tab_widget: 标签页组件
        """
        # 获取当前配置
        config = self.config_manager.get_config()
        
        # 根据标签页类型应用配置
        if tab_name == "OCR设置":
            self.apply_ocr_config(tab_widget, config.get("ocr", {}))
        elif tab_name == "监控设置":
            self.apply_monitor_config(tab_widget, config.get("monitor", {}))
        elif tab_name == "动作配置":
            self.apply_actions_config(tab_widget, config.get("actions", {}))
    
    def apply_ocr_config(self, tab_widget, config):
        """应用OCR配置到标签页
        
        Args:
            tab_widget: OCR标签页组件
            config: OCR配置
        """
        # 这里应该根据配置更新OCR标签页的组件状态
        # 简化实现，仅记录日志
        logger.info(f"应用OCR配置: {config}")
    
    def apply_monitor_config(self, tab_widget, config):
        """应用监控配置到标签页
        
        Args:
            tab_widget: 监控标签页组件
            config: 监控配置
        """
        # 这里应该根据配置更新监控标签页的组件状态
        # 简化实现，仅记录日志
        logger.info(f"应用监控配置: {config}")
    
    def apply_actions_config(self, tab_widget, config):
        """应用动作配置到标签页
        
        Args:
            tab_widget: 动作标签页组件
            config: 动作配置
        """
        # 这里应该根据配置更新动作标签页的组件状态
        # 简化实现，仅记录日志
        logger.info(f"应用动作配置: {config}")
    
    def get_config_from_tab(self, tab_name, tab_widget):
        """从标签页获取配置
        
        Args:
            tab_name: 标签页名称
            tab_widget: 标签页组件
            
        Returns:
            dict: 配置数据
        """
        # 根据标签页类型获取配置
        if tab_name == "OCR设置":
            return {"ocr": self.get_ocr_config(tab_widget)}
        elif tab_name == "监控设置":
            return {"monitor": self.get_monitor_config(tab_widget)}
        elif tab_name == "动作配置":
            return {"actions": self.get_actions_config(tab_widget)}
        else:
            return {}
    
    def get_ocr_config(self, tab_widget):
        """从OCR标签页获取配置
        
        Args:
            tab_widget: OCR标签页组件
            
        Returns:
            dict: OCR配置
        """
        # 这里应该从OCR标签页的组件获取配置
        # 简化实现，返回默认配置
        return {
            "language": "eng",
            "psm": "3",
            "oem": "3"
        }
    
    def get_monitor_config(self, tab_widget):
        """从监控标签页获取配置
        
        Args:
            tab_widget: 监控标签页组件
            
        Returns:
            dict: 监控配置
        """
        # 这里应该从监控标签页的组件获取配置
        # 简化实现，返回默认配置
        return {
            "interval": "2",
            "match_mode": "包含匹配"
        }
    
    def get_actions_config(self, tab_widget):
        """从动作标签页获取配置
        
        Args:
            tab_widget: 动作标签页组件
            
        Returns:
            dict: 动作配置
        """
        # 这里应该从动作标签页的组件获取配置
        # 简化实现，返回默认配置
        return {
            "delay": "0.5",
            "retries": "1"
        } 