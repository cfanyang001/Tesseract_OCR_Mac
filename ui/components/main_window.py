from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, QStatusBar, QMenuBar, QMenu, QAction
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

from ui.components.tabs.ocr_tab import OCRTab
from ui.components.tabs.monitor_tab import MonitorTab
from ui.components.tabs.task_tab import TaskTab
from ui.components.tabs.actions_tab import ActionsTab
from ui.components.tabs.logs_tab import LogsTab
from ui.components.status_bar import StatusBar

# 导入控制器
from ui.controllers.tabs.ocr_controller import OCRController
from loguru import logger


class MainWindow(QMainWindow):
    """主窗口类，包含标签页和菜单栏"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Tesseract OCR监控软件")
        self.setMinimumSize(QSize(900, 700))
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建标签页
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(True)
        
        # 创建各个标签页
        self.ocr_tab = OCRTab()
        self.monitor_tab = MonitorTab()
        self.task_tab = TaskTab()
        self.actions_tab = ActionsTab()
        self.logs_tab = LogsTab()
        
        # 添加标签页到标签页控件
        self.tabs.addTab(self.ocr_tab, "OCR设置")
        self.tabs.addTab(self.monitor_tab, "监控设置")
        self.tabs.addTab(self.task_tab, "任务管理")
        self.tabs.addTab(self.actions_tab, "动作配置")
        self.tabs.addTab(self.logs_tab, "日志")
        
        # 将标签页控件添加到主布局
        self.layout.addWidget(self.tabs)
        
        # 创建状态栏
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 初始化控制器
        self.init_controllers()
    
    def init_controllers(self):
        """初始化控制器"""
        try:
            # 初始化OCR控制器
            self.ocr_controller = OCRController(self.ocr_tab)
            logger.info("OCR控制器初始化成功")
            
            # 初始化其他控制器...
            # TODO: 添加其他控制器初始化
            
        except Exception as e:
            logger.error(f"控制器初始化失败: {e}")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        
        new_task_action = QAction("新建任务", self)
        new_task_action.setShortcut("Ctrl+N")
        file_menu.addAction(new_task_action)
        
        open_action = QAction("打开配置", self)
        open_action.setShortcut("Ctrl+O")
        file_menu.addAction(open_action)
        
        save_action = QAction("保存配置", self)
        save_action.setShortcut("Ctrl+S")
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menu_bar.addMenu("编辑")
        
        settings_action = QAction("设置", self)
        edit_menu.addAction(settings_action)
        
        # 视图菜单
        view_menu = menu_bar.addMenu("视图")
        
        fullscreen_action = QAction("全屏", self)
        fullscreen_action.setShortcut("F11")
        view_menu.addAction(fullscreen_action)
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        help_menu.addAction(about_action)
        
        doc_action = QAction("文档", self)
        help_menu.addAction(doc_action)
