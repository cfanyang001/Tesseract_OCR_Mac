import os
import time
import tempfile
import cv2
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from PyQt5.QtWidgets import QApplication, QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QRect, QTimer
from PyQt5.QtGui import QPixmap, QImage

from core.ocr_processor import OCRProcessor
from core.screen_capture import ScreenCapture
from core.text_recognizer import TextRecognizer
from ui.components.tabs.ocr_tab import OCRTab
from ui.components.area_selector_mac import MacScreenCaptureSelector

from loguru import logger
import cv2
import pyautogui
import traceback


class OCRController(QObject):
    """OCR标签页控制器，负责连接OCR标签页与OCR处理器"""
    
    # 定义信号
    log_message = pyqtSignal(str)  # 日志消息信号
    text_recognized = pyqtSignal(str, dict)  # 文本识别信号
    
    def __init__(self, ocr_tab: OCRTab):
        super().__init__()
        
        self.ocr_tab = ocr_tab
        
        # 将控制器实例保存到标签页中，以便配置控制器能够访问它
        self.ocr_tab.controller = self
        
        # 创建OCR处理器、屏幕捕获器和文本识别器
        try:
            self.ocr_processor = OCRProcessor()
            self.screen_capture = ScreenCapture()
            self.text_recognizer = TextRecognizer()
            logger.info("OCR控制器初始化成功")
            
            # 更新状态栏
            main_window = self.ocr_tab.window()
            if main_window and hasattr(main_window, 'status_bar'):
                main_window.status_bar.update_ocr_status(True)
                
        except Exception as e:
            logger.error(f"OCR控制器初始化失败: {e}")
            
            # 更新状态栏
            main_window = self.ocr_tab.window()
            if main_window and hasattr(main_window, 'status_bar'):
                main_window.status_bar.update_ocr_status(False)
                
            QMessageBox.critical(
                self.ocr_tab, 
                "错误", 
                f"OCR引擎初始化失败: {e}\n请确认Tesseract OCR已正确安装。"
            )
            raise
        
        # 当前选择的区域
        self.current_rect = None
        
        # 当前预览截图的路径
        self.current_screenshot = None
        
        # 监控状态标志
        self.is_monitoring = False
        
        # OCR识别结果
        self.last_ocr_text = ""
        self.last_ocr_details = {}
        
        # 自动刷新预览定时器 - 用于非监控状态下的预览刷新
        self.auto_refresh_timer = QTimer()
        self.auto_refresh_timer.timeout.connect(self.update_preview)
        
        # 监控刷新定时器 - 用于监控状态下的预览刷新
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.update_preview)
        
        # 连接信号
        self.connect_signals()
        
        # 初始化UI
        self.init_ui()
    
    def connect_signals(self):
        """连接信号"""
        # 选择区域按钮
        select_btn = self.ocr_tab.left_panel.findChild(
            QObject, "select_area_btn"
        )
        if select_btn:
            select_btn.clicked.connect(self.select_area)
        
        # 测试OCR按钮
        test_btn = self.ocr_tab.left_panel.findChild(
            QObject, "test_ocr_btn"
        )
        if test_btn:
            test_btn.clicked.connect(self.test_ocr)
        
        # 添加坐标测试按钮连接
        test_area_btn = self.ocr_tab.left_panel.findChild(
            QObject, "test_area_btn"
        )
        if test_area_btn:
            test_area_btn.clicked.connect(self.test_area_coordinates)
        
        # 添加全屏测试按钮连接
        test_fullscreen_btn = self.ocr_tab.left_panel.findChild(
            QObject, "test_fullscreen_btn"
        )
        if test_fullscreen_btn:
            test_fullscreen_btn.clicked.connect(self.test_full_screen_capture)
        
        # 语言选择
        lang_combo = self.ocr_tab.left_panel.findChild(
            QObject, "lang_combo"
        )
        if lang_combo:
            lang_combo.currentTextChanged.connect(self.update_language)
        
        # PSM模式选择
        psm_combo = self.ocr_tab.left_panel.findChild(
            QObject, "psm_combo"
        )
        if psm_combo:
            psm_combo.currentIndexChanged.connect(self.update_psm)
        
        # OEM引擎模式选择
        oem_combo = self.ocr_tab.left_panel.findChild(
            QObject, "oem_combo"
        )
        if oem_combo:
            oem_combo.currentIndexChanged.connect(self.update_oem)
        
        # 精度滑块
        accuracy_slider = self.ocr_tab.left_panel.findChild(
            QObject, "accuracy_slider"
        )
        if accuracy_slider:
            accuracy_slider.valueChanged.connect(self.update_accuracy)
        
        # 预处理选项
        preprocess_check = self.ocr_tab.left_panel.findChild(
            QObject, "preprocess_check"
        )
        if preprocess_check:
            preprocess_check.stateChanged.connect(self.update_preprocess)
        
        # 自动修正选项
        autocorrect_check = self.ocr_tab.left_panel.findChild(
            QObject, "autocorrect_check"
        )
        if autocorrect_check:
            autocorrect_check.stateChanged.connect(self.update_autocorrect)
        
        # 文本识别器信号
        self.text_recognizer.text_recognized.connect(self.on_text_recognized)
        self.text_recognizer.error_occurred.connect(self.on_error)
    
    def init_ui(self):
        """初始化UI"""
        try:
            # 获取主窗口和配置控制器
            main_window = self.ocr_tab.window()
            if main_window and hasattr(main_window, 'config_controller'):
                config_controller = main_window.config_controller
                current_config = config_controller.config_manager.current_config
                config = config_controller.config_manager.get_config(current_config)
                ocr_config = config.get('ocr', {})
                logger.info(f"正在加载OCR配置: {ocr_config}")
                
                # 使用配置更新OCR处理器
                if ocr_config:
                    self.ocr_processor.set_config(ocr_config)
                    logger.info("已更新OCR处理器配置")
            else:
                logger.warning("无法获取配置控制器，使用默认设置")
                ocr_config = {}
            
            # 设置语言选项
            lang_combo = self.ocr_tab.left_panel.findChild(QObject, "lang_combo")
            if lang_combo:
                # 阻止信号触发
                lang_combo.blockSignals(True)
                
                lang_combo.clear()
                lang_combo.addItems(self.ocr_processor.get_available_languages())
                
                # 设置默认语言
                default_lang = self.ocr_processor.config['language']
                default_lang_text = self.ocr_processor.LANGUAGE_MAPPING.get(
                    default_lang, '中文简体'
                )
                index = lang_combo.findText(default_lang_text)
                if index >= 0:
                    lang_combo.setCurrentIndex(index)
                    logger.debug(f"设置语言为: {default_lang_text}")
                
                # 恢复信号
                lang_combo.blockSignals(False)
            
            # 设置PSM模式
            psm_combo = self.ocr_tab.left_panel.findChild(QObject, "psm_combo")
            if psm_combo:
                # 阻止信号触发
                psm_combo.blockSignals(True)
                
                psm_value = int(self.ocr_processor.config['psm'])
                if 0 <= psm_value < psm_combo.count():
                    psm_combo.setCurrentIndex(psm_value)
                    logger.debug(f"设置PSM模式为: {psm_value}")
                
                # 恢复信号
                psm_combo.blockSignals(False)
            
            # 设置OEM引擎模式
            oem_combo = self.ocr_tab.left_panel.findChild(QObject, "oem_combo")
            if oem_combo:
                # 阻止信号触发
                oem_combo.blockSignals(True)
                
                oem_value = int(self.ocr_processor.config['oem'])
                if 0 <= oem_value < oem_combo.count():
                    oem_combo.setCurrentIndex(oem_value)
                    logger.debug(f"设置OEM引擎为: {oem_value}")
                
                # 恢复信号
                oem_combo.blockSignals(False)
            
            # 设置精度滑块
            accuracy_slider = self.ocr_tab.left_panel.findChild(QObject, "accuracy_slider")
            if accuracy_slider:
                # 阻止信号触发
                accuracy_slider.blockSignals(True)
                
                accuracy_value = self.ocr_processor.config.get('accuracy', 80)
                accuracy_slider.setValue(accuracy_value)
                logger.debug(f"设置精度为: {accuracy_value}")
                
                # 同时更新精度显示值
                accuracy_value_label = self.ocr_tab.left_panel.findChild(QObject, "accuracy_value")
                if accuracy_value_label:
                    accuracy_value_label.setText(f"{accuracy_value}%")
                
                # 恢复信号
                accuracy_slider.blockSignals(False)
            
            # 设置预处理选项
            preprocess_check = self.ocr_tab.left_panel.findChild(QObject, "preprocess_check")
            if preprocess_check:
                # 阻止信号触发
                preprocess_check.blockSignals(True)
                
                preprocess_value = self.ocr_processor.config.get('preprocess', True)
                preprocess_check.setChecked(preprocess_value)
                logger.debug(f"设置预处理为: {preprocess_value}")
                
                # 恢复信号
                preprocess_check.blockSignals(False)
            
            # 设置自动修正选项
            autocorrect_check = self.ocr_tab.left_panel.findChild(QObject, "autocorrect_check")
            if autocorrect_check:
                # 阻止信号触发
                autocorrect_check.blockSignals(True)
                
                autocorrect_value = self.ocr_processor.config.get('autocorrect', False)
                autocorrect_check.setChecked(autocorrect_value)
                logger.debug(f"设置自动修正为: {autocorrect_value}")
                
                # 恢复信号
                autocorrect_check.blockSignals(False)
            
            # 尝试从配置加载保存的区域
            self.load_area_from_config()
            
            # 启动自动刷新预览
            self.start_auto_refresh()
            
            logger.info("OCR UI初始化完成")
        except Exception as e:
            logger.error(f"初始化OCR UI失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    @pyqtSlot()
    def select_area(self):
        """选择屏幕区域"""
        try:
            # 使用Mac专用的屏幕区域选择器
            rect, pixmap, screenshot_path = MacScreenCaptureSelector.select_area()
            
            if rect is None or pixmap is None:
                logger.warning("用户取消了区域选择")
                return
            
            # 保存选择的区域和截图
            self.current_rect = rect
            self.current_screenshot = screenshot_path
            
            # 更新区域坐标输入框
            self.update_area_spinners()
            
            # 更新预览图像
            self.update_preview_with_image(pixmap)
            
            # 保存区域到配置
            self.save_area_to_config()
            
            # 显示成功消息
            self.show_message(f"已选择屏幕区域: X={rect.x()}, Y={rect.y()}, 宽={rect.width()}, 高={rect.height()}")
            
            # 自动执行OCR测试
            self.test_ocr()
            
            # 启动自动刷新
            self.start_auto_refresh()
            
        except Exception as e:
            logger.error(f"选择区域失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.warning(
                self.ocr_tab, 
                "错误", 
                f"选择区域失败: {e}"
            )
    
    @pyqtSlot()
    def update_preview(self):
        """更新预览"""
        try:
            # 检查是否有选择的区域
            if not self.current_rect:
                logger.debug("没有选择区域，无法更新预览")
                return
            
            # 优先检查是否有原始截图
            from ui.components.area_selector_mac import MacScreenCaptureSelector
            
            if MacScreenCaptureSelector.original_capture_path and os.path.exists(MacScreenCaptureSelector.original_capture_path):
                # 使用原始截图更新预览
                logger.debug(f"使用原始截图更新预览: {MacScreenCaptureSelector.original_capture_path}")
                pixmap = QPixmap(MacScreenCaptureSelector.original_capture_path)
                self.ocr_tab.preview.set_image(pixmap)
                return
                
            # 在监控模式下，使用特殊直接截图OCR方法
            if self.is_monitoring:
                logger.debug("监控模式：使用直接截图OCR方法更新")
                self.direct_screenshot_ocr(self.current_rect)
                return
            
            # 非监控模式下，尽量不刷新预览，保持选择的区域不变
            if self.current_screenshot and os.path.exists(self.current_screenshot):
                # 仅使用已有的截图，不尝试重新捕获
                pixmap = QPixmap(self.current_screenshot)
                # 设置预览图像
                self.ocr_tab.preview.set_image(pixmap)
                logger.debug(f"更新预览: 使用已保存的截图更新预览，图像大小: {pixmap.width()}x{pixmap.height()}")
            else:
                # 如果没有保存的截图，禁用自动刷新
                logger.debug("更新预览: 没有保存的截图，停止自动刷新预览")
                self.stop_auto_refresh()
                return
            
            # 获取当前选择的区域信息并更新状态栏（避免使用不存在的方法）
            if self.current_rect:
                x, y, width, height = (
                    self.current_rect.x(),
                    self.current_rect.y(),
                    self.current_rect.width(),
                    self.current_rect.height()
                )
                
                # 更新状态栏（安全地检查方法是否存在）
                main_window = self.ocr_tab.window()
                if main_window and hasattr(main_window, 'status_bar'):
                    # 检查status_bar是否有update_screen_area方法
                    if hasattr(main_window.status_bar, 'update_screen_area'):
                        main_window.status_bar.update_screen_area(f"{x},{y} {width}x{height}")
                    else:
                        # 使用通用的状态栏更新方法
                        status_text = f"区域: {x},{y} {width}x{height}"
                        if hasattr(main_window.status_bar, 'showMessage'):
                            main_window.status_bar.showMessage(status_text, 5000)
                        logger.debug(f"更新预览: 使用通用方法更新状态栏: {status_text}")
        
        except Exception as e:
            logger.error(f"更新预览失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 即使发生异常也不中断监控流程
    
    @pyqtSlot()
    def test_ocr(self):
        """测试OCR识别"""
        # 先导入必要的模块，避免前面报错
        import os
        import subprocess
        import tempfile
        import datetime
        import shutil
        import cv2
        import traceback
        from PyQt5.QtWidgets import QMessageBox
        
        try:
            # 检查是否有选择的区域
            if not self.current_rect:
                self.show_message("请先选择一个屏幕区域")
                return
                
            # 准备区域参数
            rect = self.current_rect
            logger.info(f"使用原始截图进行OCR测试: {rect.x()}, {rect.y()}, {rect.width()}, {rect.height()}")
            
            # 调用直接截图OCR方法
            text, details = self.direct_screenshot_ocr(rect)
            
            # 检查是否识别到文本
            if text:
                # 显示识别结果
                logger.info(f"OCR测试识别到文本: {text}")
                
                # 更新结果区域
                result_text = self.ocr_tab.right_panel.findChild(QObject, "result_text")
                if result_text and hasattr(result_text, 'setPlainText'):
                    result_text.setPlainText(text)
                
                # 更新详情区域
                details_text = self.ocr_tab.right_panel.findChild(QObject, "details_text")
                if details_text and hasattr(details_text, 'setPlainText'):
                    details_text.setPlainText(str(details))
                
                self.show_message("OCR测试完成，点击刷新查看最新结果")
                
                # 触发文本识别信号
                self.text_recognized.emit(text, details)
            else:
                self.show_message("OCR测试完成，但未识别到文本")
                logger.warning("OCR测试未识别到文本")
                
        except Exception as e:
            logger.error(f"OCR测试失败: {str(e)}")
            self.show_message(f"OCR测试失败: {str(e)}", "red")
            logger.error(f"{traceback.format_exc()}")

    def stop_auto_refresh(self):
        """停止自动刷新预览"""
        if self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.stop()
            logger.debug("已停止OCR预览自动刷新")
        
    def start_monitoring(self):
        """开始监控，启动刷新定时器"""
        if not self.current_rect:
            logger.warning("没有选择区域，无法开始监控")
            return False
        
        # 获取监控设置中的刷新间隔
        refresh_interval = 1000  # 默认1秒
        
        # 尝试从监控标签页获取刷新间隔
        try:
            main_window = self.ocr_tab.window()
            if main_window and hasattr(main_window, 'monitor_controller'):
                monitor_controller = main_window.monitor_controller
                # 获取监控标签页中的间隔设置
                monitor_tab = monitor_controller.monitor_tab
                if hasattr(monitor_tab, 'interval_combo'):
                    interval_text = monitor_tab.interval_combo.currentText()
                    try:
                        interval_seconds = int(interval_text)
                        refresh_interval = interval_seconds * 1000
                        logger.debug(f"使用监控设置的刷新间隔: {interval_seconds}秒")
                    except ValueError:
                        logger.warning(f"无法解析监控间隔值: {interval_text}，使用默认值")
        except Exception as e:
            logger.warning(f"获取监控间隔设置失败: {e}，使用默认值")
        
        # 停止自动刷新定时器
        if self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.stop()
        
        # 设置监控状态
        self.is_monitoring = True
        
        # 立即进行一次识别
        self.refresh_ocr()
        
        # 启动监控定时器
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
        self.refresh_timer.timeout.connect(self.refresh_ocr)
        self.refresh_timer.start(refresh_interval)
        
        logger.info(f"OCR监控已启动，刷新频率: {refresh_interval}毫秒")
        return True

    def show_message(self, message, color=None):
        """显示消息在状态栏或通过QMessageBox
        
        Args:
            message: 要显示的消息
            color: 消息颜色，可选 "red", "green", "orange"
        """
        logger.info(f"显示消息: {message}")
        
        # 尝试在状态栏上显示
        main_window = self.ocr_tab.window()
        if main_window and hasattr(main_window, 'status_bar'):
            if hasattr(main_window.status_bar, 'showMessage'):
                main_window.status_bar.showMessage(message, 5000)  # 显示5秒
                return
        
        # 如果没有状态栏，使用QMessageBox
        if color == "red":
            QMessageBox.warning(self.ocr_tab, "警告", message)
        elif color == "green":
            QMessageBox.information(self.ocr_tab, "成功", message)
        else:
            QMessageBox.information(self.ocr_tab, "信息", message)

    def update_preview_with_image(self, pixmap):
        """更新预览窗口中的图像
        
        Args:
            pixmap: 要显示的QPixmap图像
        """
        try:
            logger.info(f"更新预览图像, 尺寸: {pixmap.width()}x{pixmap.height()}")
            
            # 直接设置到预览控件中
            if hasattr(self.ocr_tab, "preview") and self.ocr_tab.preview is not None:
                self.ocr_tab.preview.set_image(pixmap)
                logger.debug("成功设置预览图像")
            else:
                logger.error("无法找到预览控件")
                
        except Exception as e:
            logger.error(f"更新预览图像失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def test_full_screen_capture(self):
        """测试完整屏幕捕获功能"""
        try:
            import subprocess
            import tempfile
            import os
            from PyQt5.QtWidgets import QMessageBox
            import cv2
            
            # 获取屏幕尺寸
            screen_width, screen_height = pyautogui.size()
            logger.info(f"屏幕尺寸: {screen_width}x{screen_height}")
            
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_filename = temp_file.name
            temp_file.close()
            
            # 使用screencapture命令捕获整个屏幕
            result = subprocess.run([
                'screencapture',
                '-x',  # 无声
                temp_filename
            ], check=True, capture_output=True)
            
            if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0:
                # 读取图像
                image = cv2.imread(temp_filename)
                if image is not None:
                    height, width = image.shape[:2]
                    logger.info(f"截图尺寸: {width}x{height}")
                    
                    # 创建QPixmap并显示
                    pixmap = QPixmap(temp_filename)
                    self.ocr_tab.preview.set_image(pixmap.scaled(640, 480, Qt.KeepAspectRatio))
                    
                    # 显示信息
                    QMessageBox.information(
                        self.ocr_tab,
                        "屏幕捕获测试",
                        f"屏幕尺寸: {screen_width}x{screen_height}\n"
                        f"截图尺寸: {width}x{height}\n\n"
                        "请检查预览窗口中显示的图像"
                    )
                    
                    # 清理
                    try:
                        os.remove(temp_filename)
                    except:
                        pass
                    
                    return True
                else:
                    logger.error("无法读取截图文件")
            else:
                logger.error("截图失败或文件为空")
            
            QMessageBox.warning(
                self.ocr_tab,
                "测试失败",
                "无法捕获完整屏幕，请检查系统权限设置"
            )
            return False
            
        except Exception as e:
            logger.error(f"测试完整屏幕捕获失败: {str(e)}")
            QMessageBox.critical(
                self.ocr_tab,
                "测试失败",
                f"测试过程中发生错误: {str(e)}"
            )
            return False

    def test_area_coordinates(self):
        """测试区域坐标准确性"""
        # 导入必要的模块
        import os
        import cv2
        import tempfile
        import subprocess
        import numpy as np
        import traceback
        from PyQt5.QtWidgets import QMessageBox
        from PyQt5.QtGui import QImage, QPixmap
        
        if not self.current_rect:
            QMessageBox.warning(
                self.ocr_tab,
                "提示",
                "请先选择一个屏幕区域"
            )
            return
            
        try:
            # 获取当前区域坐标
            rect = self.current_rect
            x, y, width, height = rect.x(), rect.y(), rect.width(), rect.height()
            
            logger.info(f"测试区域坐标: x={x}, y={y}, width={width}, height={height}")
            
            # 从原始截图中获取当前区域，而不是重新截图
            from ui.components.area_selector_mac import MacScreenCaptureSelector
            
            if MacScreenCaptureSelector.original_capture_path and os.path.exists(MacScreenCaptureSelector.original_capture_path):
                # 使用原始截图
                logger.info(f"使用原始截图: {MacScreenCaptureSelector.original_capture_path}")
                image = cv2.imread(MacScreenCaptureSelector.original_capture_path)
                
                if image is not None:
                    # 在原始图像上标记选定区域
                    marked_image = image.copy()
                    # 绘制红色边框
                    cv2.rectangle(marked_image, (x, y), (x + width, y + height), (0, 0, 255), 3)
                    
                    # 保存标记后的图像
                    border_filename = os.path.join(os.path.dirname(MacScreenCaptureSelector.original_capture_path), 
                                                "test_area_marked.png")
                    cv2.imwrite(border_filename, marked_image)
                    
                    # 创建QPixmap并显示
                    pixmap = QPixmap(border_filename)
                    self.ocr_tab.preview.set_image(pixmap)
                    
                    # 同时显示选定区域的放大图
                    # 截取原始图像中的ROI
                    try:
                        # 确保坐标在图像范围内
                        if (y >= 0 and y + height <= image.shape[0] and 
                            x >= 0 and x + width <= image.shape[1]):
                            roi = image[y:y+height, x:x+width]
                            # 绘制边框
                            roi_with_border = cv2.copyMakeBorder(roi, 5, 5, 5, 5, 
                                                               cv2.BORDER_CONSTANT, value=[0, 0, 255])
                            
                            roi_filename = os.path.join(os.path.dirname(MacScreenCaptureSelector.original_capture_path), 
                                                     "test_area_roi.png")
                            cv2.imwrite(roi_filename, roi_with_border)
                            
                            # 显示信息
                            QMessageBox.information(
                                self.ocr_tab,
                                "坐标测试",
                                f"当前选定区域坐标:\n"
                                f"X: {x}, Y: {y}\n"
                                f"宽: {width}, 高: {height}\n\n"
                                f"在预览窗口中用红色边框标出了选定区域。\n"
                                "请确认红色边框区域是否符合您的预期。"
                            )
                        else:
                            # 坐标超出图像范围
                            logger.warning(f"选定的区域 ({x},{y},{width},{height}) 超出图像范围 ({image.shape[1]}x{image.shape[0]})")
                            QMessageBox.warning(
                                self.ocr_tab,
                                "坐标测试",
                                f"当前选定区域坐标:\n"
                                f"X: {x}, Y: {y}\n"
                                f"宽: {width}, 高: {height}\n\n"
                                f"注意: 选定区域超出了原始图像范围({image.shape[1]}x{image.shape[0]})，\n"
                                f"请重新选择合适的区域。"
                            )
                    except Exception as e:
                        logger.error(f"截取ROI失败: {e}")
                        # 显示信息
                        QMessageBox.information(
                            self.ocr_tab,
                            "坐标测试",
                            f"当前选定区域坐标:\n"
                            f"X: {x}, Y: {y}\n"
                            f"宽: {width}, 高: {height}\n\n"
                            f"在预览窗口中已标记选定区域的位置。\n"
                            f"处理截图时发生错误: {str(e)}"
                        )
                    
                    return True
                else:
                    logger.error(f"无法读取原始截图: {MacScreenCaptureSelector.original_capture_path}")
            
            # 如果没有原始截图，使用传统方法
            logger.warning("原始截图不可用，使用传统截图方法")
            
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_filename = temp_file.name
            temp_file.close()
            
            # 使用screencapture命令捕获区域
            logger.info(f"尝试使用坐标截图: x={x}, y={y}, width={width}, height={height}")
            result = subprocess.run([
                'screencapture',
                '-x',  # 无声
                '-R', f"{x},{y},{width},{height}",  # 区域格式：x,y,width,height
                temp_filename
            ], check=True, capture_output=True)
            
            if os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 0:
                # 读取图像
                image = cv2.imread(temp_filename)
                if image is not None:
                    # 在图像边缘绘制红色边框
                    h, w = image.shape[:2]
                    border_thickness = 3
                    # 直接在图像上绘制边框，而不是添加额外边框
                    cv2.rectangle(image, (0, 0), (w-1, h-1), (0, 0, 255), border_thickness)
                    
                    border_filename = temp_filename + "_border.png"
                    cv2.imwrite(border_filename, image)
                    
                    # 创建QPixmap并显示
                    pixmap = QPixmap(border_filename)
                    self.ocr_tab.preview.set_image(pixmap)
                    
                    # 显示信息
                    QMessageBox.information(
                        self.ocr_tab,
                        "坐标测试",
                        f"当前选定区域坐标:\n"
                        f"X: {x}, Y: {y}\n"
                        f"宽: {width}, 高: {height}\n\n"
                        f"实际截图尺寸: {w}x{h}\n\n"
                        "预览窗口中显示的图像已添加红色边框，\n"
                        "请确认这是您想要识别的区域"
                    )
                    
                    # 清理临时文件
                    try:
                        os.remove(temp_filename)
                        os.remove(border_filename)
                    except:
                        pass
                    
                    return True
                else:
                    logger.error("无法读取截图文件")
            else:
                logger.error("区域截图失败或文件为空")
            
            QMessageBox.warning(
                self.ocr_tab,
                "测试失败",
                "无法捕获指定区域，坐标可能有误"
            )
            return False
            
        except Exception as e:
            logger.error(f"测试区域坐标失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(
                self.ocr_tab,
                "测试失败",
                f"测试过程中发生错误: {str(e)}"
            )
            return False

    def direct_screenshot_ocr(self, rect):
        """直接截图OCR识别
        
        Args:
            rect: 截图区域
            
        Returns:
            tuple: (识别文本, 详情)
        """
        # 导入必要的模块
        import os
        import cv2
        import numpy as np
        import tempfile
        import traceback
        from PyQt5.QtCore import QRect
        
        try:
            # 优先使用原始截图
            from ui.components.area_selector_mac import MacScreenCaptureSelector
            
            if hasattr(MacScreenCaptureSelector, 'original_capture_path') and MacScreenCaptureSelector.original_capture_path and os.path.exists(MacScreenCaptureSelector.original_capture_path):
                logger.info(f"使用原始截图: {MacScreenCaptureSelector.original_capture_path}")
                
                # 读取原始截图
                img = cv2.imread(MacScreenCaptureSelector.original_capture_path)
                if img is None:
                    logger.error("无法读取原始截图")
                    return "", {}
                    
                # 获取图像尺寸
                img_height, img_width, _ = img.shape
                
                # 记录信息但不裁剪图像
                logger.info(f"原始截图尺寸: {img_width}x{img_height}")
                logger.info(f"请求的OCR区域: x={rect.x()}, y={rect.y()}, width={rect.width()}, height={rect.height()}")
                
                # 重要修改：直接使用整个原始截图进行OCR，不进行任何裁剪
                # 因为系统截图工具已经截取了用户选择的区域
                target_img = img
                
                # 应用图像预处理（如果启用）
                config = self.ocr_processor.get_config()
                if config.get('preprocess', False):
                    target_img = self.ocr_processor.preprocess_image(target_img)
                    
                # 运行OCR识别
                text, details = self.ocr_processor.recognize_text(target_img)
                text = text.strip()
                
                logger.info(f"OCR识别成功，文本长度: {len(text)}字符")
                
                # 更新预览窗口
                pixmap = self.cv2_to_pixmap(img)
                self.update_preview_with_image(pixmap)
                
                return text, details
            
            # 如果没有原始截图或无效，使用屏幕截图方式
            logger.info(f"使用屏幕截图OCR方式: {rect.x()}, {rect.y()}, {rect.width()}, {rect.height()}")
            
            # 捕获指定区域
            image = self.screen_capture.capture_area(rect)
            if image is None:
                logger.error("屏幕捕获失败")
                return "", {}
                
            # 应用图像预处理（如果启用）
            config = self.ocr_processor.get_config()
            if config.get('preprocess', False):
                image = self.ocr_processor.preprocess_image(image)
                
            # 运行OCR识别
            text, details = self.ocr_processor.recognize_text(image)
            text = text.strip()
            
            logger.info(f"OCR识别成功，文本长度: {len(text)}字符")
            
            # 更新预览窗口
            pixmap = self.cv2_to_pixmap(image)
            self.update_preview_with_image(pixmap)
            
            return text, details
            
        except Exception as e:
            logger.error(f"直接截图OCR方法异常: {str(e)}")
            logger.error(traceback.format_exc())
            return "", {}

    def stop_monitoring(self):
        """停止监控，停止刷新定时器"""
        if self.refresh_timer.isActive():
            # 断开特殊OCR方法连接
            try:
                self.refresh_timer.timeout.disconnect()
            except Exception:
                pass
            self.refresh_timer.stop()
        self.is_monitoring = False
        
        # 重新启动自动刷新定时器
        self.start_auto_refresh()
        
        logger.info("OCR监控已停止")
        return True

    def pixmap_to_cv2(self, pixmap):
        """将QPixmap转换为OpenCV图像"""
        try:
            import numpy as np
            import cv2
            
            # 将QPixmap转换为QImage
            qimage = pixmap.toImage()
            
            # 确保图像格式正确
            if qimage.format() != QImage.Format_RGB32:
                qimage = qimage.convertToFormat(QImage.Format_RGB32)
            
            # 获取图像数据
            width = qimage.width()
            height = qimage.height()
            
            # 获取图像数据
            bits = qimage.bits()
            bits.setsize(height * width * 4)  # 4 bytes per pixel (RGBA)
            
            # 转换为numpy数组
            arr = np.frombuffer(bits, np.uint8).reshape((height, width, 4))
            
            # 仅使用RGB通道
            img_cv = arr[:, :, :3]
            
            return img_cv
        except Exception as e:
            logger.error(f"将QPixmap转换为OpenCV图像失败: {e}")
            return None
    
    def cv2_to_pixmap(self, img_cv):
        """将OpenCV图像转换为QPixmap"""
        try:
            import numpy as np
            import cv2
            
            # 确保图像是RGB格式
            if len(img_cv.shape) == 2:  # 灰度图像
                img_cv = cv2.cvtColor(img_cv, cv2.COLOR_GRAY2RGB)
            elif img_cv.shape[2] == 4:  # RGBA图像
                img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGBA2RGB)
            
            # 转换为QImage
            height, width, channel = img_cv.shape
            bytes_per_line = 3 * width
            qimg = QImage(img_cv.data, width, height, bytes_per_line, QImage.Format_RGB888)
            
            # 转换为QPixmap
            pixmap = QPixmap.fromImage(qimg)
            
            return pixmap
        except Exception as e:
            logger.error(f"将OpenCV图像转换为QPixmap失败: {e}")
            return QPixmap()

    @pyqtSlot(str, dict)
    def on_text_recognized(self, text, details):
        """文本识别信号处理"""
        try:
            # 保存识别结果
            self.last_ocr_text = text
            self.last_ocr_details = details
            
            # 更新结果显示
            result_text = self.ocr_tab.right_panel.findChild(QObject, "result_text")
            if result_text:
                result_text.setPlainText(text)
            
            # 日志记录当前区域
            if self.current_rect:
                logger.info(f"OCR识别区域: X={self.current_rect.x()}, Y={self.current_rect.y()}, "
                           f"宽={self.current_rect.width()}, 高={self.current_rect.height()}")
            
            # 检查截图是否存在及其尺寸
            if self.current_screenshot and os.path.exists(self.current_screenshot):
                try:
                    import cv2
                    image = cv2.imread(self.current_screenshot)
                    if image is not None:
                        logger.info(f"当前截图尺寸: {image.shape}")
                except Exception as e:
                    logger.error(f"检查截图尺寸失败: {e}")
            
            # 更新主窗口的监控引擎
            main_window = self.ocr_tab.window()
            if main_window and hasattr(main_window, 'monitor_engine'):
                # 传递区域信息和当前截图路径
                extra_info = {
                    'rect': self.current_rect,
                    'screenshot': self.current_screenshot
                }
                # 将额外信息添加到details中
                if isinstance(details, dict):
                    details.update(extra_info)
                
                main_window.monitor_engine.process_text(text, details)
                
            logger.debug(f"收到文本识别结果: {len(text)} 字符")
            
        except Exception as e:
            logger.error(f"处理文本识别结果失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    @pyqtSlot(str)
    def on_error(self, error):
        """错误回调"""
        logger.error(f"OCR错误: {error}")
        QMessageBox.warning(
            self.ocr_tab, 
            "OCR错误", 
            f"OCR处理过程中发生错误: {error}"
        )

    def set_monitor_engine(self, monitor_engine):
        """设置监控引擎"""
        self.monitor_engine = monitor_engine
    
    def set_log_model(self, log_model):
        """设置日志模型
        
        Args:
            log_model: 日志模型
        """
        self.log_model = log_model

    def update_area_spinners(self):
        """更新区域坐标输入框"""
        if not self.current_rect:
            return
        
        # 更新坐标输入框
        x_spin = self.ocr_tab.left_panel.findChild(QObject, "x_spin")
        y_spin = self.ocr_tab.left_panel.findChild(QObject, "y_spin")
        width_spin = self.ocr_tab.left_panel.findChild(QObject, "width_spin")
        height_spin = self.ocr_tab.left_panel.findChild(QObject, "height_spin")
        
        
        if x_spin:
            x_spin.blockSignals(True)  # 阻止信号触发循环
            x_spin.setValue(self.current_rect.x())
            x_spin.blockSignals(False)
        if y_spin:
            y_spin.blockSignals(True)
            y_spin.setValue(self.current_rect.y())
            y_spin.blockSignals(False)
        if width_spin:
            width_spin.blockSignals(True)
            width_spin.setValue(self.current_rect.width())
            width_spin.blockSignals(False)
        if height_spin:
            height_spin.blockSignals(True)
            height_spin.setValue(self.current_rect.height())
            height_spin.blockSignals(False)
        
        # 保存区域到配置
        self.save_area_to_config()

    @pyqtSlot()
    def update_area_from_spinners(self):
        """从坐标输入框更新区域
        
        注意：由于坐标输入框现在是只读的，此方法不再被主动调用。
        保留此方法是为了兼容性，以避免现有代码出错。
        """
        # 已禁用: 所有坐标输入框都设置为只读，仅用于显示
        logger.debug("已禁用：坐标输入框现在是只读的，不再从UI更新坐标")
        return
        
        # 下面的代码不再执行
        # 获取坐标输入框
        # x_spin = self.ocr_tab.left_panel.findChild(QObject, "x_spin")
        # y_spin = self.ocr_tab.left_panel.findChild(QObject, "y_spin")
        # width_spin = self.ocr_tab.left_panel.findChild(QObject, "width_spin")
        # height_spin = self.ocr_tab.left_panel.findChild(QObject, "height_spin")
        # 
        # # 创建新区域
        # if x_spin and y_spin and width_spin and height_spin:
        #     x = x_spin.value()
        #     y = y_spin.value()
        #     width = width_spin.value()
        #     height = height_spin.value()
        #     
        #     if width > 0 and height > 0:
        #         self.current_rect = QRect(x, y, width, height)
        #         logger.info(f"区域已从坐标输入框更新: {self.current_rect}")
        #         
        #         # 更新预览
        #         self.update_preview()
        #         
        #         # 保存区域到配置
        #         self.save_area_to_config()
        #         logger.info(f"已保存更新后的区域到配置: {self.current_rect}")

    @pyqtSlot(str)
    def update_language(self, language):
        """更新OCR语言"""
        if not language:
            return
        
        # 获取语言代码
        lang_code = self.ocr_processor.LANGUAGE_MAPPING_REVERSE.get(language, 'chi_sim')
        
        # 更新OCR配置
        self.ocr_processor.set_config({'language': lang_code})
        logger.info(f"OCR语言已更新: {language} ({lang_code})")

    @pyqtSlot(int)
    def update_accuracy(self, value):
        """更新OCR精度"""
        # 更新OCR配置
        self.ocr_processor.set_config({'accuracy': value})
        
        # 更新显示
        accuracy_value = self.ocr_tab.left_panel.findChild(
            QObject, "accuracy_value"
        )
        if accuracy_value:
            accuracy_value.setText(f"{value}%")
        
        logger.info(f"OCR精度已更新: {value}%")

    @pyqtSlot(int)
    def update_preprocess(self, state):
        """更新图像预处理设置"""
        # 更新OCR配置
        self.ocr_processor.set_config({'preprocess': bool(state)})
        logger.info(f"OCR预处理已{'启用' if state else '禁用'}")

    @pyqtSlot(int)
    def update_autocorrect(self, state):
        """更新文本自动修正设置"""
        # 更新OCR配置
        self.ocr_processor.set_config({'autocorrect': bool(state)})
        logger.info(f"OCR文本自动修正已{'启用' if state else '禁用'}")

    @pyqtSlot(int)
    def update_psm(self, index):
        """更新PSM模式"""
        # 更新OCR配置
        self.ocr_processor.set_config({'psm': index})
        logger.info(f"OCR PSM模式已更新: {index}")

    @pyqtSlot(int)
    def update_oem(self, index):
        """更新OEM引擎模式"""
        # 更新OCR配置
        self.ocr_processor.set_config({'oem': index})
        logger.info(f"OCR OEM引擎模式已更新: {index}")

    def save_area_to_config(self):
        """保存当前区域和OCR设置到配置"""
        try:
            # 获取主窗口
            main_window = self.ocr_tab.window()
            if not main_window or not hasattr(main_window, 'config_controller'):
                logger.warning("无法获取配置控制器，无法保存配置")
                return
            
            # 获取配置控制器
            config_controller = main_window.config_controller
            
            # 获取当前配置
            current_config = config_controller.config_manager.current_config
            config = config_controller.config_manager.get_config(current_config)
            
            # 确保OCR配置部分存在
            if 'ocr' not in config:
                config['ocr'] = {}
            
            # 获取当前OCR设置
            ocr_config = {}
            
            # 获取语言设置
            lang_combo = self.ocr_tab.left_panel.findChild(QObject, "lang_combo")
            if lang_combo:
                selected_lang = lang_combo.currentText()
                lang_code = self.ocr_processor.LANGUAGE_MAPPING_REVERSE.get(selected_lang, 'chi_sim')
                ocr_config['language'] = lang_code
                logger.debug(f"保存语言设置: {selected_lang} -> {lang_code}")
            
            # 获取PSM模式
            psm_combo = self.ocr_tab.left_panel.findChild(QObject, "psm_combo")
            if psm_combo:
                ocr_config['psm'] = str(psm_combo.currentIndex())
                logger.debug(f"保存PSM模式: {psm_combo.currentIndex()} ({psm_combo.currentText()})")
            
            # 获取OEM引擎模式
            oem_combo = self.ocr_tab.left_panel.findChild(QObject, "oem_combo")
            if oem_combo:
                ocr_config['oem'] = str(oem_combo.currentIndex())
                logger.debug(f"保存OEM引擎: {oem_combo.currentIndex()} ({oem_combo.currentText()})")
            
            # 获取精度设置
            accuracy_slider = self.ocr_tab.left_panel.findChild(QObject, "accuracy_slider")
            if accuracy_slider:
                ocr_config['accuracy'] = accuracy_slider.value()
                logger.debug(f"保存精度设置: {accuracy_slider.value()}%")
            
            # 获取预处理选项
            preprocess_check = self.ocr_tab.left_panel.findChild(QObject, "preprocess_check")
            if preprocess_check:
                ocr_config['preprocess'] = preprocess_check.isChecked()
                logger.debug(f"保存预处理选项: {preprocess_check.isChecked()}")
            
            # 获取自动修正选项
            autocorrect_check = self.ocr_tab.left_panel.findChild(QObject, "autocorrect_check")
            if autocorrect_check:
                ocr_config['autocorrect'] = autocorrect_check.isChecked()
                logger.debug(f"保存自动修正选项: {autocorrect_check.isChecked()}")
            
            # 获取屏幕区域
            if self.current_rect:
                ocr_config['screen_area'] = {
                    'x': self.current_rect.x(),
                    'y': self.current_rect.y(),
                    'width': self.current_rect.width(),
                    'height': self.current_rect.height(),
                    'is_selected': True
                }
                logger.debug(f"保存屏幕区域: {self.current_rect}")
            
            # 更新OCR配置
            config['ocr'] = ocr_config
            
            # 保存配置
            config_controller.config_manager.save_config(current_config, config)
            logger.info(f"已保存OCR配置: {ocr_config}")
            
            # 更新OCR处理器配置，但不更新UI
            self.ocr_processor.set_config(ocr_config)
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def load_area_from_config(self):
        """从配置加载保存的区域和OCR设置"""
        try:
            # 获取主窗口
            main_window = self.ocr_tab.window()
            if not main_window:
                logger.warning("无法获取主窗口")
                return
            if not hasattr(main_window, 'config_controller'):
                logger.warning("主窗口没有config_controller属性")
                return
            
            # 获取配置控制器
            config_controller = main_window.config_controller
            
            # 获取当前配置
            current_config = config_controller.config_manager.current_config
            logger.info(f"当前配置: {current_config}")
            
            config = config_controller.config_manager.get_config(current_config)
            logger.debug(f"配置内容: {config}")
            
            # 获取OCR配置
            if 'ocr' in config:
                ocr_config = config['ocr']
                logger.debug(f"OCR配置: {ocr_config}")
                
                # 加载语言设置
                if 'language' in ocr_config:
                    language_code = ocr_config['language']
                    language_text = self.ocr_processor.LANGUAGE_MAPPING.get(language_code, '中文简体')
                    
                    lang_combo = self.ocr_tab.left_panel.findChild(QObject, "lang_combo")
                    if lang_combo:
                        index = lang_combo.findText(language_text)
                        if index >= 0:
                            lang_combo.setCurrentIndex(index)
                            logger.debug(f"设置语言为: {language_text}")
                
                # 加载PSM模式
                if 'psm' in ocr_config:
                    psm_combo = self.ocr_tab.left_panel.findChild(QObject, "psm_combo")
                    if psm_combo:
                        psm_value = int(ocr_config['psm'])
                        if 0 <= psm_value < psm_combo.count():
                            psm_combo.setCurrentIndex(psm_value)
                            logger.debug(f"设置PSM模式为: {psm_value}")
                
                # 加载OEM引擎
                if 'oem' in ocr_config:
                    oem_combo = self.ocr_tab.left_panel.findChild(QObject, "oem_combo")
                    if oem_combo:
                        oem_value = int(ocr_config['oem'])
                        if 0 <= oem_value < oem_combo.count():
                            oem_combo.setCurrentIndex(oem_value)
                            logger.debug(f"设置OEM引擎为: {oem_value}")
                
                # 加载精度设置
                if 'accuracy' in ocr_config:
                    accuracy_slider = self.ocr_tab.left_panel.findChild(QObject, "accuracy_slider")
                    if accuracy_slider:
                        accuracy_slider.setValue(ocr_config['accuracy'])
                        logger.debug(f"设置精度为: {ocr_config['accuracy']}")
                        
                        # 同时更新精度显示值
                        accuracy_value = self.ocr_tab.left_panel.findChild(QObject, "accuracy_value")
                        if accuracy_value:
                            accuracy_value.setText(f"{ocr_config['accuracy']}%")
                
                # 加载预处理选项
                if 'preprocess' in ocr_config:
                    preprocess_check = self.ocr_tab.left_panel.findChild(QObject, "preprocess_check")
                    if preprocess_check:
                        preprocess_check.setChecked(ocr_config['preprocess'])
                        logger.debug(f"设置预处理为: {ocr_config['preprocess']}")
                
                # 加载文本修正选项
                if 'autocorrect' in ocr_config:
                    autocorrect_check = self.ocr_tab.left_panel.findChild(QObject, "autocorrect_check")
                    if autocorrect_check:
                        autocorrect_check.setChecked(ocr_config['autocorrect'])
                        logger.debug(f"设置自动修正为: {ocr_config['autocorrect']}")
                
                # 加载屏幕区域配置
                if 'screen_area' in ocr_config:
                    area_config = ocr_config['screen_area']
                    logger.debug(f"屏幕区域配置: {area_config}")
                    
                    if 'x' in area_config and 'y' in area_config and 'width' in area_config and 'height' in area_config:
                        # 创建区域对象
                        self.current_rect = QRect(
                            area_config['x'], area_config['y'],
                            area_config['width'], area_config['height']
                        )
                        logger.info(f"已从配置加载区域: {self.current_rect}")
                        
                        # 更新UI
                        self.update_area_spinners()
                        
                        # 更新预览
                        self.update_preview()
                
                # 确保OCR处理器更新了所有配置
                self.ocr_processor.set_config(ocr_config)
                logger.info("已更新OCR处理器配置")
            else:
                logger.warning("配置中没有ocr字段")
        except Exception as e:
            logger.error(f"从配置加载OCR设置失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def start_auto_refresh(self):
        """启动自动刷新预览"""
        if not self.current_rect:
            return
        
        # 只有在有选定区域和有截图的情况下才启动自动刷新
        if not self.current_screenshot or not os.path.exists(self.current_screenshot):
            logger.debug("没有有效的截图，不启动自动刷新")
            return
        
        # 设置较长的刷新间隔，减少刷新频率
        refresh_interval = 5000  # 5秒刷新一次，避免频繁刷新导致位置丢失
        
        # 启动定时器
        if self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.stop()
        self.auto_refresh_timer.start(refresh_interval)
        logger.debug(f"已启动OCR预览自动刷新，间隔: {refresh_interval}毫秒")

    def perform_ocr(self):
        """执行OCR操作"""
        try:
            # 检查是否有选择的区域
            if not self.current_rect:
                self.show_message("请先选择一个屏幕区域")
                return
            
            # 检查是否有截图
            if not self.current_screenshot or not os.path.exists(self.current_screenshot):
                self.show_message("没有可用的截图")
                return
            
            # 使用直接截图OCR方法获取最新图像并识别
            self.direct_screenshot_ocr(self.current_rect)
            
            # 显示结果在界面上
            if self.last_ocr_text:
                self.ocr_tab.right_panel.findChild(QObject, "result_text").setPlainText(self.last_ocr_text)
                self.show_message(f"OCR识别完成，共 {len(self.last_ocr_text)} 个字符", color="green")
            else:
                self.show_message("OCR识别完成，但没有识别到文本", color="orange")
            
        except Exception as e:
            logger.error(f"执行OCR操作失败: {e}")
            self.show_message(f"OCR识别失败: {str(e)}", color="red")
            import traceback
            logger.error(traceback.format_exc())

    @pyqtSlot()
    def refresh_ocr(self):
        """刷新OCR识别结果"""
        try:
            if not self.current_rect:
                logger.debug("刷新OCR：没有选择区域，无法刷新OCR")
                return

            # 优先使用原始截图进行OCR识别
            from ui.components.area_selector_mac import MacScreenCaptureSelector
            
            if MacScreenCaptureSelector.original_capture_path and os.path.exists(MacScreenCaptureSelector.original_capture_path):
                logger.info(f"刷新OCR：使用原始截图: {MacScreenCaptureSelector.original_capture_path}")
                
                # 读取原始截图
                image = cv2.imread(MacScreenCaptureSelector.original_capture_path)
                
                if image is not None:
                    # 转换为RGB格式
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    logger.debug(f"成功加载原始截图，尺寸: {image.shape}")
                    
                    # 使用OCR处理器识别图像
                    text, details = self.ocr_processor.recognize_text(image)
                    
                    # 保存识别结果
                    self.last_ocr_text = text
                    self.last_ocr_details = details
                    
                    # 更新结果显示
                    result_text = self.ocr_tab.right_panel.findChild(QObject, "result_text")
                    if result_text:
                        result_text.setPlainText(text)
                    
                    # 添加区域信息到结果中
                    details['rect'] = {
                        'x': self.current_rect.x(),
                        'y': self.current_rect.y(),
                        'width': self.current_rect.width(),
                        'height': self.current_rect.height(),
                        'original_rect': self.current_rect
                    }
                    
                    details['screenshot'] = MacScreenCaptureSelector.original_capture_path
                    
                    # 触发文本识别信号
                    self.text_recognized.emit(text, details)
                    
                    logger.debug(f"刷新OCR：成功识别 {len(text)} 个字符")
                    return
            
            # 如果没有原始截图，使用直接截图OCR方法
            logger.warning("刷新OCR：原始截图不可用，使用直接截图OCR方法")
            self.direct_screenshot_ocr(self.current_rect)
            
        except Exception as e:
            logger.error(f"刷新OCR识别失败: {e}")
            self.show_message(f"刷新OCR识别失败: {str(e)}", color="red")
            import traceback
            logger.error(traceback.format_exc())

    def shutdown(self):
        """关闭OCR控制器，释放资源"""
        try:
            logger.info("关闭OCR控制器...")
            
            # 停止监控
            if self.is_monitoring:
                self.stop_monitoring()
            
            # 停止定时器
            if self.auto_refresh_timer.isActive():
                self.auto_refresh_timer.stop()
            
            if self.refresh_timer.isActive():
                self.refresh_timer.stop()
            
            # 删除临时文件
            if self.current_screenshot and os.path.exists(self.current_screenshot):
                try:
                    os.remove(self.current_screenshot)
                    logger.debug(f"已删除临时截图文件: {self.current_screenshot}")
                except Exception as e:
                    logger.warning(f"删除临时截图文件失败: {e}")
            
            logger.info("OCR控制器已关闭")
        except Exception as e:
            logger.error(f"关闭OCR控制器时发生错误: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def correct_screen_coordinates(self, rect):
        """修正屏幕坐标，考虑DPI缩放和屏幕边界
        
        Args:
            rect: 原始区域
            
        Returns:
            QRect: 修正后的区域
        """
        try:
            # 获取屏幕尺寸
            screen_width, screen_height = pyautogui.size()
            
            # 获取DPI缩放因子
            dpi_scale = self.screen_capture.dpi_scale
            
            # 检查是否需要DPI缩放调整
            if dpi_scale != 1.0 and self.screen_capture.config.get('compensate_dpi', True):
                logger.info(f"应用DPI缩放调整，缩放因子: {dpi_scale}")
                # 注意：这里我们反向应用缩放因子，因为我们是从屏幕坐标转换到实际坐标
                x = int(rect.x() / dpi_scale)
                y = int(rect.y() / dpi_scale)
                width = int(rect.width() / dpi_scale)
                height = int(rect.height() / dpi_scale)
            else:
                x = rect.x()
                y = rect.y()
                width = rect.width()
                height = rect.height()
            
            # 确保坐标在屏幕范围内
            x = max(0, min(x, screen_width - 1))
            y = max(0, min(y, screen_height - 1))
            width = max(1, min(width, screen_width - x))
            height = max(1, min(height, screen_height - y))
            
            # 创建新的区域
            corrected_rect = QRect(x, y, width, height)
            
            # 记录坐标调整
            if rect != corrected_rect:
                logger.info(f"坐标已调整: {rect} -> {corrected_rect}")
            
            return corrected_rect
            
        except Exception as e:
            logger.error(f"坐标调整失败: {e}")
            return rect  # 如果调整失败，返回原始区域
