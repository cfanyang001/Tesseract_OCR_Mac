from typing import Dict, List, Any, Callable
from PyQt5.QtCore import QObject, pyqtSignal


class BaseModel(QObject):
    """基础模型类，所有模型类的父类"""
    
    # 数据变更信号
    data_changed = pyqtSignal(str, object)
    
    def __init__(self):
        super().__init__()
        self._data = {}
        self._observers = {}
    
    def get(self, key: str, default=None) -> Any:
        """获取数据"""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置数据，并触发数据变更信号"""
        old_value = self._data.get(key)
        if old_value != value:
            self._data[key] = value
            self.data_changed.emit(key, value)
            
            # 通知观察者
            if key in self._observers:
                for callback in self._observers[key]:
                    callback(value)
    
    def update(self, data: Dict[str, Any]) -> None:
        """批量更新数据"""
        for key, value in data.items():
            self.set(key, value)
    
    def observe(self, key: str, callback: Callable) -> None:
        """添加观察者，当指定键的数据变更时调用回调函数"""
        if key not in self._observers:
            self._observers[key] = []
        self._observers[key].append(callback)
    
    def remove_observer(self, key: str, callback: Callable) -> None:
        """移除观察者"""
        if key in self._observers and callback in self._observers[key]:
            self._observers[key].remove(callback)
    
    def to_dict(self) -> Dict[str, Any]:
        """将模型数据转换为字典"""
        return self._data.copy()
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """从字典加载模型数据"""
        self.update(data) 