from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
                           QGroupBox, QLabel, QLineEdit, QPushButton, 
                           QComboBox, QDoubleSpinBox, QCheckBox, QFileDialog,
                           QGridLayout, QSpinBox, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QFont
import pyqtgraph as pg
import numpy as np
from datetime import datetime
from loguru import logger


class PerformanceTab(QWidget):
    """性能监控标签页，用于显示应用程序的性能指标"""
    
    # 信号
    config_changed = pyqtSignal(dict)  # 配置变更信号
    
    def __init__(self, parent=None):
        """初始化性能监控标签页"""
        super().__init__(parent)
        
        # 设置
        self.settings = {
            'update_interval': 1000,  # 更新间隔(毫秒)
            'history_size': 60,       # 历史记录大小
            'show_system': True,      # 显示系统指标
            'show_process': True,     # 显示进程指标
            'show_custom': True,      # 显示自定义指标
            'auto_refresh': True      # 自动刷新
        }
        
        # 初始化UI
        self._init_ui()
        
        # 创建定时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_charts)
        
        # 如果自动刷新，启动定时器
        if self.settings['auto_refresh']:
            self._timer.start(self.settings['update_interval'])
    
    def _init_ui(self):
        """初始化UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        
        # 创建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 创建图表区域
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 系统性能标签页
        system_tab = QWidget()
        system_layout = QVBoxLayout(system_tab)
        self._create_system_charts(system_layout)
        tab_widget.addTab(system_tab, "系统性能")
        
        # 进程性能标签页
        process_tab = QWidget()
        process_layout = QVBoxLayout(process_tab)
        self._create_process_charts(process_layout)
        tab_widget.addTab(process_tab, "进程性能")
        
        # 自定义指标标签页
        custom_tab = QWidget()
        custom_layout = QVBoxLayout(custom_tab)
        self._create_custom_charts(custom_layout)
        tab_widget.addTab(custom_tab, "自定义指标")
        
        # 添加标签页到图表布局
        charts_layout.addWidget(tab_widget)
        
        # 创建控制面板
        control_panel = self._create_control_panel()
        
        # 添加组件到分割器
        splitter.addWidget(charts_widget)
        splitter.addWidget(control_panel)
        
        # 设置分割器比例
        splitter.setSizes([700, 100])
        
        # 添加分割器到主布局
        main_layout.addWidget(splitter)
    
    def _create_system_charts(self, layout):
        """创建系统性能图表"""
        # 创建CPU使用率图表
        cpu_group = QGroupBox("CPU使用率")
        cpu_layout = QVBoxLayout(cpu_group)
        self.cpu_chart = pg.PlotWidget()
        self.cpu_chart.setBackground('w')
        self.cpu_chart.setTitle("CPU使用率 (%)")
        self.cpu_chart.setLabel('left', "使用率 (%)")
        self.cpu_chart.setLabel('bottom', "时间 (秒)")
        self.cpu_chart.setYRange(0, 100)
        self.cpu_curve = self.cpu_chart.plot(pen=pg.mkPen(color='b', width=2))
        cpu_layout.addWidget(self.cpu_chart)
        
        # 创建内存使用率图表
        memory_group = QGroupBox("内存使用率")
        memory_layout = QVBoxLayout(memory_group)
        self.memory_chart = pg.PlotWidget()
        self.memory_chart.setBackground('w')
        self.memory_chart.setTitle("内存使用率 (%)")
        self.memory_chart.setLabel('left', "使用率 (%)")
        self.memory_chart.setLabel('bottom', "时间 (秒)")
        self.memory_chart.setYRange(0, 100)
        self.memory_curve = self.memory_chart.plot(pen=pg.mkPen(color='r', width=2))
        memory_layout.addWidget(self.memory_chart)
        
        # 创建磁盘使用率图表
        disk_group = QGroupBox("磁盘使用率")
        disk_layout = QVBoxLayout(disk_group)
        self.disk_chart = pg.PlotWidget()
        self.disk_chart.setBackground('w')
        self.disk_chart.setTitle("磁盘使用率 (%)")
        self.disk_chart.setLabel('left', "使用率 (%)")
        self.disk_chart.setLabel('bottom', "时间 (秒)")
        self.disk_chart.setYRange(0, 100)
        self.disk_curve = self.disk_chart.plot(pen=pg.mkPen(color='g', width=2))
        disk_layout.addWidget(self.disk_chart)
        
        # 创建网络使用率图表
        network_group = QGroupBox("网络使用率")
        network_layout = QVBoxLayout(network_group)
        self.network_chart = pg.PlotWidget()
        self.network_chart.setBackground('w')
        self.network_chart.setTitle("网络使用率 (KB/s)")
        self.network_chart.setLabel('left', "使用率 (KB/s)")
        self.network_chart.setLabel('bottom', "时间 (秒)")
        self.network_sent_curve = self.network_chart.plot(pen=pg.mkPen(color='b', width=2), name="发送")
        self.network_recv_curve = self.network_chart.plot(pen=pg.mkPen(color='r', width=2), name="接收")
        self.network_chart.addLegend()
        network_layout.addWidget(self.network_chart)
        
        # 添加图表到布局
        grid_layout = QGridLayout()
        grid_layout.addWidget(cpu_group, 0, 0)
        grid_layout.addWidget(memory_group, 0, 1)
        grid_layout.addWidget(disk_group, 1, 0)
        grid_layout.addWidget(network_group, 1, 1)
        layout.addLayout(grid_layout)
    
    def _create_process_charts(self, layout):
        """创建进程性能图表"""
        # 创建进程CPU使用率图表
        cpu_group = QGroupBox("进程CPU使用率")
        cpu_layout = QVBoxLayout(cpu_group)
        self.process_cpu_chart = pg.PlotWidget()
        self.process_cpu_chart.setBackground('w')
        self.process_cpu_chart.setTitle("进程CPU使用率 (%)")
        self.process_cpu_chart.setLabel('left', "使用率 (%)")
        self.process_cpu_chart.setLabel('bottom', "时间 (秒)")
        self.process_cpu_chart.setYRange(0, 100)
        self.process_cpu_curve = self.process_cpu_chart.plot(pen=pg.mkPen(color='b', width=2))
        cpu_layout.addWidget(self.process_cpu_chart)
        
        # 创建进程内存使用率图表
        memory_group = QGroupBox("进程内存使用率")
        memory_layout = QVBoxLayout(memory_group)
        self.process_memory_chart = pg.PlotWidget()
        self.process_memory_chart.setBackground('w')
        self.process_memory_chart.setTitle("进程内存使用率 (%)")
        self.process_memory_chart.setLabel('left', "使用率 (%)")
        self.process_memory_chart.setLabel('bottom', "时间 (秒)")
        self.process_memory_chart.setYRange(0, 100)
        self.process_memory_curve = self.process_memory_chart.plot(pen=pg.mkPen(color='r', width=2))
        memory_layout.addWidget(self.process_memory_chart)
        
        # 创建进程线程数图表
        threads_group = QGroupBox("进程线程数")
        threads_layout = QVBoxLayout(threads_group)
        self.threads_chart = pg.PlotWidget()
        self.threads_chart.setBackground('w')
        self.threads_chart.setTitle("进程线程数")
        self.threads_chart.setLabel('left', "线程数")
        self.threads_chart.setLabel('bottom', "时间 (秒)")
        self.threads_curve = self.threads_chart.plot(pen=pg.mkPen(color='g', width=2))
        threads_layout.addWidget(self.threads_chart)
        
        # 创建进程IO图表
        io_group = QGroupBox("进程IO")
        io_layout = QVBoxLayout(io_group)
        self.io_chart = pg.PlotWidget()
        self.io_chart.setBackground('w')
        self.io_chart.setTitle("进程IO (MB)")
        self.io_chart.setLabel('left', "IO (MB)")
        self.io_chart.setLabel('bottom', "时间 (秒)")
        self.io_read_curve = self.io_chart.plot(pen=pg.mkPen(color='b', width=2), name="读取")
        self.io_write_curve = self.io_chart.plot(pen=pg.mkPen(color='r', width=2), name="写入")
        self.io_chart.addLegend()
        io_layout.addWidget(self.io_chart)
        
        # 添加图表到布局
        grid_layout = QGridLayout()
        grid_layout.addWidget(cpu_group, 0, 0)
        grid_layout.addWidget(memory_group, 0, 1)
        grid_layout.addWidget(threads_group, 1, 0)
        grid_layout.addWidget(io_group, 1, 1)
        layout.addLayout(grid_layout)
    
    def _create_custom_charts(self, layout):
        """创建自定义指标图表"""
        # 创建自定义指标图表容器
        self.custom_charts_layout = QVBoxLayout()
        
        # 创建添加自定义指标按钮
        add_button = QPushButton("添加自定义指标")
        add_button.clicked.connect(self._add_custom_chart)
        
        # 添加组件到布局
        layout.addLayout(self.custom_charts_layout)
        layout.addWidget(add_button)
        layout.addStretch()
    
    def _add_custom_chart(self):
        """添加自定义指标图表"""
        # 创建对话框
        from PyQt5.QtWidgets import QDialog, QFormLayout
        dialog = QDialog(self)
        dialog.setWindowTitle("添加自定义指标")
        dialog_layout = QFormLayout(dialog)
        
        # 创建输入字段
        name_input = QLineEdit()
        name_input.setPlaceholderText("指标名称")
        
        # 创建按钮
        buttons_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        cancel_button = QPushButton("取消")
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)
        
        # 添加组件到布局
        dialog_layout.addRow("指标名称:", name_input)
        dialog_layout.addRow(buttons_layout)
        
        # 连接信号
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            name = name_input.text().strip()
            if name:
                self._create_custom_chart(name)
    
    def _create_custom_chart(self, name):
        """创建自定义指标图表
        
        Args:
            name: 指标名称
        """
        # 创建图表组
        group = QGroupBox(name)
        group_layout = QVBoxLayout(group)
        
        # 创建图表
        chart = pg.PlotWidget()
        chart.setBackground('w')
        chart.setTitle(name)
        chart.setLabel('left', "值")
        chart.setLabel('bottom', "时间 (秒)")
        curve = chart.plot(pen=pg.mkPen(color='b', width=2))
        group_layout.addWidget(chart)
        
        # 添加图表到布局
        self.custom_charts_layout.addWidget(group)
        
        # 保存图表引用
        if not hasattr(self, 'custom_charts'):
            self.custom_charts = {}
        
        self.custom_charts[name] = {
            'chart': chart,
            'curve': curve,
            'data': []
        }
        
        # 发送信号通知添加了自定义指标
        self.config_changed.emit({
            'custom_metrics': list(self.custom_charts.keys())
        })
    
    def _create_control_panel(self):
        """创建控制面板"""
        # 创建控制面板组
        control_group = QGroupBox("控制面板")
        control_layout = QVBoxLayout(control_group)
        
        # 创建设置布局
        settings_layout = QGridLayout()
        
        # 更新间隔
        settings_layout.addWidget(QLabel("更新间隔(毫秒):"), 0, 0)
        interval_spin = QSpinBox()
        interval_spin.setRange(100, 10000)
        interval_spin.setSingleStep(100)
        interval_spin.setValue(self.settings['update_interval'])
        interval_spin.valueChanged.connect(self._on_interval_changed)
        settings_layout.addWidget(interval_spin, 0, 1)
        
        # 历史记录大小
        settings_layout.addWidget(QLabel("历史记录大小:"), 0, 2)
        history_spin = QSpinBox()
        history_spin.setRange(10, 1000)
        history_spin.setSingleStep(10)
        history_spin.setValue(self.settings['history_size'])
        history_spin.valueChanged.connect(self._on_history_size_changed)
        settings_layout.addWidget(history_spin, 0, 3)
        
        # 显示系统指标
        show_system_check = QCheckBox("显示系统指标")
        show_system_check.setChecked(self.settings['show_system'])
        show_system_check.stateChanged.connect(self._on_show_system_changed)
        settings_layout.addWidget(show_system_check, 1, 0, 1, 2)
        
        # 显示进程指标
        show_process_check = QCheckBox("显示进程指标")
        show_process_check.setChecked(self.settings['show_process'])
        show_process_check.stateChanged.connect(self._on_show_process_changed)
        settings_layout.addWidget(show_process_check, 1, 2, 1, 2)
        
        # 自动刷新
        auto_refresh_check = QCheckBox("自动刷新")
        auto_refresh_check.setChecked(self.settings['auto_refresh'])
        auto_refresh_check.stateChanged.connect(self._on_auto_refresh_changed)
        settings_layout.addWidget(auto_refresh_check, 2, 0, 1, 2)
        
        # 按钮布局
        buttons_layout = QHBoxLayout()
        
        # 刷新按钮
        refresh_button = QPushButton("刷新")
        refresh_button.clicked.connect(self._on_refresh_clicked)
        buttons_layout.addWidget(refresh_button)
        
        # 清空按钮
        clear_button = QPushButton("清空")
        clear_button.clicked.connect(self._on_clear_clicked)
        buttons_layout.addWidget(clear_button)
        
        # 导出按钮
        export_button = QPushButton("导出报告")
        export_button.clicked.connect(self._on_export_clicked)
        buttons_layout.addWidget(export_button)
        
        # 添加布局到控制面板
        control_layout.addLayout(settings_layout)
        control_layout.addLayout(buttons_layout)
        
        return control_group
    
    def _on_interval_changed(self, value):
        """更新间隔变更事件处理"""
        self.settings['update_interval'] = value
        
        # 如果定时器在运行，重启定时器
        if self._timer.isActive():
            self._timer.stop()
            self._timer.start(value)
        
        # 发送配置变更信号
        self.config_changed.emit({'interval': value / 1000})
    
    def _on_history_size_changed(self, value):
        """历史记录大小变更事件处理"""
        self.settings['history_size'] = value
        
        # 发送配置变更信号
        self.config_changed.emit({'history_size': value})
    
    def _on_show_system_changed(self, state):
        """显示系统指标变更事件处理"""
        self.settings['show_system'] = state == Qt.Checked
        
        # 发送配置变更信号
        self.config_changed.emit({'collect_system_metrics': self.settings['show_system']})
    
    def _on_show_process_changed(self, state):
        """显示进程指标变更事件处理"""
        self.settings['show_process'] = state == Qt.Checked
        
        # 发送配置变更信号
        self.config_changed.emit({'collect_process_metrics': self.settings['show_process']})
    
    def _on_auto_refresh_changed(self, state):
        """自动刷新变更事件处理"""
        self.settings['auto_refresh'] = state == Qt.Checked
        
        # 如果自动刷新，启动定时器，否则停止定时器
        if self.settings['auto_refresh']:
            self._timer.start(self.settings['update_interval'])
        else:
            self._timer.stop()
    
    def _on_refresh_clicked(self):
        """刷新按钮点击事件处理"""
        self._update_charts()
    
    def _on_clear_clicked(self):
        """清空按钮点击事件处理"""
        # 清空图表数据
        self.cpu_curve.setData([], [])
        self.memory_curve.setData([], [])
        self.disk_curve.setData([], [])
        self.network_sent_curve.setData([], [])
        self.network_recv_curve.setData([], [])
        
        self.process_cpu_curve.setData([], [])
        self.process_memory_curve.setData([], [])
        self.threads_curve.setData([], [])
        self.io_read_curve.setData([], [])
        self.io_write_curve.setData([], [])
        
        # 清空自定义图表数据
        if hasattr(self, 'custom_charts'):
            for chart_data in self.custom_charts.values():
                chart_data['curve'].setData([], [])
                chart_data['data'] = []
        
        # 发送清空信号
        self.config_changed.emit({'clear_metrics': True})
    
    def _on_export_clicked(self):
        """导出按钮点击事件处理"""
        # 选择保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出性能报告", "", "文本文件 (*.txt)"
        )
        
        if file_path:
            # 发送导出信号
            self.config_changed.emit({'export_report': file_path})
    
    def _update_charts(self):
        """更新图表"""
        # 发送更新信号
        self.config_changed.emit({'update_charts': True})
    
    def update_metrics(self, metrics):
        """更新性能指标
        
        Args:
            metrics: 性能指标
        """
        if not metrics:
            return
        
        # 获取时间戳
        timestamps = metrics.get('timestamp', [])
        if not timestamps:
            return
        
        # 计算相对时间
        relative_times = [t - timestamps[0] for t in timestamps]
        
        # 更新系统指标图表
        if self.settings['show_system']:
            system_metrics = metrics.get('system', {})
            
            # CPU使用率
            cpu_percent = system_metrics.get('cpu_percent', [])
            if cpu_percent:
                # 确保长度相同
                min_len = min(len(relative_times), len(cpu_percent))
                self.cpu_curve.setData(relative_times[:min_len], cpu_percent[:min_len])
            
            # 内存使用率
            memory_percent = system_metrics.get('memory_percent', [])
            if memory_percent:
                # 确保长度相同
                min_len = min(len(relative_times), len(memory_percent))
                self.memory_curve.setData(relative_times[:min_len], memory_percent[:min_len])
            
            # 磁盘使用率
            disk_usage = system_metrics.get('disk_usage', [])
            if disk_usage:
                # 确保长度相同
                min_len = min(len(relative_times), len(disk_usage))
                self.disk_curve.setData(relative_times[:min_len], disk_usage[:min_len])
            
            # 网络使用率
            network_sent = system_metrics.get('network_sent', [])
            network_recv = system_metrics.get('network_recv', [])
            if network_sent and network_recv:
                # 转换为KB/s
                network_sent_kb = [s / 1024 for s in network_sent]
                network_recv_kb = [r / 1024 for r in network_recv]
                
                # 确保长度相同
                min_len = min(len(relative_times), len(network_sent_kb))
                self.network_sent_curve.setData(relative_times[:min_len], network_sent_kb[:min_len])
                
                min_len = min(len(relative_times), len(network_recv_kb))
                self.network_recv_curve.setData(relative_times[:min_len], network_recv_kb[:min_len])
        
        # 更新进程指标图表
        if self.settings['show_process']:
            process_metrics = metrics.get('process', {})
            
            # CPU使用率
            cpu_percent = process_metrics.get('cpu_percent', [])
            if cpu_percent:
                # 确保长度相同
                min_len = min(len(relative_times), len(cpu_percent))
                self.process_cpu_curve.setData(relative_times[:min_len], cpu_percent[:min_len])
            
            # 内存使用率
            memory_percent = process_metrics.get('memory_percent', [])
            if memory_percent:
                # 确保长度相同
                min_len = min(len(relative_times), len(memory_percent))
                self.process_memory_curve.setData(relative_times[:min_len], memory_percent[:min_len])
            
            # 线程数
            threads = process_metrics.get('threads', [])
            if threads:
                # 确保长度相同
                min_len = min(len(relative_times), len(threads))
                self.threads_curve.setData(relative_times[:min_len], threads[:min_len])
            
            # IO
            io_read = process_metrics.get('io_read', [])
            io_write = process_metrics.get('io_write', [])
            if io_read and io_write:
                # 确保长度相同
                min_len = min(len(relative_times), len(io_read))
                self.io_read_curve.setData(relative_times[:min_len], io_read[:min_len])
                
                min_len = min(len(relative_times), len(io_write))
                self.io_write_curve.setData(relative_times[:min_len], io_write[:min_len])
        
        # 更新自定义指标图表
        if hasattr(self, 'custom_charts'):
            custom_metrics = metrics.get('custom', {})
            for name, chart_data in self.custom_charts.items():
                if name in custom_metrics:
                    values = custom_metrics[name]
                    chart_data['data'] = values
                    # 确保长度相同
                    min_len = min(len(relative_times), len(values))
                    chart_data['curve'].setData(relative_times[:min_len], values[:min_len])
    
    def add_custom_metric_value(self, name, value):
        """添加自定义指标值
        
        Args:
            name: 指标名称
            value: 指标值
        """
        # 如果指标不存在，创建图表
        if not hasattr(self, 'custom_charts') or name not in self.custom_charts:
            self._create_custom_chart(name)
        
        # 添加值
        self.custom_charts[name]['data'].append(value)
        
        # 限制历史记录大小
        if len(self.custom_charts[name]['data']) > self.settings['history_size']:
            self.custom_charts[name]['data'] = self.custom_charts[name]['data'][-self.settings['history_size']:]
        
        # 更新图表
        self.custom_charts[name]['curve'].setData(
            list(range(len(self.custom_charts[name]['data']))),
            self.custom_charts[name]['data']
        ) 