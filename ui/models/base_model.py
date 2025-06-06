from typing import Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal


class BaseModel(QObject):
    """基础模型类，所有模型类的基类"""
    
    # 数据变化信号
    data_changed = pyqtSignal(str, object)  # 键, 值
    
    def __init__(self):
        """初始化基础模型"""
        super().__init__()
        
        # 初始化数据字典
        self._data = {}
    
    def get(self, key: str, default=None) -> Any:
        """获取数据
        
        Args:
            key: 数据键
            default: 默认值，当键不存在时返回
            
        Returns:
            Any: 数据值
        """
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置数据
        
        Args:
            key: 数据键
            value: 数据值
        """
        # 检查值是否变化
        if key in self._data and self._data[key] == value:
            return
        
        # 设置值
        self._data[key] = value
        
        # 发送数据变化信号
        self.data_changed.emit(key, value)
    
    def update(self, data: Dict[str, Any]) -> None:
        """批量更新数据
        
        Args:
            data: 数据字典
        """
        for key, value in data.items():
            self.set(key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """将模型数据转换为字典
        
        Returns:
            Dict[str, Any]: 数据字典
        """
        return self._data.copy()
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """从字典加载数据
        
        Args:
            data: 数据字典
        """
        self.update(data)
    
    def clear(self) -> None:
        """清空数据"""
        keys = list(self._data.keys())
        for key in keys:
            self.set(key, None)
        
        self._data.clear() 