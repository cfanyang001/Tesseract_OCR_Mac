from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                           QGroupBox, QLabel, QLineEdit, QPushButton, 
                           QComboBox, QDoubleSpinBox, QCheckBox, QFileDialog,
                           QGridLayout, QSpinBox, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen

from loguru import logger


class ActionTab(QWidget):
    """动作标签页，包含智能点击等功能"""
    
    # 信号
    text_click_requested = pyqtSignal(str, object, str, object)  # 文本点击请求 (文本, 区域, 类型, 偏移)
    relative_click_requested = pyqtSignal(str, float, float, object, str)  # 相对点击请求 (文本, x, y, 区域, 类型)
    template_click_requested = pyqtSignal(str, object, str, object)  # 模板点击请求 (模板路径, 区域, 类型, 偏移)
    config_changed = pyqtSignal(dict)  # 配置变更信号
    
    def __init__(self, parent=None):
        """初始化动作标签页
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 创建标签页
        tab_widget = QTabWidget(self)
        
        # 文本点击标签页
        text_click_tab = self._create_text_click_tab()
        tab_widget.addTab(text_click_tab, "文本点击")
        
        # 相对点击标签页
        relative_click_tab = self._create_relative_click_tab()
        tab_widget.addTab(relative_click_tab, "相对点击")
        
        # 模板点击标签页
        template_click_tab = self._create_template_click_tab()
        tab_widget.addTab(template_click_tab, "模板点击")
        
        # 设置标签页
        settings_tab = self._create_settings_tab()
        tab_widget.addTab(settings_tab, "设置")
        
        main_layout.addWidget(tab_widget)
        
        # 点击反馈定时器
        self.feedback_timer = QTimer(self)
        self.feedback_timer.setSingleShot(True)
        self.feedback_timer.timeout.connect(self._clear_feedback)
        
        # 默认配置
        self.current_config = {
            'confirm_before_click': True,
            'confirmation_timeout': 3.0,
            'click_delay': 0.5,
            'text_match_threshold': 0.8,
            'highlight_target': True,
            'highlight_color': (0, 255, 0),
            'highlight_duration': 1.0,
            'search_method': 'ocr',
            'max_search_attempts': 3,
        }
    
    def _create_text_click_tab(self):
        """创建文本点击标签页
        
        Returns:
            QWidget: 文本点击标签页
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文本输入组
        text_group = QGroupBox("文本搜索", tab)
        text_layout = QGridLayout(text_group)
        
        # 文本输入
        text_layout.addWidget(QLabel("搜索文本:"), 0, 0)
        self.text_input = QLineEdit(text_group)
        self.text_input.setPlaceholderText("输入要点击的文本")
        text_layout.addWidget(self.text_input, 0, 1, 1, 3)
        
        # 点击类型
        text_layout.addWidget(QLabel("点击类型:"), 1, 0)
        self.text_click_type = QComboBox(text_group)
        self.text_click_type.addItems(["单击", "双击", "右击"])
        text_layout.addWidget(self.text_click_type, 1, 1)
        
        # 偏移设置
        text_layout.addWidget(QLabel("X偏移:"), 1, 2)
        self.text_offset_x = QSpinBox(text_group)
        self.text_offset_x.setRange(-500, 500)
        self.text_offset_x.setValue(0)
        text_layout.addWidget(self.text_offset_x, 1, 3)
        
        text_layout.addWidget(QLabel("Y偏移:"), 2, 0)
        self.text_offset_y = QSpinBox(text_group)
        self.text_offset_y.setRange(-500, 500)
        self.text_offset_y.setValue(0)
        text_layout.addWidget(self.text_offset_y, 2, 1)
        
        # 搜索区域
        self.text_use_area = QCheckBox("限定搜索区域", text_group)
        text_layout.addWidget(self.text_use_area, 2, 2, 1, 2)
        
        # 执行按钮
        self.text_click_btn = QPushButton("执行点击", text_group)
        self.text_click_btn.clicked.connect(self._on_text_click)
        text_layout.addWidget(self.text_click_btn, 3, 0, 1, 4)
        
        layout.addWidget(text_group)
        
        # 预览区域
        preview_group = QGroupBox("操作预览", tab)
        preview_layout = QVBoxLayout(preview_group)
        
        self.text_preview_label = QLabel(preview_group)
        self.text_preview_label.setAlignment(Qt.AlignCenter)
        self.text_preview_label.setMinimumHeight(200)
        self.text_preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #cccccc;")
        preview_layout.addWidget(self.text_preview_label)
        
        layout.addWidget(preview_group)
        
        return tab
    
    def _create_relative_click_tab(self):
        """创建相对点击标签页
        
        Returns:
            QWidget: 相对点击标签页
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 参考文本组
        ref_group = QGroupBox("参考文本", tab)
        ref_layout = QGridLayout(ref_group)
        
        # 参考文本输入
        ref_layout.addWidget(QLabel("参考文本:"), 0, 0)
        self.ref_text_input = QLineEdit(ref_group)
        self.ref_text_input.setPlaceholderText("输入参考文本")
        ref_layout.addWidget(self.ref_text_input, 0, 1, 1, 3)
        
        # 相对位置
        ref_layout.addWidget(QLabel("相对X位置:"), 1, 0)
        self.rel_pos_x = QDoubleSpinBox(ref_group)
        self.rel_pos_x.setRange(0.0, 1.0)
        self.rel_pos_x.setSingleStep(0.1)
        self.rel_pos_x.setValue(0.5)
        ref_layout.addWidget(self.rel_pos_x, 1, 1)
        
        ref_layout.addWidget(QLabel("相对Y位置:"), 1, 2)
        self.rel_pos_y = QDoubleSpinBox(ref_group)
        self.rel_pos_y.setRange(0.0, 1.0)
        self.rel_pos_y.setSingleStep(0.1)
        self.rel_pos_y.setValue(0.5)
        ref_layout.addWidget(self.rel_pos_y, 1, 3)
        
        # 点击类型
        ref_layout.addWidget(QLabel("点击类型:"), 2, 0)
        self.rel_click_type = QComboBox(ref_group)
        self.rel_click_type.addItems(["单击", "双击", "右击"])
        ref_layout.addWidget(self.rel_click_type, 2, 1)
        
        # 搜索区域
        self.rel_use_area = QCheckBox("限定搜索区域", ref_group)
        ref_layout.addWidget(self.rel_use_area, 2, 2, 1, 2)
        
        # 执行按钮
        self.rel_click_btn = QPushButton("执行相对点击", ref_group)
        self.rel_click_btn.clicked.connect(self._on_relative_click)
        ref_layout.addWidget(self.rel_click_btn, 3, 0, 1, 4)
        
        layout.addWidget(ref_group)
        
        # 预览区域
        preview_group = QGroupBox("操作预览", tab)
        preview_layout = QVBoxLayout(preview_group)
        
        self.rel_preview_label = QLabel(preview_group)
        self.rel_preview_label.setAlignment(Qt.AlignCenter)
        self.rel_preview_label.setMinimumHeight(200)
        self.rel_preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #cccccc;")
        preview_layout.addWidget(self.rel_preview_label)
        
        layout.addWidget(preview_group)
        
        return tab
    
    def _create_template_click_tab(self):
        """创建模板点击标签页
        
        Returns:
            QWidget: 模板点击标签页
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 模板选择组
        template_group = QGroupBox("模板选择", tab)
        template_layout = QGridLayout(template_group)
        
        # 模板路径
        template_layout.addWidget(QLabel("模板路径:"), 0, 0)
        self.template_path = QLineEdit(template_group)
        self.template_path.setReadOnly(True)
        template_layout.addWidget(self.template_path, 0, 1, 1, 2)
        
        self.browse_btn = QPushButton("浏览...", template_group)
        self.browse_btn.clicked.connect(self._browse_template)
        template_layout.addWidget(self.browse_btn, 0, 3)
        
        # 点击类型
        template_layout.addWidget(QLabel("点击类型:"), 1, 0)
        self.template_click_type = QComboBox(template_group)
        self.template_click_type.addItems(["单击", "双击", "右击"])
        template_layout.addWidget(self.template_click_type, 1, 1)
        
        # 偏移设置
        template_layout.addWidget(QLabel("X偏移:"), 1, 2)
        self.template_offset_x = QSpinBox(template_group)
        self.template_offset_x.setRange(-500, 500)
        self.template_offset_x.setValue(0)
        template_layout.addWidget(self.template_offset_x, 1, 3)
        
        template_layout.addWidget(QLabel("Y偏移:"), 2, 0)
        self.template_offset_y = QSpinBox(template_group)
        self.template_offset_y.setRange(-500, 500)
        self.template_offset_y.setValue(0)
        template_layout.addWidget(self.template_offset_y, 2, 1)
        
        # 搜索区域
        self.template_use_area = QCheckBox("限定搜索区域", template_group)
        template_layout.addWidget(self.template_use_area, 2, 2, 1, 2)
        
        # 执行按钮
        self.template_click_btn = QPushButton("执行模板点击", template_group)
        self.template_click_btn.clicked.connect(self._on_template_click)
        template_layout.addWidget(self.template_click_btn, 3, 0, 1, 4)
        
        layout.addWidget(template_group)
        
        # 预览区域
        preview_group = QGroupBox("模板预览", tab)
        preview_layout = QVBoxLayout(preview_group)
        
        self.template_preview_label = QLabel(preview_group)
        self.template_preview_label.setAlignment(Qt.AlignCenter)
        self.template_preview_label.setMinimumHeight(200)
        self.template_preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #cccccc;")
        preview_layout.addWidget(self.template_preview_label)
        
        layout.addWidget(preview_group)
        
        return tab
    
    def _create_settings_tab(self):
        """创建设置标签页
        
        Returns:
            QWidget: 设置标签页
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 点击设置组
        click_group = QGroupBox("点击设置", tab)
        click_layout = QGridLayout(click_group)
        
        # 点击前确认
        self.confirm_click = QCheckBox("点击前确认", click_group)
        self.confirm_click.setChecked(True)
        self.confirm_click.stateChanged.connect(self._on_setting_changed)
        click_layout.addWidget(self.confirm_click, 0, 0)
        
        # 确认超时
        click_layout.addWidget(QLabel("确认超时(秒):"), 0, 1)
        self.confirm_timeout = QDoubleSpinBox(click_group)
        self.confirm_timeout.setRange(1.0, 10.0)
        self.confirm_timeout.setSingleStep(0.5)
        self.confirm_timeout.setValue(3.0)
        self.confirm_timeout.valueChanged.connect(self._on_setting_changed)
        click_layout.addWidget(self.confirm_timeout, 0, 2)
        
        # 点击延迟
        click_layout.addWidget(QLabel("点击延迟(秒):"), 1, 0)
        self.click_delay = QDoubleSpinBox(click_group)
        self.click_delay.setRange(0.1, 5.0)
        self.click_delay.setSingleStep(0.1)
        self.click_delay.setValue(0.5)
        self.click_delay.valueChanged.connect(self._on_setting_changed)
        click_layout.addWidget(self.click_delay, 1, 1)
        
        layout.addWidget(click_group)
        
        # 搜索设置组
        search_group = QGroupBox("搜索设置", tab)
        search_layout = QGridLayout(search_group)
        
        # 文本匹配阈值
        search_layout.addWidget(QLabel("文本匹配阈值:"), 0, 0)
        self.match_threshold = QDoubleSpinBox(search_group)
        self.match_threshold.setRange(0.5, 1.0)
        self.match_threshold.setSingleStep(0.05)
        self.match_threshold.setValue(0.8)
        self.match_threshold.valueChanged.connect(self._on_setting_changed)
        search_layout.addWidget(self.match_threshold, 0, 1)
        
        # 搜索方法
        search_layout.addWidget(QLabel("搜索方法:"), 0, 2)
        self.search_method = QComboBox(search_group)
        self.search_method.addItems(["OCR", "模板匹配", "混合"])
        self.search_method.currentIndexChanged.connect(self._on_setting_changed)
        search_layout.addWidget(self.search_method, 0, 3)
        
        # 最大搜索尝试次数
        search_layout.addWidget(QLabel("最大尝试次数:"), 1, 0)
        self.max_attempts = QSpinBox(search_group)
        self.max_attempts.setRange(1, 10)
        self.max_attempts.setValue(3)
        self.max_attempts.valueChanged.connect(self._on_setting_changed)
        search_layout.addWidget(self.max_attempts, 1, 1)
        
        layout.addWidget(search_group)
        
        # 显示设置组
        display_group = QGroupBox("显示设置", tab)
        display_layout = QGridLayout(display_group)
        
        # 高亮目标
        self.highlight_target = QCheckBox("高亮显示目标", display_group)
        self.highlight_target.setChecked(True)
        self.highlight_target.stateChanged.connect(self._on_setting_changed)
        display_layout.addWidget(self.highlight_target, 0, 0)
        
        # 高亮持续时间
        display_layout.addWidget(QLabel("高亮持续时间(秒):"), 0, 1)
        self.highlight_duration = QDoubleSpinBox(display_group)
        self.highlight_duration.setRange(0.5, 5.0)
        self.highlight_duration.setSingleStep(0.5)
        self.highlight_duration.setValue(1.0)
        self.highlight_duration.valueChanged.connect(self._on_setting_changed)
        display_layout.addWidget(self.highlight_duration, 0, 2)
        
        layout.addWidget(display_group)
        
        # 应用按钮
        self.apply_settings_btn = QPushButton("应用设置", tab)
        self.apply_settings_btn.clicked.connect(self._apply_settings)
        layout.addWidget(self.apply_settings_btn)
        
        # 添加弹性空间
        layout.addStretch()
        
        return tab
    
    def _on_text_click(self):
        """文本点击处理"""
        text = self.text_input.text().strip()
        if not text:
            return
        
        # 获取点击类型
        click_type_map = {"单击": "single", "双击": "double", "右击": "right"}
        click_type = click_type_map[self.text_click_type.currentText()]
        
        # 获取偏移
        offset = QPoint(self.text_offset_x.value(), self.text_offset_y.value())
        
        # 获取搜索区域
        search_area = None  # TODO: 实现搜索区域选择
        
        # 发送点击请求信号
        self.text_click_requested.emit(text, search_area, click_type, offset)
    
    def _on_relative_click(self):
        """相对点击处理"""
        text = self.ref_text_input.text().strip()
        if not text:
            return
        
        # 获取相对位置
        rel_x = self.rel_pos_x.value()
        rel_y = self.rel_pos_y.value()
        
        # 获取点击类型
        click_type_map = {"单击": "single", "双击": "double", "右击": "right"}
        click_type = click_type_map[self.rel_click_type.currentText()]
        
        # 获取搜索区域
        search_area = None  # TODO: 实现搜索区域选择
        
        # 发送相对点击请求信号
        self.relative_click_requested.emit(text, rel_x, rel_y, search_area, click_type)
    
    def _on_template_click(self):
        """模板点击处理"""
        template_path = self.template_path.text().strip()
        if not template_path:
            return
        
        # 获取点击类型
        click_type_map = {"单击": "single", "双击": "double", "右击": "right"}
        click_type = click_type_map[self.template_click_type.currentText()]
        
        # 获取偏移
        offset = QPoint(self.template_offset_x.value(), self.template_offset_y.value())
        
        # 获取搜索区域
        search_area = None  # TODO: 实现搜索区域选择
        
        # 发送模板点击请求信号
        self.template_click_requested.emit(template_path, search_area, click_type, offset)
    
    def _browse_template(self):
        """浏览模板文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模板图像", "", "图像文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            self.template_path.setText(file_path)
            
            # 加载并显示模板预览
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.template_preview_label.setPixmap(
                    pixmap.scaled(
                        self.template_preview_label.width(),
                        self.template_preview_label.height(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                )
    
    def _on_setting_changed(self):
        """设置变更处理"""
        # 更新当前配置
        self._update_config_from_ui()
    
    def _apply_settings(self):
        """应用设置"""
        # 更新当前配置
        self._update_config_from_ui()
        
        # 发送配置变更信号
        self.config_changed.emit(self.current_config)
    
    def _update_config_from_ui(self):
        """从UI更新配置"""
        # 点击设置
        self.current_config['confirm_before_click'] = self.confirm_click.isChecked()
        self.current_config['confirmation_timeout'] = self.confirm_timeout.value()
        self.current_config['click_delay'] = self.click_delay.value()
        
        # 搜索设置
        self.current_config['text_match_threshold'] = self.match_threshold.value()
        self.current_config['search_method'] = self.search_method.currentText().lower()
        self.current_config['max_search_attempts'] = self.max_attempts.value()
        
        # 显示设置
        self.current_config['highlight_target'] = self.highlight_target.isChecked()
        self.current_config['highlight_duration'] = self.highlight_duration.value()
    
    def update_ui_from_config(self, config):
        """从配置更新UI
        
        Args:
            config: 配置
        """
        if not config:
            return
            
        # 更新当前配置
        self.current_config.update(config)
        
        # 点击设置
        self.confirm_click.setChecked(config.get('confirm_before_click', True))
        self.confirm_timeout.setValue(config.get('confirmation_timeout', 3.0))
        self.click_delay.setValue(config.get('click_delay', 0.5))
        
        # 搜索设置
        self.match_threshold.setValue(config.get('text_match_threshold', 0.8))
        
        search_method = config.get('search_method', 'ocr')
        method_index = 0
        if search_method == 'template':
            method_index = 1
        elif search_method == 'hybrid':
            method_index = 2
        self.search_method.setCurrentIndex(method_index)
        
        self.max_attempts.setValue(config.get('max_search_attempts', 3))
        
        # 显示设置
        self.highlight_target.setChecked(config.get('highlight_target', True))
        self.highlight_duration.setValue(config.get('highlight_duration', 1.0))
    
    def highlight_target(self, rect):
        """高亮显示目标
        
        Args:
            rect: 目标区域
        """
        # TODO: 实现高亮显示
        logger.debug(f"高亮显示目标: {rect}")
    
    def show_click_feedback(self, point, click_type):
        """显示点击反馈
        
        Args:
            point: 点击位置
            click_type: 点击类型
        """
        # TODO: 实现点击反馈
        logger.debug(f"点击反馈: 位置 ({point.x()}, {point.y()}), 类型: {click_type}")
        
        # 启动反馈清除定时器
        self.feedback_timer.start(int(self.current_config['highlight_duration'] * 1000))
    
    def _clear_feedback(self):
        """清除反馈"""
        # TODO: 实现清除反馈
        logger.debug("清除点击反馈") 