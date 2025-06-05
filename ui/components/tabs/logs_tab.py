from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, 
    QComboBox, QLineEdit, QTextEdit, QCheckBox, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView, QDateTimeEdit
)
from PyQt5.QtCore import Qt, QDateTime


class LogsTab(QWidget):
    """日志标签页，用于显示和管理应用程序日志"""
    
    def __init__(self):
        super().__init__()
        
        # 创建主布局
        self.layout = QVBoxLayout(self)
        
        # 创建筛选面板
        self.filter_group = self.create_filter_group()
        self.layout.addWidget(self.filter_group)
        
        # 创建日志表格
        self.logs_table = self.create_logs_table()
        self.layout.addWidget(self.logs_table)
        
        # 创建日志详情面板
        self.detail_group = self.create_detail_group()
        self.layout.addWidget(self.detail_group)
        
        # 创建控制按钮面板
        self.control_group = self.create_control_group()
        self.layout.addWidget(self.control_group)
    
    def create_filter_group(self):
        """创建日志筛选面板"""
        group = QGroupBox("日志筛选")
        layout = QHBoxLayout(group)
        
        # 日志级别
        layout.addWidget(QLabel("级别:"))
        level_combo = QComboBox()
        level_combo.addItems(["全部", "调试", "信息", "警告", "错误", "严重"])
        layout.addWidget(level_combo)
        
        # 日志来源
        layout.addWidget(QLabel("来源:"))
        source_combo = QComboBox()
        source_combo.addItems(["全部", "OCR", "监控", "任务", "动作", "系统"])
        layout.addWidget(source_combo)
        
        # 时间范围
        layout.addWidget(QLabel("开始时间:"))
        start_time = QDateTimeEdit(QDateTime.currentDateTime().addDays(-1))
        start_time.setCalendarPopup(True)
        layout.addWidget(start_time)
        
        layout.addWidget(QLabel("结束时间:"))
        end_time = QDateTimeEdit(QDateTime.currentDateTime())
        end_time.setCalendarPopup(True)
        layout.addWidget(end_time)
        
        # 搜索框
        layout.addWidget(QLabel("搜索:"))
        search_edit = QLineEdit()
        search_edit.setPlaceholderText("输入关键词搜索")
        layout.addWidget(search_edit)
        
        # 搜索按钮
        search_btn = QPushButton("搜索")
        layout.addWidget(search_btn)
        
        # 重置按钮
        reset_btn = QPushButton("重置")
        layout.addWidget(reset_btn)
        
        return group
    
    def create_logs_table(self):
        """创建日志表格"""
        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels(["时间", "级别", "来源", "消息", "详情"])
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setMinimumHeight(300)
        
        return table
    
    def create_detail_group(self):
        """创建日志详情面板"""
        group = QGroupBox("日志详情")
        layout = QVBoxLayout(group)
        
        # 日志详情文本框
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setPlaceholderText("选择日志项查看详情")
        layout.addWidget(self.detail_text)
        
        return group
    
    def create_control_group(self):
        """创建控制按钮面板"""
        group = QWidget()
        layout = QHBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 自动滚动
        auto_scroll = QCheckBox("自动滚动")
        auto_scroll.setChecked(True)
        layout.addWidget(auto_scroll)
        
        # 自动刷新
        auto_refresh = QCheckBox("自动刷新")
        auto_refresh.setChecked(True)
        layout.addWidget(auto_refresh)
        
        # 添加弹性空间
        layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        layout.addWidget(refresh_btn)
        
        # 清空按钮
        clear_btn = QPushButton("清空日志")
        layout.addWidget(clear_btn)
        
        # 导出按钮
        export_btn = QPushButton("导出日志")
        layout.addWidget(export_btn)
        
        return group
