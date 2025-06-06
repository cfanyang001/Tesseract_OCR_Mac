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
            # 告知用户如何操作
            QMessageBox.information(
                self.ocr_tab,
                "区域选择",
                "请使用系统截图工具选择要监控的区域。\n\n操作方法：\n1. 在屏幕上拖拽选择一个区域\n2. 松开鼠标完成选择\n\n系统会自动记录所选区域的坐标。"
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
            
            # 使用MacScreenCaptureSelector返回的完整区域信息
            self.current_rect = rect
            
            # 更新UI
            self.update_area_spinners()
            
            # 保存区域到配置
            self.save_area_to_config()
            
            # 确保自动刷新已启动
            if not self.auto_refresh_timer.isActive():
                self.start_auto_refresh()
            
            logger.info(f"区域已选择: {self.current_rect}")
            
        except Exception as e:
            logger.error(f"区域选择失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.warning(
                self.ocr_tab,
                "错误",
                f"区域选择失败: {e}"
            )
    
    @pyqtSlot()
    def update_preview(self):
        """更新预览"""
        try:
            # 检查是否有选择的区域
            if not self.current_rect:
                logger.debug("没有选择区域，无法更新预览")
                return
            
            # 捕获屏幕区域
            image = self.screen_capture.capture_area(self.current_rect)
            
            # 转换为QPixmap
            if image is not None:
                try:
                    # 创建临时文件保存预览图像
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                        temp_filename = temp_file.name
                    
                    # 保存图像
                    import cv2
                    cv2.imwrite(temp_filename, image)
                    
                    # 保存当前截图路径
                    self.current_screenshot = temp_filename
                    
                    # 加载QPixmap
                    pixmap = QPixmap(temp_filename)
                    
                    # 设置预览图像
                    self.ocr_tab.preview.set_image(pixmap)
                    
                    logger.debug(f"已更新预览，图像大小: {pixmap.width()}x{pixmap.height()}")
                    
                    # 获取当前选择的区域信息
                    x, y, width, height = (
                        self.current_rect.x(),
                        self.current_rect.y(),
                        self.current_rect.width(),
                        self.current_rect.height()
                    )
                    
                    # 更新状态栏
                    main_window = self.ocr_tab.window()
                    if main_window and hasattr(main_window, 'status_bar'):
                        main_window.status_bar.update_screen_area(
                            f"{x},{y} {width}x{height}"
                        )
                except Exception as inner_e:
                    logger.error(f"处理预览图像失败: {inner_e}")
                    import traceback
                    logger.error(traceback.format_exc())
                    # 即使处理失败也不中断监控流程
            else:
                logger.warning("截图获取失败，可能是区域无效或截图权限问题")
                
        except Exception as e:
            logger.error(f"更新预览失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # 即使发生异常也不中断监控流程
    
    @pyqtSlot()
    def test_ocr(self):
        """测试OCR识别"""
        try:
            # 检查是否选择了区域
            if not self.current_rect:
                QMessageBox.warning(
                    self.ocr_tab, 
                    "警告", 
                    "请先选择一个区域"
                )
                return
            
            # 先更新预览，确保使用最新的屏幕内容
            self.update_preview()
            
            # 使用文本识别器识别当前区域
            text, details = self.text_recognizer.recognize_area(self.current_rect)
            
            # 保存识别结果
            self.last_ocr_text = text
            self.last_ocr_details = details
            
            # 更新结果显示
            result_text = self.ocr_tab.right_panel.findChild(
                QObject, "result_text"
            )
            if result_text:
                result_text.setPlainText(text)
            
            # 更新详细信息
            confidence_label = self.ocr_tab.right_panel.findChild(
                QObject, "confidence_label"
            )
            if confidence_label:
                confidence = details.get('confidence', 0)
                confidence_label.setText(f"置信度: {confidence}%")
            
            word_count_label = self.ocr_tab.right_panel.findChild(
                QObject, "word_count_label"
            )
            if word_count_label:
                word_count = details.get('word_count', 0)
                word_count_label.setText(f"词数: {word_count}")
            
            char_count_label = self.ocr_tab.right_panel.findChild(
                QObject, "char_count_label"
            )
            if char_count_label:
                char_count = details.get('char_count', 0)
                char_count_label.setText(f"字符数: {char_count}")
                
            # 显示文本框位置
            preview_label = self.ocr_tab.right_panel.findChild(
                QObject, "preview_label"
            )
            if preview_label and self.current_screenshot:
                # 加载预览图像
                pixmap = QPixmap(self.current_screenshot)
                
                # 创建带有文本框的图像
                if 'boxes' in details and pixmap and not pixmap.isNull():
                    # 转换为OpenCV图像
                    image = self.pixmap_to_cv2(pixmap)
                    
                    # 在图像上绘制文本框
                    boxes = details.get('boxes', [])
                    for box in boxes:
                        x, y, w, h = box['x'], box['y'], box['width'], box['height']
                        # 调整坐标到预览图像的大小
                        scale_x = pixmap.width() / self.current_rect.width()
                        scale_y = pixmap.height() / self.current_rect.height()
                        
                        x = int(x * scale_x)
                        y = int(y * scale_y)
                        w = int(w * scale_x)
                        h = int(h * scale_y)
                        
                        # 绘制矩形
                        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        
                    # 转换回QPixmap
                    highlighted_pixmap = self.cv2_to_pixmap(image)
                    
                    # 显示图像
                    preview_label.setPixmap(highlighted_pixmap)
                    preview_label.setScaledContents(True)
            
            logger.info(f"OCR测试成功，识别文本: {len(text)} 字符")
            
        except Exception as e:
            logger.error(f"OCR测试失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.warning(
                self.ocr_tab, 
                "错误", 
                f"OCR测试失败: {e}"
            )
    
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
        """从坐标输入框更新区域"""
        # 获取坐标输入框
        x_spin = self.ocr_tab.left_panel.findChild(QObject, "x_spin")
        y_spin = self.ocr_tab.left_panel.findChild(QObject, "y_spin")
        width_spin = self.ocr_tab.left_panel.findChild(QObject, "width_spin")
        height_spin = self.ocr_tab.left_panel.findChild(QObject, "height_spin")
        
        # 创建新区域
        if x_spin and y_spin and width_spin and height_spin:
            x = x_spin.value()
            y = y_spin.value()
            width = width_spin.value()
            height = height_spin.value()
            
            if width > 0 and height > 0:
                self.current_rect = QRect(x, y, width, height)
                logger.info(f"区域已从坐标输入框更新: {self.current_rect}")
                
                # 更新预览
                self.update_preview()
                
                # 保存区域到配置
                self.save_area_to_config()
                logger.info(f"已保存更新后的区域到配置: {self.current_rect}")
    
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
            
        # 获取监控设置中的间隔时间
        refresh_interval = 1500  # 默认值：1.5秒
        
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
                        # 监控间隔以秒为单位，转换为毫秒
                        interval_seconds = int(interval_text)
                        refresh_interval = interval_seconds * 1000
                        logger.debug(f"使用监控设置的刷新间隔: {interval_seconds}秒")
                    except ValueError:
                        logger.warning(f"无法解析监控间隔值: {interval_text}，使用默认值")
        except Exception as e:
            logger.warning(f"获取监控间隔设置失败: {e}，使用默认值")
        
        # 设置自动刷新间隔，最小500毫秒，最大5秒
        refresh_interval = max(500, min(refresh_interval, 5000))
        
        # 启动定时器
        if self.auto_refresh_timer.isActive():
            self.auto_refresh_timer.stop()
        self.auto_refresh_timer.start(refresh_interval)
        logger.debug(f"已启动OCR预览自动刷新，间隔: {refresh_interval}毫秒")

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
        
        # 启动监控定时器
        if self.refresh_timer.isActive():
            self.refresh_timer.stop()
        self.refresh_timer.start(refresh_interval)
        self.is_monitoring = True
        
        # 立即更新一次预览
        self.update_preview()
        
        logger.info(f"OCR监控已启动，刷新频率: {refresh_interval}毫秒")
        return True
    
    def stop_monitoring(self):
        """停止监控，停止刷新定时器"""
        if self.refresh_timer.isActive():
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
            
            # 更新主窗口的监控引擎
            main_window = self.ocr_tab.window()
            if main_window and hasattr(main_window, 'monitor_engine'):
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
