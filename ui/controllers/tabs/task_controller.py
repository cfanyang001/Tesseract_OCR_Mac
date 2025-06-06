from PyQt5.QtCore import QObject, pyqtSlot, Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QInputDialog, QProgressBar, QLabel
from PyQt5.QtGui import QColor

from ui.components.tabs.task_tab import TaskTab
from core.task_manager import TaskManager, TaskInfo
from core.monitor_engine import MonitorEngine
from loguru import logger


class TaskController(QObject):
    """任务管理标签页控制器，负责连接任务管理标签页与任务管理器"""
    
    # 定义信号
    log_message = pyqtSignal(str)  # 日志消息信号
    task_executed = pyqtSignal(str, float)  # 任务执行信号 (任务ID, 执行时间)
    
    def __init__(self, task_tab: TaskTab, task_manager: TaskManager = None, 
                 monitor_engine: MonitorEngine = None):
        """初始化任务控制器
        
        Args:
            task_tab: 任务标签页
            task_manager: 任务管理器
            monitor_engine: 监控引擎
        """
        super().__init__()
        
        self.task_tab = task_tab
        self.task_manager = task_manager
        self.monitor_engine = monitor_engine
        
        # 将控制器实例保存到标签页中，以便配置控制器能够访问它
        self.task_tab.controller = self
        
        # 当前选中的任务ID
        self.current_task_id = None
        
        # 任务表格中的任务ID映射
        self.task_row_map = {}  # {task_id: row_index}
        
        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.setInterval(1000)  # 每秒更新一次
        self.update_timer.timeout.connect(self.update_task_list)
        self.update_timer.start()
        
        # 连接信号
        self.connect_signals()
        
        # 初始化UI
        self.init_ui()
        
        logger.info("任务控制器初始化完成")
    
    def set_task_manager(self, task_manager: TaskManager):
        """设置任务管理器"""
        self.task_manager = task_manager
        
        # 连接任务管理器信号
        if task_manager:
            task_manager.task_added.connect(self.on_task_added)
            task_manager.task_started.connect(self.on_task_started)
            task_manager.task_completed.connect(self.on_task_completed)
            task_manager.task_failed.connect(self.on_task_failed)
            task_manager.task_stopped.connect(self.on_task_stopped)
            task_manager.task_progress.connect(self.on_task_progress)
            task_manager.task_removed.connect(self.on_task_removed)
            
            # 更新任务列表
            self.update_task_list()
    
    def set_monitor_engine(self, monitor_engine: MonitorEngine):
        """设置监控引擎"""
        self.monitor_engine = monitor_engine
        
        # 更新区域下拉框
        self.update_area_combo()
        
        # 更新规则下拉框
        self.update_rule_combo()
    
    def connect_signals(self):
        """连接信号"""
        # 任务表格选择变化
        self.task_tab.task_table.itemSelectionChanged.connect(self.on_task_selection_changed)
        
        # 控制按钮
        new_task_btn = self.task_tab.findChild(QObject, "new_task_btn")
        if new_task_btn:
            new_task_btn.clicked.connect(self.on_new_task)
        
        start_task_btn = self.task_tab.findChild(QObject, "start_task_btn")
        if start_task_btn:
            start_task_btn.clicked.connect(self.on_start_task)
        
        pause_task_btn = self.task_tab.findChild(QObject, "pause_task_btn")
        if pause_task_btn:
            pause_task_btn.clicked.connect(self.on_pause_task)
        
        stop_task_btn = self.task_tab.findChild(QObject, "stop_task_btn")
        if stop_task_btn:
            stop_task_btn.clicked.connect(self.on_stop_task)
        
        delete_task_btn = self.task_tab.findChild(QObject, "delete_task_btn")
        if delete_task_btn:
            delete_task_btn.clicked.connect(self.on_delete_task)
    
    def init_ui(self):
        """初始化UI"""
        # 设置任务表格属性
        self.task_tab.task_table.setObjectName("task_table")
        
        # 设置任务详情控件的对象名
        self.task_tab.findChild(QObject, "name_edit").setObjectName("name_edit")
        self.task_tab.findChild(QObject, "status_combo").setObjectName("status_combo")
        self.task_tab.findChild(QObject, "area_combo").setObjectName("area_combo")
        self.task_tab.findChild(QObject, "rule_combo").setObjectName("rule_combo")
        self.task_tab.findChild(QObject, "refresh_spin").setObjectName("refresh_spin")
        self.task_tab.findChild(QObject, "restart_check").setObjectName("restart_check")
        self.task_tab.findChild(QObject, "progress_bar").setObjectName("progress_bar")
        
        # 设置控制按钮对象名
        self.task_tab.findChild(QObject, "new_task_btn").setObjectName("new_task_btn")
        self.task_tab.findChild(QObject, "start_task_btn").setObjectName("start_task_btn")
        self.task_tab.findChild(QObject, "pause_task_btn").setObjectName("pause_task_btn")
        self.task_tab.findChild(QObject, "stop_task_btn").setObjectName("stop_task_btn")
        self.task_tab.findChild(QObject, "delete_task_btn").setObjectName("delete_task_btn")
        
        # 更新区域下拉框
        self.update_area_combo()
        
        # 更新规则下拉框
        self.update_rule_combo()
    
    def update_task_list(self):
        """更新任务列表"""
        if not self.task_manager:
            return
        
        # 获取所有任务
        tasks = self.task_manager.get_all_tasks()
        
        # 获取当前选中的任务ID
        selected_task_id = self.current_task_id
        
        # 清空任务行映射
        self.task_row_map.clear()
        
        # 设置表格行数
        self.task_tab.task_table.setRowCount(len(tasks))
        
        # 如果没有任务，直接返回
        if not tasks:
            return
        
        # 填充表格
        for row, (task_id, task_info) in enumerate(tasks.items()):
            # 保存任务ID与行的映射
            self.task_row_map[task_id] = row
            
            # 任务名称
            name_item = QTableWidgetItem(task_info.name)
            name_item.setData(Qt.UserRole, task_id)
            self.task_tab.task_table.setItem(row, 0, name_item)
            
            # 任务状态
            status_item = QTableWidgetItem(self.get_status_text(task_info.status))
            status_item.setForeground(self.get_status_color(task_info.status))
            self.task_tab.task_table.setItem(row, 1, status_item)
            
            # 监控区域
            area_id = task_info.metadata.get('area_id', '')
            area_name = "未设置"
            if self.monitor_engine and area_id:
                area = self.monitor_engine.get_area(area_id)
                if area:
                    area_name = area.name
            self.task_tab.task_table.setItem(row, 2, QTableWidgetItem(area_name))
            
            # 监控规则
            rule_id = task_info.metadata.get('rule_id', '')
            rule_name = "未设置"
            if self.monitor_engine and hasattr(self.monitor_engine, 'rule_matcher') and rule_id:
                # 获取规则名称
                rule = self.monitor_engine.rule_matcher.get_rule(rule_id)
                if rule:
                    rule_name = rule.name
                else:
                    rule_name = f"规则 {rule_id[:8]}"
            self.task_tab.task_table.setItem(row, 3, QTableWidgetItem(rule_name))
            
            # 上次触发时间
            last_time = "从未"
            if task_info.last_run_time:
                last_time = task_info.last_run_time.strftime("%Y-%m-%d %H:%M:%S")
            self.task_tab.task_table.setItem(row, 4, QTableWidgetItem(last_time))
        
        # 如果之前有选中的任务，尝试重新选中
        if selected_task_id and selected_task_id in self.task_row_map:
            row = self.task_row_map[selected_task_id]
            self.task_tab.task_table.selectRow(row)
        elif self.task_tab.task_table.rowCount() > 0:
            # 否则选中第一行
            self.task_tab.task_table.selectRow(0)
    
    def update_task_detail(self, task_id: str):
        """更新任务详情"""
        if not self.task_manager or not task_id:
            return
        
        task_info = self.task_manager.get_task(task_id)
        if not task_info:
            return
        
        # 更新任务名称
        name_edit = self.task_tab.findChild(QObject, "name_edit")
        if name_edit:
            name_edit.setText(task_info.name)
        
        # 更新任务状态
        status_combo = self.task_tab.findChild(QObject, "status_combo")
        if status_combo:
            status_index = {
                TaskInfo.STATUS_PENDING: 1,
                TaskInfo.STATUS_RUNNING: 0,
                TaskInfo.STATUS_COMPLETED: 3,
                TaskInfo.STATUS_FAILED: 4,
                TaskInfo.STATUS_STOPPED: 2
            }.get(task_info.status, 0)
            status_combo.setCurrentIndex(status_index)
        
        # 更新区域选择
        area_combo = self.task_tab.findChild(QObject, "area_combo")
        if area_combo:
            area_id = task_info.metadata.get('area_id', '')
            index = area_combo.findData(area_id)
            if index >= 0:
                area_combo.setCurrentIndex(index)
        
        # 更新规则选择
        rule_combo = self.task_tab.findChild(QObject, "rule_combo")
        if rule_combo:
            rule_id = task_info.metadata.get('rule_id', '')
            index = rule_combo.findData(rule_id)
            if index >= 0:
                rule_combo.setCurrentIndex(index)
        
        # 更新刷新频率
        refresh_spin = self.task_tab.findChild(QObject, "refresh_spin")
        if refresh_spin:
            refresh_rate = task_info.config.get('refresh_rate', 1000)
            # 转换为秒
            refresh_spin.setValue(refresh_rate // 1000)
        
        # 更新自动重启
        restart_check = self.task_tab.findChild(QObject, "restart_check")
        if restart_check:
            restart_check.setChecked(task_info.config.get('auto_restart', False))
        
        # 更新进度条
        progress_bar = self.task_tab.findChild(QObject, "progress_bar")
        if progress_bar:
            progress_value = int(task_info.progress * 100)
            progress_bar.setValue(progress_value)
    
    def update_area_combo(self):
        """更新监控区域下拉框"""
        area_combo = self.task_tab.findChild(QObject, "area_combo")
        if not area_combo:
            return
        
        # 保存当前选择的项
        current_text = area_combo.currentText()
        
        # 清空下拉框
        area_combo.clear()
        
        # 如果没有监控引擎，添加一个默认项
        if not self.monitor_engine:
            area_combo.addItem("未设置")
            return
        
        # 添加所有区域
        areas = self.monitor_engine.get_all_areas()
        for area_id, area in areas.items():
            area_combo.addItem(area.name, area_id)
        
        # 添加一个"新建区域"选项
        area_combo.addItem("新建区域...", "new")
        
        # 恢复之前的选择
        index = area_combo.findText(current_text)
        if index >= 0:
            area_combo.setCurrentIndex(index)
    
    def update_rule_combo(self):
        """更新监控规则下拉框"""
        rule_combo = self.task_tab.findChild(QObject, "rule_combo")
        if not rule_combo:
            return
        
        # 保存当前选择的项
        current_text = rule_combo.currentText()
        
        # 清空下拉框
        rule_combo.clear()
        
        # 如果没有监控引擎，添加一个默认项
        if not self.monitor_engine or not hasattr(self.monitor_engine, 'rule_matcher'):
            rule_combo.addItem("未设置")
            return
        
        # 添加所有规则
        rules = self.monitor_engine.rule_matcher.get_all_rules()
        for rule_id, rule in rules.items():
            rule_combo.addItem(rule.name, rule_id)
        
        # 添加一个"新建规则"选项
        rule_combo.addItem("新建规则...", "new")
        
        # 恢复之前的选择
        index = rule_combo.findText(current_text)
        if index >= 0:
            rule_combo.setCurrentIndex(index)
    
    def get_status_text(self, status: str) -> str:
        """获取状态文本"""
        return {
            TaskInfo.STATUS_PENDING: "等待中",
            TaskInfo.STATUS_RUNNING: "运行中",
            TaskInfo.STATUS_COMPLETED: "已完成",
            TaskInfo.STATUS_FAILED: "失败",
            TaskInfo.STATUS_STOPPED: "已停止"
        }.get(status, "未知")
    
    def get_status_color(self, status: str) -> QColor:
        """获取状态颜色"""
        return {
            TaskInfo.STATUS_PENDING: QColor(0, 0, 255),    # 蓝色
            TaskInfo.STATUS_RUNNING: QColor(0, 128, 0),    # 绿色
            TaskInfo.STATUS_COMPLETED: QColor(0, 0, 0),    # 黑色
            TaskInfo.STATUS_FAILED: QColor(255, 0, 0),     # 红色
            TaskInfo.STATUS_STOPPED: QColor(128, 128, 128) # 灰色
        }.get(status, QColor(0, 0, 0))
    
    @pyqtSlot()
    def on_task_selection_changed(self):
        """任务选择变化回调"""
        selected_items = self.task_tab.task_table.selectedItems()
        if not selected_items:
            return
        
        # 获取选中行的第一个单元格
        item = self.task_tab.task_table.item(selected_items[0].row(), 0)
        if not item:
            return
        
        # 获取任务ID
        task_id = item.data(Qt.UserRole)
        if not task_id:
            return
        
        # 更新当前选中的任务ID
        self.current_task_id = task_id
        
        # 更新任务详情
        self.update_task_detail(task_id)
    
    @pyqtSlot()
    def on_new_task(self):
        """新建任务回调"""
        if not self.task_manager:
            QMessageBox.warning(self.task_tab, "警告", "任务管理器未初始化")
            return
        
        # 获取任务名称
        name, ok = QInputDialog.getText(self.task_tab, "新建任务", "请输入任务名称:")
        if not ok or not name:
            return
        
        # 创建任务
        task_id = self.task_manager.add_task(
            task_id=None,
            name=name,
            description="通过UI创建的任务",
            task_func=self.dummy_task_func,  # 使用一个空任务函数
            auto_start=False
        )
        
        # 更新任务列表
        self.update_task_list()
        
        # 选中新创建的任务
        if task_id in self.task_row_map:
            row = self.task_row_map[task_id]
            self.task_tab.task_table.selectRow(row)
    
    @pyqtSlot()
    def on_start_task(self):
        """开始任务回调"""
        if not self.task_manager or not self.current_task_id:
            return
        
        # 启动任务
        self.task_manager.start_task(self.current_task_id)
        
        # 更新任务列表
        self.update_task_list()
    
    @pyqtSlot()
    def on_pause_task(self):
        """暂停任务回调"""
        if not self.task_manager or not self.current_task_id:
            return
        
        # 目前没有实现暂停功能，可以扩展
        QMessageBox.information(self.task_tab, "提示", "暂停功能尚未实现")
    
    @pyqtSlot()
    def on_stop_task(self):
        """停止任务回调"""
        if not self.task_manager or not self.current_task_id:
            return
        
        # 停止任务
        self.task_manager.stop_task(self.current_task_id)
        
        # 更新任务列表
        self.update_task_list()
    
    @pyqtSlot()
    def on_delete_task(self):
        """删除任务回调"""
        if not self.task_manager or not self.current_task_id:
            return
        
        # 确认删除
        reply = QMessageBox.question(
            self.task_tab,
            "确认删除",
            f"确定要删除任务 '{self.task_manager.get_task(self.current_task_id).name}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 删除任务
        self.task_manager.remove_task(self.current_task_id)
        
        # 清除当前选中的任务ID
        self.current_task_id = None
        
        # 更新任务列表
        self.update_task_list()
    
    @pyqtSlot(str)
    def on_task_added(self, task_id: str):
        """任务添加回调"""
        self.update_task_list()
    
    @pyqtSlot(str)
    def on_task_started(self, task_id: str):
        """任务开始回调"""
        self.update_task_list()
        if task_id == self.current_task_id:
            self.update_task_detail(task_id)
    
    @pyqtSlot(str, object)
    def on_task_completed(self, task_id: str, result: object):
        """任务完成回调"""
        self.update_task_list()
        if task_id == self.current_task_id:
            self.update_task_detail(task_id)
    
    @pyqtSlot(str, str)
    def on_task_failed(self, task_id: str, error: str):
        """任务失败回调"""
        self.update_task_list()
        if task_id == self.current_task_id:
            self.update_task_detail(task_id)
    
    @pyqtSlot(str)
    def on_task_stopped(self, task_id: str):
        """任务停止回调"""
        self.update_task_list()
        if task_id == self.current_task_id:
            self.update_task_detail(task_id)
    
    @pyqtSlot(str, float, str)
    def on_task_progress(self, task_id: str, progress: float, message: str):
        """任务进度回调"""
        # 更新任务进度条
        if task_id == self.current_task_id:
            progress_bar = self.task_tab.findChild(QObject, "progress_bar")
            if progress_bar:
                progress_value = int(progress * 100)
                progress_bar.setValue(progress_value)
    
    @pyqtSlot(str)
    def on_task_removed(self, task_id: str):
        """任务移除回调"""
        self.update_task_list()
    
    def dummy_task_func(self, check_stop=None, update_progress=None):
        """空任务函数，用于测试"""
        import time
        
        # 模拟一些进度更新
        if update_progress:
            for i in range(10):
                if check_stop and check_stop():
                    return "Task stopped"
                update_progress(i / 10, f"进度 {i+1}/10")
                time.sleep(0.5)
        
        return "Task completed"
