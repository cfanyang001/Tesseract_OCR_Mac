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
        
        # 监控控制按钮和状态标签将由MonitorController添加
        
        return group
    
    def create_rule_group(self):
        """创建规则设置组"""
        group = QGroupBox("规则设置")
        layout = QVBoxLayout(group)
        
        # 规则类型选择
        rule_type_layout = QHBoxLayout()
        rule_type_layout.addWidget(QLabel("规则类型:"))
        rule_type_combo = QComboBox()
        rule_type_combo.addItems(["包含文本", "精确匹配", "正则表达式", "数值比较"])
        rule_type_layout.addWidget(rule_type_combo)
        layout.addLayout(rule_type_layout)
        
        # 规则内容
        rule_content_layout = QHBoxLayout()
        rule_content_layout.addWidget(QLabel("规则内容:"))
        rule_content_edit = QLineEdit()
        rule_content_edit.setPlaceholderText("输入要匹配的文本或表达式")
        rule_content_layout.addWidget(rule_content_edit)
        layout.addLayout(rule_content_layout)
        
        # 规则选项
        options_layout = QHBoxLayout()
        case_sensitive_check = QCheckBox("区分大小写")
        options_layout.addWidget(case_sensitive_check)
        
        trim_check = QCheckBox("忽略首尾空格")
        trim_check.setChecked(True)
        options_layout.addWidget(trim_check)
        
        layout.addLayout(options_layout)
        
        # 添加规则按钮
        add_rule_btn = QPushButton("添加规则")
        add_rule_btn.setMinimumHeight(30)
        layout.addWidget(add_rule_btn)
        
        return group
    
    def create_rule_list_group(self):
        """创建规则列表组"""
        group = QGroupBox("规则列表")
        layout = QVBoxLayout(group)
        
        # 规则表格
        self.rule_table = QTableWidget(0, 4)
        self.rule_table.setHorizontalHeaderLabels(["类型", "内容", "选项", "操作"])
        self.rule_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.rule_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.rule_table)
        
        # 规则组合
        combination_layout = QHBoxLayout()
        combination_layout.addWidget(QLabel("规则组合:"))
        combination_combo = QComboBox()
        combination_combo.addItems(["全部满足 (AND)", "任一满足 (OR)", "自定义组合"])
        combination_layout.addWidget(combination_combo)
        layout.addLayout(combination_layout)
        
        # 自定义组合表达式
        custom_expr_edit = QLineEdit()
        custom_expr_edit.setPlaceholderText("例如: (1 AND 2) OR 3")
        custom_expr_edit.setEnabled(False)
        layout.addWidget(custom_expr_edit)
        
        return group
    
    def create_action_group(self):
        """创建动作设置组"""
        group = QGroupBox("触发动作")
        layout = QVBoxLayout(group)
        
        # 触发条件
        trigger_layout = QHBoxLayout()
        trigger_layout.addWidget(QLabel("触发条件:"))
        trigger_combo = QComboBox()
        trigger_combo.addItems(["规则满足时", "规则不满足时", "规则状态改变时"])
        trigger_layout.addWidget(trigger_combo)
        
        # 触发延迟
        trigger_layout.addWidget(QLabel("延迟:"))
        delay_spin = QSpinBox()
        delay_spin.setRange(0, 60)
        delay_spin.setSuffix(" 秒")
        trigger_layout.addWidget(delay_spin)
        
        layout.addLayout(trigger_layout)
        
        # 动作选择
        action_layout = QHBoxLayout()
        action_layout.addWidget(QLabel("执行动作:"))
        action_combo = QComboBox()
        action_combo.addItems(["发送通知", "执行按键", "点击鼠标", "运行脚本", "自定义动作"])
        action_layout.addWidget(action_combo)
        layout.addLayout(action_layout)
        
        # 动作参数
        action_param_edit = QTextEdit()
        action_param_edit.setPlaceholderText("输入动作参数...")
        action_param_edit.setMaximumHeight(80)
        layout.addWidget(action_param_edit)
        
        # 添加动作按钮
        add_action_btn = QPushButton("添加动作")
        add_action_btn.setMinimumHeight(30)
        layout.addWidget(add_action_btn)
        
        return group
