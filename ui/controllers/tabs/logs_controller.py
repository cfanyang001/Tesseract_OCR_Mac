from PyQt5.QtCore import QObject, pyqtSlot, Qt, QTimer, QDateTime
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QFileDialog
from PyQt5.QtGui import QColor
import csv
import json
from datetime import datetime, timedelta
import os

from ui.components.tabs.logs_tab import LogsTab
from ui.models.log_model import LogModel, LogEntry
from loguru import logger


class LogsController(QObject):
    """日志标签页控制器，负责连接日志标签页与日志模型"""
    
    def __init__(self, logs_tab: LogsTab, log_model: LogModel = None):
        """初始化日志控制器
        
        Args:
            logs_tab: 日志标签页
            log_model: 日志模型
        """
        super().__init__()
        
        self.logs_tab = logs_tab
        self.log_model = log_model or LogModel()
        
        # 将控制器实例保存到标签页中，以便其他控制器能够访问它
        self.logs_tab.controller = self
        
        # 当前选中的日志ID
        self.current_log_id = None
        
        # 自动刷新定时器
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(2000)  # 每2秒刷新一次
        self.refresh_timer.timeout.connect(self.refresh_logs)
        
        # 连接信号
        self.connect_signals()
        
        # 初始化UI
        self.init_ui()
        
        # 启动自动刷新
        self.refresh_timer.start()
        
        logger.info("日志控制器初始化完成")
    
    def connect_signals(self):
        """连接信号"""
        # 日志表格选择变化
        self.logs_tab.logs_table.itemSelectionChanged.connect(self.on_log_selection_changed)
        
        # 搜索按钮
        search_btn = self.logs_tab.filter_group.findChild(QObject, "search_btn")
        if search_btn:
            search_btn.clicked.connect(self.on_search)
        
        # 重置按钮
        reset_btn = self.logs_tab.filter_group.findChild(QObject, "reset_btn")
        if reset_btn:
            reset_btn.clicked.connect(self.on_reset)
        
        # 自动刷新复选框
        auto_refresh = self.logs_tab.control_group.findChild(QObject, "auto_refresh")
        if auto_refresh:
            auto_refresh.stateChanged.connect(self.on_auto_refresh_changed)
        
        # 刷新按钮
        refresh_btn = self.logs_tab.control_group.findChild(QObject, "refresh_btn")
        if refresh_btn:
            refresh_btn.clicked.connect(self.refresh_logs)
        
        # 清空按钮
        clear_btn = self.logs_tab.control_group.findChild(QObject, "clear_btn")
        if clear_btn:
            clear_btn.clicked.connect(self.on_clear_logs)
        
        # 导出按钮
        export_btn = self.logs_tab.control_group.findChild(QObject, "export_btn")
        if export_btn:
            export_btn.clicked.connect(self.on_export_logs)
    
    def init_ui(self):
        """初始化UI"""
        # 设置控件对象名
        # 筛选面板
        level_combo = self.logs_tab.filter_group.findChild(QObject, "level_combo")
        if level_combo:
            level_combo.setObjectName("level_combo")
        
        source_combo = self.logs_tab.filter_group.findChild(QObject, "source_combo")
        if source_combo:
            source_combo.setObjectName("source_combo")
        
        start_time = self.logs_tab.filter_group.findChild(QObject, "start_time")
        if start_time:
            start_time.setObjectName("start_time")
        
        end_time = self.logs_tab.filter_group.findChild(QObject, "end_time")
        if end_time:
            end_time.setObjectName("end_time")
        
        search_edit = self.logs_tab.filter_group.findChild(QObject, "search_edit")
        if search_edit:
            search_edit.setObjectName("search_edit")
        
        search_btn = self.logs_tab.filter_group.findChild(QObject, "search_btn")
        if search_btn:
            search_btn.setObjectName("search_btn")
        
        reset_btn = self.logs_tab.filter_group.findChild(QObject, "reset_btn")
        if reset_btn:
            reset_btn.setObjectName("reset_btn")
        
        # 控制面板
        auto_scroll = self.logs_tab.control_group.findChild(QObject, "auto_scroll")
        if auto_scroll:
            auto_scroll.setObjectName("auto_scroll")
        
        auto_refresh = self.logs_tab.control_group.findChild(QObject, "auto_refresh")
        if auto_refresh:
            auto_refresh.setObjectName("auto_refresh")
        
        refresh_btn = self.logs_tab.control_group.findChild(QObject, "refresh_btn")
        if refresh_btn:
            refresh_btn.setObjectName("refresh_btn")
        
        clear_btn = self.logs_tab.control_group.findChild(QObject, "clear_btn")
        if clear_btn:
            clear_btn.setObjectName("clear_btn")
        
        export_btn = self.logs_tab.control_group.findChild(QObject, "export_btn")
        if export_btn:
            export_btn.setObjectName("export_btn")
        
        # 初始化日志表格
        self.refresh_logs()
    
    def refresh_logs(self):
        """刷新日志列表"""
        if not self.log_model:
            return
        
        # 获取筛选条件
        level = self.get_selected_level()
        source = self.get_selected_source()
        start_time = self.get_start_time()
        end_time = self.get_end_time()
        search_text = self.get_search_text()
        
        # 获取过滤后的日志
        logs = self.log_model.get_filtered_logs(
            level=level,
            source=source,
            start_time=start_time,
            end_time=end_time,
            search_text=search_text
        )
        
        # 获取当前选中的日志ID
        selected_log_id = self.current_log_id
        
        # 清空表格
        self.logs_tab.logs_table.setRowCount(0)
        
        # 填充表格
        for row, log in enumerate(logs):
            self.logs_tab.logs_table.insertRow(row)
            
            # 时间
            time_item = QTableWidgetItem(log.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            time_item.setData(Qt.UserRole, log.id)
            self.logs_tab.logs_table.setItem(row, 0, time_item)
            
            # 级别
            level_item = QTableWidgetItem(self.get_level_text(log.level))
            level_item.setForeground(self.get_level_color(log.level))
            self.logs_tab.logs_table.setItem(row, 1, level_item)
            
            # 来源
            source_item = QTableWidgetItem(self.get_source_text(log.source))
            self.logs_tab.logs_table.setItem(row, 2, source_item)
            
            # 消息
            message_item = QTableWidgetItem(log.message)
            self.logs_tab.logs_table.setItem(row, 3, message_item)
            
            # 详情
            details_item = QTableWidgetItem("查看" if log.details else "")
            self.logs_tab.logs_table.setItem(row, 4, details_item)
        
        # 如果启用了自动滚动，滚动到最后一行
        auto_scroll = self.logs_tab.control_group.findChild(QObject, "auto_scroll")
        if auto_scroll and auto_scroll.isChecked() and self.logs_tab.logs_table.rowCount() > 0:
            self.logs_tab.logs_table.scrollToBottom()
        
        # 如果之前有选中的日志，尝试重新选中
        if selected_log_id:
            for row in range(self.logs_tab.logs_table.rowCount()):
                item = self.logs_tab.logs_table.item(row, 0)
                if item and item.data(Qt.UserRole) == selected_log_id:
                    self.logs_tab.logs_table.selectRow(row)
                    break
    
    def get_selected_level(self) -> str:
        """获取选中的日志级别"""
        level_combo = self.logs_tab.filter_group.findChild(QObject, "level_combo")
        if not level_combo:
            return None
        
        level_text = level_combo.currentText()
        if level_text == "全部":
            return None
        
        level_map = {
            "调试": LogEntry.LEVEL_DEBUG,
            "信息": LogEntry.LEVEL_INFO,
            "警告": LogEntry.LEVEL_WARNING,
            "错误": LogEntry.LEVEL_ERROR,
            "严重": LogEntry.LEVEL_CRITICAL
        }
        
        return level_map.get(level_text)
    
    def get_selected_source(self) -> str:
        """获取选中的日志来源"""
        source_combo = self.logs_tab.filter_group.findChild(QObject, "source_combo")
        if not source_combo:
            return None
        
        source_text = source_combo.currentText()
        if source_text == "全部":
            return None
        
        source_map = {
            "OCR": LogEntry.SOURCE_OCR,
            "监控": LogEntry.SOURCE_MONITOR,
            "任务": LogEntry.SOURCE_TASK,
            "动作": LogEntry.SOURCE_ACTION,
            "系统": LogEntry.SOURCE_SYSTEM
        }
        
        return source_map.get(source_text)
    
    def get_start_time(self) -> datetime:
        """获取开始时间"""
        start_time = self.logs_tab.filter_group.findChild(QObject, "start_time")
        if not start_time:
            return None
        
        return start_time.dateTime().toPyDateTime()
    
    def get_end_time(self) -> datetime:
        """获取结束时间"""
        end_time = self.logs_tab.filter_group.findChild(QObject, "end_time")
        if not end_time:
            return None
        
        return end_time.dateTime().toPyDateTime()
    
    def get_search_text(self) -> str:
        """获取搜索文本"""
        search_edit = self.logs_tab.filter_group.findChild(QObject, "search_edit")
        if not search_edit:
            return None
        
        text = search_edit.text().strip()
        return text if text else None
    
    def get_level_text(self, level: str) -> str:
        """获取日志级别文本"""
        level_map = {
            LogEntry.LEVEL_DEBUG: "调试",
            LogEntry.LEVEL_INFO: "信息",
            LogEntry.LEVEL_WARNING: "警告",
            LogEntry.LEVEL_ERROR: "错误",
            LogEntry.LEVEL_CRITICAL: "严重"
        }
        
        return level_map.get(level, "未知")
    
    def get_level_color(self, level: str) -> QColor:
        """获取日志级别颜色"""
        level_color = {
            LogEntry.LEVEL_DEBUG: QColor(128, 128, 128),  # 灰色
            LogEntry.LEVEL_INFO: QColor(0, 0, 0),         # 黑色
            LogEntry.LEVEL_WARNING: QColor(255, 165, 0),  # 橙色
            LogEntry.LEVEL_ERROR: QColor(255, 0, 0),      # 红色
            LogEntry.LEVEL_CRITICAL: QColor(139, 0, 0)    # 深红色
        }
        
        return level_color.get(level, QColor(0, 0, 0))
    
    def get_source_text(self, source: str) -> str:
        """获取日志来源文本"""
        source_map = {
            LogEntry.SOURCE_OCR: "OCR",
            LogEntry.SOURCE_MONITOR: "监控",
            LogEntry.SOURCE_TASK: "任务",
            LogEntry.SOURCE_ACTION: "动作",
            LogEntry.SOURCE_SYSTEM: "系统"
        }
        
        return source_map.get(source, "未知")
    
    @pyqtSlot()
    def on_log_selection_changed(self):
        """日志选择变化回调"""
        selected_items = self.logs_tab.logs_table.selectedItems()
        if not selected_items:
            return
        
        # 获取选中行的第一个单元格
        item = self.logs_tab.logs_table.item(selected_items[0].row(), 0)
        if not item:
            return
        
        # 获取日志ID
        log_id = item.data(Qt.UserRole)
        if not log_id:
            return
        
        # 更新当前选中的日志ID
        self.current_log_id = log_id
        
        # 显示日志详情
        self.show_log_details(log_id)
    
    def show_log_details(self, log_id: str):
        """显示日志详情"""
        if not self.log_model:
            return
        
        # 获取所有日志
        logs = self.log_model.get_logs()
        
        # 查找指定ID的日志
        log = next((log for log in logs if log.id == log_id), None)
        if not log:
            return
        
        # 显示日志详情
        detail_text = f"时间: {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        detail_text += f"级别: {self.get_level_text(log.level)}\n"
        detail_text += f"来源: {self.get_source_text(log.source)}\n"
        detail_text += f"消息: {log.message}\n"
        if log.details:
            detail_text += f"\n详细信息:\n{log.details}"
        
        self.logs_tab.detail_text.setText(detail_text)
    
    @pyqtSlot()
    def on_search(self):
        """搜索按钮回调"""
        self.refresh_logs()
    
    @pyqtSlot()
    def on_reset(self):
        """重置按钮回调"""
        # 重置筛选条件
        level_combo = self.logs_tab.filter_group.findChild(QObject, "level_combo")
        if level_combo:
            level_combo.setCurrentIndex(0)
        
        source_combo = self.logs_tab.filter_group.findChild(QObject, "source_combo")
        if source_combo:
            source_combo.setCurrentIndex(0)
        
        start_time = self.logs_tab.filter_group.findChild(QObject, "start_time")
        if start_time:
            start_time.setDateTime(QDateTime.currentDateTime().addDays(-1))
        
        end_time = self.logs_tab.filter_group.findChild(QObject, "end_time")
        if end_time:
            end_time.setDateTime(QDateTime.currentDateTime())
        
        search_edit = self.logs_tab.filter_group.findChild(QObject, "search_edit")
        if search_edit:
            search_edit.clear()
        
        # 刷新日志
        self.refresh_logs()
    
    @pyqtSlot(int)
    def on_auto_refresh_changed(self, state: int):
        """自动刷新状态变化回调"""
        if state == Qt.Checked:
            self.refresh_timer.start()
        else:
            self.refresh_timer.stop()
    
    @pyqtSlot()
    def on_clear_logs(self):
        """清空日志按钮回调"""
        if not self.log_model:
            return
        
        # 确认清空
        reply = QMessageBox.question(
            self.logs_tab,
            "确认清空",
            "确定要清空所有日志吗？此操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 清空日志
        self.log_model.clear_logs()
        
        # 刷新日志表格
        self.refresh_logs()
        
        # 清空详情
        self.logs_tab.detail_text.clear()
        
        # 清除当前选中的日志ID
        self.current_log_id = None
    
    @pyqtSlot()
    def on_export_logs(self):
        """导出日志按钮回调"""
        if not self.log_model:
            return
        
        # 获取过滤后的日志
        level = self.get_selected_level()
        source = self.get_selected_source()
        start_time = self.get_start_time()
        end_time = self.get_end_time()
        search_text = self.get_search_text()
        
        logs = self.log_model.get_filtered_logs(
            level=level,
            source=source,
            start_time=start_time,
            end_time=end_time,
            search_text=search_text
        )
        
        if not logs:
            QMessageBox.information(self.logs_tab, "导出日志", "没有符合条件的日志可导出")
            return
        
        # 选择导出格式
        formats = ["CSV (*.csv)", "JSON (*.json)", "文本 (*.txt)"]
        format_str, _ = QFileDialog.getSaveFileName(
            self.logs_tab,
            "导出日志",
            f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            ";;".join(formats)
        )
        
        if not format_str:
            return
        
        try:
            # 根据格式导出
            if format_str.endswith(".csv"):
                self.export_to_csv(format_str, logs)
            elif format_str.endswith(".json"):
                self.export_to_json(format_str, logs)
            elif format_str.endswith(".txt"):
                self.export_to_text(format_str, logs)
            
            QMessageBox.information(self.logs_tab, "导出日志", f"日志已成功导出到: {format_str}")
        except Exception as e:
            QMessageBox.critical(self.logs_tab, "导出失败", f"导出日志时发生错误: {e}")
            logger.error(f"导出日志失败: {e}")
    
    def export_to_csv(self, filename: str, logs: list):
        """导出为CSV格式"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 写入表头
            writer.writerow(['时间', '级别', '来源', '消息', '详情'])
            # 写入数据
            for log in logs:
                writer.writerow([
                    log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    self.get_level_text(log.level),
                    self.get_source_text(log.source),
                    log.message,
                    log.details
                ])
    
    def export_to_json(self, filename: str, logs: list):
        """导出为JSON格式"""
        data = [log.to_dict() for log in logs]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def export_to_text(self, filename: str, logs: list):
        """导出为文本格式"""
        with open(filename, 'w', encoding='utf-8') as f:
            for log in logs:
                f.write(f"[{log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] ")
                f.write(f"[{self.get_level_text(log.level)}] ")
                f.write(f"[{self.get_source_text(log.source)}] ")
                f.write(f"{log.message}\n")
                if log.details:
                    f.write(f"详情: {log.details}\n")
                f.write("\n")
