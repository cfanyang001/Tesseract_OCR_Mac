from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton,
    QGroupBox, QSpinBox, QDoubleSpinBox, QFormLayout,
    QRadioButton, QButtonGroup, QFrame, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QSize
from PyQt5.QtGui import QIcon

from core.rule_matcher import Rule
from loguru import logger


class RuleEditor(QWidget):
    """规则编辑器，用于创建和编辑监控规则"""
    
    # 信号
    rule_created = pyqtSignal(object)  # 规则创建信号
    rule_updated = pyqtSignal(object)  # 规则更新信号
    rule_deleted = pyqtSignal(str)     # 规则删除信号
    
    def __init__(self, parent=None):
        """初始化规则编辑器"""
        super().__init__(parent)
        
        # 当前规则
        self.current_rule = None
        
        # 创建UI
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 规则类型选择
        type_group = QGroupBox("规则类型")
        type_layout = QVBoxLayout(type_group)
        
        self.rule_type_combo = QComboBox()
        self.rule_type_combo.addItems([
            "包含文本 (文本包含指定内容)",
            "精确匹配 (文本完全相同)",
            "正则表达式 (正则匹配文本)",
            "数值比较 (比较文本中的数值)",
            "不包含文本 (文本不包含指定内容)",
            "文本变化 (文本内容发生变化)"
        ])
        self.rule_type_combo.currentIndexChanged.connect(self._on_rule_type_changed)
        type_layout.addWidget(self.rule_type_combo)
        
        main_layout.addWidget(type_group)
        
        # 规则内容编辑
        content_group = QGroupBox("规则内容")
        content_layout = QVBoxLayout(content_group)
        
        self.content_label = QLabel("匹配文本:")
        content_layout.addWidget(self.content_label)
        
        self.content_edit = QLineEdit()
        self.content_edit.setPlaceholderText("输入要匹配的文本")
        content_layout.addWidget(self.content_edit)
        
        # 数值比较操作符（初始隐藏）
        self.numeric_op_frame = QFrame()
        numeric_op_layout = QHBoxLayout(self.numeric_op_frame)
        self.numeric_op_label = QLabel("比较操作符:")
        numeric_op_layout.addWidget(self.numeric_op_label)
        
        self.numeric_op_combo = QComboBox()
        self.numeric_op_combo.addItems([
            "等于 (==)",
            "不等于 (!=)",
            "大于 (>)",
            "大于等于 (>=)",
            "小于 (<)",
            "小于等于 (<=)"
        ])
        numeric_op_layout.addWidget(self.numeric_op_combo)
        
        content_layout.addWidget(self.numeric_op_frame)
        self.numeric_op_frame.setVisible(False)
        
        main_layout.addWidget(content_group)
        
        # 规则参数
        params_group = QGroupBox("规则参数")
        params_layout = QVBoxLayout(params_group)
        
        # 大小写敏感
        self.case_sensitive_check = QCheckBox("区分大小写")
        params_layout.addWidget(self.case_sensitive_check)
        
        main_layout.addWidget(params_group)
        
        # 规则描述
        desc_group = QGroupBox("规则描述")
        desc_layout = QVBoxLayout(desc_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("给规则起一个描述性的名称")
        desc_layout.addWidget(self.name_edit)
        
        main_layout.addWidget(desc_group)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("保存规则")
        self.save_btn.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(self.save_btn)
        
        self.delete_btn = QPushButton("删除规则")
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        button_layout.addWidget(self.delete_btn)
        self.delete_btn.setEnabled(False)  # 初始状态禁用删除按钮
        
        main_layout.addLayout(button_layout)
        main_layout.addStretch()
    
    def _on_rule_type_changed(self, index):
        """规则类型改变的事件处理"""
        # 重置UI
        self.content_label.setText("匹配文本:")
        self.content_edit.setPlaceholderText("输入要匹配的文本")
        self.numeric_op_frame.setVisible(False)
        
        # 根据规则类型调整UI
        if index == 0:  # 包含文本
            self.content_label.setText("包含文本:")
            self.content_edit.setPlaceholderText("输入要检测的文本内容")
        
        elif index == 1:  # 精确匹配
            self.content_label.setText("匹配文本:")
            self.content_edit.setPlaceholderText("输入要完全匹配的文本")
        
        elif index == 2:  # 正则表达式
            self.content_label.setText("正则表达式:")
            self.content_edit.setPlaceholderText("输入正则表达式，如: [0-9]+")
        
        elif index == 3:  # 数值比较
            self.content_label.setText("比较数值:")
            self.content_edit.setPlaceholderText("输入比较的数值")
            self.numeric_op_frame.setVisible(True)
        
        elif index == 4:  # 不包含文本
            self.content_label.setText("不包含文本:")
            self.content_edit.setPlaceholderText("输入不应出现的文本内容")
        
        elif index == 5:  # 文本变化
            self.content_label.setText("文本描述:")
            self.content_edit.setPlaceholderText("(可选) 输入规则描述")
    
    def set_rule(self, rule: Rule):
        """设置当前编辑的规则
        
        Args:
            rule: 规则对象
        """
        self.current_rule = rule
        
        if rule is None:
            # 清空表单
            self.rule_type_combo.setCurrentIndex(0)
            self.content_edit.clear()
            self.case_sensitive_check.setChecked(False)
            self.name_edit.clear()
            self.delete_btn.setEnabled(False)
            return
        
        # 填充表单
        # 设置规则类型
        if rule.type == Rule.TYPE_CONTAINS:
            self.rule_type_combo.setCurrentIndex(0)
        elif rule.type == Rule.TYPE_EXACT:
            self.rule_type_combo.setCurrentIndex(1)
        elif rule.type == Rule.TYPE_REGEX:
            self.rule_type_combo.setCurrentIndex(2)
        elif rule.type == Rule.TYPE_NUMERIC:
            self.rule_type_combo.setCurrentIndex(3)
            # 设置数值操作符
            op = rule.params.get('operator', Rule.OP_EQ)
            if op == Rule.OP_EQ:
                self.numeric_op_combo.setCurrentIndex(0)
            elif op == Rule.OP_NE:
                self.numeric_op_combo.setCurrentIndex(1)
            elif op == Rule.OP_GT:
                self.numeric_op_combo.setCurrentIndex(2)
            elif op == Rule.OP_GE:
                self.numeric_op_combo.setCurrentIndex(3)
            elif op == Rule.OP_LT:
                self.numeric_op_combo.setCurrentIndex(4)
            elif op == Rule.OP_LE:
                self.numeric_op_combo.setCurrentIndex(5)
        elif rule.type == Rule.TYPE_NOT_CONTAINS:
            self.rule_type_combo.setCurrentIndex(4)
        elif rule.type == Rule.TYPE_CHANGED:
            self.rule_type_combo.setCurrentIndex(5)
        
        # 设置规则内容
        self.content_edit.setText(rule.content)
        
        # 设置参数
        self.case_sensitive_check.setChecked(rule.params.get('case_sensitive', False))
        
        # 设置名称
        self.name_edit.setText(rule.name)
        
        # 启用删除按钮
        self.delete_btn.setEnabled(True)
    
    def _on_save_clicked(self):
        """保存按钮点击事件处理"""
        # 获取规则类型
        rule_type_index = self.rule_type_combo.currentIndex()
        rule_type = Rule.TYPE_CONTAINS  # 默认为包含文本
        
        if rule_type_index == 0:
            rule_type = Rule.TYPE_CONTAINS
        elif rule_type_index == 1:
            rule_type = Rule.TYPE_EXACT
        elif rule_type_index == 2:
            rule_type = Rule.TYPE_REGEX
        elif rule_type_index == 3:
            rule_type = Rule.TYPE_NUMERIC
        elif rule_type_index == 4:
            rule_type = Rule.TYPE_NOT_CONTAINS
        elif rule_type_index == 5:
            rule_type = Rule.TYPE_CHANGED
        
        # 获取规则内容
        content = self.content_edit.text()
        
        # 获取参数
        params = {
            'case_sensitive': self.case_sensitive_check.isChecked()
        }
        
        # 对于数值比较规则，添加操作符
        if rule_type == Rule.TYPE_NUMERIC:
            op_index = self.numeric_op_combo.currentIndex()
            if op_index == 0:
                params['operator'] = Rule.OP_EQ
            elif op_index == 1:
                params['operator'] = Rule.OP_NE
            elif op_index == 2:
                params['operator'] = Rule.OP_GT
            elif op_index == 3:
                params['operator'] = Rule.OP_GE
            elif op_index == 4:
                params['operator'] = Rule.OP_LT
            elif op_index == 5:
                params['operator'] = Rule.OP_LE
        
        # 获取名称
        name = self.name_edit.text()
        
        try:
            if self.current_rule:
                # 更新现有规则
                self.current_rule.type = rule_type
                self.current_rule.content = content
                self.current_rule.params = params
                self.current_rule.name = name
                
                self.rule_updated.emit(self.current_rule)
                logger.info(f"规则已更新: {self.current_rule.id}")
            else:
                # 创建新规则
                new_rule = Rule(rule_type=rule_type, content=content, params=params)
                new_rule.name = name
                
                self.rule_created.emit(new_rule)
                logger.info(f"规则已创建: {new_rule.id}")
                
                # 更新当前规则
                self.current_rule = new_rule
                self.delete_btn.setEnabled(True)
        except Exception as e:
            logger.error(f"保存规则失败: {e}")
    
    def _on_delete_clicked(self):
        """删除按钮点击事件处理"""
        if self.current_rule:
            rule_id = self.current_rule.id
            self.rule_deleted.emit(rule_id)
            logger.info(f"规则已删除: {rule_id}")
            
            # 清空表单
            self.set_rule(None)


class RuleEditorDialog(QDialog):
    """规则编辑器对话框"""
    
    rule_created = pyqtSignal(object)  # 规则创建信号
    rule_updated = pyqtSignal(object)  # 规则更新信号
    
    def __init__(self, parent=None, rule=None):
        """初始化规则编辑器对话框
        
        Args:
            parent: 父窗口
            rule: 要编辑的规则，为None时创建新规则
        """
        super().__init__(parent)
        
        self.setWindowTitle("编辑规则" if rule else "创建规则")
        self.setMinimumSize(QSize(500, 400))
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 创建规则编辑器
        self.rule_editor = RuleEditor(self)
        self.rule_editor.set_rule(rule)
        layout.addWidget(self.rule_editor)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 连接信号
        self.rule_editor.rule_created.connect(self.rule_created)
        self.rule_editor.rule_updated.connect(self.rule_updated)
    
    def get_rule(self):
        """获取当前规则"""
        return self.rule_editor.current_rule
