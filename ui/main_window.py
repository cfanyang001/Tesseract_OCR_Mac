from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QPushButton, QAction, QMenu, QStatusBar, QLabel, QSplitter,
    QToolBar, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSlot
from PyQt5.QtGui import QIcon, QFont

import os
import platform
import time
from loguru import logger

# 导入自定义组件
from ui.components.notification_center import get_notification_center
from ui.components.shortcut_manager import get_shortcut_manager
from ui.components.dialogs.help_dialog import HelpDialog

# 导入其他必要模块
from config.mac_compatibility import MacCompatibility
from core.updater import get_updater
from core.error_handler import get_error_handler


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        """初始化主窗口"""
        super().__init__()
        
        # 设置基本属性
        self.setWindowTitle("Tesseract OCR监控软件")
        self.setMinimumSize(800, 600)
        
        # 初始化实例变量
        self.is_monitoring = False
        self.is_mac = platform.system() == "Darwin"
        self.is_apple_silicon = False
        self.mac_model = ""
        
        # 检查Mac兼容性
        if self.is_mac:
            self._check_mac_compatibility()
        
        # 设置UI
        self._setup_ui()
        
        # 初始化组件
        self._init_components()
        
        # 连接信号槽
        self._connect_signals()
        
        # 设置初始状态
        self._update_status("就绪")
        
        # 检查更新
        QTimer.singleShot(3000, self._check_updates)
    
    def _check_mac_compatibility(self):
        """检查Mac兼容性"""
        try:
            mac_compat = MacCompatibility()
            self.is_apple_silicon = mac_compat.is_apple_silicon()
            
            if self.is_apple_silicon:
                chip_info = mac_compat.get_chip_info()
                self.mac_model = chip_info.get("model", "")
                logger.info(f"检测到Apple Silicon芯片: {self.mac_model}")
                
                # 更新窗口标题以显示芯片信息
                if self.mac_model:
                    self.setWindowTitle(f"Tesseract OCR监控软件 - {self.mac_model}")
                    
        except Exception as e:
            logger.warning(f"检查Mac兼容性失败: {e}")
    
    def _setup_ui(self):
        """设置UI"""
        # 设置中央部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # 主布局
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # 创建主要标签页
        self._create_monitor_tab()
        self._create_rules_tab()
        self._create_settings_tab()
        
        # 创建底部状态栏
        self._create_status_bar()
        
        # 创建菜单栏
        self._create_menus()
        
        # 创建工具栏
        self._create_toolbar()
    
    def _create_monitor_tab(self):
        """创建监控标签页"""
        monitor_tab = QWidget()
        layout = QVBoxLayout(monitor_tab)
        
        # 占位标签
        label = QLabel("监控区域将显示在这里")
        label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        label.setFont(font)
        layout.addWidget(label)
        
        # 添加到标签页
        self.tab_widget.addTab(monitor_tab, "监控")
    
    def _create_rules_tab(self):
        """创建规则标签页"""
        rules_tab = QWidget()
        layout = QVBoxLayout(rules_tab)
        
        # 占位标签
        label = QLabel("规则编辑器将显示在这里")
        label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        label.setFont(font)
        layout.addWidget(label)
        
        # 添加到标签页
        self.tab_widget.addTab(rules_tab, "规则")
    
    def _create_settings_tab(self):
        """创建设置标签页"""
        settings_tab = QWidget()
        layout = QVBoxLayout(settings_tab)
        
        # 占位标签
        label = QLabel("设置选项将显示在这里")
        label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        label.setFont(font)
        layout.addWidget(label)
        
        # 添加到标签页
        self.tab_widget.addTab(settings_tab, "设置")
    
    def _create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 状态标签
        self.status_label = QLabel("状态: 就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 系统信息标签
        system_info = f"{platform.system()} {platform.release()}"
        if self.is_apple_silicon and self.mac_model:
            system_info += f" ({self.mac_model})"
        self.system_label = QLabel(system_info)
        self.status_bar.addPermanentWidget(self.system_label)
    
    def _create_menus(self):
        """创建菜单"""
        # 文件菜单
        file_menu = self.menuBar().addMenu("文件")
        
        new_action = QAction("新建任务", self)
        new_action.triggered.connect(self._on_new_task)
        file_menu.addAction(new_action)
        
        open_action = QAction("打开配置", self)
        open_action.triggered.connect(self._on_open_config)
        file_menu.addAction(open_action)
        
        save_action = QAction("保存配置", self)
        save_action.triggered.connect(self._on_save_config)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 动作菜单
        action_menu = self.menuBar().addMenu("动作")
        
        start_action = QAction("开始监控", self)
        start_action.triggered.connect(self._on_start_monitor)
        action_menu.addAction(start_action)
        self.start_action = start_action
        
        stop_action = QAction("停止监控", self)
        stop_action.triggered.connect(self._on_stop_monitor)
        stop_action.setEnabled(False)
        action_menu.addAction(stop_action)
        self.stop_action = stop_action
        
        action_menu.addSeparator()
        
        capture_action = QAction("捕获屏幕", self)
        capture_action.triggered.connect(self._on_capture_screen)
        action_menu.addAction(capture_action)
        
        # 工具菜单
        tools_menu = self.menuBar().addMenu("工具")
        
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self._on_show_settings)
        tools_menu.addAction(settings_action)
        
        # M系列芯片特定菜单项
        if self.is_apple_silicon:
            tools_menu.addSeparator()
            
            optimize_action = QAction("M系列芯片优化", self)
            optimize_action.setCheckable(True)
            optimize_action.setChecked(True)
            optimize_action.triggered.connect(self._on_toggle_optimization)
            tools_menu.addAction(optimize_action)
            self.optimize_action = optimize_action
        
        tools_menu.addSeparator()
        
        check_updates_action = QAction("检查更新", self)
        check_updates_action.triggered.connect(self._on_check_updates)
        tools_menu.addAction(check_updates_action)
        
        # 帮助菜单
        help_menu = self.menuBar().addMenu("帮助")
        
        help_action = QAction("帮助", self)
        help_action.triggered.connect(self._on_show_help)
        help_menu.addAction(help_action)
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self._on_show_about)
        help_menu.addAction(about_action)
    
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        
        # 开始监控
        start_button = QPushButton("开始监控")
        start_button.clicked.connect(self._on_start_monitor)
        toolbar.addWidget(start_button)
        self.start_button = start_button
        
        # 停止监控
        stop_button = QPushButton("停止监控")
        stop_button.clicked.connect(self._on_stop_monitor)
        stop_button.setEnabled(False)
        toolbar.addWidget(stop_button)
        self.stop_button = stop_button
        
        toolbar.addSeparator()
        
        # 捕获屏幕
        capture_button = QPushButton("捕获屏幕")
        capture_button.clicked.connect(self._on_capture_screen)
        toolbar.addWidget(capture_button)
        
        # 右侧空间
        spacer = QWidget()
        spacer.setSizePolicy(1, 0)
        spacer.setMinimumWidth(10)
        toolbar.addWidget(spacer)
        
        # 帮助
        help_button = QPushButton("帮助")
        help_button.clicked.connect(self._on_show_help)
        toolbar.addWidget(help_button)
    
    def _init_components(self):
        """初始化组件"""
        # 获取通知中心
        self.notification_center = get_notification_center()
        
        # 获取快捷键管理器
        self.shortcut_manager = get_shortcut_manager()
        
        # 注册应用程序快捷键
        self.shortcut_manager.register_app_shortcuts(self)
        
        # 创建帮助对话框
        self.help_dialog = HelpDialog(self)
        
        # 获取更新检查器
        self.updater = get_updater()
        
        # 获取错误处理器
        self.error_handler = get_error_handler()
    
    def _connect_signals(self):
        """连接信号槽"""
        # 连接快捷键信号
        self.shortcut_manager.shortcut_triggered.connect(self._on_shortcut_triggered)
        
        # 连接更新检查器信号
        self.updater.update_available.connect(self._on_update_available)
        self.updater.update_error.connect(self._on_update_error)
        self.updater.update_complete.connect(self._on_update_complete)
        
        # 连接错误处理器信号
        if self.error_handler:
            self.error_handler.error_occurred.connect(self._on_error_occurred)
    
    def _update_status(self, message: str):
        """更新状态栏消息"""
        self.status_label.setText(f"状态: {message}")
        logger.debug(f"状态更新: {message}")
    
    def _check_updates(self):
        """检查更新"""
        try:
            # 仅在非调试模式下自动检查更新
            import sys
            if not any(x in sys.argv for x in ['-d', '--debug']):
                self.updater.check_for_updates()
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
    
    @pyqtSlot()
    def _on_new_task(self):
        """新建任务"""
        self._show_notification("新建任务功能尚未实现", "warning")
    
    @pyqtSlot()
    def _on_open_config(self):
        """打开配置"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "打开配置文件",
                "",
                "配置文件 (*.json);;所有文件 (*)"
            )
            
            if file_path:
                # 将在此处添加加载配置的代码
                self._show_notification(f"加载配置文件: {os.path.basename(file_path)}", "info")
                
        except Exception as e:
            logger.error(f"打开配置失败: {e}")
            self._show_notification(f"打开配置失败: {str(e)}", "error")
    
    @pyqtSlot()
    def _on_save_config(self):
        """保存配置"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存配置文件",
                "",
                "配置文件 (*.json);;所有文件 (*)"
            )
            
            if file_path:
                # 将在此处添加保存配置的代码
                self._show_notification(f"保存配置文件: {os.path.basename(file_path)}", "success")
                
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            self._show_notification(f"保存配置失败: {str(e)}", "error")
    
    @pyqtSlot()
    def _on_start_monitor(self):
        """开始监控"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self._update_status("监控中...")
            self._update_monitoring_ui(True)
            self._show_notification("监控已启动", "success")
    
    @pyqtSlot()
    def _on_stop_monitor(self):
        """停止监控"""
        if self.is_monitoring:
            self.is_monitoring = False
            self._update_status("就绪")
            self._update_monitoring_ui(False)
            self._show_notification("监控已停止", "warning")
    
    def _update_monitoring_ui(self, is_monitoring: bool):
        """更新监控状态的UI"""
        # 更新按钮状态
        self.start_button.setEnabled(not is_monitoring)
        self.stop_button.setEnabled(is_monitoring)
        
        # 更新菜单项状态
        self.start_action.setEnabled(not is_monitoring)
        self.stop_action.setEnabled(is_monitoring)
    
    @pyqtSlot()
    def _on_capture_screen(self):
        """捕获屏幕"""
        self._show_notification("屏幕捕获功能尚未实现", "warning")
    
    @pyqtSlot()
    def _on_show_settings(self):
        """显示设置"""
        self._show_notification("设置功能尚未实现", "warning")
    
    @pyqtSlot(bool)
    def _on_toggle_optimization(self, checked: bool):
        """切换M系列芯片优化"""
        if checked:
            self._show_notification("已启用M系列芯片优化", "info")
        else:
            self._show_notification("已禁用M系列芯片优化", "warning")
    
    @pyqtSlot()
    def _on_check_updates(self):
        """手动检查更新"""
        self._show_notification("正在检查更新...", "info")
        
        # 执行更新检查
        has_update, info = self.updater.check_for_updates()
        
        if not has_update and "error" not in info:
            self._show_notification("当前已是最新版本", "info")
    
    @pyqtSlot(dict)
    def _on_update_available(self, update_info: dict):
        """有更新可用"""
        version = update_info.get("version", "未知")
        
        # 显示更新对话框
        reply = QMessageBox.question(
            self,
            "有新版本可用",
            f"发现新版本: {version}\n\n是否立即更新？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            # 下载更新
            download_url = update_info.get("download_url")
            if download_url:
                # 开始下载
                self._show_notification(f"开始下载版本 {version}...", "info")
                self.updater.download_update(download_url)
                
                # 安装更新
                # 注: 在实际应用中，应该在下载完成后才安装
                # 这里简化处理
                self.updater.install_update()
    
    @pyqtSlot(str)
    def _on_update_error(self, error_msg: str):
        """更新错误"""
        self._show_notification(f"更新错误: {error_msg}", "error")
    
    @pyqtSlot(bool, str)
    def _on_update_complete(self, success: bool, message: str):
        """更新完成"""
        if success:
            self._show_notification(message, "success", duration=10000)
            
            # 显示提示对话框
            QMessageBox.information(
                self,
                "更新完成",
                f"{message}\n\n点击确定重启应用程序。",
                QMessageBox.Ok
            )
            
            # 重启应用程序
            # 这里应该有重启应用程序的代码
            # 现在简化为关闭应用程序
            self.close()
        else:
            self._show_notification(message, "error")
    
    @pyqtSlot(str, str, str)
    def _on_error_occurred(self, error_type: str, error_msg: str, error_traceback: str):
        """错误发生"""
        # 在状态栏显示错误
        self._update_status(f"错误: {error_msg}")
        
        # 显示错误通知
        self._show_notification(f"错误: {error_msg}", "error")
    
    @pyqtSlot(str)
    def _on_shortcut_triggered(self, action_name: str):
        """快捷键触发"""
        logger.debug(f"快捷键触发: {action_name}")
        
        # 处理各种快捷键动作
        if action_name == "start_monitor":
            self._on_start_monitor()
        elif action_name == "stop_monitor":
            self._on_stop_monitor()
        elif action_name == "capture_screen":
            self._on_capture_screen()
        elif action_name == "save_config":
            self._on_save_config()
        elif action_name == "open_config":
            self._on_open_config()
        elif action_name == "show_settings":
            self._on_show_settings()
        elif action_name == "optimize_performance" and self.is_apple_silicon:
            if hasattr(self, 'optimize_action'):
                self.optimize_action.setChecked(not self.optimize_action.isChecked())
                self._on_toggle_optimization(self.optimize_action.isChecked())
    
    @pyqtSlot()
    def _on_show_help(self):
        """显示帮助对话框"""
        self.help_dialog.exec_()
    
    @pyqtSlot()
    def _on_show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于 Tesseract OCR监控软件",
            """<h3>Tesseract OCR监控软件</h3>
            <p>版本: 1.0.0</p>
            <p>基于Python 3.9和Tesseract OCR的屏幕监控软件</p>
            <p>© 2025 开发团队</p>"""
        )
    
    def _show_notification(self, message: str, notification_type: str = "info", duration: int = 5000):
        """显示通知
        
        Args:
            message: 通知消息
            notification_type: 通知类型，可选值: info, success, warning, error
            duration: 显示时长(毫秒)
        """
        self.notification_center.show_notification(message, notification_type, duration)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.is_monitoring:
            reply = QMessageBox.question(
                self,
                "确认退出",
                "监控任务正在运行，确认要退出吗？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 停止监控
                self._on_stop_monitor()
                event.accept()
            else:
                event.ignore()
        else:
            # 清理资源
            self.updater.cleanup()
            
            # 接受关闭事件
            event.accept() 