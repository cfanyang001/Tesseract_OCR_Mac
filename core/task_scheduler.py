import time
import threading
import schedule
from datetime import datetime, timedelta
from typing import Dict, Any, List, Callable, Optional, Union
from PyQt5.QtCore import QObject, pyqtSignal
from loguru import logger


class Task:
    """任务类，表示一个定时或触发执行的任务"""
    
    # 任务类型
    TYPE_ONCE = 'once'           # 一次性任务
    TYPE_INTERVAL = 'interval'   # 间隔任务
    TYPE_DAILY = 'daily'         # 每日任务
    TYPE_WEEKLY = 'weekly'       # 每周任务
    TYPE_MONTHLY = 'monthly'     # 每月任务
    TYPE_CRON = 'cron'           # Cron表达式任务
    TYPE_EVENT = 'event'         # 事件触发任务
    
    # 任务状态
    STATUS_PENDING = 'pending'   # 待执行
    STATUS_RUNNING = 'running'   # 执行中
    STATUS_COMPLETED = 'completed'  # 已完成
    STATUS_FAILED = 'failed'     # 执行失败
    STATUS_CANCELLED = 'cancelled'  # 已取消
    
    def __init__(self, task_id: str = None, name: str = '', task_type: str = TYPE_ONCE, 
                 target_type: str = '', target_id: str = '', 
                 schedule_time: Union[datetime, Dict[str, Any]] = None,
                 enabled: bool = True):
        """初始化任务
        
        Args:
            task_id: 任务ID，为None时自动生成
            name: 任务名称
            task_type: 任务类型
            target_type: 目标类型 ('action', 'sequence', 'rule', 'callback')
            target_id: 目标ID
            schedule_time: 调度时间，根据任务类型不同含义不同
                - TYPE_ONCE: datetime对象
                - TYPE_INTERVAL: {'interval': 秒数, 'start_time': datetime, 'end_time': datetime}
                - TYPE_DAILY: {'hour': 小时, 'minute': 分钟, 'second': 秒}
                - TYPE_WEEKLY: {'day': 星期几(0-6), 'hour': 小时, 'minute': 分钟}
                - TYPE_MONTHLY: {'day': 日期(1-31), 'hour': 小时, 'minute': 分钟}
                - TYPE_CRON: {'expression': 'cron表达式'}
                - TYPE_EVENT: {'event_type': 事件类型, 'event_params': 事件参数}
            enabled: 是否启用
        """
        from uuid import uuid4
        self.id = task_id or str(uuid4())
        self.name = name or f"任务 {self.id[:8]}"
        self.type = task_type
        self.target_type = target_type
        self.target_id = target_id
        self.schedule_time = schedule_time or {}
        self.enabled = enabled
        
        # 运行状态
        self.status = self.STATUS_PENDING
        self.last_run_time = None
        self.next_run_time = None
        self.run_count = 0
        self.last_result = None
        self.error_message = None
        
        # 额外参数
        self.params = {}
        
        # 更新下次运行时间
        self._update_next_run_time()
    
    def _update_next_run_time(self):
        """更新下次运行时间"""
        now = datetime.now()
        
        try:
            if self.type == self.TYPE_ONCE:
                # 一次性任务
                if isinstance(self.schedule_time, datetime):
                    self.next_run_time = self.schedule_time
                else:
                    self.next_run_time = None
                    
            elif self.type == self.TYPE_INTERVAL:
                # 间隔任务
                interval = self.schedule_time.get('interval', 60)  # 默认60秒
                start_time = self.schedule_time.get('start_time')
                end_time = self.schedule_time.get('end_time')
                
                # 检查是否在有效时间范围内
                if end_time and now > end_time:
                    self.next_run_time = None
                    return
                
                # 计算下次运行时间
                if self.last_run_time:
                    self.next_run_time = self.last_run_time + timedelta(seconds=interval)
                elif start_time and start_time > now:
                    self.next_run_time = start_time
                else:
                    self.next_run_time = now + timedelta(seconds=interval)
                    
            elif self.type == self.TYPE_DAILY:
                # 每日任务
                hour = self.schedule_time.get('hour', 0)
                minute = self.schedule_time.get('minute', 0)
                second = self.schedule_time.get('second', 0)
                
                next_run = now.replace(hour=hour, minute=minute, second=second)
                if next_run <= now:
                    next_run += timedelta(days=1)
                self.next_run_time = next_run
                
            elif self.type == self.TYPE_WEEKLY:
                # 每周任务
                day = self.schedule_time.get('day', 0)  # 0=周一
                hour = self.schedule_time.get('hour', 0)
                minute = self.schedule_time.get('minute', 0)
                
                # 计算下次运行日期
                days_ahead = day - now.weekday()
                if days_ahead <= 0:  # 如果今天已经过了指定的星期几，等到下周
                    days_ahead += 7
                
                next_run = now.replace(hour=hour, minute=minute, second=0) + timedelta(days=days_ahead)
                self.next_run_time = next_run
                
            elif self.type == self.TYPE_MONTHLY:
                # 每月任务
                day = self.schedule_time.get('day', 1)
                hour = self.schedule_time.get('hour', 0)
                minute = self.schedule_time.get('minute', 0)
                
                # 计算下次运行日期
                if now.day < day:
                    # 本月还没到指定日期
                    next_run = now.replace(day=day, hour=hour, minute=minute, second=0)
                else:
                    # 已经过了本月的指定日期，等到下个月
                    if now.month == 12:
                        next_run = now.replace(year=now.year+1, month=1, day=day, 
                                              hour=hour, minute=minute, second=0)
                    else:
                        next_run = now.replace(month=now.month+1, day=day, 
                                              hour=hour, minute=minute, second=0)
                
                self.next_run_time = next_run
                
            elif self.type == self.TYPE_CRON:
                # Cron表达式任务 - 使用schedule库处理
                # 这里简化处理，实际实现可能需要更复杂的逻辑
                self.next_run_time = now + timedelta(minutes=5)  # 占位符
                
            elif self.type == self.TYPE_EVENT:
                # 事件触发任务 - 没有固定的下次运行时间
                self.next_run_time = None
                
            else:
                self.next_run_time = None
                
        except Exception as e:
            logger.error(f"更新任务下次运行时间失败: {e}")
            self.next_run_time = None
    
    def mark_as_running(self):
        """标记为运行中"""
        self.status = self.STATUS_RUNNING
        self.last_run_time = datetime.now()
        self.run_count += 1
    
    def mark_as_completed(self, result: Any = None):
        """标记为已完成"""
        self.status = self.STATUS_COMPLETED
        self.last_result = result
        
        # 更新下次运行时间
        if self.type == self.TYPE_ONCE:
            # 一次性任务完成后禁用
            self.enabled = False
            self.next_run_time = None
        else:
            self._update_next_run_time()
    
    def mark_as_failed(self, error_message: str = None):
        """标记为执行失败"""
        self.status = self.STATUS_FAILED
        self.error_message = error_message
        
        # 更新下次运行时间
        self._update_next_run_time()
    
    def cancel(self):
        """取消任务"""
        self.status = self.STATUS_CANCELLED
        self.enabled = False
        self.next_run_time = None
    
    def to_dict(self) -> Dict[str, Any]:
        """将任务转换为字典"""
        data = {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'enabled': self.enabled,
            'status': self.status,
            'run_count': self.run_count,
            'params': self.params,
            'last_run_time': self.last_run_time.isoformat() if self.last_run_time else None,
            'next_run_time': self.next_run_time.isoformat() if self.next_run_time else None,
        }
        
        # 根据任务类型保存调度时间
        if self.type == self.TYPE_ONCE and isinstance(self.schedule_time, datetime):
            data['schedule_time'] = self.schedule_time.isoformat()
        else:
            data['schedule_time'] = self.schedule_time
            
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建任务"""
        # 处理调度时间
        schedule_time = data.get('schedule_time')
        if data.get('type') == cls.TYPE_ONCE and isinstance(schedule_time, str):
            schedule_time = datetime.fromisoformat(schedule_time)
            
        task = cls(
            task_id=data.get('id'),
            name=data.get('name', ''),
            task_type=data.get('type', cls.TYPE_ONCE),
            target_type=data.get('target_type', ''),
            target_id=data.get('target_id', ''),
            schedule_time=schedule_time,
            enabled=data.get('enabled', True)
        )
        
        # 设置其他属性
        task.status = data.get('status', cls.STATUS_PENDING)
        task.run_count = data.get('run_count', 0)
        task.params = data.get('params', {})
        
        if data.get('last_run_time'):
            task.last_run_time = datetime.fromisoformat(data['last_run_time'])
            
        if data.get('next_run_time'):
            task.next_run_time = datetime.fromisoformat(data['next_run_time'])
        else:
            task._update_next_run_time()
            
        return task


class TaskScheduler(QObject):
    """任务调度器，用于调度和执行任务"""
    
    # 信号
    task_started = pyqtSignal(str)  # 任务开始信号 (任务ID)
    task_completed = pyqtSignal(str, bool, object)  # 任务完成信号 (任务ID, 是否成功, 结果)
    task_added = pyqtSignal(str)  # 任务添加信号 (任务ID)
    task_removed = pyqtSignal(str)  # 任务移除信号 (任务ID)
    task_enabled = pyqtSignal(str, bool)  # 任务启用/禁用信号 (任务ID, 是否启用)
    
    def __init__(self):
        """初始化任务调度器"""
        super().__init__()
        
        # 任务字典
        self.tasks = {}  # {task_id: Task}
        
        # 回调函数字典
        self.callbacks = {}  # {callback_id: Callable}
        
        # 运行状态
        self._running = False
        self._stop_event = threading.Event()
        self._scheduler_thread = None
        
        # 关联的执行器
        self._action_executor = None
        self._rule_matcher = None
        
        # 配置
        self.config = {
            'check_interval': 1.0,  # 检查间隔 (秒)
            'max_concurrent_tasks': 5,  # 最大并发任务数
            'task_timeout': 60.0,  # 任务超时时间 (秒)
            'retry_failed_tasks': True,  # 是否重试失败任务
            'max_retries': 3,  # 最大重试次数
            'retry_delay': 60.0  # 重试延迟 (秒)
        }
        
        # 运行中的任务
        self._running_tasks = {}  # {task_id: Thread}
        self._task_results = {}  # {task_id: (success, result)}
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """设置配置"""
        self.config.update(config)
    
    def set_action_executor(self, executor: Any) -> None:
        """设置动作执行器"""
        self._action_executor = executor
    
    def set_rule_matcher(self, matcher: Any) -> None:
        """设置规则匹配器"""
        self._rule_matcher = matcher
    
    def register_callback(self, callback_id: str, callback: Callable) -> None:
        """注册回调函数
        
        Args:
            callback_id: 回调ID
            callback: 回调函数
        """
        self.callbacks[callback_id] = callback
    
    def unregister_callback(self, callback_id: str) -> bool:
        """注销回调函数
        
        Args:
            callback_id: 回调ID
            
        Returns:
            bool: 是否成功注销
        """
        if callback_id in self.callbacks:
            del self.callbacks[callback_id]
            return True
        return False 

    def add_task(self, task: Task) -> None:
        """添加任务
        
        Args:
            task: 任务对象
        """
        self.tasks[task.id] = task
        self.task_added.emit(task.id)
        logger.info(f"任务已添加: {task.name}")
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功移除
        """
        if task_id in self.tasks:
            # 如果任务正在运行，先停止
            if task_id in self._running_tasks:
                self.cancel_task(task_id)
            
            del self.tasks[task_id]
            self.task_removed.emit(task_id)
            logger.info(f"任务已移除: {task_id}")
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Task]: 任务对象，不存在时返回None
        """
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Task]:
        """获取所有任务
        
        Returns:
            Dict[str, Task]: 任务字典
        """
        return self.tasks.copy()
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功启用
        """
        task = self.get_task(task_id)
        if task:
            task.enabled = True
            self.task_enabled.emit(task_id, True)
            logger.info(f"任务已启用: {task.name}")
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功禁用
        """
        task = self.get_task(task_id)
        if task:
            task.enabled = False
            self.task_enabled.emit(task_id, False)
            logger.info(f"任务已禁用: {task.name}")
            return True
        return False
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功取消
        """
        task = self.get_task(task_id)
        if not task:
            return False
        
        # 标记任务为已取消
        task.cancel()
        
        # 如果任务正在运行，等待结束
        if task_id in self._running_tasks:
            # 线程无法直接中断，只能等待结束
            logger.info(f"等待任务结束: {task.name}")
            # 这里不等待线程结束，只是标记状态
        
        logger.info(f"任务已取消: {task.name}")
        return True
    
    def run_task(self, task_id: str) -> bool:
        """立即运行任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功运行
        """
        task = self.get_task(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        # 检查任务是否已在运行
        if task_id in self._running_tasks and self._running_tasks[task_id].is_alive():
            logger.warning(f"任务已在运行中: {task.name}")
            return False
        
        # 创建任务线程
        thread = threading.Thread(
            target=self._execute_task,
            args=(task,),
            daemon=True
        )
        
        # 记录运行状态
        self._running_tasks[task_id] = thread
        
        # 启动线程
        thread.start()
        
        logger.info(f"任务已启动: {task.name}")
        return True
    
    def start(self) -> bool:
        """启动调度器"""
        if self._running:
            logger.warning("调度器已在运行")
            return False
        
        try:
            # 设置运行状态
            self._running = True
            self._stop_event.clear()
            
            # 创建并启动调度线程
            self._scheduler_thread = threading.Thread(
                target=self._scheduler_loop,
                daemon=True
            )
            self._scheduler_thread.start()
            
            logger.info("任务调度器已启动")
            return True
            
        except Exception as e:
            self._running = False
            logger.error(f"启动调度器失败: {e}")
            return False
    
    def stop(self) -> bool:
        """停止调度器"""
        if not self._running:
            logger.warning("调度器未在运行")
            return False
        
        try:
            # 设置停止事件
            self._stop_event.set()
            
            # 等待调度线程结束
            if self._scheduler_thread and self._scheduler_thread.is_alive():
                self._scheduler_thread.join(timeout=2.0)
            
            # 等待所有运行中的任务完成
            for task_id, thread in list(self._running_tasks.items()):
                if thread.is_alive():
                    logger.info(f"等待任务完成: {task_id}")
                    thread.join(timeout=1.0)
            
            # 重置状态
            self._running = False
            self._running_tasks.clear()
            
            logger.info("任务调度器已停止")
            return True
            
        except Exception as e:
            logger.error(f"停止调度器失败: {e}")
            return False
    
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running
    
    def trigger_event(self, event_type: str, event_params: Dict[str, Any] = None) -> int:
        """触发事件，执行对应的事件任务
        
        Args:
            event_type: 事件类型
            event_params: 事件参数
            
        Returns:
            int: 触发的任务数量
        """
        if not self._running:
            logger.warning("调度器未在运行，无法触发事件")
            return 0
        
        event_params = event_params or {}
        count = 0
        
        # 查找匹配的事件任务
        for task in self.tasks.values():
            if (task.enabled and 
                task.type == Task.TYPE_EVENT and 
                task.schedule_time.get('event_type') == event_type):
                
                # 检查事件参数
                task_event_params = task.schedule_time.get('event_params', {})
                if all(task_event_params.get(key) == event_params.get(key) 
                       for key in task_event_params):
                    # 运行任务
                    self.run_task(task.id)
                    count += 1
        
        logger.info(f"事件触发: {event_type}, 触发了 {count} 个任务")
        return count
    
    def _scheduler_loop(self) -> None:
        """调度器主循环"""
        logger.info("调度器循环已启动")
        
        while not self._stop_event.is_set():
            try:
                # 获取当前时间
                now = datetime.now()
                
                # 检查并执行到期任务
                for task_id, task in list(self.tasks.items()):
                    # 跳过禁用或已取消的任务
                    if not task.enabled or task.status == Task.STATUS_CANCELLED:
                        continue
                    
                    # 跳过事件触发任务
                    if task.type == Task.TYPE_EVENT:
                        continue
                    
                    # 跳过已在运行的任务
                    if task_id in self._running_tasks and self._running_tasks[task_id].is_alive():
                        continue
                    
                    # 检查是否到期
                    if task.next_run_time and task.next_run_time <= now:
                        # 检查是否超过最大并发任务数
                        running_count = sum(1 for t in self._running_tasks.values() if t.is_alive())
                        if running_count >= self.config['max_concurrent_tasks']:
                            logger.warning(f"已达到最大并发任务数 ({running_count}), 延迟执行任务: {task.name}")
                            continue
                        
                        # 运行任务
                        self.run_task(task_id)
                
                # 清理已完成的任务线程
                for task_id in list(self._running_tasks.keys()):
                    thread = self._running_tasks[task_id]
                    if not thread.is_alive():
                        del self._running_tasks[task_id]
                
                # 等待下一次检查
                self._stop_event.wait(self.config['check_interval'])
                
            except Exception as e:
                logger.error(f"调度器循环异常: {e}")
                time.sleep(1.0)  # 发生错误时短暂暂停
    
    def _execute_task(self, task: Task) -> None:
        """执行任务
        
        Args:
            task: 任务对象
        """
        success = False
        result = None
        
        try:
            # 标记任务开始
            task.mark_as_running()
            self.task_started.emit(task.id)
            
            logger.info(f"开始执行任务: {task.name}")
            
            # 根据目标类型执行
            if task.target_type == 'action' and self._action_executor:
                # 执行动作
                success = self._action_executor.execute_action(task.target_id)
                result = "动作执行" + ("成功" if success else "失败")
                
            elif task.target_type == 'sequence' and self._action_executor:
                # 执行动作序列
                success = self._action_executor.execute_sequence(task.target_id)
                result = "序列执行" + ("成功" if success else "失败")
                
            elif task.target_type == 'rule' and self._rule_matcher:
                # 执行规则匹配
                success = True  # 规则匹配总是视为成功
                result = self._rule_matcher.match(task.params.get('text', ''))
                
            elif task.target_type == 'callback':
                # 执行回调函数
                callback = self.callbacks.get(task.target_id)
                if callback:
                    result = callback(**task.params)
                    success = True
                else:
                    raise ValueError(f"回调函数不存在: {task.target_id}")
                    
            else:
                raise ValueError(f"不支持的目标类型: {task.target_type}")
            
            # 标记任务完成
            if success:
                task.mark_as_completed(result)
                logger.info(f"任务执行成功: {task.name}")
            else:
                task.mark_as_failed(str(result))
                logger.warning(f"任务执行失败: {task.name}")
            
            # 发送完成信号
            self.task_completed.emit(task.id, success, result)
            
        except Exception as e:
            # 标记任务失败
            error_msg = f"任务执行异常: {str(e)}"
            task.mark_as_failed(error_msg)
            logger.error(error_msg)
            
            # 发送完成信号
            self.task_completed.emit(task.id, False, error_msg)
    
    def to_dict(self) -> Dict[str, Any]:
        """将任务调度器转换为字典"""
        return {
            'tasks': {task_id: task.to_dict() for task_id, task in self.tasks.items()},
            'config': self.config.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskScheduler':
        """从字典创建任务调度器"""
        scheduler = cls()
        
        # 设置配置
        if 'config' in data:
            scheduler.set_config(data['config'])
        
        # 加载任务
        tasks_data = data.get('tasks', {})
        for task_data in tasks_data.values():
            task = Task.from_dict(task_data)
            scheduler.add_task(task)
        
        return scheduler 