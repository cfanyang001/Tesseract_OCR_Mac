import os
from PyQt5.QtCore import QObject, QRect, pyqtSlot, QTimer, QBuffer
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QMessageBox, QInputDialog

from core.ocr_processor import OCRProcessor
from core.screen_capture import ScreenCapture
from core.text_recognizer import TextRecognizer
from ui.components.tabs.ocr_tab import OCRTab
from ui.components.area_selector_mac import MacScreenCaptureSelector

from loguru import logger
import tempfile
import cv2


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
        
        # 设置PSM模式
        psm_combo = self.ocr_tab.left_panel.findChild(
            QObject, "psm_combo"
        )
        if psm_combo:
            psm_combo.setCurrentIndex(self.ocr_processor.config['psm'])
        
        # 设置OEM引擎模式
        oem_combo = self.ocr_tab.left_panel.findChild(
            QObject, "oem_combo"
        )
        if oem_combo:
            oem_combo.setCurrentIndex(self.ocr_processor.config['oem'])
        
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
            
            # 使用Mac原生截图工具
            rect, pixmap, temp_filename = MacScreenCaptureSelector.select_area()
            
            if not rect or not pixmap:
                logger.warning("区域选择被取消或失败")
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
            
            # 直接使用系统截图工具返回的区域，默认从(0,0)开始
            # 如果需要调整位置，用户可以通过坐标输入框调整
            width = pixmap.width()
            height = pixmap.height()
            
            # 使用之前的位置（如果有）
            x = 0
            y = 0
            if self.current_rect:
                x = self.current_rect.x()
                y = self.current_rect.y()
            
            # 创建新区域
            self.current_rect = QRect(x, y, width, height)
            
            # 更新UI
            self.update_area_spinners()
            
            logger.info(f"区域已选择: {self.current_rect}")
            
        except Exception as e:
            logger.error(f"区域选择失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
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
            # 使用Mac原生截图工具捕获当前区域
            pixmap, temp_filename = MacScreenCaptureSelector.capture_rect(self.current_rect)
            
            if not pixmap:
                logger.error("区域截图失败")
                return
            
            # 更新预览
            self.ocr_tab.preview.set_image(pixmap)
            
            # 更新当前截图路径
            if self.current_screenshot and os.path.exists(self.current_screenshot) and self.current_screenshot != temp_filename:
                try:
                    os.remove(self.current_screenshot)
                except:
                    pass
            self.current_screenshot = temp_filename
            
            logger.debug(f"预览已更新: {pixmap.width()}x{pixmap.height()}")
            
        except Exception as e:
            logger.error(f"更新预览失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    @pyqtSlot()
    def test_ocr(self):
        """测试OCR识别"""
        try:
            # 直接使用当前预览图像进行识别
            pixmap = self.ocr_tab.preview.preview_image
            
            if pixmap is None or pixmap.isNull():
                QMessageBox.warning(
                    self.ocr_tab, 
                    "警告", 
                    "预览图像为空，请先选择区域"
                )
                return
            
            # 将QPixmap转换为PIL Image
            import numpy as np
            from PIL import Image
            import io
            import cv2
            
            # 将QPixmap转换为QImage
            qimage = pixmap.toImage()
            
            # 获取图像数据
            width = qimage.width()
            height = qimage.height()
            
            # 转换为RGB格式
            if qimage.format() != QImage.Format_RGB32:
                qimage = qimage.convertToFormat(QImage.Format_RGB32)
            
            # 获取图像数据
            bits = qimage.bits()
            bits.setsize(height * width * 4)  # 4 bytes per pixel (RGBA)
            
            # 转换为numpy数组
            arr = np.frombuffer(bits, np.uint8).reshape((height, width, 4))
            
            # 仅使用RGB通道
            img_np = arr[:, :, :3]
            
            # 保存原始图像用于显示
            original_img = Image.fromarray(img_np)
            
            # 创建多种预处理图像
            processed_images = []
            
            # 1. 灰度图像
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            processed_images.append(("灰度", gray))
            
            # 2. 反相图像 - 对于白色文字在黑色背景上效果好
            inverted = cv2.bitwise_not(gray)
            processed_images.append(("反相", inverted))
            
            # 3. 二值化 - 自适应阈值
            binary_adaptive = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            processed_images.append(("二值化(自适应)", binary_adaptive))
            
            # 4. 二值化 - Otsu's方法
            _, binary_otsu = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            processed_images.append(("二值化(Otsu)", binary_otsu))
            
            # 5. 边缘增强
            edges = cv2.Canny(gray, 100, 200)
            processed_images.append(("边缘", edges))
            
            # 6. 锐化
            kernel_sharpen = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(gray, -1, kernel_sharpen)
            processed_images.append(("锐化", sharpened))
            
            # 7. 膨胀 - 连接断开的笔画
            kernel = np.ones((2, 2), np.uint8)
            dilated = cv2.dilate(binary_adaptive, kernel, iterations=1)
            processed_images.append(("膨胀", dilated))
            
            # 8. 放大图像
            scale_factor = 2
            enlarged = cv2.resize(binary_adaptive, None, 
                                 fx=scale_factor, fy=scale_factor, 
                                 interpolation=cv2.INTER_CUBIC)
            processed_images.append(("放大", enlarged))
            
            # 获取当前选择的PSM和OEM模式
            psm_combo = self.ocr_tab.left_panel.findChild(QObject, "psm_combo")
            oem_combo = self.ocr_tab.left_panel.findChild(QObject, "oem_combo")
            
            psm_index = psm_combo.currentIndex() if psm_combo else 7
            oem_index = oem_combo.currentIndex() if oem_combo else 1
            
            # 获取当前语言
            lang_code = self.ocr_processor.config['language']
            
            # 尝试所有预处理方法并保存结果
            results = []
            
            for name, img in processed_images:
                # 构建Tesseract配置
                config = f'--psm {psm_index} --oem {oem_index} -l {lang_code}'
                
                # 识别文本
                pil_img = Image.fromarray(img)
                text, details = self.ocr_processor.recognize_text(
                    np.array(pil_img), config=config
                )
                
                # 保存结果
                if text.strip():
                    results.append((text, details['confidence'], name, img))
            
            # 如果没有结果，尝试直接使用原始图像
            if not results:
                config = f'--psm {psm_index} --oem {oem_index} -l {lang_code}'
                text, details = self.ocr_processor.recognize_text(
                    img_np, config=config
                )
                if text.strip():
                    results.append((text, details['confidence'], "原始", img_np))
            
            # 选择最佳结果
            if results:
                # 按置信度排序
                results.sort(key=lambda x: x[1], reverse=True)
                best_text, best_confidence, best_method, best_img = results[0]
                
                # 显示最佳预处理图像
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                temp_filename = temp_file.name
                temp_file.close()
                
                # 保存最佳图像
                Image.fromarray(best_img).save(temp_filename)
                
                # 加载到QPixmap并显示
                enhanced_pixmap = QPixmap(temp_filename)
                if not enhanced_pixmap.isNull():
                    self.ocr_tab.preview.set_image(enhanced_pixmap)
                
                # 显示结果
                result_text = f"""识别文本:
{best_text}

置信度: {best_confidence}%
预处理方法: {best_method}
PSM模式: {psm_index}
OEM引擎: {oem_index}
"""
                self.ocr_tab.result_label.setText(result_text)
                logger.info(f"OCR测试完成: '{best_text}', 置信度: {best_confidence}%, 方法: {best_method}")
                
                # 清理临时文件
                try:
                    os.remove(temp_filename)
                except:
                    pass
            else:
                self.ocr_tab.result_label.setText("未识别到文本")
                logger.warning("OCR未能识别任何文本")
            
        except Exception as e:
            logger.error(f"OCR测试失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
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
