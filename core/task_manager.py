import threading
import queue
import time
from typing import Dict, List, Any, Optional, Callable, Tuple
from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime
import os

from core.task_scheduler import TaskScheduler, Task
from core.monitor_engine import MonitorEngine
from loguru import logger


class TaskInfo:
    """任务信息类，存储任务的详细信息"""
    
    # 任务状态
    STATUS_PENDING = 'pending'    # 等待中
    STATUS_RUNNING = 'running'    # 运行中
    STATUS_COMPLETED = 'completed'  # 已完成
    STATUS_FAILED = 'failed'      # 失败
    STATUS_STOPPED = 'stopped'    # 已停止
    
    def __init__(self, task_id: str, name: str = '', description: str = ''):
        """初始化任务信息
        
        Args:
            task_id: 任务ID
            name: 任务名称
            description: 任务描述
        """
        self.id = task_id
        self.name = name or f"任务 {task_id[:8]}"
        self.description = description
        
        # 任务状态
        self.status = self.STATUS_PENDING
        self.progress = 0.0  # 进度 (0.0-1.0)
        self.message = ""    # 状态消息
        
        # 执行时间
        self.create_time = datetime.now()
        self.start_time = None
        self.end_time = None
        self.last_run_time = None
        
        # 执行结果
        self.result = None
        self.error = None
        
        # 配置
        self.config = {
            'auto_restart': False,   # 失败时是否自动重启
            'max_retries': 3,        # 最大重试次数
            'retry_delay': 60,       # 重试延迟 (秒)
            'refresh_rate': 1000,    # 刷新率 (毫秒)
        }
        
        # 元数据（存储额外信息）
        self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """将任务信息转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'progress': self.progress,
            'message': self.message,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'last_run_time': self.last_run_time.isoformat() if self.last_run_time else None,
            'config': self.config,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskInfo':
        """从字典创建任务信息"""
        task_info = cls(
            task_id=data['id'],
            name=data.get('name', ''),
            description=data.get('description', '')
        )
        
        task_info.status = data.get('status', cls.STATUS_PENDING)
        task_info.progress = data.get('progress', 0.0)
        task_info.message = data.get('message', '')
        
        # 解析时间
        if data.get('create_time'):
            task_info.create_time = datetime.fromisoformat(data['create_time'])
        if data.get('start_time'):
            task_info.start_time = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            task_info.end_time = datetime.fromisoformat(data['end_time'])
        if data.get('last_run_time'):
            task_info.last_run_time = datetime.fromisoformat(data['last_run_time'])
        
        # 配置和元数据
        task_info.config = data.get('config', task_info.config)
        task_info.metadata = data.get('metadata', {})
        
        return task_info


class TaskManager(QObject):
    """任务管理器，用于管理和监控多个任务"""
    
    # 信号
    task_added = pyqtSignal(str)  # 任务添加信号 (任务ID)
    task_started = pyqtSignal(str)  # 任务开始信号 (任务ID)
    task_completed = pyqtSignal(str, object)  # 任务完成信号 (任务ID, 结果)
    task_failed = pyqtSignal(str, str)  # 任务失败信号 (任务ID, 错误信息)
    task_stopped = pyqtSignal(str)  # 任务停止信号 (任务ID)
    task_progress = pyqtSignal(str, float, str)  # 任务进度信号 (任务ID, 进度, 消息)
    task_removed = pyqtSignal(str)  # 任务移除信号 (任务ID)
    
    def __init__(self, monitor_engine: Optional[MonitorEngine] = None,
                 task_scheduler: Optional[TaskScheduler] = None):
        """初始化任务管理器
        
        Args:
            monitor_engine: 监控引擎
            task_scheduler: 任务调度器
        """
        super().__init__()
        
        # 任务信息字典
        self.tasks = {}  # {task_id: TaskInfo}
        
        # 工作线程池
        self.worker_threads = {}  # {task_id: Thread}
        
        # 任务队列
        self.task_queue = queue.Queue()
        
        # 最大并发任务数
        self.max_concurrent_tasks = 5
        
        # 当前运行的任务数
        self.running_tasks = 0
        
        # 停止标志
        self.stop_flag = threading.Event()
        
        # 监控引擎和任务调度器
        self.monitor_engine = monitor_engine
        self.task_scheduler = task_scheduler
        
        # 启动调度线程
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("任务管理器初始化完成")
    
    def set_monitor_engine(self, engine: MonitorEngine):
        """设置监控引擎"""
        self.monitor_engine = engine
    
    def set_task_scheduler(self, scheduler: TaskScheduler):
        """设置任务调度器"""
        self.task_scheduler = scheduler
    
    def add_task(self, task_id: str, name: str = '', description: str = '',
                 task_func: Callable = None, task_args: Tuple = None,
                 task_kwargs: Dict = None, auto_start: bool = False) -> str:
        """添加任务
        
        Args:
            task_id: 任务ID，为None时自动生成
            name: 任务名称
            description: 任务描述
            task_func: 任务函数
            task_args: 任务函数参数
            task_kwargs: 任务函数关键字参数
            auto_start: 是否自动启动
            
        Returns:
            str: 任务ID
        """
        # 如果没有指定ID，生成一个
        if not task_id:
            from uuid import uuid4
            task_id = str(uuid4())
        
        # 创建任务信息
        task_info = TaskInfo(task_id, name, description)
        
        # 保存任务函数和参数
        task_info.metadata['func'] = task_func
        task_info.metadata['args'] = task_args or ()
        task_info.metadata['kwargs'] = task_kwargs or {}
        
        # 添加到任务字典
        self.tasks[task_id] = task_info
        
        # 发送任务添加信号
        self.task_added.emit(task_id)
        
        logger.info(f"任务已添加: {name} ({task_id})")
        
        # 如果需要自动启动
        if auto_start:
            self.start_task(task_id)
        
        return task_id
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功移除
        """
        if task_id not in self.tasks:
            logger.warning(f"任务不存在: {task_id}")
            return False
        
        # 如果任务正在运行，先停止
        if task_id in self.worker_threads and self.worker_threads[task_id].is_alive():
            self.stop_task(task_id)
        
        # 从任务字典中移除
        del self.tasks[task_id]
        
        # 从工作线程池中移除
        if task_id in self.worker_threads:
            del self.worker_threads[task_id]
        
        # 发送任务移除信号
        self.task_removed.emit(task_id)
        
        logger.info(f"任务已移除: {task_id}")
        return True
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[TaskInfo]: 任务信息，不存在时返回None
        """
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, TaskInfo]:
        """获取所有任务
        
        Returns:
            Dict[str, TaskInfo]: 任务字典
        """
        return self.tasks.copy()
    
    def start_task(self, task_id: str) -> bool:
        """启动任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功启动
        """
        task_info = self.get_task(task_id)
        if not task_info:
            logger.warning(f"任务不存在: {task_id}")
            return False
        
        # 如果任务已经在运行
        if task_id in self.worker_threads and self.worker_threads[task_id].is_alive():
            logger.warning(f"任务已在运行中: {task_info.name}")
            return False
        
        # 获取任务函数和参数
        task_func = task_info.metadata.get('func')
        task_args = task_info.metadata.get('args', ())
        task_kwargs = task_info.metadata.get('kwargs', {})
        
        if not task_func:
            logger.error(f"任务函数未定义: {task_id}")
            task_info.status = TaskInfo.STATUS_FAILED
            task_info.error = "任务函数未定义"
            self.task_failed.emit(task_id, "任务函数未定义")
            return False
        
        # 更新任务状态
        task_info.status = TaskInfo.STATUS_RUNNING
        task_info.start_time = datetime.now()
        task_info.last_run_time = datetime.now()
        task_info.progress = 0.0
        task_info.message = "任务已启动"
        task_info.error = None
        task_info.result = None
        
        # 创建工作线程
        thread = threading.Thread(
            target=self._task_worker,
            args=(task_id, task_func, task_args, task_kwargs),
            daemon=True
        )
        
        # 保存线程
        self.worker_threads[task_id] = thread
        
        # 启动线程
        thread.start()
        
        # 发送任务开始信号
        self.task_started.emit(task_id)
        
        logger.info(f"任务已启动: {task_info.name} ({task_id})")
        return True
    
    def stop_task(self, task_id: str) -> bool:
        """停止任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功停止
        """
        task_info = self.get_task(task_id)
        if not task_info:
            logger.warning(f"任务不存在: {task_id}")
            return False
        
        # 如果任务不在运行中
        if task_id not in self.worker_threads or not self.worker_threads[task_id].is_alive():
            logger.warning(f"任务未在运行中: {task_info.name}")
            return False
        
        # 更新任务状态
        task_info.status = TaskInfo.STATUS_STOPPED
        task_info.end_time = datetime.now()
        task_info.message = "任务已停止"
        
        # 发送任务停止信号
        self.task_stopped.emit(task_id)
        
        logger.info(f"任务已停止: {task_info.name} ({task_id})")
        return True
    
    def update_task_progress(self, task_id: str, progress: float, message: str = '') -> bool:
        """更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度 (0.0-1.0)
            message: 状态消息
            
        Returns:
            bool: 是否成功更新
        """
        task_info = self.get_task(task_id)
        if not task_info:
            return False
        
        # 限制进度范围
        progress = max(0.0, min(1.0, progress))
        
        # 更新任务信息
        task_info.progress = progress
        if message:
            task_info.message = message
        
        # 发送进度信号
        self.task_progress.emit(task_id, progress, message)
        
        return True
    
    def shutdown(self):
        """关闭任务管理器"""
        # 设置停止标志
        self.stop_flag.set()
        
        # 停止所有任务
        for task_id in list(self.worker_threads.keys()):
            self.stop_task(task_id)
        
        # 等待调度线程结束
        if self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=2.0)
        
        logger.info("任务管理器已关闭")
    
    def _task_worker(self, task_id: str, task_func: Callable,
                    task_args: Tuple, task_kwargs: Dict):
        """任务工作线程
        
        Args:
            task_id: 任务ID
            task_func: 任务函数
            task_args: 任务函数参数
            task_kwargs: 任务函数关键字参数
        """
        task_info = self.tasks.get(task_id)
        if not task_info:
            return
        
        # 增加运行中任务计数
        self.running_tasks += 1
        
        try:
            # 创建停止检查函数
            def check_stop():
                return task_info.status == TaskInfo.STATUS_STOPPED
            
            # 创建进度更新函数
            def update_progress(progress, message=''):
                self.update_task_progress(task_id, progress, message)
            
            # 添加额外参数
            kwargs = task_kwargs.copy()
            kwargs['check_stop'] = check_stop
            kwargs['update_progress'] = update_progress
            
            # 执行任务函数
            result = task_func(*task_args, **kwargs)
            
            # 如果任务被停止
            if task_info.status == TaskInfo.STATUS_STOPPED:
                return
            
            # 更新任务状态
            task_info.status = TaskInfo.STATUS_COMPLETED
            task_info.end_time = datetime.now()
            task_info.result = result
            task_info.progress = 1.0
            task_info.message = "任务已完成"
            
            # 发送任务完成信号
            self.task_completed.emit(task_id, result)
            
            logger.info(f"任务已完成: {task_info.name} ({task_id})")
            
        except Exception as e:
            # 如果任务被停止
            if task_info.status == TaskInfo.STATUS_STOPPED:
                return
                
            # 更新任务状态
            task_info.status = TaskInfo.STATUS_FAILED
            task_info.end_time = datetime.now()
            task_info.error = str(e)
            task_info.message = f"任务失败: {e}"
            
            # 发送任务失败信号
            self.task_failed.emit(task_id, str(e))
            
            logger.error(f"任务执行失败: {task_info.name} ({task_id}): {e}")
            import traceback
            logger.error(traceback.format_exc())
            
        finally:
            # 减少运行中任务计数
            self.running_tasks -= 1
    
    def _scheduler_loop(self):
        """任务调度循环"""
        while not self.stop_flag.is_set():
            try:
                # 检查是否有可用的任务槽
                if self.running_tasks < self.max_concurrent_tasks:
                    # 尝试从队列获取任务，不阻塞
                    try:
                        task_id = self.task_queue.get_nowait()
                        # 启动任务
                        self.start_task(task_id)
                        # 标记任务完成
                        self.task_queue.task_done()
                    except queue.Empty:
                        pass
                
                # 检查任务调度器
                if self.task_scheduler:
                    # 这里可以实现与任务调度器的集成
                    pass
                
                # 休眠一段时间
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"任务调度循环异常: {e}")
                import traceback
                logger.error(traceback.format_exc())
                time.sleep(1.0)  # 出错后暂停一段时间
