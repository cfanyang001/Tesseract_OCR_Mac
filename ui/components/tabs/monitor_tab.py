from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, 
    QComboBox, QLineEdit, QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QSpinBox, QTextEdit
)
from PyQt5.QtCore import Qt


class MonitorTab(QWidget):
    """监控设置标签页，包含规则和触发条件设置"""
    
    def __init__(self):
        super().__init__()
        
        # 控制器引用，将由MonitorController设置
        self.controller = None
        
        # 创建主布局
        self.layout = QVBoxLayout(self)
        
        # 创建监控状态区域
        self.status_group = self.create_status_group()
        self.layout.addWidget(self.status_group)
        
        # 创建监控配置区域
        self.monitor_config_group = self.create_monitor_config_group()
        self.layout.addWidget(self.monitor_config_group)
        
        # 创建规则设置区域
        self.rule_group = self.create_rule_group()
        self.layout.addWidget(self.rule_group)
        
        # 创建规则列表区域
        self.rule_list_group = self.create_rule_list_group()
        self.layout.addWidget(self.rule_list_group)
        
        # 创建动作设置区域
        self.action_group = self.create_action_group()
        self.layout.addWidget(self.action_group)
    
    def create_status_group(self):
        """创建监控状态组"""
        group = QGroupBox("监控状态")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 6)
        
        # 监控控制按钮和状态标签将由MonitorController添加
        
        return group
    
    def create_monitor_config_group(self):
        """创建监控配置组"""
        group = QGroupBox("监控设置")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(10)
        
        # 监控间隔
        interval_layout = QHBoxLayout()
        interval_layout.setSpacing(5)
        interval_layout.addWidget(QLabel("监控间隔(秒):"))
        self.interval_combo = QComboBox()
        self.interval_combo.setObjectName("interval_combo")
        self.interval_combo.addItems(["1", "2", "3", "5", "10"])
        self.interval_combo.setCurrentText("2")
        self.interval_combo.setFixedWidth(60)
        interval_layout.addWidget(self.interval_combo)
        layout.addLayout(interval_layout)
        
        # 匹配模式
        match_mode_layout = QHBoxLayout()
        match_mode_layout.setSpacing(5)
        match_mode_layout.addWidget(QLabel("匹配模式:"))
        self.match_mode_combo = QComboBox()
        self.match_mode_combo.setObjectName("match_mode_combo")
        self.match_mode_combo.addItems(["包含匹配", "精确匹配", "正则匹配"])
        self.match_mode_combo.setCurrentText("包含匹配")
        self.match_mode_combo.setFixedWidth(100)
        match_mode_layout.addWidget(self.match_mode_combo)
        layout.addLayout(match_mode_layout)
        
        return group
    
    def create_rule_group(self):
        """创建规则设置组"""
        group = QGroupBox("规则设置")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)
        
        # 规则类型选择和内容输入水平布局
        rule_input_layout = QHBoxLayout()
        rule_input_layout.setSpacing(5)
        
        # 规则类型选择
        rule_type_layout = QHBoxLayout()
        rule_type_layout.setSpacing(5)
        rule_type_layout.addWidget(QLabel("规则类型:"))
        rule_type_combo = QComboBox()
        rule_type_combo.setObjectName("rule_type_combo")
        rule_type_combo.addItems(["包含文本", "精确匹配", "正则表达式", "数值比较"])
        rule_type_combo.setFixedWidth(100)
        rule_type_layout.addWidget(rule_type_combo)
        rule_input_layout.addLayout(rule_type_layout)
        
        # 规则内容
        rule_content_layout = QHBoxLayout()
        rule_content_layout.setSpacing(5)
        rule_content_layout.addWidget(QLabel("规则内容:"))
        rule_content_edit = QLineEdit()
        rule_content_edit.setObjectName("rule_content_edit")
        rule_content_edit.setPlaceholderText("输入要匹配的文本或表达式")
        rule_content_layout.addWidget(rule_content_edit)
        rule_input_layout.addLayout(rule_content_layout, 1)  # 内容输入框占据更多空间
        
        layout.addLayout(rule_input_layout)
        
        # 规则选项和添加按钮的水平布局
        options_button_layout = QHBoxLayout()
        
        # 规则选项
        options_layout = QHBoxLayout()
        options_layout.setSpacing(10)
        case_sensitive_check = QCheckBox("区分大小写")
        case_sensitive_check.setObjectName("case_sensitive_check")
        options_layout.addWidget(case_sensitive_check)
        
        trim_check = QCheckBox("忽略首尾空格")
        trim_check.setObjectName("trim_check")
        trim_check.setChecked(True)
        options_layout.addWidget(trim_check)
        
        options_button_layout.addLayout(options_layout)
        
        # 添加弹性空间，将按钮推到右侧
        options_button_layout.addStretch(1)
        
        # 添加规则按钮
        add_rule_btn = QPushButton("添加规则")
        add_rule_btn.setObjectName("add_rule_btn")
        add_rule_btn.setMinimumHeight(25)
        add_rule_btn.setFixedWidth(100)
        add_rule_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        options_button_layout.addWidget(add_rule_btn)
        
        layout.addLayout(options_button_layout)
        
        return group
    
    def create_rule_list_group(self):
        """创建规则列表组"""
        group = QGroupBox("规则列表")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)
        
        # 规则表格
        self.rule_table = QTableWidget(0, 5)
        self.rule_table.setObjectName("rule_table")
        self.rule_table.setHorizontalHeaderLabels(["编号", "类型", "内容", "选项", "操作"])
        self.rule_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.rule_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.rule_table.setMaximumHeight(150)
        layout.addWidget(self.rule_table)
        
        # 规则组合和自定义表达式的水平布局
        rule_combination_layout = QHBoxLayout()
        rule_combination_layout.setSpacing(5)
        
        # 规则组合
        combination_layout = QHBoxLayout()
        combination_layout.addWidget(QLabel("规则组合:"))
        combination_combo = QComboBox()
        combination_combo.setObjectName("combination_combo")
        combination_combo.addItems(["全部满足 (AND)", "任一满足 (OR)", "自定义组合"])
        combination_combo.setFixedWidth(150)
        combination_layout.addWidget(combination_combo)
        rule_combination_layout.addLayout(combination_layout)
        
        # 自定义表达式
        custom_expr_layout = QHBoxLayout()
        custom_expr_layout.addWidget(QLabel("表达式:"))
        custom_expr_edit = QLineEdit()
        custom_expr_edit.setObjectName("custom_expr_edit")
        custom_expr_edit.setPlaceholderText("例如: (1 AND 2) OR 3")
        custom_expr_edit.setEnabled(False)
        custom_expr_layout.addWidget(custom_expr_edit)
        rule_combination_layout.addLayout(custom_expr_layout, 1)
        
        layout.addLayout(rule_combination_layout)
        
        return group
    
    def create_action_group(self):
        """创建动作设置组"""
        group = QGroupBox("触发动作")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)
        
        # 触发条件和动作类型水平布局
        trigger_action_layout = QHBoxLayout()
        trigger_action_layout.setSpacing(10)
        
        # 触发条件
        trigger_layout = QHBoxLayout()
        trigger_layout.setSpacing(5)
        trigger_layout.addWidget(QLabel("触发条件:"))
        trigger_combo = QComboBox()
        trigger_combo.setObjectName("trigger_combo")
        trigger_combo.addItems(["规则满足时", "规则不满足时", "规则状态改变时"])
        trigger_combo.setFixedWidth(120)
        trigger_layout.addWidget(trigger_combo)
        trigger_action_layout.addLayout(trigger_layout)
        
        # 触发延迟
        delay_layout = QHBoxLayout()
        delay_layout.setSpacing(5)
        delay_layout.addWidget(QLabel("延迟:"))
        delay_spin = QSpinBox()
        delay_spin.setObjectName("delay_spin")
        delay_spin.setRange(0, 60)
        delay_spin.setSuffix(" 秒")
        delay_spin.setFixedWidth(70)
        delay_layout.addWidget(delay_spin)
        trigger_action_layout.addLayout(delay_layout)
        
        # 动作选择
        action_layout = QHBoxLayout()
        action_layout.setSpacing(5)
        action_layout.addWidget(QLabel("执行动作:"))
        action_combo = QComboBox()
        action_combo.setObjectName("action_combo")
        action_combo.addItems(["发送通知", "执行按键", "点击鼠标", "运行脚本", "自定义动作"])
        action_combo.setFixedWidth(100)
        action_layout.addWidget(action_combo)
        trigger_action_layout.addLayout(action_layout)
        
        layout.addLayout(trigger_action_layout)
        
        # 鼠标点击设置区域（默认隐藏）
        self.mouse_settings_group = QGroupBox("鼠标点击设置")
        self.mouse_settings_group.setObjectName("mouse_settings_group")
        self.mouse_settings_group.setVisible(False)
        mouse_settings_layout = QVBoxLayout(self.mouse_settings_group)
        mouse_settings_layout.setContentsMargins(6, 6, 6, 6)
        mouse_settings_layout.setSpacing(8)
        
        # 坐标选择和点击设置分两行显示
        # 坐标选择
        coords_layout = QHBoxLayout()
        coords_layout.setSpacing(8)
        
        # X坐标
        x_layout = QHBoxLayout()
        x_layout.setSpacing(3)
        x_layout.addWidget(QLabel("X:"))
        self.mouse_x_spin = QSpinBox()
        self.mouse_x_spin.setObjectName("mouse_x_spin")
        self.mouse_x_spin.setRange(0, 9999)
        self.mouse_x_spin.setFixedWidth(70)
        x_layout.addWidget(self.mouse_x_spin)
        coords_layout.addLayout(x_layout)
        
        # Y坐标
        y_layout = QHBoxLayout()
        y_layout.setSpacing(3)
        y_layout.addWidget(QLabel("Y:"))
        self.mouse_y_spin = QSpinBox()
        self.mouse_y_spin.setObjectName("mouse_y_spin")
        self.mouse_y_spin.setRange(0, 9999)
        self.mouse_y_spin.setFixedWidth(70)
        y_layout.addWidget(self.mouse_y_spin)
        coords_layout.addLayout(y_layout)
        
        # 选择区域按钮
        self.select_mouse_pos_btn = QPushButton("选择坐标")
        self.select_mouse_pos_btn.setObjectName("select_mouse_pos_btn")
        self.select_mouse_pos_btn.setFixedWidth(80)
        self.select_mouse_pos_btn.setStyleSheet("QPushButton { background-color: #007BFF; color: white; }")
        coords_layout.addWidget(self.select_mouse_pos_btn)
        
        # 添加弹性空间填充
        coords_layout.addStretch(1)
        
        mouse_settings_layout.addLayout(coords_layout)
        
        # 点击设置
        click_settings_layout = QHBoxLayout()
        click_settings_layout.setSpacing(8)
        
        # 点击次数
        click_count_layout = QHBoxLayout()
        click_count_layout.setSpacing(3)
        click_count_layout.addWidget(QLabel("点击次数:"))
        self.click_count_spin = QSpinBox()
        self.click_count_spin.setObjectName("click_count_spin")
        self.click_count_spin.setRange(1, 100)
        self.click_count_spin.setValue(1)
        self.click_count_spin.setFixedWidth(50)
        click_count_layout.addWidget(self.click_count_spin)
        click_settings_layout.addLayout(click_count_layout)
        
        # 点击间隔（冷却时间）
        click_interval_layout = QHBoxLayout()
        click_interval_layout.setSpacing(3)
        click_interval_layout.addWidget(QLabel("间隔时间:"))
        self.click_interval_spin = QSpinBox()
        self.click_interval_spin.setObjectName("click_interval_spin")
        self.click_interval_spin.setRange(0, 10000)
        self.click_interval_spin.setValue(100)
        self.click_interval_spin.setSuffix(" 毫秒")
        self.click_interval_spin.setFixedWidth(80)
        click_interval_layout.addWidget(self.click_interval_spin)
        click_settings_layout.addLayout(click_interval_layout)
        
        # 鼠标按钮选择
        button_layout = QHBoxLayout()
        button_layout.setSpacing(3)
        button_layout.addWidget(QLabel("鼠标按钮:"))
        self.mouse_button_combo = QComboBox()
        self.mouse_button_combo.setObjectName("mouse_button_combo")
        self.mouse_button_combo.addItems(["左键", "右键", "中键"])
        self.mouse_button_combo.setFixedWidth(60)
        button_layout.addWidget(self.mouse_button_combo)
        click_settings_layout.addLayout(button_layout)
        
        # 添加弹性空间填充
        click_settings_layout.addStretch(1)
        
        mouse_settings_layout.addLayout(click_settings_layout)
        
        layout.addWidget(self.mouse_settings_group)
        
        # 动作参数和添加按钮的水平布局
        param_button_layout = QHBoxLayout()
        param_button_layout.setSpacing(8)
        
        # 动作参数
        action_param_layout = QHBoxLayout()
        action_param_layout.setSpacing(5)
        action_param_layout.addWidget(QLabel("动作参数:"))
        self.action_param_edit = QLineEdit()
        self.action_param_edit.setObjectName("action_param_edit")
        self.action_param_edit.setPlaceholderText("输入动作参数...")
        action_param_layout.addWidget(self.action_param_edit)
        param_button_layout.addLayout(action_param_layout, 1)
        
        # 添加动作按钮
        add_action_btn = QPushButton("添加动作")
        add_action_btn.setObjectName("add_action_btn")
        add_action_btn.setMinimumHeight(25)
        add_action_btn.setFixedWidth(100)
        add_action_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        param_button_layout.addWidget(add_action_btn)
        
        layout.addLayout(param_button_layout)
        
        return group
