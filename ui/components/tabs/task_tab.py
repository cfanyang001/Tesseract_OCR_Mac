from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QSpinBox,
    QLineEdit, QCheckBox, QProgressBar, QSplitter
)
from PyQt5.QtCore import Qt, QSize


class TaskTab(QWidget):
    """任务管理标签页，用于管理监控任务"""
    
    def __init__(self):
        super().__init__()
        
        # 创建主布局
        self.layout = QVBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        
        # 创建任务列表区域
        self.task_list_group = self.create_task_list_group()
        splitter.addWidget(self.task_list_group)
        
        # 创建任务详情区域
        self.task_detail_group = self.create_task_detail_group()
        splitter.addWidget(self.task_detail_group)
        
        # 添加分割器到主布局
        self.layout.addWidget(splitter)
        
        # 创建控制按钮区域
        self.control_group = self.create_control_group()
        self.layout.addWidget(self.control_group)
    
    def create_task_list_group(self):
        """创建任务列表组"""
        group = QGroupBox("任务列表")
        layout = QVBoxLayout(group)
        
        # 任务表格
        self.task_table = QTableWidget(0, 5)
        self.task_table.setObjectName("task_table")
        self.task_table.setHorizontalHeaderLabels(["任务名称", "状态", "区域", "规则", "上次触发"])
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.task_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.task_table.setMinimumHeight(200)
        layout.addWidget(self.task_table)
        
        return group
    
    def create_task_detail_group(self):
        """创建任务详情组"""
        group = QGroupBox("任务详情")
        layout = QVBoxLayout(group)
        
        # 任务名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("任务名称:"))
        name_edit = QLineEdit()
        name_edit.setObjectName("name_edit")
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)
        
        # 任务状态
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("任务状态:"))
        status_combo = QComboBox()
        status_combo.setObjectName("status_combo")
        status_combo.addItems(["运行中", "等待中", "已停止", "已完成", "已失败"])
        status_combo.setEnabled(False)  # 设为只读
        status_layout.addWidget(status_combo)
        layout.addLayout(status_layout)
        
        # 监控区域
        area_layout = QHBoxLayout()
        area_layout.addWidget(QLabel("监控区域:"))
        area_combo = QComboBox()
        area_combo.setObjectName("area_combo")
        area_layout.addWidget(area_combo)
        layout.addLayout(area_layout)
        
        # 监控规则
        rule_layout = QHBoxLayout()
        rule_layout.addWidget(QLabel("监控规则:"))
        rule_combo = QComboBox()
        rule_combo.setObjectName("rule_combo")
        rule_layout.addWidget(rule_combo)
        layout.addLayout(rule_layout)
        
        # 刷新频率
        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(QLabel("刷新频率(秒):"))
        refresh_spin = QSpinBox()
        refresh_spin.setObjectName("refresh_spin")
        refresh_spin.setMinimum(1)
        refresh_spin.setMaximum(3600)
        refresh_spin.setValue(5)
        refresh_layout.addWidget(refresh_spin)
        layout.addLayout(refresh_layout)
        
        # 自动重启
        restart_check = QCheckBox("出错时自动重启")
        restart_check.setObjectName("restart_check")
        layout.addWidget(restart_check)
        
        # 任务进度
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("任务进度:"))
        progress_bar = QProgressBar()
        progress_bar.setObjectName("progress_bar")
        progress_bar.setValue(0)
        progress_layout.addWidget(progress_bar)
        layout.addLayout(progress_layout)
        
        return group
    
    def create_control_group(self):
        """创建控制按钮组"""
        group = QWidget()
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 新建任务按钮
        new_task_btn = QPushButton("新建任务")
        new_task_btn.setObjectName("new_task_btn")
        new_task_btn.setMinimumHeight(40)
        layout.addWidget(new_task_btn)
        
        # 开始任务按钮
        start_task_btn = QPushButton("开始任务")
        start_task_btn.setObjectName("start_task_btn")
        start_task_btn.setMinimumHeight(40)
        layout.addWidget(start_task_btn)
        
        # 暂停任务按钮
        pause_task_btn = QPushButton("暂停任务")
        pause_task_btn.setObjectName("pause_task_btn")
        pause_task_btn.setMinimumHeight(40)
        layout.addWidget(pause_task_btn)
        
        # 停止任务按钮
        stop_task_btn = QPushButton("停止任务")
        stop_task_btn.setObjectName("stop_task_btn")
        stop_task_btn.setMinimumHeight(40)
        layout.addWidget(stop_task_btn)
        
        # 删除任务按钮
        delete_task_btn = QPushButton("删除任务")
        delete_task_btn.setObjectName("delete_task_btn")
        delete_task_btn.setMinimumHeight(40)
        layout.addWidget(delete_task_btn)
        
        return group
