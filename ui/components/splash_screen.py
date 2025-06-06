from PyQt5.QtWidgets import QSplashScreen, QProgressBar, QVBoxLayout, QLabel, QWidget
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QFontMetrics

import os
import platform
import time
from loguru import logger

class SplashScreen(QSplashScreen):
    """启动屏幕，在应用程序加载时显示"""
    
    # 进度更新信号
    progress_updated = pyqtSignal(int, str)  # 进度值, 消息
    
    def __init__(self, pixmap=None, parent=None):
        """初始化启动屏幕
        
        Args:
            pixmap: 启动屏幕图像
            parent: 父窗口
        """
        # 如果未提供图像，创建默认图像
        if pixmap is None:
            pixmap = self._create_default_splash_image()
        
        super().__init__(pixmap, Qt.WindowStaysOnTopHint)
        
        # 设置窗口属性
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # 添加进度条
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(20, pixmap.height() - 40, pixmap.width() - 40, 20)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #AAAAAA;
                border-radius: 4px;
                background-color: #FAFAFA;
            }
            QProgressBar::chunk {
                background-color: #4A86E8;
                border-radius: 3px;
            }
        """)
        
        # 添加消息标签
        self.message_label = QLabel(self)
        self.message_label.setGeometry(20, pixmap.height() - 70, pixmap.width() - 40, 30)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("""
            color: #444444;
            font-weight: normal;
        """)
        
        # 当前进度和消息
        self.current_progress = 0
        self.current_message = "正在启动应用程序..."
        
        # 检测系统环境
        self.is_mac = platform.system() == "Darwin"
        self.is_apple_silicon = False
        
        if self.is_mac:
            try:
                if platform.machine() == 'arm64':
                    self.is_apple_silicon = True
            except:
                pass
        
        # 连接信号
        self.progress_updated.connect(self._on_progress_updated)
        
        # 显示初始消息
        self.showMessage(self.current_message)
    
    def _create_default_splash_image(self) -> QPixmap:
        """创建默认启动屏幕图像
        
        Returns:
            QPixmap: 默认启动屏幕图像
        """
        width = 450
        height = 280
        
        # 创建图像
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.white)
        
        # 创建画笔
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制背景
        painter.fillRect(0, 0, width, height, QColor('#FFFFFF'))
        
        # 绘制边框
        painter.setPen(QColor('#DDDDDD'))
        painter.drawRect(0, 0, width - 1, height - 1)
        
        # 绘制标题
        title_font = QFont("Arial", 24, QFont.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor('#333333'))
        
        title_text = "Tesseract OCR监控软件"
        title_metrics = QFontMetrics(title_font)
        title_width = title_metrics.width(title_text)
        
        painter.drawText((width - title_width) // 2, 80, title_text)
        
        # 绘制版本
        version_font = QFont("Arial", 12)
        painter.setFont(version_font)
        painter.setPen(QColor('#666666'))
        
        version_text = "版本 1.0.0"
        version_metrics = QFontMetrics(version_font)
        version_width = version_metrics.width(version_text)
        
        painter.drawText((width - version_width) // 2, 120, version_text)
        
        # 绘制描述
        desc_font = QFont("Arial", 10)
        painter.setFont(desc_font)
        painter.setPen(QColor('#999999'))
        
        desc_text = "基于Python 3.9和Tesseract OCR的屏幕监控软件"
        desc_metrics = QFontMetrics(desc_font)
        desc_width = desc_metrics.width(desc_text)
        
        painter.drawText((width - desc_width) // 2, 150, desc_text)
        
        # 绘制底部信息
        footer_font = QFont("Arial", 9)
        painter.setFont(footer_font)
        painter.setPen(QColor('#AAAAAA'))
        
        footer_text = "© 2025 开发团队"
        footer_metrics = QFontMetrics(footer_font)
        footer_width = footer_metrics.width(footer_text)
        
        painter.drawText((width - footer_width) // 2, height - 80, footer_text)
        
        # 完成绘制
        painter.end()
        
        return pixmap
    
    def showMessage(self, message: str, alignment=Qt.AlignBottom | Qt.AlignHCenter, color=Qt.black):
        """显示消息
        
        Args:
            message: 消息内容
            alignment: 对齐方式
            color: 文字颜色
        """
        self.message_label.setText(message)
        
        # 调用父类方法
        super().showMessage(message, alignment, color)
    
    def drawContents(self, painter: QPainter):
        """绘制内容
        
        Args:
            painter: 画笔
        """
        # 调用父类方法
        super().drawContents(painter)
    
    def update_progress(self, value: int, message: str = ""):
        """更新进度
        
        Args:
            value: 进度值 (0-100)
            message: 消息内容
        """
        if message == "":
            message = self.current_message
            
        self.progress_updated.emit(value, message)
    
    def _on_progress_updated(self, value: int, message: str):
        """进度更新处理
        
        Args:
            value: 进度值
            message: 消息内容
        """
        # 更新进度条
        self.progress_bar.setValue(value)
        
        # 更新消息
        if message != self.current_message:
            self.current_message = message
            self.showMessage(message)
        
        # 更新当前进度
        self.current_progress = value
        
        # 刷新界面
        self.repaint()


def show_splash_screen() -> SplashScreen:
    """显示启动屏幕
    
    Returns:
        SplashScreen: 启动屏幕实例
    """
    # 创建启动屏幕
    splash = SplashScreen()
    
    # 显示启动屏幕
    splash.show()
    
    # 处理事件，确保启动屏幕可见
    from PyQt5.QtWidgets import QApplication
    QApplication.processEvents()
    
    return splash 