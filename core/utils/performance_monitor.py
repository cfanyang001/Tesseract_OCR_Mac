import os
import time
import threading
import psutil
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal
from loguru import logger


class PerformanceMonitor(QObject):
    """性能监控工具，用于收集和显示应用程序的性能指标"""
    
    # 信号
    metrics_updated = pyqtSignal(dict)  # 指标更新信号
    
    def __init__(self, interval=5.0):
        """初始化性能监控工具
        
        Args:
            interval: 监控间隔(秒)
        """
        super().__init__()
        
        # 配置
        self.config = {
            'interval': interval,         # 监控间隔(秒)
            'history_size': 60,           # 历史记录大小
            'process_name': 'python',     # 进程名称
            'collect_system_metrics': True,  # 是否收集系统指标
            'collect_process_metrics': True,  # 是否收集进程指标
            'collect_memory_metrics': True,   # 是否收集内存指标
            'collect_disk_metrics': True,     # 是否收集磁盘指标
            'collect_network_metrics': True,  # 是否收集网络指标
            'alert_cpu_threshold': 80,    # CPU使用率警告阈值
            'alert_memory_threshold': 80  # 内存使用率警告阈值
        }
        
        # 性能指标
        self.metrics = {
            'timestamp': [],
            'system': {
                'cpu_percent': [],
                'memory_percent': [],
                'memory_used': [],
                'memory_total': [],
                'disk_usage': [],
                'disk_io': [],
                'network_sent': [],
                'network_recv': []
            },
            'process': {
                'cpu_percent': [],
                'memory_percent': [],
                'memory_used': [],
                'threads': [],
                'io_read': [],
                'io_write': []
            },
            'custom': {}
        }
        
        # 状态
        self._running = False
        self._thread = None
        self._stop_event = threading.Event()
        self._process = None
        self._last_io = None
        self._last_network = None
        self._last_time = None
        
        # 初始化进程
        self._init_process()
    
    def _init_process(self):
        """初始化进程"""
        try:
            # 获取当前进程
            self._process = psutil.Process(os.getpid())
            logger.debug(f"性能监控初始化成功，监控进程ID: {self._process.pid}")
        except Exception as e:
            logger.error(f"性能监控初始化失败: {e}")
            self._process = None
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """设置配置"""
        self.config.update(config)
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.config.copy()
    
    def start_monitoring(self) -> None:
        """开始监控"""
        if self._running:
            logger.warning("性能监控已经在运行")
            return
        
        # 重置停止事件
        self._stop_event.clear()
        
        # 设置运行状态
        self._running = True
        
        # 创建并启动监控线程
        self._thread = threading.Thread(
            target=self._monitoring_thread,
            daemon=True
        )
        self._thread.start()
        
        logger.info("性能监控已启动")
    
    def stop_monitoring(self) -> None:
        """停止监控"""
        if not self._running:
            logger.warning("性能监控未在运行")
            return
        
        # 设置停止事件
        self._stop_event.set()
        
        # 等待线程结束
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        
        # 设置运行状态
        self._running = False
        
        logger.info("性能监控已停止")
    
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.metrics.copy()
    
    def get_latest_metrics(self) -> Dict[str, Any]:
        """获取最新性能指标"""
        result = {
            'timestamp': self.metrics['timestamp'][-1] if self.metrics['timestamp'] else None,
            'system': {},
            'process': {},
            'custom': {}
        }
        
        # 获取系统指标
        for key, values in self.metrics['system'].items():
            result['system'][key] = values[-1] if values else None
        
        # 获取进程指标
        for key, values in self.metrics['process'].items():
            result['process'][key] = values[-1] if values else None
        
        # 获取自定义指标
        for key, values in self.metrics['custom'].items():
            result['custom'][key] = values[-1] if values else None
        
        return result
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取性能指标摘要"""
        result = {
            'system': {},
            'process': {},
            'custom': {}
        }
        
        # 计算系统指标摘要
        for key, values in self.metrics['system'].items():
            if not values:
                continue
            result['system'][key] = {
                'current': values[-1],
                'avg': np.mean(values),
                'min': np.min(values),
                'max': np.max(values)
            }
        
        # 计算进程指标摘要
        for key, values in self.metrics['process'].items():
            if not values:
                continue
            result['process'][key] = {
                'current': values[-1],
                'avg': np.mean(values),
                'min': np.min(values),
                'max': np.max(values)
            }
        
        # 计算自定义指标摘要
        for key, values in self.metrics['custom'].items():
            if not values:
                continue
            result['custom'][key] = {
                'current': values[-1],
                'avg': np.mean(values),
                'min': np.min(values),
                'max': np.max(values)
            }
        
        return result
    
    def add_custom_metric(self, name: str, value: float) -> None:
        """添加自定义指标
        
        Args:
            name: 指标名称
            value: 指标值
        """
        if name not in self.metrics['custom']:
            self.metrics['custom'][name] = []
        
        self.metrics['custom'][name].append(value)
        
        # 限制历史记录大小
        if len(self.metrics['custom'][name]) > self.config['history_size']:
            self.metrics['custom'][name] = self.metrics['custom'][name][-self.config['history_size']:]
    
    def clear_metrics(self) -> None:
        """清空性能指标"""
        self.metrics = {
            'timestamp': [],
            'system': {
                'cpu_percent': [],
                'memory_percent': [],
                'memory_used': [],
                'memory_total': [],
                'disk_usage': [],
                'disk_io': [],
                'network_sent': [],
                'network_recv': []
            },
            'process': {
                'cpu_percent': [],
                'memory_percent': [],
                'memory_used': [],
                'threads': [],
                'io_read': [],
                'io_write': []
            },
            'custom': self.metrics['custom'].copy()  # 保留自定义指标
        }
        
        logger.debug("性能指标已清空")
    
    def _monitoring_thread(self) -> None:
        """监控线程"""
        try:
            while not self._stop_event.is_set():
                try:
                    # 收集性能指标
                    self._collect_metrics()
                    
                    # 发送信号
                    self.metrics_updated.emit(self.get_latest_metrics())
                    
                    # 检查警告阈值
                    self._check_alerts()
                    
                except Exception as e:
                    logger.error(f"性能监控过程中发生错误: {e}")
                
                # 等待下一次收集
                if not self._stop_event.wait(self.config['interval']):
                    continue
                else:
                    break
        
        except Exception as e:
            logger.error(f"性能监控线程异常: {e}")
            self._running = False
    
    def _collect_metrics(self) -> None:
        """收集性能指标"""
        now = time.time()
        self.metrics['timestamp'].append(now)
        
        # 限制历史记录大小
        if len(self.metrics['timestamp']) > self.config['history_size']:
            self.metrics['timestamp'] = self.metrics['timestamp'][-self.config['history_size']:]
        
        # 收集系统指标
        if self.config['collect_system_metrics']:
            self._collect_system_metrics()
        
        # 收集进程指标
        if self.config['collect_process_metrics'] and self._process:
            self._collect_process_metrics()
        
        # 更新最后时间
        self._last_time = now
    
    def _collect_system_metrics(self) -> None:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=None)
            self.metrics['system']['cpu_percent'].append(cpu_percent)
            
            # 内存使用率
            if self.config['collect_memory_metrics']:
                memory = psutil.virtual_memory()
                self.metrics['system']['memory_percent'].append(memory.percent)
                self.metrics['system']['memory_used'].append(memory.used / (1024 * 1024))  # MB
                self.metrics['system']['memory_total'].append(memory.total / (1024 * 1024))  # MB
            
            # 磁盘使用率
            if self.config['collect_disk_metrics']:
                disk = psutil.disk_usage('/')
                self.metrics['system']['disk_usage'].append(disk.percent)
                
                # 磁盘IO
                disk_io = psutil.disk_io_counters()
                if self._last_io:
                    read_bytes = disk_io.read_bytes - self._last_io.read_bytes
                    write_bytes = disk_io.write_bytes - self._last_io.write_bytes
                    
                    # 计算每秒IO
                    if self._last_time:
                        elapsed = time.time() - self._last_time
                        if elapsed > 0:
                            read_bytes /= elapsed
                            write_bytes /= elapsed
                    
                    self.metrics['system']['disk_io'].append((read_bytes, write_bytes))
                else:
                    self.metrics['system']['disk_io'].append((0, 0))
                
                self._last_io = disk_io
            
            # 网络使用率
            if self.config['collect_network_metrics']:
                network = psutil.net_io_counters()
                if self._last_network:
                    sent_bytes = network.bytes_sent - self._last_network.bytes_sent
                    recv_bytes = network.bytes_recv - self._last_network.bytes_recv
                    
                    # 计算每秒网络流量
                    if self._last_time:
                        elapsed = time.time() - self._last_time
                        if elapsed > 0:
                            sent_bytes /= elapsed
                            recv_bytes /= elapsed
                    
                    self.metrics['system']['network_sent'].append(sent_bytes)
                    self.metrics['system']['network_recv'].append(recv_bytes)
                else:
                    self.metrics['system']['network_sent'].append(0)
                    self.metrics['system']['network_recv'].append(0)
                
                self._last_network = network
            
            # 限制历史记录大小
            for key, values in self.metrics['system'].items():
                if len(values) > self.config['history_size']:
                    self.metrics['system'][key] = values[-self.config['history_size']:]
        
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
    
    def _collect_process_metrics(self) -> None:
        """收集进程指标"""
        try:
            # 更新进程信息
            self._process.cpu_percent(interval=None)  # 第一次调用总是返回0，需要先调用一次
            
            # CPU使用率
            cpu_percent = self._process.cpu_percent(interval=None) / psutil.cpu_count()
            self.metrics['process']['cpu_percent'].append(cpu_percent)
            
            # 内存使用率
            memory_info = self._process.memory_info()
            memory_percent = self._process.memory_percent()
            self.metrics['process']['memory_percent'].append(memory_percent)
            self.metrics['process']['memory_used'].append(memory_info.rss / (1024 * 1024))  # MB
            
            # 线程数
            self.metrics['process']['threads'].append(self._process.num_threads())
            
            # IO计数 - 在某些系统（如macOS）上可能不可用
            try:
                if hasattr(self._process, 'io_counters'):
                    io_counters = self._process.io_counters()
                    self.metrics['process']['io_read'].append(io_counters.read_bytes / (1024 * 1024))  # MB
                    self.metrics['process']['io_write'].append(io_counters.write_bytes / (1024 * 1024))  # MB
                else:
                    # 如果不可用，添加0值
                    self.metrics['process']['io_read'].append(0)
                    self.metrics['process']['io_write'].append(0)
            except Exception as io_error:
                logger.debug(f"获取进程IO计数失败: {io_error}")
                # 如果获取失败，添加0值
                self.metrics['process']['io_read'].append(0)
                self.metrics['process']['io_write'].append(0)
            
            # 限制历史记录大小
            for key, values in self.metrics['process'].items():
                if len(values) > self.config['history_size']:
                    self.metrics['process'][key] = values[-self.config['history_size']:]
        
        except Exception as e:
            logger.error(f"收集进程指标失败: {e}")
    
    def _check_alerts(self) -> None:
        """检查警告阈值"""
        try:
            # 检查CPU使用率
            if self.metrics['system']['cpu_percent'] and self.metrics['system']['cpu_percent'][-1] > self.config['alert_cpu_threshold']:
                logger.warning(f"CPU使用率过高: {self.metrics['system']['cpu_percent'][-1]}%")
            
            # 检查内存使用率
            if self.metrics['system']['memory_percent'] and self.metrics['system']['memory_percent'][-1] > self.config['alert_memory_threshold']:
                logger.warning(f"内存使用率过高: {self.metrics['system']['memory_percent'][-1]}%")
        
        except Exception as e:
            logger.error(f"检查警告阈值失败: {e}")
    
    def get_performance_report(self) -> str:
        """生成性能报告"""
        try:
            summary = self.get_metrics_summary()
            
            report = "性能监控报告\n"
            report += "=" * 50 + "\n"
            report += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += f"监控间隔: {self.config['interval']}秒\n"
            report += f"历史记录大小: {self.config['history_size']}\n"
            report += "=" * 50 + "\n\n"
            
            # 系统指标
            report += "系统指标:\n"
            report += "-" * 50 + "\n"
            for key, value in summary['system'].items():
                report += f"{key}: 当前={value['current']:.2f}, 平均={value['avg']:.2f}, 最小={value['min']:.2f}, 最大={value['max']:.2f}\n"
            report += "\n"
            
            # 进程指标
            report += "进程指标:\n"
            report += "-" * 50 + "\n"
            for key, value in summary['process'].items():
                report += f"{key}: 当前={value['current']:.2f}, 平均={value['avg']:.2f}, 最小={value['min']:.2f}, 最大={value['max']:.2f}\n"
            report += "\n"
            
            # 自定义指标
            if summary['custom']:
                report += "自定义指标:\n"
                report += "-" * 50 + "\n"
                for key, value in summary['custom'].items():
                    report += f"{key}: 当前={value['current']:.2f}, 平均={value['avg']:.2f}, 最小={value['min']:.2f}, 最大={value['max']:.2f}\n"
            
            return report
        
        except Exception as e:
            logger.error(f"生成性能报告失败: {e}")
            return f"生成性能报告失败: {e}"
    
    def save_performance_report(self, file_path: str) -> bool:
        """保存性能报告到文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # 生成报告
            report = self.get_performance_report()
            
            # 保存到文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"性能报告保存成功: {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"保存性能报告失败: {e}")
            return False 