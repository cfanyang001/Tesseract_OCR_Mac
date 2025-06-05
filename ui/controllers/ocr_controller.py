from typing import Dict, Any, Optional
from PyQt5.QtCore import QRect, pyqtSlot

from ui.controllers.base_controller import BaseController
from ui.models.ocr_model import OCRModel
from ui.components.tabs.ocr_tab import OCRTab
from ui.components.area_selector import AreaSelector


class OCRController(BaseController):
    """OCR控制器类，处理OCR标签页的业务逻辑"""
    
    def __init__(self, model: OCRModel = None, view: OCRTab = None):
        super().__init__(model)
        self._view = view
    
    @property
    def view(self) -> Optional[OCRTab]:
        """获取视图"""
        return self._view
    
    @view.setter
    def view(self, view: OCRTab) -> None:
        """设置视图"""
        self._view = view
        if view:
            self.connect_signals()
    
    def connect_signals(self) -> None:
        """连接信号"""
        if not self._view:
            return
        
        # 获取视图中的控件
        select_area_btn = self._view.findChild(type(self._view.left_panel.findChild(type(self._view.left_panel))), "select_area_btn")
        if select_area_btn:
            select_area_btn.clicked.connect(self.on_select_area)
    
    def disconnect_signals(self) -> None:
        """断开信号"""
        if not self._view:
            return
        
        # 获取视图中的控件
        select_area_btn = self._view.findChild(type(self._view.left_panel.findChild(type(self._view.left_panel))), "select_area_btn")
        if select_area_btn:
            select_area_btn.clicked.disconnect(self.on_select_area)
    
    @pyqtSlot()
    def on_select_area(self) -> None:
        """选择区域按钮点击事件"""
        # 创建区域选择器
        area_selector = AreaSelector()
        area_selector.show()
        
        # 等待区域选择完成
        area_selector.exec_()
        
        # 获取选择的区域
        selected_rect = area_selector.selected_rect
        if selected_rect:
            # 更新模型
            self.model.set_selected_area(selected_rect)
            
            # 更新视图
            self.update_view()
    
    def update_view(self) -> None:
        """更新视图"""
        if not self._view or not self._model:
            return
        
        # 更新区域信息
        selected_area = self._model.get_selected_area()
        if selected_area:
            # 更新坐标输入框
            x_spin = self._view.findChild(type(self._view.left_panel.findChild(type(self._view.left_panel))), "x_spin")
            y_spin = self._view.findChild(type(self._view.left_panel.findChild(type(self._view.left_panel))), "y_spin")
            width_spin = self._view.findChild(type(self._view.left_panel.findChild(type(self._view.left_panel))), "width_spin")
            height_spin = self._view.findChild(type(self._view.left_panel.findChild(type(self._view.left_panel))), "height_spin")
            
            if x_spin:
                x_spin.setValue(selected_area.x())
            if y_spin:
                y_spin.setValue(selected_area.y())
            if width_spin:
                width_spin.setValue(selected_area.width())
            if height_spin:
                height_spin.setValue(selected_area.height())
            
            # 更新预览图像
            self._view.preview.set_image(self._model.get_last_image())
            
            # 更新识别结果
            self._view.result_label.setText(self._model.get_last_result() or '点击"测试OCR"按钮进行文字识别测试')
    
    def test_ocr(self) -> None:
        """测试OCR识别"""
        if not self._model:
            return
        
        # 获取选择的区域
        selected_area = self._model.get_selected_area()
        if not selected_area:
            return
        
        # TODO: 实现OCR识别功能
        # 1. 捕获屏幕区域
        # 2. 进行OCR识别
        # 3. 更新模型和视图
        
        # 临时模拟结果
        self._model.set_last_result("OCR识别测试结果")
        
        # 更新视图
        self.update_view() 