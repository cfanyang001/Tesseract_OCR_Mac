from PyQt5.QtCore import QObject, pyqtSignal, QPoint, QRect, Qt
from PyQt5.QtWidgets import QMessageBox

from core.smart_click import SmartClick
from ui.components.tabs.action_tab import ActionTab
from ui.components.dialogs.click_confirm_dialog import ClickConfirmDialog
from loguru import logger


class ActionController(QObject):
    """动作控制器，负责处理智能点击等动作"""
    
    # 信号
    log_message = pyqtSignal(str, str, str, str)  # 日志信号 (级别, 来源, 消息, 详情)
    
    def __init__(self, action_tab):
        """初始化动作控制器
        
        Args:
            action_tab: 动作标签页
        """
        super().__init__()
        
        self.action_tab = action_tab
        
        # 创建智能点击功能
        try:
            self.smart_click = SmartClick()
            logger.info("智能点击功能初始化成功")
            self.log_message.emit("info", "action", "智能点击功能初始化成功", "")
        except Exception as e:
            error_msg = f"智能点击功能初始化失败: {e}"
            logger.error(error_msg)
            self.log_message.emit("error", "action", "智能点击功能初始化失败", str(e))
            raise
        
        # 连接信号
        self._connect_signals()
    
    def _connect_signals(self):
        """连接信号"""
        # 智能点击信号
        self.smart_click.target_found.connect(self._on_target_found)
        self.smart_click.click_performed.connect(self._on_click_performed)
        self.smart_click.error_occurred.connect(self._on_error_occurred)
        
        # UI信号
        self.action_tab.text_click_requested.connect(self.click_on_text)
        self.action_tab.relative_click_requested.connect(self.click_relative_to_text)
        self.action_tab.template_click_requested.connect(self.click_on_element)
        self.action_tab.config_changed.connect(self._on_config_changed)
    
    def click_on_text(self, text, search_area=None, click_type="single", offset=None):
        """点击文本
        
        Args:
            text: 要点击的文本
            search_area: 搜索区域
            click_type: 点击类型
            offset: 偏移
        """
        logger.info(f"请求点击文本: '{text}', 类型: {click_type}")
        self.log_message.emit("info", "action", f"尝试点击文本: '{text}'", f"类型: {click_type}")
        
        # 执行点击
        success = self.smart_click.click_on_text(text, search_area, click_type, offset)
        
        if success:
            self.log_message.emit("info", "action", f"成功点击文本: '{text}'", f"类型: {click_type}")
        else:
            self.log_message.emit("warning", "action", f"点击文本失败: '{text}'", f"类型: {click_type}")
    
    def click_relative_to_text(self, text, relative_x, relative_y, search_area=None, click_type="single"):
        """相对于文本点击
        
        Args:
            text: 参考文本
            relative_x: 相对X位置 (0.0-1.0)
            relative_y: 相对Y位置 (0.0-1.0)
            search_area: 搜索区域
            click_type: 点击类型
        """
        logger.info(f"请求相对点击: 参考文本 '{text}', 相对位置: ({relative_x:.2f}, {relative_y:.2f})")
        self.log_message.emit("info", "action", f"尝试相对点击: 参考文本 '{text}'", 
                             f"相对位置: ({relative_x:.2f}, {relative_y:.2f}), 类型: {click_type}")
        
        # 执行点击
        success = self.smart_click.click_relative_to_text(text, relative_x, relative_y, search_area, click_type)
        
        if success:
            self.log_message.emit("info", "action", f"成功执行相对点击: 参考文本 '{text}'", 
                                f"相对位置: ({relative_x:.2f}, {relative_y:.2f})")
        else:
            self.log_message.emit("warning", "action", f"相对点击失败: 参考文本 '{text}'", 
                                f"相对位置: ({relative_x:.2f}, {relative_y:.2f})")
    
    def click_on_element(self, template_path, search_area=None, click_type="single", offset=None):
        """点击元素
        
        Args:
            template_path: 模板图像路径
            search_area: 搜索区域
            click_type: 点击类型
            offset: 偏移
        """
        logger.info(f"请求点击元素: 模板 '{template_path}', 类型: {click_type}")
        self.log_message.emit("info", "action", f"尝试点击元素: 模板 '{template_path}'", f"类型: {click_type}")
        
        # 执行点击
        success = self.smart_click.click_on_element(template_path, search_area, click_type, offset)
        
        if success:
            self.log_message.emit("info", "action", f"成功点击元素: 模板 '{template_path}'", f"类型: {click_type}")
        else:
            self.log_message.emit("warning", "action", f"点击元素失败: 模板 '{template_path}'", f"类型: {click_type}")
    
    def _on_target_found(self, text, rect):
        """目标找到处理
        
        Args:
            text: 找到的文本
            rect: 文本区域
        """
        logger.info(f"找到目标: '{text}', 位置: {rect}")
        self.action_tab.highlight_target(rect)
    
    def _on_click_performed(self, point, click_type):
        """点击执行处理
        
        Args:
            point: 点击位置
            click_type: 点击类型
        """
        logger.info(f"执行点击: 位置 ({point.x()}, {point.y()}), 类型: {click_type}")
        self.action_tab.show_click_feedback(point, click_type)
    
    def _on_error_occurred(self, error_msg):
        """错误处理
        
        Args:
            error_msg: 错误消息
        """
        logger.error(f"智能点击错误: {error_msg}")
        self.log_message.emit("error", "action", "智能点击错误", error_msg)
        
        # 显示错误消息
        QMessageBox.warning(self.action_tab, "智能点击错误", error_msg)
    
    def _on_config_changed(self, config):
        """配置变更处理
        
        Args:
            config: 新配置
        """
        logger.info("更新智能点击配置")
        self.smart_click.set_config(config)
    
    def apply_config(self, config):
        """应用配置
        
        Args:
            config: 配置
        """
        if not config:
            return
            
        # 提取智能点击相关配置
        smart_click_config = config.get('smart_click', {})
        if smart_click_config:
            self.smart_click.set_config(smart_click_config)
            self.action_tab.update_ui_from_config(smart_click_config)
            logger.info(f"已应用智能点击配置: {smart_click_config}") 