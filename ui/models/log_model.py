from typing import Dict, List, Any, Tuple
from datetime import datetime

from ui.models.base_model import BaseModel


class LogEntry:
    """日志条目类，表示一条日志记录"""
    
    LEVEL_DEBUG = 'debug'       # 调试
    LEVEL_INFO = 'info'         # 信息
    LEVEL_WARNING = 'warning'   # 警告
    LEVEL_ERROR = 'error'       # 错误
    LEVEL_CRITICAL = 'critical' # 严重
    
    SOURCE_OCR = 'ocr'          # OCR
    SOURCE_MONITOR = 'monitor'  # 监控
    SOURCE_TASK = 'task'        # 任务
    SOURCE_ACTION = 'action'    # 动作
    SOURCE_SYSTEM = 'system'    # 系统
    
    def __init__(self, log_id: str, level: str, source: str, message: str, 
                 details: str = '', timestamp: datetime = None):
        self.id = log_id                      # 日志ID
        self.level = level                    # 日志级别
        self.source = source                  # 日志来源
        self.message = message                # 日志消息
        self.details = details                # 日志详情
        self.timestamp = timestamp or datetime.now()  # 时间戳
    
    def to_dict(self) -> Dict[str, Any]:
        """将日志条目转换为字典"""
        return {
            'id': self.id,
            'level': self.level,
            'source': self.source,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """从字典创建日志条目"""
        return cls(
            log_id=data['id'],
            level=data['level'],
            source=data['source'],
            message=data['message'],
            details=data.get('details', ''),
            timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else None
        )


class LogModel(BaseModel):
    """日志模型类，存储应用程序日志"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化默认数据
        self._data = {
            'logs': [],          # 日志列表 [LogEntry]
            'max_logs': 1000,    # 最大日志数量
        }
    
    def add_log(self, log: LogEntry) -> None:
        """添加日志"""
        logs = self.get('logs').copy()
        logs.append(log)
        
        # 限制日志数量
        max_logs = self.get('max_logs')
        if len(logs) > max_logs:
            logs = logs[-max_logs:]
        
        self.set('logs', logs)
    
    def get_logs(self) -> List[LogEntry]:
        """获取所有日志"""
        return self.get('logs')
    
    def clear_logs(self) -> None:
        """清空日志"""
        self.set('logs', [])
    
    def set_max_logs(self, max_logs: int) -> None:
        """设置最大日志数量"""
        self.set('max_logs', max(100, min(10000, max_logs)))
    
    def get_max_logs(self) -> int:
        """获取最大日志数量"""
        return self.get('max_logs')
    
    def get_filtered_logs(self, level: str = None, source: str = None, 
                          start_time: datetime = None, end_time: datetime = None,
                          search_text: str = None) -> List[LogEntry]:
        """获取过滤后的日志"""
        logs = self.get_logs()
        
        # 过滤日志级别
        if level and level != 'all':
            logs = [log for log in logs if log.level == level]
        
        # 过滤日志来源
        if source and source != 'all':
            logs = [log for log in logs if log.source == source]
        
        # 过滤时间范围
        if start_time:
            logs = [log for log in logs if log.timestamp >= start_time]
        if end_time:
            logs = [log for log in logs if log.timestamp <= end_time]
        
        # 过滤搜索文本
        if search_text:
            search_text = search_text.lower()
            logs = [log for log in logs if search_text in log.message.lower() or search_text in log.details.lower()]
        
        return logs
    
    def add_debug_log(self, source: str, message: str, details: str = '') -> None:
        """添加调试日志"""
        import uuid
        log = LogEntry(
            log_id=str(uuid.uuid4()),
            level=LogEntry.LEVEL_DEBUG,
            source=source,
            message=message,
            details=details
        )
        self.add_log(log)
    
    def add_info_log(self, source: str, message: str, details: str = '') -> None:
        """添加信息日志"""
        import uuid
        log = LogEntry(
            log_id=str(uuid.uuid4()),
            level=LogEntry.LEVEL_INFO,
            source=source,
            message=message,
            details=details
        )
        self.add_log(log)
    
    def add_warning_log(self, source: str, message: str, details: str = '') -> None:
        """添加警告日志"""
        import uuid
        log = LogEntry(
            log_id=str(uuid.uuid4()),
            level=LogEntry.LEVEL_WARNING,
            source=source,
            message=message,
            details=details
        )
        self.add_log(log)
    
    def add_error_log(self, source: str, message: str, details: str = '') -> None:
        """添加错误日志"""
        import uuid
        log = LogEntry(
            log_id=str(uuid.uuid4()),
            level=LogEntry.LEVEL_ERROR,
            source=source,
            message=message,
            details=details
        )
        self.add_log(log)
    
    def add_critical_log(self, source: str, message: str, details: str = '') -> None:
        """添加严重日志"""
        import uuid
        log = LogEntry(
            log_id=str(uuid.uuid4()),
            level=LogEntry.LEVEL_CRITICAL,
            source=source,
            message=message,
            details=details
        )
        self.add_log(log) 