from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, QStatusBar, QMenuBar, QMenu, QAction,
    QHBoxLayout, QSplitter
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

from ui.components.tabs.ocr_tab import OCRTab
from ui.components.tabs.monitor_tab import MonitorTab
from ui.components.tabs.task_tab import TaskTab
from ui.components.tabs.actions_tab import ActionsTab
from ui.components.tabs.logs_tab import LogsTab
from ui.components.status_bar import StatusBar
from ui.components.config_panel import ConfigPanel

# 导入控制器
from ui.controllers.tabs.ocr_controller import OCRController
from ui.controllers.config_controller import ConfigController
from loguru import logger


class MainWindow(QMainWindow):
    """主窗口类，包含标签页和菜单栏"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Tesseract OCR监控软件")
        self.setMinimumSize(QSize(1100, 700))
        
        # 创建中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建水平分割器
        self.splitter = QSplitter(Qt.Horizontal)
        
        # 创建左侧标签页容器
        self.tabs_container = QWidget()
        self.tabs_layout = QVBoxLayout(self.tabs_container)
        self.tabs_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建标签页
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setMovable(True)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        
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
        
        # 将标签页控件添加到布局
        self.tabs_layout.addWidget(self.tabs)
        
        # 创建右侧配置面板
        self.config_panel = ConfigPanel()
        
        # 将标签页容器和配置面板添加到分割器
        self.splitter.addWidget(self.tabs_container)
        self.splitter.addWidget(self.config_panel)
        
        # 设置分割器比例
        self.splitter.setSizes([700, 300])
        
        # 将分割器添加到主布局
        self.layout.addWidget(self.splitter)
        
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
            
            # 初始化配置控制器
            self.config_controller = ConfigController(self.config_panel)
            logger.info("配置控制器初始化成功")
            
            # 设置初始标签页配置
            self.on_tab_changed(self.tabs.currentIndex())
            
            # 其他控制器...
            # TODO: 添加其他控制器初始化
            
        except Exception as e:
            logger.error(f"控制器初始化失败: {e}")
    
    def on_tab_changed(self, index):
        """当标签页改变时"""
        try:
            # 获取当前标签页名称和组件
            tab_name = self.tabs.tabText(index)
            tab_widget = self.tabs.widget(index)
            
            # 更新配置面板
            self.config_panel.set_current_tab(tab_name, tab_widget)
            
            # 应用配置到标签页
            if hasattr(self, 'config_controller'):
                self.config_controller.apply_config_to_tab(tab_name, tab_widget)
            
            logger.info(f"切换到标签页: {tab_name}")
        
        except Exception as e:
            logger.error(f"切换标签页时发生错误: {e}")
    
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
        save_action.triggered.connect(self.save_current_config)
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
    
    def save_current_config(self):
        """保存当前配置"""
        if hasattr(self, 'config_controller'):
            # 获取当前标签页
            index = self.tabs.currentIndex()
            tab_name = self.tabs.tabText(index)
            tab_widget = self.tabs.widget(index)
            
            # 获取配置并保存
            config = self.config_controller.get_config_from_tab(tab_name, tab_widget)
            self.config_panel.save_current_config()
