from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton,
    QGroupBox, QSpinBox, QDoubleSpinBox, QFormLayout,
    QRadioButton, QButtonGroup, QFrame, QSlider
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon

from loguru import logger


class SettingsDialog(QDialog):
    """设置对话框，用于配置软件设置"""
    
    # 信号
    settings_saved = pyqtSignal(dict)  # 设置保存信号
    
    def __init__(self, parent=None, settings=None):
        """初始化设置对话框
        
        Args:
            parent: 父窗口
            settings: 当前设置
        """
        super().__init__(parent)
        
        self.setWindowTitle("软件设置")
        self.setMinimumSize(QSize(600, 450))
        
        # 当前设置
        self.settings = settings or {}
        
        # 创建UI
        self._setup_ui()
        
        # 加载设置
        self._load_settings()
    
    def _setup_ui(self):
        """设置UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建标签页
        self.ocr_tab = self._create_ocr_tab()
        self.tab_widget.addTab(self.ocr_tab, "OCR设置")
        
        self.monitor_tab = self._create_monitor_tab()
        self.tab_widget.addTab(self.monitor_tab, "监控设置")
        
        self.action_tab = self._create_action_tab()
        self.tab_widget.addTab(self.action_tab, "动作设置")
        
        self.system_tab = self._create_system_tab()
        self.tab_widget.addTab(self.system_tab, "系统设置")
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.reset_btn = QPushButton("重置为默认")
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.save_btn.setDefault(True)
        button_layout.addWidget(self.save_btn)
        
        main_layout.addLayout(button_layout)
    
    def _create_ocr_tab(self):
        """创建OCR设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # OCR引擎设置
        engine_group = QGroupBox("OCR引擎设置")
        engine_layout = QFormLayout(engine_group)
        
        # 语言选择
        self.ocr_lang_combo = QComboBox()
        self.ocr_lang_combo.addItems(["中文简体", "中文繁体", "英语", "日语", "韩语"])
        engine_layout.addRow("识别语言:", self.ocr_lang_combo)
        
        # PSM模式
        self.ocr_psm_combo = QComboBox()
        self.ocr_psm_combo.addItems([
            "3 - 全自动页面分割（默认）",
            "4 - 假设单列文本",
            "6 - 假设统一文本块",
            "7 - 将图像视为单行文本",
            "8 - 将图像视为单词",
            "10 - 将图像视为单个字符"
        ])
        engine_layout.addRow("PSM模式:", self.ocr_psm_combo)
        
        # OEM引擎
        self.ocr_oem_combo = QComboBox()
        self.ocr_oem_combo.addItems([
            "1 - 神经网络LSTM引擎",
            "0 - 传统Tesseract引擎",
            "2 - 传统+LSTM引擎",
            "3 - 默认自动选择"
        ])
        engine_layout.addRow("OCR引擎:", self.ocr_oem_combo)
        
        layout.addWidget(engine_group)
        
        # 图像预处理设置
        preprocess_group = QGroupBox("图像预处理设置")
        preprocess_layout = QFormLayout(preprocess_group)
        
        # 启用预处理
        self.preprocess_check = QCheckBox("启用图像预处理")
        preprocess_layout.addRow("", self.preprocess_check)
        
        # 精度设置
        self.accuracy_slider = QSlider(Qt.Horizontal)
        self.accuracy_slider.setRange(0, 100)
        self.accuracy_slider.setValue(80)
        self.accuracy_label = QLabel("80%")
        
        accuracy_layout = QHBoxLayout()
        accuracy_layout.addWidget(self.accuracy_slider)
        accuracy_layout.addWidget(self.accuracy_label)
        
        preprocess_layout.addRow("识别精度:", accuracy_layout)
        
        # 连接信号
        self.accuracy_slider.valueChanged.connect(self._update_accuracy_label)
        
        layout.addWidget(preprocess_group)
        
        # 高级设置
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QFormLayout(advanced_group)
        
        # 自动修正
        self.autocorrect_check = QCheckBox("启用文本自动修正")
        advanced_layout.addRow("", self.autocorrect_check)
        
        # 缓存设置
        self.cache_check = QCheckBox("使用结果缓存")
        advanced_layout.addRow("", self.cache_check)
        
        # 缓存大小
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(10, 200)
        self.cache_size_spin.setValue(50)
        advanced_layout.addRow("缓存大小:", self.cache_size_spin)
        
        layout.addWidget(advanced_group)
        
        layout.addStretch()
        return tab
    
    def _create_monitor_tab(self):
        """创建监控设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 监控刷新设置
        refresh_group = QGroupBox("监控刷新设置")
        refresh_layout = QFormLayout(refresh_group)
        
        # 刷新频率
        self.refresh_rate_spin = QSpinBox()
        self.refresh_rate_spin.setRange(100, 10000)
        self.refresh_rate_spin.setValue(1000)
        self.refresh_rate_spin.setSingleStep(100)
        self.refresh_rate_spin.setSuffix(" 毫秒")
        refresh_layout.addRow("刷新频率:", self.refresh_rate_spin)
        
        # 自适应刷新
        self.adaptive_refresh_check = QCheckBox("启用自适应刷新率")
        refresh_layout.addRow("", self.adaptive_refresh_check)
        
        # 最小刷新率
        self.min_refresh_spin = QSpinBox()
        self.min_refresh_spin.setRange(100, 5000)
        self.min_refresh_spin.setValue(200)
        self.min_refresh_spin.setSingleStep(100)
        self.min_refresh_spin.setSuffix(" 毫秒")
        refresh_layout.addRow("最小刷新率:", self.min_refresh_spin)
        
        # 最大刷新率
        self.max_refresh_spin = QSpinBox()
        self.max_refresh_spin.setRange(500, 10000)
        self.max_refresh_spin.setValue(2000)
        self.max_refresh_spin.setSingleStep(100)
        self.max_refresh_spin.setSuffix(" 毫秒")
        refresh_layout.addRow("最大刷新率:", self.max_refresh_spin)
        
        layout.addWidget(refresh_group)
        
        # 规则设置
        rule_group = QGroupBox("规则设置")
        rule_layout = QFormLayout(rule_group)
        
        # 默认组合方式
        self.rule_combine_combo = QComboBox()
        self.rule_combine_combo.addItems(["AND - 所有规则都满足", "OR - 任一规则满足", "自定义表达式"])
        rule_layout.addRow("默认组合方式:", self.rule_combine_combo)
        
        # 规则匹配阈值
        self.rule_threshold_spin = QDoubleSpinBox()
        self.rule_threshold_spin.setRange(0.1, 1.0)
        self.rule_threshold_spin.setValue(0.8)
        self.rule_threshold_spin.setSingleStep(0.05)
        rule_layout.addRow("匹配阈值:", self.rule_threshold_spin)
        
        layout.addWidget(rule_group)
        
        # 保存设置
        save_group = QGroupBox("保存设置")
        save_layout = QFormLayout(save_group)
        
        # 保存图像
        self.save_images_check = QCheckBox("保存捕获图像")
        save_layout.addRow("", self.save_images_check)
        
        # 保存目录
        self.save_dir_edit = QLineEdit("./captures")
        save_layout.addRow("保存目录:", self.save_dir_edit)
        
        layout.addWidget(save_group)
        
        layout.addStretch()
        return tab
    
    def _create_action_tab(self):
        """创建动作设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 鼠标设置
        mouse_group = QGroupBox("鼠标设置")
        mouse_layout = QFormLayout(mouse_group)
        
        # 鼠标移动速度
        self.mouse_speed_spin = QDoubleSpinBox()
        self.mouse_speed_spin.setRange(0.1, 5.0)
        self.mouse_speed_spin.setValue(1.0)
        self.mouse_speed_spin.setSingleStep(0.1)
        mouse_layout.addRow("鼠标移动速度:", self.mouse_speed_spin)
        
        # 点击前确认
        self.confirm_click_check = QCheckBox("点击前确认")
        mouse_layout.addRow("", self.confirm_click_check)
        
        # 确认超时
        self.confirm_timeout_spin = QDoubleSpinBox()
        self.confirm_timeout_spin.setRange(1.0, 10.0)
        self.confirm_timeout_spin.setValue(3.0)
        self.confirm_timeout_spin.setSingleStep(0.5)
        self.confirm_timeout_spin.setSuffix(" 秒")
        mouse_layout.addRow("确认超时:", self.confirm_timeout_spin)
        
        layout.addWidget(mouse_group)
        
        # 键盘设置
        keyboard_group = QGroupBox("键盘设置")
        keyboard_layout = QFormLayout(keyboard_group)
        
        # 按键延迟
        self.key_delay_spin = QDoubleSpinBox()
        self.key_delay_spin.setRange(0.0, 1.0)
        self.key_delay_spin.setValue(0.1)
        self.key_delay_spin.setSingleStep(0.05)
        self.key_delay_spin.setSuffix(" 秒")
        keyboard_layout.addRow("按键延迟:", self.key_delay_spin)
        
        layout.addWidget(keyboard_group)
        
        # 脚本设置
        script_group = QGroupBox("脚本设置")
        script_layout = QFormLayout(script_group)
        
        # 允许命令
        self.allow_commands_check = QCheckBox("允许执行系统命令")
        script_layout.addRow("", self.allow_commands_check)
        
        # 命令超时
        self.command_timeout_spin = QDoubleSpinBox()
        self.command_timeout_spin.setRange(1.0, 60.0)
        self.command_timeout_spin.setValue(10.0)
        self.command_timeout_spin.setSingleStep(1.0)
        self.command_timeout_spin.setSuffix(" 秒")
        script_layout.addRow("命令超时:", self.command_timeout_spin)
        
        layout.addWidget(script_group)
        
        layout.addStretch()
        return tab
    
    def _create_system_tab(self):
        """创建系统设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 启动设置
        startup_group = QGroupBox("启动设置")
        startup_layout = QFormLayout(startup_group)
        
        # 自动启动
        self.auto_start_check = QCheckBox("启动时自动开始监控")
        startup_layout.addRow("", self.auto_start_check)
        
        layout.addWidget(startup_group)
        
        # 日志设置
        log_group = QGroupBox("日志设置")
        log_layout = QFormLayout(log_group)
        
        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level_combo.setCurrentIndex(1)  # 默认INFO
        log_layout.addRow("日志级别:", self.log_level_combo)
        
        # 最大日志文件
        self.max_log_spin = QSpinBox()
        self.max_log_spin.setRange(1, 100)
        self.max_log_spin.setValue(10)
        log_layout.addRow("最大日志文件数:", self.max_log_spin)
        
        layout.addWidget(log_group)
        
        # 通知设置
        notify_group = QGroupBox("通知设置")
        notify_layout = QFormLayout(notify_group)
        
        # 启用通知
        self.enable_notify_check = QCheckBox("启用系统通知")
        notify_layout.addRow("", self.enable_notify_check)
        
        layout.addWidget(notify_group)
        
        # 高级设置
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QFormLayout(advanced_group)
        
        # 自动保存
        self.auto_save_check = QCheckBox("自动保存配置")
        advanced_layout.addRow("", self.auto_save_check)
        
        # 保存间隔
        self.save_interval_spin = QSpinBox()
        self.save_interval_spin.setRange(30, 3600)
        self.save_interval_spin.setValue(300)
        self.save_interval_spin.setSingleStep(30)
        self.save_interval_spin.setSuffix(" 秒")
        advanced_layout.addRow("保存间隔:", self.save_interval_spin)
        
        layout.addWidget(advanced_group)
        
        layout.addStretch()
        return tab
    
    def _update_accuracy_label(self, value):
        """更新精度标签"""
        self.accuracy_label.setText(f"{value}%")
    
    def _load_settings(self):
        """加载设置"""
        if not self.settings:
            return
            
        # OCR设置
        ocr = self.settings.get('ocr', {})
        if ocr:
            # 语言
            lang_map = {
                'chi_sim': 0,  # 中文简体
                'chi_tra': 1,  # 中文繁体
                'eng': 2,      # 英语
                'jpn': 3,      # 日语
                'kor': 4       # 韩语
            }
            self.ocr_lang_combo.setCurrentIndex(lang_map.get(ocr.get('language'), 0))
            
            # PSM模式
            psm_map = {
                3: 0,  # 全自动页面分割
                4: 1,  # 假设单列文本
                6: 2,  # 假设统一文本块
                7: 3,  # 单行文本
                8: 4,  # 单词
                10: 5  # 单个字符
            }
            self.ocr_psm_combo.setCurrentIndex(psm_map.get(ocr.get('psm'), 3))
            
            # OEM引擎
            oem_map = {
                1: 0,  # LSTM引擎
                0: 1,  # 传统引擎
                2: 2,  # 传统+LSTM
                3: 3   # 自动选择
            }
            self.ocr_oem_combo.setCurrentIndex(oem_map.get(ocr.get('oem'), 0))
            
            # 预处理设置
            self.preprocess_check.setChecked(ocr.get('preprocess', True))
            self.accuracy_slider.setValue(ocr.get('accuracy', 80))
            self._update_accuracy_label(self.accuracy_slider.value())
            
            # 高级设置
            self.autocorrect_check.setChecked(ocr.get('autocorrect', False))
            self.cache_check.setChecked(ocr.get('use_cache', True))
            self.cache_size_spin.setValue(ocr.get('cache_size', 50))
        
        # 监控设置
        monitor = self.settings.get('monitor', {})
        if monitor:
            self.refresh_rate_spin.setValue(monitor.get('refresh_rate', 1000))
            self.adaptive_refresh_check.setChecked(monitor.get('adaptive_refresh', True))
            self.min_refresh_spin.setValue(monitor.get('min_refresh_rate', 200))
            self.max_refresh_spin.setValue(monitor.get('max_refresh_rate', 2000))
            
            # 规则设置
            combine_map = {
                'AND': 0,
                'OR': 1,
                'CUSTOM': 2
            }
            self.rule_combine_combo.setCurrentIndex(combine_map.get(monitor.get('rule_combination'), 0))
            self.rule_threshold_spin.setValue(monitor.get('text_match_threshold', 0.8))
            
            # 保存设置
            self.save_images_check.setChecked(monitor.get('save_images', False))
            self.save_dir_edit.setText(monitor.get('save_dir', './captures'))
        
        # 动作设置
        action = self.settings.get('action', {})
        if action:
            self.mouse_speed_spin.setValue(action.get('mouse_speed', 1.0))
            self.confirm_click_check.setChecked(action.get('confirm_before_click', True))
            self.confirm_timeout_spin.setValue(action.get('confirmation_timeout', 3.0))
            self.key_delay_spin.setValue(action.get('default_delay', 0.1))
            self.allow_commands_check.setChecked(action.get('allow_commands', False))
            self.command_timeout_spin.setValue(action.get('command_timeout', 10.0))
        
        # 系统设置
        system = self.settings.get('system', {})
        if system:
            self.auto_start_check.setChecked(system.get('auto_start', False))
            
            # 日志设置
            log_level_map = {
                'DEBUG': 0,
                'INFO': 1,
                'WARNING': 2,
                'ERROR': 3,
                'CRITICAL': 4
            }
            self.log_level_combo.setCurrentIndex(log_level_map.get(system.get('log_level'), 1))
            self.max_log_spin.setValue(system.get('max_log_files', 10))
            
            # 通知设置
            self.enable_notify_check.setChecked(system.get('enable_notification', True))
            
            # 高级设置
            self.auto_save_check.setChecked(system.get('auto_save', True))
            self.save_interval_spin.setValue(system.get('save_interval', 300))
    
    def _on_reset_clicked(self):
        """重置按钮点击事件处理"""
        # OCR设置
        self.ocr_lang_combo.setCurrentIndex(0)  # 中文简体
        self.ocr_psm_combo.setCurrentIndex(3)   # 单行文本
        self.ocr_oem_combo.setCurrentIndex(0)   # LSTM引擎
        self.preprocess_check.setChecked(True)
        self.accuracy_slider.setValue(80)
        self.autocorrect_check.setChecked(False)
        self.cache_check.setChecked(True)
        self.cache_size_spin.setValue(50)
        
        # 监控设置
        self.refresh_rate_spin.setValue(1000)
        self.adaptive_refresh_check.setChecked(True)
        self.min_refresh_spin.setValue(200)
        self.max_refresh_spin.setValue(2000)
        self.rule_combine_combo.setCurrentIndex(0)  # AND
        self.rule_threshold_spin.setValue(0.8)
        self.save_images_check.setChecked(False)
        self.save_dir_edit.setText('./captures')
        
        # 动作设置
        self.mouse_speed_spin.setValue(1.0)
        self.confirm_click_check.setChecked(True)
        self.confirm_timeout_spin.setValue(3.0)
        self.key_delay_spin.setValue(0.1)
        self.allow_commands_check.setChecked(False)
        self.command_timeout_spin.setValue(10.0)
        
        # 系统设置
        self.auto_start_check.setChecked(False)
        self.log_level_combo.setCurrentIndex(1)  # INFO
        self.max_log_spin.setValue(10)
        self.enable_notify_check.setChecked(True)
        self.auto_save_check.setChecked(True)
        self.save_interval_spin.setValue(300)
    
    def _on_save_clicked(self):
        """保存按钮点击事件处理"""
        settings = {}
        
        # OCR设置
        settings['ocr'] = {
            'language': ['chi_sim', 'chi_tra', 'eng', 'jpn', 'kor'][self.ocr_lang_combo.currentIndex()],
            'psm': [3, 4, 6, 7, 8, 10][self.ocr_psm_combo.currentIndex()],
            'oem': [1, 0, 2, 3][self.ocr_oem_combo.currentIndex()],
            'preprocess': self.preprocess_check.isChecked(),
            'accuracy': self.accuracy_slider.value(),
            'autocorrect': self.autocorrect_check.isChecked(),
            'use_cache': self.cache_check.isChecked(),
            'cache_size': self.cache_size_spin.value()
        }
        
        # 监控设置
        settings['monitor'] = {
            'refresh_rate': self.refresh_rate_spin.value(),
            'adaptive_refresh': self.adaptive_refresh_check.isChecked(),
            'min_refresh_rate': self.min_refresh_spin.value(),
            'max_refresh_rate': self.max_refresh_spin.value(),
            'rule_combination': ['AND', 'OR', 'CUSTOM'][self.rule_combine_combo.currentIndex()],
            'text_match_threshold': self.rule_threshold_spin.value(),
            'save_images': self.save_images_check.isChecked(),
            'save_dir': self.save_dir_edit.text()
        }
        
        # 动作设置
        settings['action'] = {
            'mouse_speed': self.mouse_speed_spin.value(),
            'confirm_before_click': self.confirm_click_check.isChecked(),
            'confirmation_timeout': self.confirm_timeout_spin.value(),
            'default_delay': self.key_delay_spin.value(),
            'allow_commands': self.allow_commands_check.isChecked(),
            'command_timeout': self.command_timeout_spin.value()
        }
        
        # 系统设置
        settings['system'] = {
            'auto_start': self.auto_start_check.isChecked(),
            'log_level': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'][self.log_level_combo.currentIndex()],
            'max_log_files': self.max_log_spin.value(),
            'enable_notification': self.enable_notify_check.isChecked(),
            'auto_save': self.auto_save_check.isChecked(),
            'save_interval': self.save_interval_spin.value()
        }
        
        # 发送设置保存信号
        self.settings_saved.emit(settings)
        
        # 关闭对话框
        self.accept()
