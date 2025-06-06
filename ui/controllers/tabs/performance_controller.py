from PyQt5.QtCore import QObject, pyqtSlot, Qt
from PyQt5.QtWidgets import QMessageBox
import os
from datetime import datetime

from core.utils.performance_monitor import PerformanceMonitor
from ui.components.tabs.performance_tab import PerformanceTab
from loguru import logger


class PerformanceController(QObject):
    """性能监控控制器，连接性能监控标签页和性能监控工具"""
    
    def __init__(self, performance_tab):
        """初始化性能监控控制器
        
        Args:
            performance_tab: 性能监控标签页
        """
        super().__init__()
        
        self.performance_tab = performance_tab
        
        # 创建性能监控工具
        try:
            self.performance_monitor = PerformanceMonitor(interval=5.0)
            logger.info("性能监控工具初始化成功")
        except Exception as e:
            logger.error(f"性能监控工具初始化失败: {e}")
            self.performance_monitor = None
            QMessageBox.critical(
                self.performance_tab,
                "错误",
                f"性能监控工具初始化失败: {e}"
            )
            return
        
        # 连接信号
        self._connect_signals()
        
        # 初始化性能监控
        self._init_performance_monitor()
    
    def _connect_signals(self):
        """连接信号"""
        # 连接性能监控标签页的配置变更信号
        self.performance_tab.config_changed.connect(self._on_config_changed)
        
        # 连接性能监控工具的指标更新信号
        if self.performance_monitor:
            self.performance_monitor.metrics_updated.connect(self._on_metrics_updated)
    
    def _init_performance_monitor(self):
        """初始化性能监控"""
        if not self.performance_monitor:
            return
        
        # 获取性能监控标签页的设置
        settings = self.performance_tab.settings
        
        # 设置性能监控工具的配置
        self.performance_monitor.set_config({
            'interval': settings['update_interval'] / 1000,
            'history_size': settings['history_size'],
            'collect_system_metrics': settings['show_system'],
            'collect_process_metrics': settings['show_process']
        })
        
        # 启动性能监控
        self.performance_monitor.start_monitoring()
        logger.info("性能监控已启动")
    
    @pyqtSlot(dict)
    def _on_config_changed(self, config):
        """配置变更事件处理
        
        Args:
            config: 配置字典
        """
        if not self.performance_monitor:
            return
        
        # 处理配置变更
        if 'interval' in config:
            self.performance_monitor.set_config({'interval': config['interval']})
        
        if 'history_size' in config:
            self.performance_monitor.set_config({'history_size': config['history_size']})
        
        if 'collect_system_metrics' in config:
            self.performance_monitor.set_config({'collect_system_metrics': config['collect_system_metrics']})
        
        if 'collect_process_metrics' in config:
            self.performance_monitor.set_config({'collect_process_metrics': config['collect_process_metrics']})
        
        # 处理清空指标
        if config.get('clear_metrics', False):
            self.performance_monitor.clear_metrics()
        
        # 处理更新图表
        if config.get('update_charts', False):
            self._update_charts()
        
        # 处理导出报告
        if 'export_report' in config:
            self._export_performance_report(config['export_report'])
        
        # 处理自定义指标
        if 'custom_metrics' in config:
            logger.debug(f"添加自定义指标: {config['custom_metrics']}")
    
    @pyqtSlot(dict)
    def _on_metrics_updated(self, metrics):
        """指标更新事件处理
        
        Args:
            metrics: 性能指标
        """
        # 更新性能监控标签页的指标
        self.performance_tab.update_metrics(self.performance_monitor.get_metrics())
    
    def _update_charts(self):
        """更新图表"""
        if not self.performance_monitor:
            return
        
        # 获取性能指标
        metrics = self.performance_monitor.get_metrics()
        
        # 更新性能监控标签页的指标
        self.performance_tab.update_metrics(metrics)
    
    def _export_performance_report(self, file_path):
        """导出性能报告
        
        Args:
            file_path: 文件路径
        """
        if not self.performance_monitor:
            return
        
        try:
            # 保存性能报告
            success = self.performance_monitor.save_performance_report(file_path)
            
            if success:
                QMessageBox.information(
                    self.performance_tab,
                    "导出成功",
                    f"性能报告已导出到: {file_path}"
                )
            else:
                QMessageBox.warning(
                    self.performance_tab,
                    "导出失败",
                    "性能报告导出失败"
                )
        
        except Exception as e:
            logger.error(f"导出性能报告失败: {e}")
            QMessageBox.critical(
                self.performance_tab,
                "错误",
                f"导出性能报告失败: {e}"
            )
    
    def add_custom_metric(self, name, value):
        """添加自定义指标
        
        Args:
            name: 指标名称
            value: 指标值
        """
        if not self.performance_monitor:
            return
        
        # 添加自定义指标到性能监控工具
        self.performance_monitor.add_custom_metric(name, value)
        
        # 添加自定义指标到性能监控标签页
        self.performance_tab.add_custom_metric_value(name, value)
    
    def shutdown(self):
        """关闭性能监控"""
        if not self.performance_monitor:
            return
        
        # 停止性能监控
        self.performance_monitor.stop_monitoring()
        logger.info("性能监控已停止") 