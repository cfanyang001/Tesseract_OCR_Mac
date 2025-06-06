from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, QStatusBar, QMenuBar, QMenu, QAction,
    QHBoxLayout, QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon
import traceback

from ui.components.tabs.ocr_tab import OCRTab
from ui.components.tabs.monitor_tab import MonitorTab
from ui.components.tabs.task_tab import TaskTab
from ui.components.tabs.logs_tab import LogsTab
from ui.components.tabs.action_tab import ActionTab
from ui.components.tabs.performance_tab import PerformanceTab
from ui.components.status_bar import StatusBar
from ui.components.config_panel import ConfigPanel

# 导入控制器
from ui.controllers.tabs.ocr_controller import OCRController
from ui.controllers.tabs.monitor_controller import MonitorController
from ui.controllers.tabs.task_controller import TaskController
from ui.controllers.tabs.logs_controller import LogsController
from ui.controllers.tabs.action_controller import ActionController
from ui.controllers.tabs.performance_controller import PerformanceController
from ui.controllers.config_controller import ConfigController
from loguru import logger

# 导入配置管理器
from config.config_manager import ConfigManager


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Tesseract OCR监控软件")
        self.setMinimumSize(1200, 800)
        
        # 创建配置管理器
        self.config_manager = ConfigManager()
        
        # 创建中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建分割器
        self.splitter = QSplitter(Qt.Horizontal)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 创建OCR标签页
        self.ocr_tab = OCRTab()
        self.tab_widget.addTab(self.ocr_tab, "OCR识别")
        
        # 创建监控标签页
        self.monitor_tab = MonitorTab()
        self.tab_widget.addTab(self.monitor_tab, "屏幕监控")
        
        # 创建任务标签页
        self.task_tab = TaskTab()
        self.tab_widget.addTab(self.task_tab, "任务管理")
        
        # 创建动作标签页
        self.action_tab = ActionTab()
        self.tab_widget.addTab(self.action_tab, "智能点击")
        
        # 创建日志标签页
        self.logs_tab = LogsTab()
        self.tab_widget.addTab(self.logs_tab, "日志")
        
        # 创建性能监控标签页
        self.performance_tab = PerformanceTab()
        self.tab_widget.addTab(self.performance_tab, "性能监控")
        
        # 创建配置面板
        self.config_panel = ConfigPanel()
        
        # 添加组件到分割器
        self.splitter.addWidget(self.tab_widget)
        self.splitter.addWidget(self.config_panel)
        
        # 设置分割比例
        self.splitter.setSizes([800, 400])
        
        # 添加分割器到主布局
        self.main_layout.addWidget(self.splitter)
        
        # 创建状态栏
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)
        
        # 创建菜单栏
        self._create_menu_bar()
        
        # 初始化控制器
        self._init_controllers()
        
        # 连接信号
        self._connect_signals()
        
        # 加载配置
        self._load_config()
        
        logger.info("主窗口初始化完成")
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        
        # 保存配置
        save_config_action = QAction("保存配置", self)
        save_config_action.triggered.connect(self._save_config)
        file_menu.addAction(save_config_action)
        
        # 加载配置
        load_config_action = QAction("加载配置", self)
        load_config_action.triggered.connect(self._load_config)
        file_menu.addAction(load_config_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menu_bar.addMenu("视图")
        
        # 显示/隐藏配置面板
        toggle_config_panel_action = QAction("显示/隐藏配置面板", self)
        toggle_config_panel_action.triggered.connect(self._toggle_config_panel)
        view_menu.addAction(toggle_config_panel_action)
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")
        
        # 关于
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _init_controllers(self):
        """初始化控制器"""
        try:
            # 创建控制器
            self.config_controller = ConfigController(self.config_panel)
            logger.info("配置控制器初始化成功")
            
            self.ocr_controller = OCRController(self.ocr_tab)
            logger.info("OCR控制器初始化成功")
            
            self.monitor_controller = MonitorController(self.monitor_tab)
            logger.info("监控控制器初始化成功")
            
            self.task_controller = TaskController(self.task_tab)
            logger.info("任务控制器初始化成功")
            
            self.logs_controller = LogsController(self.logs_tab)
            logger.info("日志控制器初始化成功")
            
            self.action_controller = ActionController(self.action_tab)
            logger.info("动作控制器初始化成功")
            
            self.performance_controller = PerformanceController(self.performance_tab)
            logger.info("性能监控控制器初始化成功")
            
            # 连接控制器
            self.ocr_controller.log_message.connect(self.logs_controller.add_log)
            self.monitor_controller.log_message.connect(self.logs_controller.add_log)
            self.task_controller.log_message.connect(self.logs_controller.add_log)
            self.action_controller.log_message.connect(self.logs_controller.add_log)
            
            # 设置控制器引用
            self.monitor_controller.set_ocr_controller(self.ocr_controller)
            self.task_controller.set_ocr_controller(self.ocr_controller)
            self.task_controller.set_monitor_controller(self.monitor_controller)
            self.task_controller.set_action_controller(self.action_controller)
            
            # 添加性能监控
            self._add_performance_metrics()
        except Exception as e:
            logger.error(f"初始化控制器失败: {str(e)}")
            logger.error(traceback.format_exc())
    
    def _add_performance_metrics(self):
        """添加性能监控指标"""
        # 添加OCR识别时间指标
        self.ocr_controller.text_recognized.connect(
            lambda text, details: self.performance_controller.add_custom_metric(
                "OCR识别时间(毫秒)", details.get("recognition_time", 0) * 1000
            )
        )
        
        # 添加监控刷新时间指标
        self.monitor_controller.monitor_refreshed.connect(
            lambda: self.performance_controller.add_custom_metric(
                "监控刷新时间(毫秒)", self.monitor_controller.get_last_refresh_time() * 1000
            )
        )
        
        # 添加任务执行时间指标
        self.task_controller.task_executed.connect(
            lambda task_id, duration: self.performance_controller.add_custom_metric(
                "任务执行时间(毫秒)", duration * 1000
            )
        )
    
    def _connect_signals(self):
        """连接信号"""
        # 标签页切换信号
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        
        # 配置变更信号
        self.config_controller.config_changed.connect(self._on_config_changed)
    
    def _on_tab_changed(self, index):
        """标签页切换事件处理"""
        try:
            # 更新状态栏
            tab_name = self.tab_widget.tabText(index)
            self.status_bar.set_message(f"当前标签页: {tab_name}")
            
            # 更新配置面板当前标签页
            if hasattr(self, 'config_panel') and self.config_panel is not None:
                self.config_panel.set_current_tab(tab_name, self.tab_widget.widget(index))
        except Exception as e:
            logger.error(f"切换标签页时发生错误: {str(e)}")
            logger.error(traceback.format_exc())
    
    def _on_config_changed(self, config):
        """配置变更事件处理"""
        # 更新状态栏
        self.status_bar.set_message("配置已更新")
    
    def _save_config(self):
        """保存配置"""
        try:
            self.config_manager.save_config()
            self.status_bar.set_message("配置已保存")
            logger.info("配置已保存")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存配置失败: {e}")
    
    def _load_config(self):
        """加载配置"""
        try:
            self.config_manager.load_config()
            self.status_bar.set_message("配置已加载")
            logger.info("配置已加载")
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            QMessageBox.critical(self, "错误", f"加载配置失败: {e}")
    
    def _toggle_config_panel(self):
        """显示/隐藏配置面板"""
        if self.config_panel.isVisible():
            self.config_panel.hide()
        else:
            self.config_panel.show()
    
    def _show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "Tesseract OCR监控软件\n\n"
            "版本: 1.0.0\n"
            "作者: AI助手\n"
            "日期: 2025-06-08\n\n"
            "基于Tesseract OCR引擎的屏幕文本识别和监控软件"
        )
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 停止所有控制器
        if hasattr(self, 'ocr_controller'):
            self.ocr_controller.shutdown()
        
        if hasattr(self, 'monitor_controller'):
            self.monitor_controller.shutdown()
        
        if hasattr(self, 'task_controller'):
            self.task_controller.shutdown()
        
        if hasattr(self, 'performance_controller'):
            self.performance_controller.shutdown()
        
        # 保存配置
        try:
            self.config_manager.save_config()
            logger.info("配置已保存")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
        
        logger.info("应用程序关闭")
        event.accept()
