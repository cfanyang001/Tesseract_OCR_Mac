import sys
import os
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QRubberBand, QApplication, 
    QPushButton, QHBoxLayout, QDialog, QSizeGrip, QSizePolicy
)
from PyQt5.QtCore import Qt, QRect, QSize, QPoint, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QCursor, QImage
import pyautogui
import numpy as np


class AreaSelector(QDialog):
    """屏幕区域选择器对话框，用于选择OCR识别区域"""
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # 获取屏幕截图
        self.screenshot = self.take_screenshot()
        
        # 设置背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 创建主布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建指导标签（空白，因为指导文字会在paintEvent中绘制）
        self.guide_label = QLabel("")
        self.guide_label.setFixedHeight(30)
        self.guide_label.setStyleSheet("background-color: transparent;")
        self.layout.addWidget(self.guide_label)
        
        # 中间占位区域
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        spacer.setStyleSheet("background-color: transparent;")
        self.layout.addWidget(spacer)
        
        # 创建按钮布局
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setFixedSize(100, 30)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                color: white; 
                background-color: #666;
                border-radius: 4px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #777;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        # 间隔
        button_layout.addSpacing(20)
        
        # 确认按钮
        self.confirm_button = QPushButton("确认")
        self.confirm_button.setFixedSize(100, 30)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                color: white; 
                background-color: #007BFF;
                border-radius: 4px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
            QPushButton:disabled {
                background-color: #65a9e6;
            }
        """)
        self.confirm_button.clicked.connect(self.accept)
        self.confirm_button.setEnabled(False)  # 初始禁用
        button_layout.addWidget(self.confirm_button)
        
        # 添加按钮布局
        button_container = QWidget()
        button_container.setLayout(button_layout)
        button_container.setFixedHeight(50)
        button_container.setStyleSheet("background-color: rgba(0, 0, 0, 150); border-radius: 4px;")
        self.layout.addWidget(button_container)
        
        # 橡皮筋选择框
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        
        # 选择状态
        self.origin = QPoint()
        self.current = QPoint()
        self.selected_rect = None
        self.is_selecting = False
        
        # 设置鼠标为十字光标
        self.setCursor(Qt.CrossCursor)
        
        # 设置全屏
        self.showFullScreen()
    
    def take_screenshot(self):
        """获取全屏截图"""
        try:
            # 使用pyautogui获取屏幕截图
            screenshot = pyautogui.screenshot()
            # 转换为PIL Image
            img = screenshot
            # 转换为QPixmap
            img_data = img.tobytes("raw", "RGB")
            qimage = QImage(img_data, img.width, img.height, img.width * 3, QImage.Format_RGB888)
            return QPixmap.fromImage(qimage)
        except Exception as e:
            print(f"截图获取失败: {e}")
            # 返回空白图像
            return QPixmap()
    
    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)
        
        # 在整个窗口绘制屏幕截图
        painter = QPainter(self)
        
        # 如果截图存在且有效
        if not self.screenshot.isNull():
            # 绘制截图作为背景
            painter.drawPixmap(self.rect(), self.screenshot)
            
            # 绘制半透明蒙版
            overlay = QColor(0, 0, 0, 100)  # 半透明黑色
            painter.fillRect(self.rect(), overlay)
            
            # 如果有选择区域，清除该区域的蒙版
            if self.selected_rect and self.selected_rect.isValid():
                rect = self.selected_rect
                
                # 重新绘制选择区域的截图（不带蒙版）
                painter.setCompositionMode(QPainter.CompositionMode_Source)
                screenshot_rect = QRect(rect)
                painter.drawPixmap(rect, self.screenshot, screenshot_rect)
                
                # 绘制选择框边框
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                pen = QPen(QColor(0, 174, 255), 2)  # 蓝色边框
                painter.setPen(pen)
                painter.drawRect(rect)
                
                # 显示尺寸和位置信息
                info_text = f"位置: ({rect.x()}, {rect.y()}) 尺寸: {rect.width()} x {rect.height()}"
                
                # 确定文本位置
                text_x = rect.right() + 5
                text_y = rect.bottom() + 20
                
                # 如果文本会超出屏幕右边界，则显示在左侧
                if text_x + 200 > self.width():
                    text_x = rect.left() - 200
                
                # 创建文本背景
                text_rect = QRect(text_x, text_y - 15, 200, 20)
                painter.fillRect(text_rect, QColor(0, 0, 0, 180))
                
                # 绘制文本
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, info_text)
        else:
            # 如果没有截图，填充黑色
            painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        # 绘制指导文本
        guide_rect = QRect(10, 10, self.width() - 20, 30)
        painter.fillRect(guide_rect, QColor(0, 0, 0, 180))
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(guide_rect, Qt.AlignCenter, "点击并拖动鼠标选择区域，然后点击确认按钮")
    
    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            # 重置之前的选择
            if self.selected_rect:
                self.rubber_band.hide()
                self.selected_rect = None
                self.update()
                
            self.origin = event.pos()
            self.current = self.origin
            self.rubber_band.setGeometry(QRect(self.origin, QSize()))
            self.rubber_band.show()
            self.is_selecting = True
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.is_selecting:
            # 更新当前位置
            self.current = event.pos()
            
            # 计算选择区域（相对于窗口的坐标）
            rect = QRect(self.origin, self.current).normalized()
            
            # 更新橡皮筋
            self.rubber_band.setGeometry(rect)
            
            # 保存选择区域（相对于屏幕的绝对坐标）
            # 因为我们的窗口是全屏的，所以窗口坐标就是屏幕坐标
            self.selected_rect = rect
            
            # 启用确认按钮
            self.confirm_button.setEnabled(True)
            
            # 重绘以显示选择区域
            self.update()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            
            # 确保矩形有效
            if self.selected_rect and (self.selected_rect.width() < 10 or self.selected_rect.height() < 10):
                self.rubber_band.hide()
                self.selected_rect = None
                self.confirm_button.setEnabled(False)
                self.update()
                return
    
    def keyPressEvent(self, event):
        """按键事件"""
        if event.key() == Qt.Key_Escape:
            self.reject()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if self.selected_rect and self.selected_rect.isValid():
                self.accept()
    
    def get_selection(self):
        """获取选择的区域"""
        return self.selected_rect


class AreaPreview(QWidget):
    """区域预览组件，显示选择的屏幕区域"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        # 预览标签
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(QSize(320, 240))
        self.preview_label.setStyleSheet("""
            background-color: #f0f0f0; 
            border: 1px solid #cccccc;
            padding: 2px;
        """)
        self.preview_label.setText("尚未选择区域")
        
        self.layout.addWidget(self.preview_label)
        
        # 预览图像
        self.preview_image = None
    
    def set_image(self, pixmap):
        """设置预览图像"""
        if pixmap and not pixmap.isNull():
            print(f"设置预览图像: {pixmap.width()}x{pixmap.height()}")
            
            # 清除文本
            self.preview_label.clear()
            
            # 保存原始图像
            self.preview_image = pixmap
            
            # 计算缩放比例
            label_width = self.preview_label.width() - 4
            label_height = self.preview_label.height() - 4
            pix_width = pixmap.width()
            pix_height = pixmap.height()
            
            # 计算缩放因子
            width_ratio = label_width / pix_width
            height_ratio = label_height / pix_height
            scale_factor = min(width_ratio, height_ratio)
            
            # 缩放图像
            if scale_factor < 1:
                new_width = int(pix_width * scale_factor)
                new_height = int(pix_height * scale_factor)
                scaled_pixmap = pixmap.scaled(
                    new_width, new_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            else:
                scaled_pixmap = pixmap
            
            print(f"缩放后的图像: {scaled_pixmap.width()}x{scaled_pixmap.height()}")
            
            # 设置图像
            self.preview_label.setPixmap(scaled_pixmap)
            self.preview_label.setAlignment(Qt.AlignCenter)
        else:
            print("设置空预览图像")
            self.preview_image = None
            self.preview_label.clear()
            self.preview_label.setText("尚未选择区域")
    
    def resizeEvent(self, event):
        """重新调整大小时，更新预览图像"""
        super().resizeEvent(event)
        if self.preview_image and not self.preview_image.isNull():
            # 重新计算缩放比例
            label_width = self.preview_label.width() - 4
            label_height = self.preview_label.height() - 4
            pix_width = self.preview_image.width()
            pix_height = self.preview_image.height()
            
            # 计算缩放因子
            width_ratio = label_width / pix_width
            height_ratio = label_height / pix_height
            scale_factor = min(width_ratio, height_ratio)
            
            # 缩放图像
            if scale_factor < 1:
                new_width = int(pix_width * scale_factor)
                new_height = int(pix_height * scale_factor)
                scaled_pixmap = self.preview_image.scaled(
                    new_width, new_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            else:
                scaled_pixmap = self.preview_image
                
            self.preview_label.setPixmap(scaled_pixmap)
