from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGraphicsOpacityEffect, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont

import time
from typing import List, Dict, Any, Optional
from loguru import logger

class NotificationItem(QFrame):
    """单个通知项"""
    
    # 通知类型
    TYPE_INFO = "info"
    TYPE_SUCCESS = "success"
    TYPE_WARNING = "warning"
    TYPE_ERROR = "error"
    
    # 通知关闭信号
    closed = pyqtSignal(str)  # 通知ID
    
    def __init__(self, notification_id: str, message: str, 
                notification_type: str = TYPE_INFO, 
                duration: int = 5000, parent=None):
        """初始化通知项
        
        Args:
            notification_id: 通知ID
            message: 通知消息
            notification_type: 通知类型，可选值: info, success, warning, error
            duration: 显示时长(毫秒)，为0表示不自动关闭
            parent: 父窗口
        """
        super().__init__(parent)
        
        self.notification_id = notification_id
        self.message = message
        self.notification_type = notification_type
        self.duration = duration
        self.creation_time = time.time()
        
        self._setup_ui()
        
        # 设置自动关闭定时器
        if duration > 0:
            QTimer.singleShot(duration, self._on_auto_close)
    
    def _setup_ui(self):
        """设置UI"""
        # 设置阴影和边框
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(1)
        
        # 设置大小策略
        self.setMinimumWidth(250)
        self.setMaximumWidth(400)
        self.setMinimumHeight(50)
        
        # 设置样式
        self._apply_style()
        
        # 主布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # 图标
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        self._set_icon()
        layout.addWidget(self.icon_label)
        
        # 消息
        self.message_label = QLabel(self.message)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label, 1)
        
        # 关闭按钮
        self.close_button = QPushButton("×")
        self.close_button.setFlat(True)
        self.close_button.setFixedSize(20, 20)
        self.close_button.clicked.connect(self._on_close)
        layout.addWidget(self.close_button)
        
        # 初始透明度
        self.setWindowOpacity(0.0)
        
        # 淡入动画
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(200)
        self.fade_in_animation.setStartValue(0.0)
        self.fade_in_animation.setEndValue(1.0)
        self.fade_in_animation.start()
    
    def _apply_style(self):
        """应用样式"""
        base_style = """
            QFrame {
                border-radius: 6px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
            QLabel {
                color: rgba(0, 0, 0, 0.8);
            }
            QPushButton {
                border: none;
                font-weight: bold;
                color: rgba(0, 0, 0, 0.5);
            }
            QPushButton:hover {
                color: rgba(0, 0, 0, 0.8);
            }
        """
        
        # 根据类型设置不同的颜色
        if self.notification_type == self.TYPE_INFO:
            style = base_style + """
                QFrame {
                    background-color: #E8F1FD;
                }
            """
        elif self.notification_type == self.TYPE_SUCCESS:
            style = base_style + """
                QFrame {
                    background-color: #E3F6E6;
                }
            """
        elif self.notification_type == self.TYPE_WARNING:
            style = base_style + """
                QFrame {
                    background-color: #FFEFD6;
                }
            """
        elif self.notification_type == self.TYPE_ERROR:
            style = base_style + """
                QFrame {
                    background-color: #FFE9E9;
                }
                QLabel {
                    color: #8B0000;
                }
            """
        else:
            style = base_style
        
        self.setStyleSheet(style)
    
    def _set_icon(self):
        """设置图标"""
        # 使用emoji作为简单图标
        if self.notification_type == self.TYPE_INFO:
            self.icon_label.setText("ℹ️")
        elif self.notification_type == self.TYPE_SUCCESS:
            self.icon_label.setText("✅")
        elif self.notification_type == self.TYPE_WARNING:
            self.icon_label.setText("⚠️")
        elif self.notification_type == self.TYPE_ERROR:
            self.icon_label.setText("❌")
    
    def _on_close(self):
        """关闭按钮点击事件"""
        # 淡出动画
        self.fade_out_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_out_animation.setDuration(200)
        self.fade_out_animation.setStartValue(1.0)
        self.fade_out_animation.setEndValue(0.0)
        self.fade_out_animation.finished.connect(self._finish_close)
        self.fade_out_animation.start()
    
    def _on_auto_close(self):
        """自动关闭"""
        self._on_close()
    
    def _finish_close(self):
        """完成关闭动画后的操作"""
        # 发送关闭信号
        self.closed.emit(self.notification_id)
        
        # 标记为隐藏
        self.hide()


class NotificationCenter(QWidget):
    """通知中心，管理和显示通知"""
    
    def __init__(self, parent=None):
        """初始化通知中心
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumWidth(300)
        
        # 通知项列表
        self.notifications = {}  # {id: NotificationItem}
        
        # 最大通知数
        self.max_notifications = 5
        
        # 设置UI
        self._setup_ui()
        
        # 初始隐藏
        self.hide()
    
    def _setup_ui(self):
        """设置UI"""
        # 主布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)
        self.layout.addStretch()
    
    def show_notification(self, message: str, notification_type: str = "info", 
                         duration: int = 5000) -> str:
        """显示通知
        
        Args:
            message: 通知消息
            notification_type: 通知类型，可选值: info, success, warning, error
            duration: 显示时长(毫秒)，为0表示不自动关闭
            
        Returns:
            str: 通知ID
        """
        try:
            # 生成通知ID
            notification_id = f"{notification_type}_{int(time.time())}"
            
            # 创建通知项
            notification = NotificationItem(
                notification_id, message, notification_type, duration, self
            )
            notification.closed.connect(self._on_notification_closed)
            
            # 添加到布局
            self.layout.insertWidget(0, notification)
            
            # 保存到字典
            self.notifications[notification_id] = notification
            
            # 显示通知中心
            self._position_notifications()
            self.show()
            
            # 如果超过最大数量，移除最旧的
            self._clean_old_notifications()
            
            logger.debug(f"显示通知: {notification_id} - {message}")
            return notification_id
            
        except Exception as e:
            logger.error(f"显示通知失败: {e}")
            return ""
    
    def _position_notifications(self):
        """定位通知窗口"""
        try:
            if not self.parent():
                # 如果没有父窗口，居中显示
                return
                
            # 获取父窗口右下角坐标
            parent_rect = self.parent().geometry()
            parent_right = parent_rect.x() + parent_rect.width()
            parent_bottom = parent_rect.y() + parent_rect.height()
            
            # 计算通知中心位置
            x = parent_right - self.width() - 20
            y = parent_bottom - self.height() - 20
            
            # 移动窗口
            self.move(x, y)
            
        except Exception as e:
            logger.error(f"定位通知窗口失败: {e}")
    
    def _on_notification_closed(self, notification_id: str):
        """通知关闭事件处理
        
        Args:
            notification_id: 通知ID
        """
        try:
            if notification_id in self.notifications:
                notification = self.notifications[notification_id]
                
                # 从布局移除
                self.layout.removeWidget(notification)
                
                # 从字典移除
                del self.notifications[notification_id]
                
                # 销毁通知
                notification.deleteLater()
            
            # 如果没有通知了，隐藏通知中心
            if not self.notifications:
                self.hide()
                
        except Exception as e:
            logger.error(f"关闭通知失败: {e}")
    
    def _clean_old_notifications(self):
        """清理旧通知"""
        try:
            if len(self.notifications) <= self.max_notifications:
                return
                
            # 按时间排序
            sorted_notifications = sorted(
                self.notifications.items(),
                key=lambda x: x[1].creation_time
            )
            
            # 删除最旧的
            for i in range(len(sorted_notifications) - self.max_notifications):
                notification_id = sorted_notifications[i][0]
                self._on_notification_closed(notification_id)
                
        except Exception as e:
            logger.error(f"清理旧通知失败: {e}")
    
    def clear_all_notifications(self):
        """清除所有通知"""
        try:
            # 复制ID列表，避免在迭代过程中修改字典
            notification_ids = list(self.notifications.keys())
            
            for notification_id in notification_ids:
                self._on_notification_closed(notification_id)
                
        except Exception as e:
            logger.error(f"清除所有通知失败: {e}")


# 全局单例
_instance = None

def get_notification_center() -> NotificationCenter:
    """获取通知中心单例"""
    global _instance
    if _instance is None:
        _instance = NotificationCenter()
    return _instance 