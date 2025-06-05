from typing import Dict, List, Any, Tuple
from datetime import datetime
from PyQt5.QtCore import QRect

from ui.models.base_model import BaseModel


class Task:
    """任务类，表示一个监控任务"""
    
    STATUS_RUNNING = 'running'       # 运行中
    STATUS_PAUSED = 'paused'         # 已暂停
    STATUS_STOPPED = 'stopped'       # 已停止
    STATUS_COMPLETED = 'completed'   # 已完成
    STATUS_ERROR = 'error'           # 出错
    
    def __init__(self, task_id: str, name: str, area_id: str = None, rule_id: str = None):
        self.id = task_id                # 任务ID
        self.name = name                 # 任务名称
        self.area_id = area_id           # 区域ID
        self.rule_id = rule_id           # 规则ID
        self.status = self.STATUS_STOPPED  # 任务状态
        self.refresh_rate = 1000         # 刷新频率 (毫秒)
        self.auto_restart = False        # 是否自动重启
        self.created_at = datetime.now() # 创建时间
        self.last_run = None             # 上次运行时间
        self.last_trigger = None         # 上次触发时间
        self.progress = 0                # 进度 (0-100)
    
    def to_dict(self) -> Dict[str, Any]:
        """将任务转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'area_id': self.area_id,
            'rule_id': self.rule_id,
            'status': self.status,
            'refresh_rate': self.refresh_rate,
            'auto_restart': self.auto_restart,
            'created_at': self.created_at.isoformat(),
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'last_trigger': self.last_trigger.isoformat() if self.last_trigger else None,
            'progress': self.progress
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建任务"""
        task = cls(
            task_id=data['id'],
            name=data['name'],
            area_id=data.get('area_id'),
            rule_id=data.get('rule_id')
        )
        task.status = data.get('status', cls.STATUS_STOPPED)
        task.refresh_rate = data.get('refresh_rate', 1000)
        task.auto_restart = data.get('auto_restart', False)
        task.created_at = datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now()
        task.last_run = datetime.fromisoformat(data['last_run']) if data.get('last_run') else None
        task.last_trigger = datetime.fromisoformat(data['last_trigger']) if data.get('last_trigger') else None
        task.progress = data.get('progress', 0)
        return task


class Area:
    """区域类，表示一个屏幕区域"""
    
    def __init__(self, area_id: str, name: str, rect: QRect):
        self.id = area_id        # 区域ID
        self.name = name         # 区域名称
        self.rect = rect         # 区域矩形
    
    def to_dict(self) -> Dict[str, Any]:
        """将区域转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'x': self.rect.x(),
            'y': self.rect.y(),
            'width': self.rect.width(),
            'height': self.rect.height()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Area':
        """从字典创建区域"""
        rect = QRect(
            data['x'],
            data['y'],
            data['width'],
            data['height']
        )
        return cls(
            area_id=data['id'],
            name=data['name'],
            rect=rect
        )


class TaskModel(BaseModel):
    """任务模型类，存储监控任务和区域"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化默认数据
        self._data = {
            'tasks': {},     # 任务字典 {task_id: Task}
            'areas': {},     # 区域字典 {area_id: Area}
        }
    
    def add_task(self, task: Task) -> None:
        """添加任务"""
        tasks = self.get('tasks').copy()
        tasks[task.id] = task
        self.set('tasks', tasks)
    
    def remove_task(self, task_id: str) -> None:
        """移除任务"""
        tasks = self.get('tasks').copy()
        if task_id in tasks:
            del tasks[task_id]
            self.set('tasks', tasks)
    
    def get_task(self, task_id: str) -> Task:
        """获取任务"""
        return self.get('tasks').get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Task]:
        """获取所有任务"""
        return self.get('tasks')
    
    def update_task_status(self, task_id: str, status: str) -> None:
        """更新任务状态"""
        task = self.get_task(task_id)
        if task:
            task.status = status
            self.add_task(task)  # 更新任务
    
    def update_task_progress(self, task_id: str, progress: int) -> None:
        """更新任务进度"""
        task = self.get_task(task_id)
        if task:
            task.progress = max(0, min(100, progress))
            self.add_task(task)  # 更新任务
    
    def update_task_last_run(self, task_id: str) -> None:
        """更新任务上次运行时间"""
        task = self.get_task(task_id)
        if task:
            task.last_run = datetime.now()
            self.add_task(task)  # 更新任务
    
    def update_task_last_trigger(self, task_id: str) -> None:
        """更新任务上次触发时间"""
        task = self.get_task(task_id)
        if task:
            task.last_trigger = datetime.now()
            self.add_task(task)  # 更新任务
    
    def add_area(self, area: Area) -> None:
        """添加区域"""
        areas = self.get('areas').copy()
        areas[area.id] = area
        self.set('areas', areas)
    
    def remove_area(self, area_id: str) -> None:
        """移除区域"""
        areas = self.get('areas').copy()
        if area_id in areas:
            del areas[area_id]
            self.set('areas', areas)
    
    def get_area(self, area_id: str) -> Area:
        """获取区域"""
        return self.get('areas').get(area_id)
    
    def get_all_areas(self) -> Dict[str, Area]:
        """获取所有区域"""
        return self.get('areas') 