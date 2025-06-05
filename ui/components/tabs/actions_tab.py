from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QSpinBox,
    QLineEdit, QTextEdit, QSplitter, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QSize


class ActionsTab(QWidget):
    """动作标签页，用于管理自动化动作"""
    
    def __init__(self):
        super().__init__()
        
        # 创建主布局
        self.layout = QVBoxLayout(self)
        
        # 创建水平分割器
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # 创建左侧动作类型面板
        self.action_types_panel = self.create_action_types_panel()
        splitter.addWidget(self.action_types_panel)
        
        # 创建右侧动作编辑面板
        self.action_edit_panel = self.create_action_edit_panel()
        splitter.addWidget(self.action_edit_panel)
        
        # 设置分割器比例
        splitter.setSizes([200, 600])
        
        # 添加分割器到主布局
        self.layout.addWidget(splitter)
        
        # 创建动作列表面板
        self.action_list_panel = self.create_action_list_panel()
        self.layout.addWidget(self.action_list_panel)
    
    def create_action_types_panel(self):
        """创建动作类型面板"""
        group = QGroupBox("动作类型")
        layout = QVBoxLayout(group)
        
        # 动作类型列表
        self.action_types_list = QListWidget()
        self.action_types_list.addItems([
            "键盘输入",
            "鼠标点击",
            "鼠标移动",
            "系统通知",
            "延时等待",
            "条件判断",
            "循环执行",
            "运行脚本",
            "自定义动作"
        ])
        layout.addWidget(self.action_types_list)
        
        # 添加新类型按钮
        add_type_btn = QPushButton("添加自定义类型")
        layout.addWidget(add_type_btn)
        
        return group
    
    def create_action_edit_panel(self):
        """创建动作编辑面板"""
        group = QGroupBox("动作编辑")
        layout = QVBoxLayout(group)
        
        # 动作名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("动作名称:"))
        name_edit = QLineEdit()
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)
        
        # 动作类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("动作类型:"))
        type_combo = QComboBox()
        type_combo.addItems([
            "键盘输入",
            "鼠标点击",
            "鼠标移动",
            "系统通知",
            "延时等待",
            "条件判断",
            "循环执行",
            "运行脚本",
            "自定义动作"
        ])
        type_layout.addWidget(type_combo)
        layout.addLayout(type_layout)
        
        # 动作参数
        layout.addWidget(QLabel("动作参数:"))
        params_edit = QTextEdit()
        params_edit.setPlaceholderText("输入动作参数...")
        params_edit.setMinimumHeight(100)
        layout.addWidget(params_edit)
        
        # 动作描述
        layout.addWidget(QLabel("动作描述:"))
        desc_edit = QTextEdit()
        desc_edit.setPlaceholderText("输入动作描述...")
        desc_edit.setMaximumHeight(80)
        layout.addWidget(desc_edit)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("保存动作")
        test_btn = QPushButton("测试动作")
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(test_btn)
        layout.addLayout(buttons_layout)
        
        return group
    
    def create_action_list_panel(self):
        """创建动作列表面板"""
        group = QGroupBox("已保存动作")
        layout = QVBoxLayout(group)
        
        # 动作表格
        self.actions_table = QTableWidget(0, 4)
        self.actions_table.setHorizontalHeaderLabels(["动作名称", "类型", "描述", "操作"])
        self.actions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.actions_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.actions_table)
        
        # 按钮区域
        buttons_layout = QHBoxLayout()
        import_btn = QPushButton("导入动作")
        export_btn = QPushButton("导出动作")
        delete_btn = QPushButton("删除动作")
        buttons_layout.addWidget(import_btn)
        buttons_layout.addWidget(export_btn)
        buttons_layout.addWidget(delete_btn)
        layout.addLayout(buttons_layout)
        
        return group
