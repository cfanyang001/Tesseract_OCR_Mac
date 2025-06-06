from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QFrame, QGraphicsOpacityEffect)
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen


class ClickConfirmDialog(QDialog):
    """点击确认对话框，用于在执行智能点击前让用户确认"""
    
    # 信号
    confirmed = pyqtSignal()  # 确认信号
    cancelled = pyqtSignal()  # 取消信号
    
    def __init__(self, parent=None, point=None, target_desc="", screenshot=None):
        """初始化点击确认对话框
        
        Args:
            parent: 父窗口
            point: 点击位置
            target_desc: 目标描述
            screenshot: 屏幕截图
        """
        super().__init__(parent, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        self.point = point or QPoint(0, 0)
        self.target_desc = target_desc
        self.screenshot = screenshot
        self.timeout = 3000  # 默认超时时间 (毫秒)
        self.remaining_time = self.timeout // 1000
        
        self._init_ui()
        self._setup_timer()
    
    def _init_ui(self):
        """初始化UI"""
        # 设置窗口属性
        self.setWindowTitle("点击确认")
        self.setMinimumWidth(300)
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
            QLabel {
                color: #333333;
            }
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px 10px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton#confirmButton {
                background-color: #4CAF50;
                color: white;
            }
            QPushButton#confirmButton:hover {
                background-color: #45a049;
            }
            QPushButton#cancelButton {
                background-color: #f44336;
                color: white;
            }
            QPushButton#cancelButton:hover {
                background-color: #d32f2f;
            }
        """)
        
        # 创建布局
        main_layout = QVBoxLayout(self)
        
        # 添加标题
        title_label = QLabel("确认点击", self)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 添加分隔线
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # 添加目标信息
        info_layout = QVBoxLayout()
        
        target_label = QLabel(f"目标: {self.target_desc}", self)
        target_label.setWordWrap(True)
        info_layout.addWidget(target_label)
        
        position_label = QLabel(f"位置: ({self.point.x()}, {self.point.y()})", self)
        info_layout.addWidget(position_label)
        
        # 添加截图预览 (如果有)
        if self.screenshot:
            preview_label = QLabel(self)
            preview_pixmap = QPixmap.fromImage(self.screenshot)
            
            # 标记点击位置
            painter = QPainter(preview_pixmap)
            painter.setPen(QPen(QColor(255, 0, 0), 3))
            painter.drawEllipse(self.point.x() - 5, self.point.y() - 5, 10, 10)
            painter.end()
            
            # 设置预览图像
            preview_label.setPixmap(preview_pixmap.scaled(
                280, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
            preview_label.setAlignment(Qt.AlignCenter)
            info_layout.addWidget(preview_label)
        
        main_layout.addLayout(info_layout)
        
        # 添加倒计时
        self.timer_label = QLabel(f"自动确认倒计时: {self.remaining_time}秒", self)
        self.timer_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.timer_label)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        
        self.confirm_button = QPushButton("确认", self)
        self.confirm_button.setObjectName("confirmButton")
        self.confirm_button.clicked.connect(self.accept)
        button_layout.addWidget(self.confirm_button)
        
        self.cancel_button = QPushButton("取消", self)
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # 设置透明度效果
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.95)
        self.setGraphicsEffect(self.opacity_effect)
    
    def _setup_timer(self):
        """设置倒计时定时器"""
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # 1秒
        self.timer.timeout.connect(self._update_timer)
        self.timer.start()
    
    def _update_timer(self):
        """更新倒计时"""
        self.remaining_time -= 1
        self.timer_label.setText(f"自动确认倒计时: {self.remaining_time}秒")
        
        if self.remaining_time <= 0:
            self.timer.stop()
            self.accept()
    
    def set_timeout(self, timeout_ms):
        """设置超时时间
        
        Args:
            timeout_ms: 超时时间 (毫秒)
        """
        self.timeout = timeout_ms
        self.remaining_time = timeout_ms // 1000
        self.timer_label.setText(f"自动确认倒计时: {self.remaining_time}秒")
    
    def accept(self):
        """确认点击"""
        self.timer.stop()
        self.confirmed.emit()
        super().accept()
    
    def reject(self):
        """取消点击"""
        self.timer.stop()
        self.cancelled.emit()
        super().reject() 