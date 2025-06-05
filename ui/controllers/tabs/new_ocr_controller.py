import os
import subprocess
import tempfile
import traceback
from PyQt5.QtCore import QObject, QRect, pyqtSlot, QTimer, QBuffer
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QMessageBox, QInputDialog

from core.ocr_processor import OCRProcessor
from core.screen_capture import ScreenCapture
from core.text_recognizer import TextRecognizer
from ui.components.tabs.ocr_tab import OCRTab

from loguru import logger


class OCRController(QObject):
    """OCR标签页控制器，负责连接OCR标签页与OCR处理器"""
    
    def __init__(self, ocr_tab: OCRTab):
        super().__init__()
        
        self.ocr_tab = ocr_tab
        
        # 创建OCR处理器、屏幕捕获器和文本识别器
        try:
            self.ocr_processor = OCRProcessor()
            self.screen_capture = ScreenCapture()
            self.text_recognizer = TextRecognizer()
            logger.info("OCR控制器初始化成功")
        except Exception as e:
            logger.error(f"OCR控制器初始化失败: {e}")
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
        
        # 自动刷新定时器
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
        
        # 语言选择
        lang_combo = self.ocr_tab.left_panel.findChild(
            QObject, "lang_combo"
        )
        if lang_combo:
            lang_combo.currentTextChanged.connect(self.update_language)
        
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
        
        # 刷新频率
        refresh_combo = self.ocr_tab.left_panel.findChild(
            QObject, "refresh_combo"
        )
        if refresh_combo:
            refresh_combo.currentTextChanged.connect(self.update_refresh_rate)
        
        # 区域坐标输入
        for name in ["x_spin", "y_spin", "width_spin", "height_spin"]:
            spin = self.ocr_tab.left_panel.findChild(QObject, name)
            if spin:
                spin.valueChanged.connect(self.update_area_from_spinners)
        
        # 文本识别器信号
        self.text_recognizer.text_recognized.connect(self.on_text_recognized)
        self.text_recognizer.error_occurred.connect(self.on_error)
    
    def init_ui(self):
        """初始化UI"""
        # 设置语言选项
        lang_combo = self.ocr_tab.left_panel.findChild(
            QObject, "lang_combo"
        )
        if lang_combo:
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
        
        # 设置精度
        accuracy_slider = self.ocr_tab.left_panel.findChild(
            QObject, "accuracy_slider"
        )
        if accuracy_slider:
            accuracy_slider.setValue(self.ocr_processor.config['accuracy'])
        
        # 设置预处理选项
        preprocess_check = self.ocr_tab.left_panel.findChild(
            QObject, "preprocess_check"
        )
        if preprocess_check:
            preprocess_check.setChecked(self.ocr_processor.config['preprocess'])
        
        # 设置自动修正选项
        autocorrect_check = self.ocr_tab.left_panel.findChild(
            QObject, "autocorrect_check"
        )
        if autocorrect_check:
            autocorrect_check.setChecked(self.ocr_processor.config['autocorrect'])
    
    @pyqtSlot()
    def select_area(self):
        """选择屏幕区域"""
        try:
            # 告知用户如何操作
            QMessageBox.information(
                self.ocr_tab,
                "区域选择",
                "请使用系统截图工具选择要监控的区域。\n\n操作方法：\n1. 在屏幕上拖拽选择一个区域\n2. 松开鼠标完成选择"
            )
            
            # 使用系统截图工具
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_filename = temp_file.name
            temp_file.close()
            
            # 启动截图工具
            logger.info("启动系统截图工具")
            
            # 获取当前活跃窗口
            import AppKit
            active_app = AppKit.NSWorkspace.sharedWorkspace().activeApplication()
            
            # 运行截图命令
            subprocess.run(['screencapture', '-i', '-s', temp_filename], check=True)
            
            # 激活原应用窗口
            if active_app:
                app_name = active_app['NSApplicationName']
                subprocess.run(['osascript', '-e', f'tell application "{app_name}" to activate'], check=False)
            
            # 检查文件是否存在和有效
            if not os.path.exists(temp_filename) or os.path.getsize(temp_filename) == 0:
                logger.warning("未选择区域或截图被取消")
                try:
                    os.remove(temp_filename)
                except:
                    pass
                return
            
            # 加载截图
            pixmap = QPixmap(temp_filename)
            if pixmap.isNull():
                logger.error("截图加载失败")
                QMessageBox.warning(self.ocr_tab, "错误", "无法加载截图")
                try:
                    os.remove(temp_filename)
                except:
                    pass
                return
            
            # 设置截图预览
            self.ocr_tab.preview.set_image(pixmap)
            
            # 保存当前截图路径
            if self.current_screenshot and os.path.exists(self.current_screenshot):
                try:
                    os.remove(self.current_screenshot)
                except:
                    pass
            self.current_screenshot = temp_filename
            
            # 获取鼠标当前位置作为区域的左上角（简化实现）
            # 在macOS中，无法直接获取选择的区域坐标，但我们可以使用截图的大小
            width = pixmap.width()
            height = pixmap.height()
            
            # 获取鼠标当前位置
            cursor_pos = self.ocr_tab.mapFromGlobal(self.ocr_tab.cursor().pos())
            x = max(0, cursor_pos.x() - width//2)
            y = max(0, cursor_pos.y() - height//2)
            
            # 创建新区域
            self.current_rect = QRect(x, y, width, height)
            
            # 更新UI
            self.update_area_spinners()
            
            # 告知用户
            QMessageBox.information(
                self.ocr_tab,
                "区域已选择",
                f"已选择区域大小: {width}x{height}\n\n您可以在坐标输入框中调整区域位置。"
            )
            
            logger.info(f"区域已选择: {self.current_rect}")
            
        except Exception as e:
            logger.error(f"区域选择失败: {e}")
            traceback.print_exc()
            QMessageBox.warning(
                self.ocr_tab,
                "选择失败",
                f"区域选择过程出错: {e}"
            )
    
    @pyqtSlot()
    def update_preview(self):
        """更新预览"""
        if not self.current_rect:
            return
        
        try:
            # 重新截图
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            temp_filename = temp_file.name
            temp_file.close()
            
            x = self.current_rect.x()
            y = self.current_rect.y()
            width = self.current_rect.width()
            height = self.current_rect.height()
            
            # 使用screencapture截取指定区域
            logger.debug(f"截取区域: x={x}, y={y}, w={width}, h={height}")
            subprocess.run([
                'screencapture',
                '-R', f"{x},{y},{width},{height}",
                '-x',  # 静默模式，不发出声音
                temp_filename
            ], check=True)
            
            # 检查文件是否有效
            if not os.path.exists(temp_filename) or os.path.getsize(temp_filename) == 0:
                logger.error("区域截图失败")
                try:
                    os.remove(temp_filename)
                except:
                    pass
                return
            
            # 加载新截图
            pixmap = QPixmap(temp_filename)
            if pixmap.isNull():
                logger.error("新截图加载失败")
                try:
                    os.remove(temp_filename)
                except:
                    pass
                return
            
            logger.debug(f"截图尺寸: {pixmap.width()}x{pixmap.height()}")
            
            # 更新预览
            self.ocr_tab.preview.set_image(pixmap)
            
            # 更新当前截图路径
            if self.current_screenshot and os.path.exists(self.current_screenshot) and self.current_screenshot != temp_filename:
                try:
                    os.remove(self.current_screenshot)
                except:
                    pass
            self.current_screenshot = temp_filename
            
            logger.debug(f"预览已更新: {width}x{height}")
            
        except Exception as e:
            logger.error(f"更新预览失败: {e}")
            traceback.print_exc()
    
    @pyqtSlot()
    def test_ocr(self):
        """测试OCR识别"""
        if not self.current_rect:
            QMessageBox.warning(
                self.ocr_tab,
                "警告",
                "请先选择屏幕区域"
            )
            return
        
        try:
            # 确保有最新截图
            self.update_preview()
            
            # 检查截图是否有效
            if not self.current_screenshot or not os.path.exists(self.current_screenshot):
                QMessageBox.warning(
                    self.ocr_tab,
                    "警告",
                    "无法获取当前区域的截图"
                )
                return
            
            # 加载截图
            from PIL import Image
            import numpy as np
            
            # 打开图像
            pil_image = Image.open(self.current_screenshot)
            
            # 转换为numpy数组
            image_array = np.array(pil_image)
            
            # 识别文本
            text, details = self.ocr_processor.recognize_text(image_array)
            
            # 显示结果
            if text:
                result_text = f"""识别文本:
{text}

置信度: {details['confidence']}%
词数: {details['word_count']}
字符数: {details['char_count']}
"""
                self.ocr_tab.result_label.setText(result_text)
            else:
                self.ocr_tab.result_label.setText("未识别到文本")
            
            logger.info(f"OCR测试完成: {len(text)} 字符, 置信度: {details['confidence']}%")
            
        except Exception as e:
            logger.error(f"OCR测试失败: {e}")
            traceback.print_exc()
            self.ocr_tab.result_label.setText(f"OCR识别失败: {e}")
    
    def update_area_spinners(self):
        """根据当前区域更新坐标输入框"""
        if not self.current_rect:
            return
        
        # 更新坐标输入框
        for name, value in [
            ("x_spin", self.current_rect.x()),
            ("y_spin", self.current_rect.y()),
            ("width_spin", self.current_rect.width()),
            ("height_spin", self.current_rect.height())
        ]:
            spin = self.ocr_tab.left_panel.findChild(QObject, name)
            if spin:
                spin.blockSignals(True)  # 阻止信号触发循环
                spin.setValue(value)
                spin.blockSignals(False)
    
    @pyqtSlot()
    def update_area_from_spinners(self):
        """根据坐标输入框更新当前区域"""
        # 获取坐标值
        x_spin = self.ocr_tab.left_panel.findChild(QObject, "x_spin")
        y_spin = self.ocr_tab.left_panel.findChild(QObject, "y_spin")
        width_spin = self.ocr_tab.left_panel.findChild(QObject, "width_spin")
        height_spin = self.ocr_tab.left_panel.findChild(QObject, "height_spin")
        
        if not all([x_spin, y_spin, width_spin, height_spin]):
            return
        
        # 创建新的区域
        x = x_spin.value()
        y = y_spin.value()
        width = width_spin.value()
        height = height_spin.value()
        
        self.current_rect = QRect(x, y, width, height)
        
        # 更新预览
        self.update_preview()
    
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
    
    @pyqtSlot(str)
    def update_refresh_rate(self, rate_text):
        """更新刷新频率"""
        # 获取刷新频率值 (毫秒)
        if rate_text == "低 (1秒)":
            rate = 1000
        elif rate_text == "中 (0.5秒)":
            rate = 500
        elif rate_text == "高 (0.2秒)":
            rate = 200
        else:  # 自定义
            rate = 1000
        
        # 更新文本识别器配置
        self.text_recognizer.set_config({'refresh_rate': rate})
        
        # 更新定时器
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
            self.refresh_timer.start(rate)
        
        logger.info(f"刷新频率已更新: {rate_text} ({rate}毫秒)")
    
    @pyqtSlot(str, dict)
    def on_text_recognized(self, text, details):
        """文本识别回调"""
        if not text:
            return
        
        # 更新结果显示
        result_text = f"""识别文本:
{text}

置信度: {details['confidence']}%
词数: {details['word_count']}
字符数: {details['char_count']}
"""
        self.ocr_tab.result_label.setText(result_text)
    
    @pyqtSlot(str)
    def on_error(self, error):
        """错误回调"""
        logger.error(f"OCR错误: {error}")
        QMessageBox.warning(
            self.ocr_tab, 
            "OCR错误", 
            f"OCR处理过程中发生错误: {error}"
        ) 