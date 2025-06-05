from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QMessageBox, QPushButton, QLabel
from loguru import logger


class MonitorController(QObject):
    """监控标签页控制器，负责连接监控标签页与OCR控制器"""
    
    def __init__(self, monitor_tab):
        super().__init__()
        
        self.monitor_tab = monitor_tab
        
        # 将控制器实例保存到标签页中
        self.monitor_tab.controller = self
        
        # 监控状态
        self.is_monitoring = False
        
        # 添加开始/停止监控按钮
        self.add_monitor_control_button()
        
        # 连接信号
        self.connect_signals()
        
        logger.info("监控控制器初始化成功")
    
    def add_monitor_control_button(self):
        """添加开始/停止监控按钮"""
        # 创建状态标签和控制按钮
        status_layout = self.monitor_tab.layout.itemAt(0).widget().layout()
        
        # 添加状态标签
        self.status_label = QLabel("监控状态: 未启动")
        status_layout.addWidget(self.status_label)
        
        # 添加弹性空间
        status_layout.addStretch()
        
        # 添加控制按钮
        self.monitor_button = QPushButton("开始监控")
        self.monitor_button.setMinimumHeight(30)
        self.monitor_button.setStyleSheet("background-color: #4CAF50; color: white;")
        status_layout.addWidget(self.monitor_button)
    
    def connect_signals(self):
        """连接信号"""
        if hasattr(self, 'monitor_button'):
            self.monitor_button.clicked.connect(self.toggle_monitoring)
    
    @pyqtSlot()
    def toggle_monitoring(self):
        """切换监控状态"""
        try:
            # 获取主窗口
            main_window = self.monitor_tab.window()
            if not main_window:
                logger.warning("无法获取主窗口")
                return
            
            # 获取OCR控制器
            if not hasattr(main_window, 'ocr_controller'):
                logger.warning("主窗口没有ocr_controller属性")
                QMessageBox.warning(
                    self.monitor_tab, 
                    "错误", 
                    "无法获取OCR控制器，请先配置OCR设置"
                )
                return
            
            ocr_controller = main_window.ocr_controller
            
            if not self.is_monitoring:
                # 开始监控
                success = ocr_controller.start_monitoring()
                if success:
                    self.is_monitoring = True
                    self.monitor_button.setText("停止监控")
                    self.monitor_button.setStyleSheet("background-color: #F44336; color: white;")
                    self.status_label.setText("监控状态: 正在监控")
                    logger.info("监控已启动")
                else:
                    QMessageBox.warning(
                        self.monitor_tab, 
                        "警告", 
                        "无法启动监控，请先在OCR设置中选择一个区域"
                    )
            else:
                # 停止监控
                success = ocr_controller.stop_monitoring()
                if success:
                    self.is_monitoring = False
                    self.monitor_button.setText("开始监控")
                    self.monitor_button.setStyleSheet("background-color: #4CAF50; color: white;")
                    self.status_label.setText("监控状态: 已停止")
                    logger.info("监控已停止")
        
        except Exception as e:
            logger.error(f"切换监控状态失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.warning(
                self.monitor_tab, 
                "错误", 
                f"切换监控状态失败: {e}"
            )
