from typing import Dict, List, Any, Tuple
from PyQt5.QtCore import QRect

from ui.models.base_model import BaseModel


class OCRModel(BaseModel):
    """OCR模型类，存储OCR相关的数据"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化默认数据
        self._data = {
            'selected_area': None,  # 选中的区域 (QRect)
            'language': 'chi_sim',  # OCR语言 (chi_sim, chi_tra, eng, jpn, kor)
            'accuracy': 80,         # 精度 (0-100)
            'preprocess': True,     # 是否启用图像预处理
            'autocorrect': False,   # 是否启用文本自动修正
            'refresh_rate': 1000,   # 刷新频率 (毫秒)
            'last_result': '',      # 最后一次OCR识别结果
            'last_image': None      # 最后一次截图
        }
    
    def set_selected_area(self, rect: QRect) -> None:
        """设置选中的区域"""
        self.set('selected_area', rect)
    
    def get_selected_area(self) -> QRect:
        """获取选中的区域"""
        return self.get('selected_area')
    
    def set_language(self, language: str) -> None:
        """设置OCR语言"""
        self.set('language', language)
    
    def get_language(self) -> str:
        """获取OCR语言"""
        return self.get('language')
    
    def set_accuracy(self, accuracy: int) -> None:
        """设置精度"""
        self.set('accuracy', max(0, min(100, accuracy)))
    
    def get_accuracy(self) -> int:
        """获取精度"""
        return self.get('accuracy')
    
    def set_preprocess(self, enabled: bool) -> None:
        """设置是否启用图像预处理"""
        self.set('preprocess', enabled)
    
    def is_preprocess_enabled(self) -> bool:
        """获取是否启用图像预处理"""
        return self.get('preprocess')
    
    def set_autocorrect(self, enabled: bool) -> None:
        """设置是否启用文本自动修正"""
        self.set('autocorrect', enabled)
    
    def is_autocorrect_enabled(self) -> bool:
        """获取是否启用文本自动修正"""
        return self.get('autocorrect')
    
    def set_refresh_rate(self, rate: int) -> None:
        """设置刷新频率 (毫秒)"""
        self.set('refresh_rate', max(100, min(10000, rate)))
    
    def get_refresh_rate(self) -> int:
        """获取刷新频率 (毫秒)"""
        return self.get('refresh_rate')
    
    def set_last_result(self, result: str) -> None:
        """设置最后一次OCR识别结果"""
        self.set('last_result', result)
    
    def get_last_result(self) -> str:
        """获取最后一次OCR识别结果"""
        return self.get('last_result')
    
    def set_last_image(self, image) -> None:
        """设置最后一次截图"""
        self.set('last_image', image)
    
    def get_last_image(self):
        """获取最后一次截图"""
        return self.get('last_image') 