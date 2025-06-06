from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, QStatusBar, QMenuBar, QMenu, QAction,
    QHBoxLayout, QSplitter, QMessageBox
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon

from ui.components.tabs.ocr_tab import OCRTab
from ui.components.tabs.monitor_tab import MonitorTab
from ui.components.tabs.task_tab import TaskTab
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
        self.logs_tab = LogsTab()
        
        # 添加标签页到标签页控件
        self.tabs.addTab(self.ocr_tab, "OCR设置")
        self.tabs.addTab(self.monitor_tab, "监控设置")
        self.tabs.addTab(self.task_tab, "任务管理")
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
        
        # 使用定时器确保在UI完全加载后应用配置
        QTimer.singleShot(100, self.apply_initial_config)
    
    def init_controllers(self):
        """初始化控制器"""
        try:
            # 配置控制器
            from ui.controllers.config_controller import ConfigController
            from config.config_manager import ConfigManager
            
            config_manager = ConfigManager()
            self.config_controller = ConfigController(self.config_panel, config_manager)
            logger.info("配置控制器初始化成功")
            
            # OCR控制器
            from ui.controllers.tabs.ocr_controller import OCRController
            from core.ocr_processor import OCRProcessor
            from core.screen_capture import ScreenCapture
            from core.text_recognizer import TextRecognizer
            
            ocr_processor = OCRProcessor()
            screen_capture = ScreenCapture()
            text_recognizer = TextRecognizer(ocr_processor, screen_capture)
            
            self.ocr_controller = OCRController(self.ocr_tab, text_recognizer, config_manager)
            logger.info("OCR控制器初始化成功")
            
            # 监控控制器
            from ui.controllers.tabs.monitor_controller import MonitorController
            from core.monitor_engine import MonitorEngine
            
            monitor_engine = MonitorEngine(text_recognizer)
            self.monitor_controller = MonitorController(self.monitor_tab, monitor_engine, config_manager)
            
            # 设置OCR控制器的监控引擎
            self.ocr_controller.set_monitor_engine(monitor_engine)
            logger.info("监控控制器初始化成功")
            
            # 任务控制器
            from ui.controllers.tabs.task_controller import TaskController
            from core.task_manager import TaskManager
            
            task_manager = TaskManager(monitor_engine)
            self.task_controller = TaskController(self.task_tab, task_manager, monitor_engine)
            logger.info("任务控制器初始化成功")
            
            # 日志控制器
            from ui.controllers.tabs.logs_controller import LogsController
            from ui.models.log_model import LogModel
            
            log_model = LogModel()
            self.logs_controller = LogsController(self.logs_tab, log_model)
            logger.info("日志控制器初始化成功")
            
            # 连接控制器之间的信号
            self.connect_controllers()
            
        except Exception as e:
            logger.error(f"初始化控制器失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def register_tabs_to_config_controller(self):
        """注册所有标签页到配置控制器"""
        try:
            # 注册所有标签页
            self.config_controller.register_tab("OCR设置", self.ocr_tab)
            self.config_controller.register_tab("监控设置", self.monitor_tab)
            self.config_controller.register_tab("任务管理", self.task_tab)
            self.config_controller.register_tab("日志", self.logs_tab)
            logger.info("所有标签页已注册到配置控制器")
        except Exception as e:
            logger.error(f"注册标签页到配置控制器失败: {e}")
    
    def apply_initial_config(self):
        """应用初始配置到所有标签页"""
        try:
            if hasattr(self, 'config_controller'):
                self.config_controller.apply_config_to_all_tabs()
                logger.info("已应用初始配置到所有标签页")
        except Exception as e:
            logger.error(f"应用初始配置失败: {e}")
    
    def on_tab_changed(self, index):
        """当标签页改变时"""
        try:
            # 获取当前标签页名称和组件
            tab_name = self.tabs.tabText(index)
            tab_widget = self.tabs.widget(index)
            
            # 如果离开监控标签页，停止监控
            if hasattr(self, 'monitor_controller') and self.monitor_controller.is_monitoring:
                # 获取之前的标签页名称
                previous_index = getattr(self, '_previous_tab_index', -1)
                if previous_index >= 0:
                    previous_tab_name = self.tabs.tabText(previous_index)
                    if previous_tab_name == "监控设置" and tab_name != "监控设置":
                        # 停止监控
                        self.monitor_controller.toggle_monitoring()
                        logger.info("离开监控标签页，自动停止监控")
            
            # 更新配置面板
            self.config_panel.set_current_tab(tab_name, tab_widget)
            
            # 记住当前标签页索引
            self._previous_tab_index = index
            
            logger.info(f"切换到标签页: {tab_name}")
        
        except Exception as e:
            logger.error(f"切换标签页时发生错误: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menu_bar = self.menuBar()
        
        # 文件菜单
        file_menu = menu_bar.addMenu("文件")
        
        new_task_action = QAction("新建任务", self)
        new_task_action.setShortcut("Ctrl+N")
        new_task_action.triggered.connect(self.on_new_task)
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
            try:
                # 获取当前标签页名称和组件
                current_index = self.tabs.currentIndex()
                tab_name = self.tabs.tabText(current_index)
                tab_widget = self.tabs.widget(current_index)
                
                # 获取当前配置名称（从配置面板获取）
                current_config = self.config_panel.current_config
                
                # 从当前标签页获取最新的配置
                config_data = self.config_controller.get_config_from_tab(tab_name, tab_widget)
                
                # 发送保存信号
                self.config_panel.config_saved.emit(current_config, config_data)
                
                # 显示成功消息
                QMessageBox.information(self, "保存成功", f"配置 '{current_config}' 已保存")
                
                logger.info(f"配置 {current_config} 已保存")
            except Exception as e:
                logger.error(f"保存配置失败: {e}")
                QMessageBox.warning(self, "保存失败", f"保存配置时发生错误: {e}")
    
    def on_new_task(self):
        """创建新任务"""
        try:
            # 切换到任务管理标签页
            task_tab_index = self.tabs.indexOf(self.task_tab)
            self.tabs.setCurrentIndex(task_tab_index)
            
            # 调用任务控制器的新建任务方法
            if hasattr(self, 'task_controller'):
                self.task_controller.on_new_task()
            else:
                logger.warning("任务控制器未初始化，无法创建新任务")
        except Exception as e:
            logger.error(f"创建新任务失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            # 关闭任务管理器
            if hasattr(self, 'task_manager'):
                self.task_manager.shutdown()
                logger.info("任务管理器已关闭")
                
            # 关闭任务调度器
            if hasattr(self, 'task_scheduler'):
                self.task_scheduler.stop()
                logger.info("任务调度器已关闭")
                
        except Exception as e:
            logger.error(f"关闭窗口时发生错误: {e}")
            
        # 继续默认的关闭事件
        super().closeEvent(event)

    def connect_controllers(self):
        """连接控制器之间的信号"""
        try:
            # 注册所有标签页到配置控制器
            self.register_tabs_to_config_controller()
            
            # 连接监控引擎到任务管理器
            if hasattr(self, 'monitor_controller') and hasattr(self, 'task_controller'):
                monitor_engine = self.monitor_controller.monitor_engine
                task_manager = self.task_controller.task_manager
                
                # 设置任务管理器的监控引擎
                if task_manager and monitor_engine:
                    task_manager.set_monitor_engine(monitor_engine)
                    logger.info("已连接监控引擎到任务管理器")
            
            # 连接日志模型到其他控制器
            if hasattr(self, 'logs_controller') and hasattr(self.logs_controller, 'log_model'):
                log_model = self.logs_controller.log_model
                
                # 连接OCR控制器的日志
                if hasattr(self, 'ocr_controller'):
                    self.ocr_controller.set_log_model(log_model)
                
                # 连接监控控制器的日志
                if hasattr(self, 'monitor_controller'):
                    self.monitor_controller.set_log_model(log_model)
                
                # 连接任务控制器的日志
                if hasattr(self, 'task_controller'):
                    self.task_controller.set_log_model(log_model)
                
                logger.info("已连接日志模型到所有控制器")
        
        except Exception as e:
            logger.error(f"连接控制器失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
