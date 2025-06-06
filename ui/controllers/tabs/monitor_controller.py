from PyQt5.QtCore import QObject, pyqtSlot, Qt, QTimer, QPoint, QEvent
from PyQt5.QtWidgets import (
    QMessageBox, QPushButton, QLabel, QComboBox, QLineEdit, QCheckBox, 
    QTableWidgetItem, QTableWidget, QSpinBox, QDialog, QVBoxLayout, QHBoxLayout, QApplication
)
from loguru import logger
import re

from core.rule_matcher import Rule


class MonitorController(QObject):
    """监控标签页控制器，负责连接监控标签页与OCR控制器"""
    
    def __init__(self, monitor_tab):
        super().__init__()
        
        self.monitor_tab = monitor_tab
        
        # 将控制器实例保存到标签页中
        self.monitor_tab.controller = self
        
        # 监控状态
        self.is_monitoring = False
        
        # 添加开始/停止监控按钮
        self.add_monitor_control_button()
        
        # 连接信号
        self.connect_signals()
        
        # 加载保存的配置
        QTimer.singleShot(100, self.load_monitor_tab_config)
        
        logger.info("监控控制器初始化成功")
    
    def add_monitor_control_button(self):
        """添加开始/停止监控按钮"""
        # 创建状态标签和控制按钮
        status_layout = self.monitor_tab.layout.itemAt(0).widget().layout()
        
        # 添加状态标签
        self.status_label = QLabel("监控状态: 未启动")
        status_layout.addWidget(self.status_label)
        
        # 添加弹性空间
        status_layout.addStretch()
        
        # 添加控制按钮
        self.monitor_button = QPushButton("开始监控")
        self.monitor_button.setMinimumHeight(25)
        self.monitor_button.setFixedWidth(100)
        self.monitor_button.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 4px;")
        status_layout.addWidget(self.monitor_button)
    
    def connect_signals(self):
        """连接信号"""
        if hasattr(self, 'monitor_button'):
            self.monitor_button.clicked.connect(self.toggle_monitoring)
        
        # 连接监控配置控件的信号
        if hasattr(self.monitor_tab, 'interval_combo'):
            self.monitor_tab.interval_combo.currentTextChanged.connect(self.on_monitor_config_changed)
            
        if hasattr(self.monitor_tab, 'match_mode_combo'):
            self.monitor_tab.match_mode_combo.currentTextChanged.connect(self.on_monitor_config_changed)
        
        # 连接添加规则按钮
        rule_group = self.monitor_tab.rule_group
        add_rule_btn = rule_group.findChild(QPushButton, "add_rule_btn")
        if add_rule_btn:
            add_rule_btn.clicked.connect(self.on_add_rule)
        else:
            # 如果没有找到按钮，尝试查找所有按钮
            buttons = rule_group.findChildren(QPushButton)
            for btn in buttons:
                if btn.text() == "添加规则":
                    btn.setObjectName("add_rule_btn")
                    btn.clicked.connect(self.on_add_rule)
                    logger.info("已连接添加规则按钮")
                    break
        
        # 连接规则组合下拉框变化事件
        rule_list_group = self.monitor_tab.rule_list_group
        combination_combo = rule_list_group.findChild(QComboBox, "combination_combo")
        if combination_combo:
            combination_combo.currentTextChanged.connect(self.on_rule_combination_changed)
        
        # 连接自定义表达式变化事件
        custom_expr_edit = rule_list_group.findChild(QLineEdit, "custom_expr_edit")
        if custom_expr_edit:
            custom_expr_edit.textChanged.connect(self.on_custom_expression_changed)
        
        # 连接添加动作按钮
        action_group = self.monitor_tab.action_group
        add_action_btn = action_group.findChild(QPushButton, "add_action_btn")
        if add_action_btn:
            add_action_btn.clicked.connect(self.on_add_action)
        
        # 连接动作类型变化事件
        action_combo = action_group.findChild(QComboBox, "action_combo")
        if action_combo:
            action_combo.currentTextChanged.connect(self.on_action_type_changed)
        
        # 连接选择坐标按钮点击事件
        if hasattr(self.monitor_tab, 'select_mouse_pos_btn'):
            self.monitor_tab.select_mouse_pos_btn.clicked.connect(self.on_select_mouse_pos)
        
        # 连接动作相关控件变化事件
        trigger_combo = action_group.findChild(QComboBox, "trigger_combo")
        if trigger_combo:
            trigger_combo.currentTextChanged.connect(self.on_monitor_config_changed)
            
        delay_spin = action_group.findChild(QSpinBox, "delay_spin")
        if delay_spin:
            delay_spin.valueChanged.connect(self.on_monitor_config_changed)
            
        # 连接鼠标点击设置控件变化事件
        if hasattr(self.monitor_tab, 'mouse_x_spin'):
            self.monitor_tab.mouse_x_spin.valueChanged.connect(self.on_mouse_settings_changed)
            
        if hasattr(self.monitor_tab, 'mouse_y_spin'):
            self.monitor_tab.mouse_y_spin.valueChanged.connect(self.on_mouse_settings_changed)
            
        if hasattr(self.monitor_tab, 'click_count_spin'):
            self.monitor_tab.click_count_spin.valueChanged.connect(self.on_mouse_settings_changed)
            
        if hasattr(self.monitor_tab, 'click_interval_spin'):
            self.monitor_tab.click_interval_spin.valueChanged.connect(self.on_mouse_settings_changed)
            
        if hasattr(self.monitor_tab, 'mouse_button_combo'):
            self.monitor_tab.mouse_button_combo.currentTextChanged.connect(self.on_mouse_settings_changed)
    
    @pyqtSlot()
    def toggle_monitoring(self):
        """切换监控状态"""
        try:
            # 获取主窗口
            main_window = self.monitor_tab.window()
            if not main_window:
                logger.warning("无法获取主窗口")
                return
            
            # 获取OCR控制器
            if not hasattr(main_window, 'ocr_controller'):
                logger.warning("主窗口没有ocr_controller属性")
                QMessageBox.warning(
                    self.monitor_tab, 
                    "错误", 
                    "无法获取OCR控制器，请先配置OCR设置"
                )
                return
            
            ocr_controller = main_window.ocr_controller
            
            if not self.is_monitoring:
                try:
                    # 开始监控
                    success = ocr_controller.start_monitoring()
                    if success:
                        self.is_monitoring = True
                        self.monitor_button.setText("停止监控")
                        self.monitor_button.setStyleSheet("background-color: #F44336; color: white; border-radius: 4px;")
                        self.status_label.setText("监控状态: 正在监控")
                        logger.info("监控已启动")
                        
                        # 创建心跳检查定时器，每5秒检查一次监控状态
                        if not hasattr(self, 'heartbeat_timer'):
                            self.heartbeat_timer = QTimer()
                            self.heartbeat_timer.timeout.connect(self.check_monitoring_status)
                        
                        self.heartbeat_timer.start(5000)  # 5秒检查一次
                    else:
                        QMessageBox.warning(
                            self.monitor_tab, 
                            "警告", 
                            "无法启动监控，请先在OCR设置中选择一个区域"
                        )
                except Exception as start_error:
                    logger.error(f"启动监控失败: {start_error}")
                    import traceback
                    logger.error(traceback.format_exc())
                    QMessageBox.warning(
                        self.monitor_tab, 
                        "错误", 
                        f"启动监控失败: {start_error}\n请检查是否有屏幕录制权限。"
                    )
            else:
                # 停止监控
                try:
                    success = ocr_controller.stop_monitoring()
                    if success:
                        self.is_monitoring = False
                        self.monitor_button.setText("开始监控")
                        self.monitor_button.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 4px;")
                        self.status_label.setText("监控状态: 已停止")
                        logger.info("监控已停止")
                        
                        # 停止心跳检查
                        if hasattr(self, 'heartbeat_timer') and self.heartbeat_timer.isActive():
                            self.heartbeat_timer.stop()
                except Exception as stop_error:
                    logger.error(f"停止监控失败: {stop_error}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    # 强制更新UI状态，确保用户可以重新开始
                    self.is_monitoring = False
                    self.monitor_button.setText("开始监控")
                    self.monitor_button.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 4px;")
                    self.status_label.setText("监控状态: 已停止(强制)")
                    
                    # 停止心跳检查
                    if hasattr(self, 'heartbeat_timer') and self.heartbeat_timer.isActive():
                        self.heartbeat_timer.stop()
                    
                    QMessageBox.warning(
                        self.monitor_tab, 
                        "警告", 
                        f"停止监控出现异常，已强制停止: {stop_error}"
                    )
        
        except Exception as e:
            logger.error(f"切换监控状态失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.warning(
                self.monitor_tab, 
                "错误", 
                f"切换监控状态失败: {e}"
            )
    
    def check_monitoring_status(self):
        """检查监控状态，确保监控不会意外停止"""
        try:
            if not self.is_monitoring:
                # 如果不是监控状态，停止心跳检查
                if hasattr(self, 'heartbeat_timer') and self.heartbeat_timer.isActive():
                    self.heartbeat_timer.stop()
                return
            
            # 获取主窗口
            main_window = self.monitor_tab.window()
            if not main_window or not hasattr(main_window, 'ocr_controller'):
                return
            
            ocr_controller = main_window.ocr_controller
            
            # 检查OCR控制器的监控状态
            if not ocr_controller.is_monitoring:
                logger.warning("检测到监控已意外停止，尝试重新启动")
                
                # 尝试重新启动监控
                try:
                    success = ocr_controller.start_monitoring()
                    if success:
                        logger.info("监控已自动重新启动")
                    else:
                        logger.warning("自动重新启动监控失败")
                        # 更新UI状态
                        self.is_monitoring = False
                        self.monitor_button.setText("开始监控")
                        self.monitor_button.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 4px;")
                        self.status_label.setText("监控状态: 已停止(自动)")
                        
                        # 停止心跳检查
                        if hasattr(self, 'heartbeat_timer') and self.heartbeat_timer.isActive():
                            self.heartbeat_timer.stop()
                        
                        # 通知用户
                        QMessageBox.warning(
                            self.monitor_tab, 
                            "警告", 
                            "监控已意外停止，自动重启失败。\n请手动重新启动监控。"
                        )
                except Exception as restart_error:
                    logger.error(f"自动重启监控失败: {restart_error}")
                    # 更新UI状态
                    self.is_monitoring = False
                    self.monitor_button.setText("开始监控")
                    self.monitor_button.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 4px;")
                    self.status_label.setText("监控状态: 已停止(错误)")
                    
                    # 停止心跳检查
                    if hasattr(self, 'heartbeat_timer') and self.heartbeat_timer.isActive():
                        self.heartbeat_timer.stop()
        
        except Exception as e:
            logger.error(f"检查监控状态失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    @pyqtSlot()
    def on_add_rule(self):
        """添加规则"""
        try:
            # 获取规则类型
            rule_type_combo = self.monitor_tab.rule_group.findChild(QComboBox, "rule_type_combo")
            if not rule_type_combo:
                logger.error("无法找到规则类型下拉框")
                return
                
            rule_type_text = rule_type_combo.currentText()
            rule_type = self.get_rule_type_from_text(rule_type_text)
            
            # 获取规则内容
            rule_content_edit = self.monitor_tab.rule_group.findChild(QLineEdit, "rule_content_edit")
            if not rule_content_edit or not rule_content_edit.text().strip():
                QMessageBox.warning(
                    self.monitor_tab,
                    "输入错误",
                    "请输入规则内容"
                )
                return
                
            rule_content = rule_content_edit.text().strip()
            
            # 获取规则选项
            case_sensitive_check = self.monitor_tab.rule_group.findChild(QCheckBox, "case_sensitive_check")
            case_sensitive = case_sensitive_check.isChecked() if case_sensitive_check else False
            
            trim_check = self.monitor_tab.rule_group.findChild(QCheckBox, "trim_check")
            trim = trim_check.isChecked() if trim_check else True
            
            # 验证规则内容
            if rule_type == Rule.TYPE_REGEX:
                try:
                    # 测试正则表达式是否有效
                    re.compile(rule_content)
                except re.error as e:
                    QMessageBox.warning(
                        self.monitor_tab,
                        "正则表达式错误",
                        f"正则表达式格式错误: {e}"
                    )
                    return
                    
            elif rule_type == Rule.TYPE_NUMERIC:
                try:
                    # 测试数值是否有效
                    float(rule_content)
                except ValueError:
                    QMessageBox.warning(
                        self.monitor_tab,
                        "数值错误",
                        "请输入有效的数值"
                    )
                    return
            
            # 创建规则参数
            params = {
                'case_sensitive': case_sensitive,
                'trim': trim
            }
            
            # 对于数值比较规则，添加操作符
            if rule_type == Rule.TYPE_NUMERIC:
                # 获取操作符，默认为等于
                params['operator'] = Rule.OP_EQ
            
            # 创建规则对象
            rule = Rule(
                rule_type=rule_type,
                content=rule_content,
                params=params
            )
            
            # 添加规则到引擎
            main_window = self.monitor_tab.window()
            if not main_window or not hasattr(main_window, 'monitor_engine'):
                logger.error("无法获取监控引擎")
                return
                
            monitor_engine = main_window.monitor_engine
            if not monitor_engine or not hasattr(monitor_engine, 'rule_matcher'):
                logger.error("监控引擎未初始化")
                return
            
            # 添加规则
            monitor_engine.rule_matcher.add_rule(rule)
            
            # 添加规则到表格
            self.add_rule_to_table(rule)
            
            # 清空规则内容输入框
            rule_content_edit.clear()
            
            # 保存配置
            self.save_monitor_tab_config()
            
            # 通知用户
            logger.info(f"已添加规则: {rule.id}")
            
        except Exception as e:
            logger.error(f"添加规则失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.warning(
                self.monitor_tab, 
                "错误", 
                f"添加规则失败: {e}"
            )
    
    def get_rule_type_from_text(self, type_text: str) -> str:
        """根据规则类型文本获取规则类型"""
        type_map = {
            "包含文本": Rule.TYPE_CONTAINS,
            "精确匹配": Rule.TYPE_EXACT,
            "正则表达式": Rule.TYPE_REGEX,
            "数值比较": Rule.TYPE_NUMERIC,
            "不包含文本": Rule.TYPE_NOT_CONTAINS,
            "文本变化": Rule.TYPE_CHANGED
        }
        return type_map.get(type_text, Rule.TYPE_CONTAINS)
    
    def add_rule_to_table(self, rule: Rule):
        """添加规则到表格"""
        try:
            table = self.monitor_tab.rule_table
            if not table:
                return
            
            # 获取当前行数
            row = table.rowCount()
            table.insertRow(row)
            
            # 添加行号
            row_num_item = QTableWidgetItem(str(row + 1))
            table.setItem(row, 0, row_num_item)
            
            # 设置规则类型
            type_text = self.get_rule_type_text(rule.type)
            table.setItem(row, 1, QTableWidgetItem(type_text))
            
            # 设置规则内容
            table.setItem(row, 2, QTableWidgetItem(rule.content))
            
            # 添加规则状态
            status_item = QTableWidgetItem("accept")
            table.setItem(row, 3, status_item)
            
            # 设置规则选项
            options = []
            if rule.params.get('case_sensitive'):
                options.append("区分大小写")
            if rule.params.get('trim'):
                options.append("忽略首尾空格")
            
            table.setItem(row, 4, QTableWidgetItem(", ".join(options)))
            
            # 添加删除按钮
            self._add_delete_button(table, row, rule.rule_id)
            
        except Exception as e:
            logger.error(f"添加规则到表格失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _add_delete_button(self, table, row, rule_id):
        """添加删除按钮到表格"""
        from PyQt5.QtWidgets import QPushButton
        
        # 创建删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setFixedWidth(60)
        delete_btn.setStyleSheet("QPushButton { background-color: #F44336; color: white; border-radius: 3px; }")
        
        # 存储规则ID为属性
        delete_btn.setProperty("rule_id", rule_id)
        
        # 连接删除按钮点击事件
        delete_btn.clicked.connect(lambda: self.on_delete_rule(rule_id))
        
        # 添加按钮到表格
        table.setCellWidget(row, 5, delete_btn)

    def on_delete_rule(self, rule_id):
        """删除规则按钮点击事件"""
        try:
            # 获取主窗口
            main_window = self.monitor_tab.window()
            if not main_window or not hasattr(main_window, 'monitor_engine'):
                logger.warning("无法获取监控引擎")
                return
                
            monitor_engine = main_window.monitor_engine
            if not monitor_engine or not hasattr(monitor_engine, 'rule_matcher'):
                logger.warning("无法获取规则匹配器")
                return
            
            # 删除规则
            if monitor_engine.rule_matcher.remove_rule(rule_id):
                # 更新表格
                self.update_rule_table()
                
                # 保存配置
                monitor_engine.save_config()
                
                # 保存当前标签页配置
                self.save_monitor_tab_config()
                
                logger.info(f"规则已删除: {rule_id}")
            else:
                logger.warning(f"删除规则失败: {rule_id}")
        
        except Exception as e:
            logger.error(f"删除规则失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def get_rule_type_text(self, rule_type: str) -> str:
        """根据规则类型获取规则类型文本"""
        type_map = {
            Rule.TYPE_CONTAINS: "包含文本",
            Rule.TYPE_EXACT: "精确匹配",
            Rule.TYPE_REGEX: "正则表达式",
            Rule.TYPE_NUMERIC: "数值比较",
            Rule.TYPE_NOT_CONTAINS: "不包含文本",
            Rule.TYPE_CHANGED: "文本变化"
        }
        return type_map.get(rule_type, "未知类型")
    
    @pyqtSlot(str)
    def on_rule_combination_changed(self, combination_text):
        """规则组合方式改变事件"""
        try:
            # 获取自定义表达式输入框
            rule_list_group = self.monitor_tab.rule_list_group
            custom_expr_edit = rule_list_group.findChild(QLineEdit, "custom_expr_edit")
            if not custom_expr_edit:
                logger.error("无法找到自定义表达式输入框")
                return
            
            # 根据选择启用或禁用自定义表达式输入框
            if combination_text == "自定义组合":
                custom_expr_edit.setEnabled(True)
            else:
                custom_expr_edit.setEnabled(False)
            
            # 获取主窗口
            main_window = self.monitor_tab.window()
            if not main_window or not hasattr(main_window, 'monitor_engine'):
                logger.warning("无法获取监控引擎")
                return
                
            monitor_engine = main_window.monitor_engine
            if not monitor_engine or not hasattr(monitor_engine, 'rule_matcher'):
                logger.warning("无法获取规则匹配器")
                return
                
            # 设置规则组合方式
            if combination_text == "全部满足 (AND)":
                monitor_engine.rule_matcher.set_rule_combination("AND")
            elif combination_text == "任一满足 (OR)":
                monitor_engine.rule_matcher.set_rule_combination("OR")
            elif combination_text == "自定义组合":
                monitor_engine.rule_matcher.set_rule_combination("CUSTOM")
                
                # 获取自定义表达式
                if custom_expr_edit.text().strip():
                    # 设置自定义表达式
                    monitor_engine.rule_matcher.set_custom_expression(custom_expr_edit.text())
            
            # 保存配置
            monitor_engine.save_config()
            
            # 保存当前标签页配置
            self.save_monitor_tab_config()
            
            logger.info(f"规则组合方式已设置为: {combination_text}")
            
        except Exception as e:
            logger.error(f"设置规则组合方式失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    @pyqtSlot()
    def on_add_action(self):
        """添加动作"""
        try:
            # 获取主窗口
            main_window = self.monitor_tab.window()
            if not main_window:
                logger.error("无法获取主窗口")
                return
                
            # 获取动作执行器
            if not hasattr(main_window, 'monitor_engine') or not hasattr(main_window.monitor_engine, 'action_executor'):
                logger.error("无法获取动作执行器")
                QMessageBox.warning(
                    self.monitor_tab, 
                    "错误", 
                    "无法获取动作执行器，请检查系统配置"
                )
                return
            
            action_executor = main_window.monitor_engine.action_executor
            
            # 获取动作类型
            action_combo = self.monitor_tab.action_group.findChild(QComboBox, "action_combo")
            if not action_combo:
                logger.error("无法找到动作类型下拉框")
                return
                
            action_type_text = action_combo.currentText()
            action_type = self.get_action_type_from_text(action_type_text)
            
            # 获取动作参数
            action_param_edit = self.monitor_tab.action_group.findChild(QLineEdit, "action_param_edit")
            if not action_param_edit:
                logger.error("无法找到动作参数输入框")
                return
                
            action_param = action_param_edit.text().strip()
            
            # 验证参数
            if not action_param and action_type not in ['mousemove', 'mouseclick']:
                QMessageBox.warning(
                    self.monitor_tab,
                    "参数错误",
                    "请输入动作参数"
                )
                return
            
            # 获取触发条件
            trigger_combo = self.monitor_tab.action_group.findChild(QComboBox, "trigger_combo")
            if not trigger_combo:
                logger.error("无法找到触发条件下拉框")
                return
                
            trigger_condition = trigger_combo.currentText()
            
            # 获取触发延迟
            delay_spin = self.monitor_tab.action_group.findChild(QSpinBox, "delay_spin")
            if not delay_spin:
                logger.error("无法找到延迟设置框")
                return
                
            trigger_delay = delay_spin.value()
            
            # 创建动作参数字典
            params = {
                'trigger_condition': trigger_condition,
                'trigger_delay': trigger_delay
            }
            
            # 处理鼠标点击类型的特殊参数
            if action_type == 'mouseclick' and hasattr(self.monitor_tab, 'mouse_settings_group'):
                # 获取鼠标坐标
                x_spin = self.monitor_tab.findChild(QSpinBox, "mouse_x_spin")
                y_spin = self.monitor_tab.findChild(QSpinBox, "mouse_y_spin")
                if x_spin and y_spin:
                    params['x'] = x_spin.value()
                    params['y'] = y_spin.value()
                
                # 获取点击设置
                click_count_spin = self.monitor_tab.findChild(QSpinBox, "click_count_spin")
                if click_count_spin:
                    params['click_count'] = click_count_spin.value()
                
                click_interval_spin = self.monitor_tab.findChild(QSpinBox, "click_interval_spin")
                if click_interval_spin:
                    params['click_interval'] = click_interval_spin.value()
                
                # 获取鼠标按钮
                button_combo = self.monitor_tab.findChild(QComboBox, "mouse_button_combo")
                if button_combo:
                    button_text = button_combo.currentText()
                    if button_text == "左键":
                        params['button'] = 'left'
                    elif button_text == "右键":
                        params['button'] = 'right'
                    elif button_text == "中键":
                        params['button'] = 'middle'
            
            # 创建动作对象
            from core.action_executor import Action
            action = Action(
                action_type=action_type,
                content=action_param,
                params=params
            )
            
            # 添加动作到执行器
            action_executor.add_action(action)
            
            # 更新UI，显示已添加的动作
            if not hasattr(self, 'action_list'):
                # 创建动作列表
                self.action_list = []
            
            self.action_list.append(action)
            
            # 保存配置
            self.save_monitor_tab_config()
            
            # 通知用户
            QMessageBox.information(
                self.monitor_tab,
                "成功",
                f"动作已添加: {action_type_text}\n参数: {action_param}"
            )
            
            logger.info(f"已添加动作: {action.id} - {action_type_text}")
            
        except Exception as e:
            logger.error(f"添加动作失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.warning(
                self.monitor_tab, 
                "错误", 
                f"添加动作失败: {e}"
            )
    
    def get_action_type_from_text(self, type_text: str) -> str:
        """将动作类型文本转换为内部类型
        
        Args:
            type_text: 动作类型文本
            
        Returns:
            str: 内部动作类型
        """
        from core.action_executor import Action
        
        # 动作类型映射
        action_type_map = {
            "发送通知": Action.TYPE_NOTIFICATION,
            "执行按键": Action.TYPE_KEYBOARD,
            "点击鼠标": "mouseclick",  # 特殊类型，会被转换为 Action.TYPE_MOUSE
            "运行脚本": Action.TYPE_SCRIPT,
            "自定义动作": Action.TYPE_CUSTOM
        }
        
        return action_type_map.get(type_text, Action.TYPE_NOTIFICATION)
    
    def save_monitor_tab_config(self):
        """保存监控标签页配置"""
        try:
            # 获取主窗口
            main_window = self.monitor_tab.window()
            if not main_window:
                return
                
            # 获取配置控制器
            if not hasattr(main_window, 'config_controller'):
                return
                
            config_controller = main_window.config_controller
            
            # 获取当前标签页配置
            config = config_controller.get_config_from_tab("监控设置", self.monitor_tab)
            
            # 确保触发动作配置正确保存
            action_group = self.monitor_tab.action_group
            
            # 获取触发条件
            trigger_combo = action_group.findChild(QComboBox, "trigger_combo")
            if trigger_combo:
                config['monitor']['trigger_condition'] = trigger_combo.currentText()
            
            # 获取延迟
            delay_spin = action_group.findChild(QSpinBox, "delay_spin")
            if delay_spin:
                config['monitor']['trigger_delay'] = delay_spin.value()
            
            # 获取执行动作
            action_combo = action_group.findChild(QComboBox, "action_combo")
            if action_combo:
                config['monitor']['action_type'] = action_combo.currentText()
                
            # 获取动作参数
            action_param_edit = action_group.findChild(QLineEdit, "action_param_edit")
            if action_param_edit:
                config['monitor']['action_param'] = action_param_edit.text()
                
            # 如果是鼠标点击类型，获取鼠标设置
            if hasattr(self.monitor_tab, 'mouse_settings_group') and self.monitor_tab.mouse_settings_group.isVisible():
                mouse_settings = {}
                
                # 获取坐标
                if hasattr(self.monitor_tab, 'mouse_x_spin') and hasattr(self.monitor_tab, 'mouse_y_spin'):
                    mouse_settings['x'] = self.monitor_tab.mouse_x_spin.value()
                    mouse_settings['y'] = self.monitor_tab.mouse_y_spin.value()
                
                # 获取点击次数和间隔
                if hasattr(self.monitor_tab, 'click_count_spin'):
                    mouse_settings['click_count'] = self.monitor_tab.click_count_spin.value()
                
                if hasattr(self.monitor_tab, 'click_interval_spin'):
                    mouse_settings['click_interval'] = self.monitor_tab.click_interval_spin.value()
                
                # 获取鼠标按钮
                if hasattr(self.monitor_tab, 'mouse_button_combo'):
                    mouse_settings['button'] = self.monitor_tab.mouse_button_combo.currentText()
                
                config['monitor']['mouse_settings'] = mouse_settings
            
            # 保存配置到配置管理器
            current_config_name = config_controller.config_manager.current_config
            config_controller.config_manager.save_config(current_config_name, config)
            
            logger.info(f"监控标签页配置已保存到 {current_config_name}")
            
        except Exception as e:
            logger.error(f"保存监控标签页配置失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def load_monitor_tab_config(self):
        """加载监控标签页配置"""
        try:
            # 获取主窗口
            main_window = self.monitor_tab.window()
            if not main_window:
                return
                
            # 获取配置控制器
            if not hasattr(main_window, 'config_controller'):
                return
                
            config_controller = main_window.config_controller
            
            # 应用配置到标签页
            config_controller.apply_config_to_tab("监控设置", self.monitor_tab)
            
            # 加载触发动作相关配置
            action_group = self.monitor_tab.action_group
            
            # 获取当前配置
            current_config = config_controller.config_manager.get_config()
            if 'monitor' not in current_config:
                logger.warning("配置中没有monitor部分")
                return
                
            monitor_config = current_config.get('monitor', {})
            
            # 设置触发条件
            trigger_combo = action_group.findChild(QComboBox, "trigger_combo")
            if trigger_combo and 'trigger_condition' in monitor_config:
                trigger_combo.setCurrentText(monitor_config['trigger_condition'])
            
            # 设置延迟
            delay_spin = action_group.findChild(QSpinBox, "delay_spin")
            if delay_spin and 'trigger_delay' in monitor_config:
                delay_spin.setValue(monitor_config['trigger_delay'])
            
            # 设置执行动作
            action_combo = action_group.findChild(QComboBox, "action_combo")
            if action_combo and 'action_type' in monitor_config:
                action_type = monitor_config['action_type']
                action_combo.setCurrentText(action_type)
                
                # 如果是鼠标点击类型，显示鼠标设置组
                if action_type == "点击鼠标" and hasattr(self.monitor_tab, 'mouse_settings_group'):
                    self.monitor_tab.mouse_settings_group.setVisible(True)
                    
                    # 加载鼠标设置
                    mouse_settings = monitor_config.get('mouse_settings', {})
                    
                    # 设置坐标
                    if hasattr(self.monitor_tab, 'mouse_x_spin') and 'x' in mouse_settings:
                        self.monitor_tab.mouse_x_spin.setValue(mouse_settings['x'])
                    
                    if hasattr(self.monitor_tab, 'mouse_y_spin') and 'y' in mouse_settings:
                        self.monitor_tab.mouse_y_spin.setValue(mouse_settings['y'])
                    
                    # 设置点击次数和间隔
                    if hasattr(self.monitor_tab, 'click_count_spin') and 'click_count' in mouse_settings:
                        self.monitor_tab.click_count_spin.setValue(mouse_settings['click_count'])
                    
                    if hasattr(self.monitor_tab, 'click_interval_spin') and 'click_interval' in mouse_settings:
                        self.monitor_tab.click_interval_spin.setValue(mouse_settings['click_interval'])
                    
                    # 设置鼠标按钮
                    if hasattr(self.monitor_tab, 'mouse_button_combo') and 'button' in mouse_settings:
                        self.monitor_tab.mouse_button_combo.setCurrentText(mouse_settings['button'])
                else:
                    # 其他类型，隐藏鼠标设置组
                    if hasattr(self.monitor_tab, 'mouse_settings_group'):
                        self.monitor_tab.mouse_settings_group.setVisible(False)
            
            # 设置动作参数
            action_param_edit = action_group.findChild(QLineEdit, "action_param_edit")
            if action_param_edit and 'action_param' in monitor_config:
                action_param_edit.setText(monitor_config['action_param'])
            
            # 更新规则表格
            QTimer.singleShot(100, self.update_rule_table)
            
            logger.info("监控标签页配置已加载")
            
        except Exception as e:
            logger.error(f"加载监控标签页配置失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    @pyqtSlot()
    def on_monitor_config_changed(self):
        """监控配置变化事件"""
        try:
            # 保存配置
            self.save_monitor_tab_config()
            
            # 获取主窗口
            main_window = self.monitor_tab.window()
            if main_window and hasattr(main_window, 'monitor_engine'):
                # 更新监控引擎配置
                interval = int(self.monitor_tab.interval_combo.currentText())
                match_mode = self.monitor_tab.match_mode_combo.currentText()
                
                # 构建监控配置
                monitor_config = {
                    'refresh_rate': interval * 1000,  # 转换为毫秒
                    'match_mode': match_mode
                }
                
                # 获取触发条件、延迟和执行动作
                action_group = self.monitor_tab.action_group
                
                # 获取触发条件
                trigger_combo = action_group.findChild(QComboBox, "trigger_combo")
                if trigger_combo:
                    monitor_config['trigger_condition'] = trigger_combo.currentText()
                
                # 获取延迟
                delay_spin = action_group.findChild(QSpinBox, "delay_spin")
                if delay_spin:
                    monitor_config['trigger_delay'] = delay_spin.value()
                
                # 获取执行动作
                action_combo = action_group.findChild(QComboBox, "action_combo")
                if action_combo:
                    monitor_config['action_type'] = action_combo.currentText()
                
                # 应用到所有监控区域
                for area in main_window.monitor_engine.get_all_areas().values():
                    area.config.update(monitor_config)
                
                # 保存监控引擎配置
                main_window.monitor_engine.save_config()
                
                logger.info(f"已更新监控配置: 间隔={interval}秒, 匹配模式={match_mode}, 触发条件={monitor_config.get('trigger_condition', '')}, 延迟={monitor_config.get('trigger_delay', 0)}秒")
            
        except Exception as e:
            logger.error(f"更新监控配置失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    @pyqtSlot(str)
    def on_custom_expression_changed(self, expression):
        """自定义表达式变化事件"""
        try:
            # 获取主窗口
            main_window = self.monitor_tab.window()
            if not main_window or not hasattr(main_window, 'monitor_engine'):
                return
                
            monitor_engine = main_window.monitor_engine
            if not monitor_engine or not hasattr(monitor_engine, 'rule_matcher'):
                return
                
            # 设置自定义表达式
            monitor_engine.rule_matcher.set_custom_expression(expression)
            
            # 保存配置
            monitor_engine.save_config()
            
            # 保存当前标签页配置
            self.save_monitor_tab_config()
            
            logger.info(f"已更新自定义表达式: {expression}")
            
        except Exception as e:
            logger.error(f"更新自定义表达式失败: {e}")

    def update_rule_table(self):
        """更新规则表格"""
        try:
            # 获取规则表格
            rule_table = self.monitor_tab.rule_table
            if not rule_table:
                logger.warning("无法获取规则表格")
                return
            
            # 获取主窗口
            main_window = self.monitor_tab.window()
            if not main_window or not hasattr(main_window, 'monitor_engine'):
                logger.warning("无法获取监控引擎")
                return
            
            monitor_engine = main_window.monitor_engine
            if not monitor_engine or not hasattr(monitor_engine, 'rule_matcher'):
                logger.warning("无法获取规则匹配器")
                return
            
            # 获取所有规则
            rules = monitor_engine.rule_matcher.get_all_rules()
            
            # 清空表格
            rule_table.setRowCount(0)
            
            # 填充表格
            for rule_id, rule in rules.items():
                row_position = rule_table.rowCount()
                rule_table.insertRow(row_position)
                
                # 添加行号
                row_num_item = QTableWidgetItem(str(row_position + 1))
                rule_table.setItem(row_position, 0, row_num_item)
                
                # 添加规则类型
                type_item = QTableWidgetItem(self.get_rule_type_text(rule.type))
                rule_table.setItem(row_position, 1, type_item)
                
                # 添加规则内容
                content_item = QTableWidgetItem(rule.content)
                rule_table.setItem(row_position, 2, content_item)
                
                # 添加规则状态
                status_item = QTableWidgetItem("accept")
                rule_table.setItem(row_position, 3, status_item)
                
                # 添加规则选项
                options = []
                if rule.params.get('case_sensitive'):
                    options.append("区分大小写")
                if rule.params.get('trim'):
                    options.append("忽略首尾空格")
                
                options_item = QTableWidgetItem(", ".join(options))
                rule_table.setItem(row_position, 4, options_item)
                
                # 添加删除按钮
                self._add_delete_button(rule_table, row_position, rule_id)
            
            logger.info(f"已更新规则表格，共{len(rules)}条规则")
            
        except Exception as e:
            logger.error(f"更新规则表格失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

    @pyqtSlot(str)
    def on_action_type_changed(self, action_type):
        """动作类型变化回调"""
        try:
            # 处理鼠标点击设置组的显示/隐藏
            if hasattr(self.monitor_tab, 'mouse_settings_group'):
                if action_type == "点击鼠标":
                    self.monitor_tab.mouse_settings_group.setVisible(True)
                else:
                    self.monitor_tab.mouse_settings_group.setVisible(False)
            
            # 更新动作参数提示文本
            action_param_edit = self.monitor_tab.action_group.findChild(QLineEdit, "action_param_edit")
            if action_param_edit:
                if action_type == "发送通知":
                    action_param_edit.setPlaceholderText("输入通知消息内容...")
                    action_param_edit.setEnabled(True)
                elif action_type == "执行按键":
                    action_param_edit.setPlaceholderText("输入按键，例如: ctrl+c, enter, space...")
                    action_param_edit.setEnabled(True)
                elif action_type == "点击鼠标":
                    action_param_edit.setPlaceholderText("可选：输入点击后的确认提示")
                    action_param_edit.setEnabled(True)
                elif action_type == "运行脚本":
                    action_param_edit.setPlaceholderText("输入脚本路径或Python代码...")
                    action_param_edit.setEnabled(True)
                elif action_type == "自定义动作":
                    action_param_edit.setPlaceholderText("输入自定义动作数据，格式为JSON...")
                    action_param_edit.setEnabled(True)
                else:
                    action_param_edit.setPlaceholderText("输入动作参数...")
                    action_param_edit.setEnabled(True)
                
                # 清空当前参数
                action_param_edit.clear()
            
            # 保存配置
            self.save_monitor_tab_config()
            
        except Exception as e:
            logger.error(f"动作类型变化处理失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

    @pyqtSlot()
    def on_select_mouse_pos(self):
        """选择鼠标位置按钮点击事件"""
        try:
            # 创建选择坐标对话框
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
            from PyQt5.QtCore import Qt, QTimer
            
            class MousePosDialog(QDialog):
                def __init__(self, parent=None):
                    super().__init__(parent)
                    self.setWindowTitle("选择鼠标位置")
                    self.setFixedSize(300, 150)
                    self.setWindowFlags(Qt.WindowStaysOnTopHint)
                    
                    self.layout = QVBoxLayout(self)
                    
                    # 提示文本
                    self.info_label = QLabel("请将鼠标移动到目标位置，然后按下鼠标左键进行选择。\n按ESC取消。")
                    self.info_label.setAlignment(Qt.AlignCenter)
                    self.layout.addWidget(self.info_label)
                    
                    # 坐标显示
                    self.pos_label = QLabel("X: 0, Y: 0")
                    self.pos_label.setAlignment(Qt.AlignCenter)
                    self.layout.addWidget(self.pos_label)
                    
                    # 按钮区域
                    self.button_layout = QHBoxLayout()
                    
                    self.cancel_btn = QPushButton("取消")
                    self.cancel_btn.clicked.connect(self.reject)
                    self.button_layout.addWidget(self.cancel_btn)
                    
                    self.select_btn = QPushButton("选择当前位置")
                    self.select_btn.clicked.connect(self.accept)
                    self.button_layout.addWidget(self.select_btn)
                    
                    self.layout.addLayout(self.button_layout)
                    
                    # 当前坐标
                    self.current_pos = (0, 0)
                    
                    # 更新坐标的定时器
                    self.timer = QTimer(self)
                    self.timer.timeout.connect(self.update_mouse_pos)
                    self.timer.start(100)  # 每100毫秒更新一次
                
                def update_mouse_pos(self):
                    """更新鼠标位置"""
                    import pyautogui
                    try:
                        x, y = pyautogui.position()
                        self.current_pos = (x, y)
                        self.pos_label.setText(f"X: {x}, Y: {y}")
                    except Exception as e:
                        self.pos_label.setText(f"错误: {e}")
                
                def keyPressEvent(self, event):
                    """按键事件处理"""
                    if event.key() == Qt.Key_Escape:
                        self.reject()
                    else:
                        super().keyPressEvent(event)
            
            # 显示对话框
            dialog = MousePosDialog(self.monitor_tab)
            if dialog.exec_() == QDialog.Accepted:
                x, y = dialog.current_pos
                
                # 设置坐标到鼠标设置组件
                if hasattr(self.monitor_tab, 'mouse_x_spin') and hasattr(self.monitor_tab, 'mouse_y_spin'):
                    self.monitor_tab.mouse_x_spin.setValue(x)
                    self.monitor_tab.mouse_y_spin.setValue(y)
                    
                    # 保存配置
                    self.save_monitor_tab_config()
                    
                    # 通知用户
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.information(
                        self.monitor_tab,
                        "坐标已选择",
                        f"已选择坐标 X: {x}, Y: {y}"
                    )
        
        except Exception as e:
            logger.error(f"选择鼠标位置失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.monitor_tab,
                "错误",
                f"选择鼠标位置失败: {e}"
            )

    @pyqtSlot()
    def on_mouse_settings_changed(self):
        """鼠标设置变化事件"""
        try:
            # 保存配置
            self.save_monitor_tab_config()
            
            # 获取主窗口
            main_window = self.monitor_tab.window()
            if not main_window or not hasattr(main_window, 'monitor_engine'):
                logger.warning("无法获取监控引擎")
                return
            
            # 获取当前鼠标设置
            mouse_settings = {}
            
            # 获取坐标
            if hasattr(self.monitor_tab, 'mouse_x_spin') and hasattr(self.monitor_tab, 'mouse_y_spin'):
                mouse_settings['x'] = self.monitor_tab.mouse_x_spin.value()
                mouse_settings['y'] = self.monitor_tab.mouse_y_spin.value()
            
            # 获取点击次数和间隔
            if hasattr(self.monitor_tab, 'click_count_spin'):
                mouse_settings['click_count'] = self.monitor_tab.click_count_spin.value()
            
            if hasattr(self.monitor_tab, 'click_interval_spin'):
                mouse_settings['click_interval'] = self.monitor_tab.click_interval_spin.value()
            
            # 获取鼠标按钮
            if hasattr(self.monitor_tab, 'mouse_button_combo'):
                button_text = self.monitor_tab.mouse_button_combo.currentText()
                if button_text == "左键":
                    mouse_settings['button'] = 'left'
                elif button_text == "右键":
                    mouse_settings['button'] = 'right'
                elif button_text == "中键":
                    mouse_settings['button'] = 'middle'
            
            # 更新监控引擎配置
            monitor_engine = main_window.monitor_engine
            
            # 更新鼠标设置到监控配置
            current_config = monitor_engine.config.copy()
            if 'mouse_settings' not in current_config:
                current_config['mouse_settings'] = {}
            
            current_config['mouse_settings'].update(mouse_settings)
            monitor_engine.set_config(current_config)
            
            # 保存引擎配置
            monitor_engine.save_config()
            
            logger.info(f"鼠标设置已更新: X={mouse_settings.get('x')}, Y={mouse_settings.get('y')}, 点击次数={mouse_settings.get('click_count')}, 间隔={mouse_settings.get('click_interval')}毫秒, 按钮={mouse_settings.get('button')}")
            
        except Exception as e:
            logger.error(f"更新鼠标设置失败: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def set_log_model(self, log_model):
        """设置日志模型
        
        Args:
            log_model: 日志模型
        """
        self.log_model = log_model
