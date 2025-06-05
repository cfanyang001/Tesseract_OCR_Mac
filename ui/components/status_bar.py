from PyQt5.QtWidgets import QStatusBar, QLabel, QProgressBar, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt


class StatusBar(QStatusBar):
    """自定义状态栏，显示软件状态信息"""
    
    def __init__(self):
        super().__init__()
        
        # 创建布局
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(20)
        
        # 创建状态标签
        self.ocr_status_label = QLabel("OCR引擎: 已初始化")
        self.ocr_status_label.setStyleSheet("color: green;")
        
        self.task_status_label = QLabel("任务: 0")
        
        # 添加标签到布局
        self.layout.addWidget(self.ocr_status_label)
        self.layout.addWidget(self.task_status_label)
        
        # 添加弹簧
        self.layout.addStretch()
        
        # 创建容器小部件
        container = QWidget()
        container.setLayout(self.layout)
        
        # 添加容器到状态栏
        self.addPermanentWidget(container, 1)
    
    def update_ocr_status(self, initialized=True):
        """更新OCR引擎状态"""
        if initialized:
            self.ocr_status_label.setText("OCR引擎: 已初始化")
            self.ocr_status_label.setStyleSheet("color: green;")
        else:
            self.ocr_status_label.setText("OCR引擎: 未初始化")
            self.ocr_status_label.setStyleSheet("color: red;")
    
    def update_task_count(self, count=0):
        """更新任务数量"""
        self.task_status_label.setText(f"任务: {count}")
