from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject

from ui.models.base_model import BaseModel


class BaseController(QObject):
    """基础控制器类，所有控制器类的父类"""
    
    def __init__(self, model: BaseModel = None):
        super().__init__()
        self._model = model
    
    @property
    def model(self) -> Optional[BaseModel]:
        """获取模型"""
        return self._model
    
    @model.setter
    def model(self, model: BaseModel) -> None:
        """设置模型"""
        self._model = model
    
    def connect_signals(self) -> None:
        """连接信号"""
        pass
    
    def disconnect_signals(self) -> None:
        """断开信号"""
        pass
    
    def initialize(self) -> None:
        """初始化控制器"""
        self.connect_signals()
    
    def cleanup(self) -> None:
        """清理控制器"""
        self.disconnect_signals()
    
    def get_model_data(self, key: str, default=None) -> Any:
        """获取模型数据"""
        if self._model:
            return self._model.get(key, default)
        return default
    
    def set_model_data(self, key: str, value: Any) -> None:
        """设置模型数据"""
        if self._model:
            self._model.set(key, value)
    
    def update_model_data(self, data: Dict[str, Any]) -> None:
        """批量更新模型数据"""
        if self._model:
            self._model.update(data) 