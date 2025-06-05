from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel, 
    QComboBox, QSpinBox, QCheckBox, QSlider, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPixmap, QImage

from ui.components.area_selector import AreaPreview


class OCRTab(QWidget):
    """OCR标签页，包含区域选择和OCR设置"""
    
    def __init__(self):
        super().__init__()
        
        # 控制器引用，将由OCRController设置
        self.controller = None
        
        # 创建主布局
        self.layout = QHBoxLayout(self)
        
        # 创建左侧面板（OCR设置）
        self.left_panel = self.create_settings_panel()
        self.layout.addWidget(self.left_panel, 1)
        
        # 创建右侧面板（区域预览）
        self.right_panel = self.create_preview_panel()
        self.layout.addWidget(self.right_panel, 2)
    
    def create_settings_panel(self):
        """创建OCR设置面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 区域选择组
        area_group = QGroupBox("区域选择")
        area_layout = QVBoxLayout(area_group)
        
        # 选择区域按钮
        select_area_btn = QPushButton("选择屏幕区域")
        select_area_btn.setMinimumHeight(40)
        select_area_btn.setObjectName("select_area_btn")
        area_layout.addWidget(select_area_btn)
        
        # 区域信息
        area_info_frame = QFrame()
        area_info_layout = QHBoxLayout(area_info_frame)
        area_info_layout.addWidget(QLabel("X:"))
        x_spin = QSpinBox()
        x_spin.setRange(0, 9999)
        x_spin.setObjectName("x_spin")
        area_info_layout.addWidget(x_spin)
        
        area_info_layout.addWidget(QLabel("Y:"))
        y_spin = QSpinBox()
        y_spin.setRange(0, 9999)
        y_spin.setObjectName("y_spin")
        area_info_layout.addWidget(y_spin)
        
        area_info_layout.addWidget(QLabel("宽:"))
        width_spin = QSpinBox()
        width_spin.setRange(1, 9999)
        width_spin.setObjectName("width_spin")
        area_info_layout.addWidget(width_spin)
        
        area_info_layout.addWidget(QLabel("高:"))
        height_spin = QSpinBox()
        height_spin.setRange(1, 9999)
        height_spin.setObjectName("height_spin")
        area_info_layout.addWidget(height_spin)
        
        area_layout.addWidget(area_info_frame)
        layout.addWidget(area_group)
        
        # OCR设置组
        ocr_group = QGroupBox("OCR设置")
        ocr_layout = QVBoxLayout(ocr_group)
        
        # 语言选择
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("语言:"))
        lang_combo = QComboBox()
        lang_combo.setObjectName("lang_combo")
        lang_combo.addItems(["中文简体", "中文繁体", "英语", "日语", "韩语"])
        lang_layout.addWidget(lang_combo)
        ocr_layout.addLayout(lang_layout)
        
        # PSM模式选择
        psm_layout = QHBoxLayout()
        psm_layout.addWidget(QLabel("PSM模式:"))
        psm_combo = QComboBox()
        psm_combo.setObjectName("psm_combo")
        psm_combo.addItems([
            "0 - 仅方向和脚本检测",
            "1 - 自动页面分割",
            "2 - 自动页面分割，但无OSD",
            "3 - 全自动页面分割（默认）",
            "4 - 假设单列文本",
            "5 - 假设垂直对齐文本块",
            "6 - 假设统一文本块",
            "7 - 将图像视为单行文本",
            "8 - 将图像视为单词",
            "9 - 将图像视为单词圆圈",
            "10 - 将图像视为单个字符",
            "11 - 稀疏文本",
            "12 - 稀疏文本与OSD",
            "13 - 原始行"
        ])
        psm_combo.setCurrentIndex(7)  # 默认选择单行文本模式
        psm_layout.addWidget(psm_combo)
        ocr_layout.addLayout(psm_layout)
        
        # OEM引擎模式
        oem_layout = QHBoxLayout()
        oem_layout.addWidget(QLabel("OCR引擎:"))
        oem_combo = QComboBox()
        oem_combo.setObjectName("oem_combo")
        oem_combo.addItems([
            "0 - 传统Tesseract引擎",
            "1 - 神经网络LSTM引擎",
            "2 - 传统+LSTM引擎",
            "3 - 默认自动选择"
        ])
        oem_combo.setCurrentIndex(1)  # 默认选择LSTM引擎
        oem_layout.addWidget(oem_combo)
        ocr_layout.addLayout(oem_layout)
        
        # 精度设置
        accuracy_layout = QHBoxLayout()
        accuracy_layout.addWidget(QLabel("精度:"))
        accuracy_slider = QSlider(Qt.Horizontal)
        accuracy_slider.setObjectName("accuracy_slider")
        accuracy_slider.setRange(0, 100)
        accuracy_slider.setValue(80)
        accuracy_layout.addWidget(accuracy_slider)
        accuracy_value = QLabel("80%")
        accuracy_value.setObjectName("accuracy_value")
        accuracy_layout.addWidget(accuracy_value)
        ocr_layout.addLayout(accuracy_layout)
        
        # 预处理选项
        preprocess_check = QCheckBox("启用图像预处理")
        preprocess_check.setObjectName("preprocess_check")
        preprocess_check.setChecked(True)
        ocr_layout.addWidget(preprocess_check)
        
        # 自动修正
        autocorrect_check = QCheckBox("启用文本自动修正")
        autocorrect_check.setObjectName("autocorrect_check")
        ocr_layout.addWidget(autocorrect_check)
        
        # 刷新频率
        refresh_layout = QHBoxLayout()
        refresh_layout.addWidget(QLabel("刷新频率:"))
        refresh_combo = QComboBox()
        refresh_combo.setObjectName("refresh_combo")
        refresh_combo.addItems(["低 (1秒)", "中 (0.5秒)", "高 (0.2秒)", "自定义"])
        refresh_layout.addWidget(refresh_combo)
        ocr_layout.addLayout(refresh_layout)
        
        layout.addWidget(ocr_group)
        
        # 测试按钮
        test_btn = QPushButton("测试OCR")
        test_btn.setObjectName("test_ocr_btn")
        test_btn.setMinimumHeight(40)
        layout.addWidget(test_btn)
        
        layout.addStretch()
        return panel
    
    def create_preview_panel(self):
        """创建区域预览面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 预览标题
        preview_title = QLabel("区域预览")
        preview_title.setAlignment(Qt.AlignCenter)
        preview_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(preview_title)
        
        # 预览区域框架
        preview_frame = QFrame()
        preview_frame.setFrameShape(QFrame.StyledPanel)
        preview_frame.setFrameShadow(QFrame.Sunken)
        preview_frame.setStyleSheet("background-color: white;")
        preview_layout = QVBoxLayout(preview_frame)
        
        # 预览区域
        self.preview = AreaPreview()
        self.preview.setMinimumSize(QSize(350, 250))
        preview_layout.addWidget(self.preview)
        
        layout.addWidget(preview_frame)
        
        # 识别结果组
        result_group = QGroupBox("识别结果")
        result_layout = QVBoxLayout(result_group)
        
        # 结果文本区域（使用滚动区域）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        self.result_label = QLabel('点击"测试OCR"按钮进行文字识别测试')
        self.result_label.setObjectName("result_label")
        self.result_label.setWordWrap(True)
        self.result_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.result_label.setMinimumHeight(100)
        scroll_layout.addWidget(self.result_label)
        
        scroll_area.setWidget(scroll_content)
        result_layout.addWidget(scroll_area)
        
        layout.addWidget(result_group)
        
        return panel
