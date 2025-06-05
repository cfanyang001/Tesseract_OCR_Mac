from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QLineEdit, QGroupBox, QFormLayout, QMessageBox, QScrollArea, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from loguru import logger

class ConfigPanel(QWidget):
    """配置面板组件，显示在主窗口右侧，用于管理不同标签页的配置"""
    
    # 信号定义
    config_changed = pyqtSignal(str)  # 当配置改变时发出信号
    config_saved = pyqtSignal(str, dict)  # 当配置保存时发出信号 (配置名称, 配置数据)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_tab = None
        self.current_config = "默认配置"
        self.configs = {
            "默认配置": {}  # 初始默认配置
        }
        
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 标题
        title_label = QLabel("配置管理")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # 配置选择组
        config_group = QGroupBox("配置选择")
        config_layout = QVBoxLayout()
        
        # 配置选择下拉框
        config_form = QFormLayout()
        self.config_combo = QComboBox()
        self.config_combo.addItem("默认配置")
        self.config_combo.currentTextChanged.connect(self.on_config_changed)
        config_form.addRow("当前配置:", self.config_combo)
        config_layout.addLayout(config_form)
        
        # 配置管理按钮组
        buttons_layout = QHBoxLayout()
        
        self.new_config_btn = QPushButton("新建")
        self.new_config_btn.clicked.connect(self.create_new_config)
        buttons_layout.addWidget(self.new_config_btn)
        
        self.save_config_btn = QPushButton("保存")
        self.save_config_btn.clicked.connect(self.save_current_config)
        buttons_layout.addWidget(self.save_config_btn)
        
        self.delete_config_btn = QPushButton("删除")
        self.delete_config_btn.clicked.connect(self.delete_current_config)
        buttons_layout.addWidget(self.delete_config_btn)
        
        config_layout.addLayout(buttons_layout)
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # 配置内容区域（使用滚动区域）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.config_content = QWidget()
        self.config_content_layout = QVBoxLayout(self.config_content)
        
        scroll.setWidget(self.config_content)
        main_layout.addWidget(scroll)
        
        # 占位标签
        self.placeholder = QLabel("请选择标签页查看配置选项")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setStyleSheet("color: gray; font-style: italic;")
        self.config_content_layout.addWidget(self.placeholder)
        
        # 设置固定宽度
        self.setFixedWidth(250)
    
    def on_config_changed(self, config_name):
        """当选择的配置改变时"""
        if config_name != self.current_config:
            self.current_config = config_name
            self.config_changed.emit(config_name)
            self.update_config_display()
    
    def create_new_config(self):
        """创建新配置"""
        # 弹出对话框输入新配置名称
        name, ok = QInputDialog.getText(self, "新建配置", "请输入配置名称:")
        
        if ok and name:
            if name in self.configs:
                QMessageBox.warning(self, "警告", f"配置 '{name}' 已存在!")
                return
            
            # 创建新配置（复制当前配置）
            self.configs[name] = self.get_current_tab_config().copy()
            
            # 更新下拉框
            self.config_combo.addItem(name)
            self.config_combo.setCurrentText(name)
            
            # 更新当前配置名称
            self.current_config = name
            
            # 发送配置改变信号
            self.config_changed.emit(name)
            
            logger.info(f"已创建新配置: {name}")
    
    def save_current_config(self):
        """保存当前配置"""
        try:
            # 获取主窗口
            main_window = self.window()
            if main_window and hasattr(main_window, 'save_current_config'):
                # 通过主窗口的方法保存配置
                main_window.save_current_config()
            else:
                logger.warning("无法获取主窗口或主窗口没有save_current_config方法")
                # 使用旧的方式保存
                config_data = self.configs.get(self.current_config, {})
                self.config_saved.emit(self.current_config, config_data)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def delete_current_config(self):
        """删除当前配置"""
        if self.current_config == "默认配置":
            QMessageBox.warning(self, "警告", "默认配置不能删除!")
            return
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除配置 '{self.current_config}' 吗?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 删除配置
            del self.configs[self.current_config]
            
            # 更新下拉框
            idx = self.config_combo.findText(self.current_config)
            self.config_combo.removeItem(idx)
            
            # 切换到默认配置
            self.config_combo.setCurrentText("默认配置")
    
    def set_current_tab(self, tab_name, tab_widget):
        """设置当前标签页"""
        self.current_tab = tab_name
        
        # 清除之前的配置显示
        self.clear_config_display()
        
        # 如果是任务管理或日志标签，显示不支持信息
        if tab_name in ["任务管理", "日志"]:
            label = QLabel(f"{tab_name}标签页不支持配置管理")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("color: gray; font-style: italic;")
            self.config_content_layout.addWidget(label)
        else:
            # 显示当前标签页的配置选项
            self.update_config_display()
    
    def clear_config_display(self):
        """清除配置显示区域"""
        # 清除配置内容布局中的所有组件
        while self.config_content_layout.count():
            item = self.config_content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def update_config_display(self):
        """更新配置显示"""
        if not self.current_tab or self.current_tab in ["任务管理", "日志"]:
            return
        
        self.clear_config_display()
        
        # 显示当前标签页的配置选项
        if self.current_tab == "OCR设置":
            self.show_ocr_config()
        elif self.current_tab == "监控设置":
            self.show_monitor_config()
        elif self.current_tab == "动作配置":
            self.show_actions_config()
    
    def show_ocr_config(self):
        """显示OCR配置选项"""
        # 获取当前配置
        config = self.configs.get(self.current_config, {}).get("ocr", {})
        
        # 高级OCR选项
        group = QGroupBox("高级OCR选项")
        form = QFormLayout()
        
        # 自动修正
        autocorrect_combo = QComboBox()
        autocorrect_combo.addItems(["启用", "禁用"])
        autocorrect_value = config.get("autocorrect", False)
        autocorrect_combo.setCurrentText("启用" if autocorrect_value else "禁用")
        form.addRow("文本自动修正:", autocorrect_combo)
        
        # 识别模式
        mode_combo = QComboBox()
        mode_combo.addItems(["标准模式", "快速模式", "精确模式"])
        mode = config.get("recognition_mode", "标准模式")
        mode_combo.setCurrentText(mode)
        form.addRow("识别模式:", mode_combo)
        
        group.setLayout(form)
        self.config_content_layout.addWidget(group)
        
        # 缓存设置
        cache_group = QGroupBox("缓存设置")
        cache_form = QFormLayout()
        
        # 缓存大小
        cache_combo = QComboBox()
        cache_combo.addItems(["5", "10", "20", "50"])
        cache_size = str(config.get("result_cache_size", 10))
        cache_combo.setCurrentText(cache_size if cache_size in ["5", "10", "20", "50"] else "10")
        cache_form.addRow("结果缓存大小:", cache_combo)
        
        cache_group.setLayout(cache_form)
        self.config_content_layout.addWidget(cache_group)
    
    def show_monitor_config(self):
        """显示监控配置选项"""
        group = QGroupBox("监控设置")
        form = QFormLayout()
        
        # 获取当前配置
        config = self.configs.get(self.current_config, {}).get("monitor", {})
        
        # 监控间隔
        interval_combo = QComboBox()
        interval_combo.addItems(["1", "2", "3", "5", "10"])
        interval_combo.setCurrentText(str(config.get("interval", "2")))
        form.addRow("监控间隔(秒):", interval_combo)
        
        # 匹配模式
        match_combo = QComboBox()
        match_combo.addItems(["精确匹配", "包含匹配", "正则匹配"])
        match_combo.setCurrentText(config.get("match_mode", "包含匹配"))
        form.addRow("匹配模式:", match_combo)
        
        group.setLayout(form)
        self.config_content_layout.addWidget(group)
    
    def show_actions_config(self):
        """显示动作配置选项"""
        group = QGroupBox("动作设置")
        form = QFormLayout()
        
        # 获取当前配置
        config = self.configs.get(self.current_config, {}).get("actions", {})
        
        # 动作延迟
        delay_combo = QComboBox()
        delay_combo.addItems(["0", "0.5", "1", "2", "3"])
        delay_combo.setCurrentText(str(config.get("delay", "0.5")))
        form.addRow("动作延迟(秒):", delay_combo)
        
        # 重试次数
        retry_combo = QComboBox()
        retry_combo.addItems(["0", "1", "2", "3", "5"])
        retry_combo.setCurrentText(str(config.get("retries", "1")))
        form.addRow("重试次数:", retry_combo)
        
        group.setLayout(form)
        self.config_content_layout.addWidget(group)
    
    def get_current_tab_config(self):
        """获取当前标签页的配置"""
        # 这个方法不再使用，但保留为空方法以防其他地方调用
        logger.warning("get_current_tab_config方法已废弃，请使用全局配置管理")
        return self.configs.get(self.current_config, {}) 