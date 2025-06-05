from PyQt5.QtCore import QObject, pyqtSlot, Qt, QTimer, QPoint, QEvent
from PyQt5.QtWidgets import (
    QMessageBox, QPushButton, QLabel, QComboBox, QLineEdit, QCheckBox, 
    QTableWidgetItem, QTableWidget, QSpinBox, QDialog, QVBoxLayout, QHBoxLayout, QApplication
)
from loguru import logger

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
        """添加规则按钮点击事件"""
        try:
            # 获取主窗口
            main_window = self.monitor_tab.window()
            if not main_window:
                logger.warning("无法获取主窗口")
                return
            
            # 获取监控引擎
            if not hasattr(main_window, 'monitor_controller') or not hasattr(main_window, 'monitor_engine'):
                logger.warning("主窗口没有monitor_engine属性")
                QMessageBox.warning(
                    self.monitor_tab, 
                    "错误", 
                    "无法获取监控引擎，请先配置监控设置"
                )
                return
            
            # 获取规则设置
            rule_group = self.monitor_tab.rule_group
            
            # 获取规则类型
            rule_type_combo = rule_group.findChild(QComboBox)
            if not rule_type_combo:
                logger.warning("无法获取规则类型下拉框")
                return
            
            rule_type_text = rule_type_combo.currentText()
            rule_type = self.get_rule_type_from_text(rule_type_text)
            
            # 获取规则内容
            rule_content_edit = rule_group.findChild(QLineEdit)
            if not rule_content_edit:
                logger.warning("无法获取规则内容输入框")
                return
            
            rule_content = rule_content_edit.text().strip()
            if not rule_content:
                QMessageBox.warning(
                    self.monitor_tab, 
                    "警告", 
                    "规则内容不能为空"
                )
                return
            
            # 获取规则选项
            case_sensitive_check = None
            trim_check = None
            
            for check in rule_group.findChildren(QCheckBox):
                if check.text() == "区分大小写":
                    case_sensitive_check = check
                elif check.text() == "忽略首尾空格":
                    trim_check = check
            
            case_sensitive = case_sensitive_check.isChecked() if case_sensitive_check else False
            trim = trim_check.isChecked() if trim_check else True
            
            # 创建规则参数
            params = {
                'case_sensitive': case_sensitive,
                'trim': trim
            }
            
            # 创建规则
            rule = Rule(
                rule_id=None,  # 自动生成ID
                rule_type=rule_type,
                content=rule_content,
                params=params
            )
            
            # 添加规则到监控引擎
            monitor_engine = main_window.monitor_engine
            if monitor_engine and hasattr(monitor_engine, 'rule_matcher'):
                monitor_engine.rule_matcher.add_rule(rule)
                logger.info(f"规则已添加: {rule_type}:{rule_content}")
                
                # 添加规则到表格
                self.add_rule_to_table(rule)
                
                # 清空输入框
                rule_content_edit.clear()
                
                # 保存监控引擎配置
                monitor_engine.save_config()
                
                # 保存当前标签页配置
                self.save_monitor_tab_config()
                
                QMessageBox.information(
                    self.monitor_tab,
                    "成功",
                    f"规则已添加: {self.get_rule_type_text(rule_type)} - {rule_content}"
                )
            
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
            # 获取主窗口
            main_window = self.monitor_tab.window()
            if not main_window or not hasattr(main_window, 'monitor_engine'):
                return
                
            monitor_engine = main_window.monitor_engine
            if not monitor_engine or not hasattr(monitor_engine, 'rule_matcher'):
                return
                
            # 设置规则组合方式
            if combination_text == "全部满足 (AND)":
                monitor_engine.rule_matcher.set_rule_combination("AND")
            elif combination_text == "任一满足 (OR)":
                monitor_engine.rule_matcher.set_rule_combination("OR")
            elif combination_text == "自定义组合":
                monitor_engine.rule_matcher.set_rule_combination("CUSTOM")
                
                # 获取自定义表达式
                rule_list_group = self.monitor_tab.rule_list_group
                custom_expr_edit = rule_list_group.findChild(QLineEdit, "custom_expr_edit")
                if custom_expr_edit:
                    # 启用自定义表达式输入框
                    custom_expr_edit.setEnabled(True)
                    # 设置自定义表达式
                    monitor_engine.rule_matcher.set_custom_expression(custom_expr_edit.text())
            
            # 保存配置
            monitor_engine.save_config()
            
            # 保存当前标签页配置
            self.save_monitor_tab_config()
            
            logger.info(f"规则组合方式已设置为: {combination_text}")
            
        except Exception as e:
            logger.error(f"设置规则组合方式失败: {e}")
    
    @pyqtSlot()
    def on_add_action(self):
        """添加动作按钮点击事件"""
        try:
            # 获取主窗口
            main_window = self.monitor_tab.window()
            if not main_window or not hasattr(main_window, 'monitor_engine'):
                return
                
            # 获取动作设置
            action_group = self.monitor_tab.action_group
            
            # 获取触发条件
            trigger_combo = action_group.findChild(QComboBox, "trigger_combo")
            if not trigger_combo:
                return
            trigger_condition = trigger_combo.currentText()
            
            # 获取延迟
            delay_spin = action_group.findChild(QSpinBox, "delay_spin")
            if not delay_spin:
                return
            delay = delay_spin.value()
            
            # 获取动作类型
            action_combo = action_group.findChild(QComboBox, "action_combo")
            if not action_combo:
                return
            action_type = action_combo.currentText()
            
            # 创建动作
            from core.action_executor import Action
            
            # 根据动作类型处理不同参数
            if action_type == "点击鼠标":
                # 获取鼠标点击设置
                if not hasattr(self.monitor_tab, 'mouse_x_spin') or \
                   not hasattr(self.monitor_tab, 'mouse_y_spin') or \
                   not hasattr(self.monitor_tab, 'click_count_spin') or \
                   not hasattr(self.monitor_tab, 'click_interval_spin') or \
                   not hasattr(self.monitor_tab, 'mouse_button_combo'):
                    QMessageBox.warning(
                        self.monitor_tab, 
                        "错误", 
                        "无法获取鼠标点击设置控件"
                    )
                    return
                
                # 获取鼠标点击参数
                mouse_x = self.monitor_tab.mouse_x_spin.value()
                mouse_y = self.monitor_tab.mouse_y_spin.value()
                click_count = self.monitor_tab.click_count_spin.value()
                click_interval = self.monitor_tab.click_interval_spin.value() / 1000.0  # 转换为秒
                
                # 获取鼠标按钮
                button_text = self.monitor_tab.mouse_button_combo.currentText()
                button_map = {"左键": "left", "右键": "right", "中键": "middle"}
                button = button_map.get(button_text, "left")
                
                # 创建动作参数
                action_params = {
                    'mouse_type': Action.MOUSE_CLICK,
                    'x': mouse_x,
                    'y': mouse_y,
                    'clicks': click_count,
                    'interval': click_interval,
                    'button': button
                }
                
                # 创建动作
                action = Action(
                    action_id=None,
                    action_type=Action.TYPE_MOUSE,
                    params=action_params,
                    name=f"鼠标点击 - ({mouse_x},{mouse_y}) {button_text} {click_count}次"
                )
                
                # 添加动作到执行器
                monitor_engine = main_window.monitor_engine
                if monitor_engine and hasattr(monitor_engine, 'action_executor'):
                    monitor_engine.action_executor.add_action(action)
                    logger.info(f"鼠标点击动作已添加: ({mouse_x},{mouse_y}) {button_text} {click_count}次")
                    
                    # 保存配置
                    monitor_engine.save_config()
                    
                    # 保存当前标签页配置
                    self.save_monitor_tab_config()
                    
                    QMessageBox.information(
                        self.monitor_tab, 
                        "成功", 
                        f"鼠标点击动作已添加: ({mouse_x},{mouse_y}) {button_text} {click_count}次"
                    )
            else:
                # 获取动作参数
                action_param_edit = action_group.findChild(QLineEdit, "action_param_edit")
                if not action_param_edit:
                    return
                action_params = action_param_edit.text().strip()
                
                # 创建动作
                action = Action(
                    action_id=None,  # 自动生成ID
                    action_type=self.get_action_type_from_text(action_type),
                    params={
                        'trigger': trigger_condition,
                        'delay': delay,
                        'content': action_params
                    },
                    name=f"{action_type} - {action_params[:20]}"
                )
                
                # 添加动作到执行器
                monitor_engine = main_window.monitor_engine
                if monitor_engine and hasattr(monitor_engine, 'action_executor'):
                    monitor_engine.action_executor.add_action(action)
                    logger.info(f"动作已添加: {action_type}:{action_params}")
                    
                    # 保存配置
                    monitor_engine.save_config()
                    
                    # 保存当前标签页配置
                    self.save_monitor_tab_config()
                    
                    # 清空动作参数输入框
                    action_param_edit.clear()
                    
                    QMessageBox.information(
                        self.monitor_tab, 
                        "成功", 
                        f"动作已添加: {action_type}"
                    )
            
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
        """根据动作类型文本获取动作类型"""
        from core.action_executor import Action
        type_map = {
            "发送通知": Action.TYPE_NOTIFICATION,
            "执行按键": Action.TYPE_KEYBOARD,
            "点击鼠标": Action.TYPE_MOUSE,
            "运行脚本": Action.TYPE_SCRIPT,
            "自定义动作": "custom"
        }
        return type_map.get(type_text, Action.TYPE_NOTIFICATION)
    
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
            
            # 获取配置面板
            config_panel = main_window.config_panel
            
            # 保存配置
            config_panel.configs[config_panel.current_config] = config
            
            logger.info("监控标签页配置已保存")
            
        except Exception as e:
            logger.error(f"保存监控标签页配置失败: {e}")
    
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
                
                # 应用到所有监控区域
                for area in main_window.monitor_engine.get_all_areas().values():
                    area.config.update(monitor_config)
                
                logger.info(f"已更新监控配置: 间隔={interval}秒, 匹配模式={match_mode}")
                
        except Exception as e:
            logger.error(f"更新监控配置失败: {e}")
    
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
        """动作类型变化事件"""
        try:
            # 根据动作类型显示/隐藏相应的设置区域
            if action_type == "点击鼠标":
                # 显示鼠标点击设置区域
                self.monitor_tab.mouse_settings_group.setVisible(True)
                # 隐藏通用动作参数编辑框
                self.monitor_tab.action_param_edit.setVisible(False)
            else:
                # 隐藏鼠标点击设置区域
                self.monitor_tab.mouse_settings_group.setVisible(False)
                # 显示通用动作参数编辑框
                self.monitor_tab.action_param_edit.setVisible(True)
            
            logger.info(f"动作类型已变更: {action_type}")
                
        except Exception as e:
            logger.error(f"动作类型变更处理失败: {e}")
    
    @pyqtSlot()
    def on_select_mouse_pos(self):
        """选择坐标按钮点击事件"""
        try:
            from PyQt5.QtCore import Qt, QTimer, QPoint
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QCheckBox
            import pyautogui
            import time
            
            # 获取主窗口
            main_window = self.monitor_tab.window()
            
            # 创建一个自定义对话框
            class ClickCaptureDialog(QDialog):
                def __init__(self, parent=None, only_text_areas=False):
                    super().__init__(parent, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
                    self.setWindowTitle("选择鼠标位置")
                    self.setStyleSheet("background-color: rgba(0, 0, 0, 150); color: white;")
                    self.setFixedSize(300, 130)
                    
                    # 创建布局
                    self.layout = QVBoxLayout(self)
                    
                    # 添加说明标签
                    self.label = QLabel("请移动到目标位置，然后点击鼠标左键确认位置。\n按ESC键取消。")
                    self.label.setAlignment(Qt.AlignCenter)
                    self.label.setStyleSheet("font-size: 14px;")
                    self.layout.addWidget(self.label)
                    
                    # 创建一个标签显示当前坐标
                    self.coords_label = QLabel("当前坐标: (0, 0)")
                    self.coords_label.setAlignment(Qt.AlignCenter)
                    self.coords_label.setStyleSheet("font-size: 16px; font-weight: bold;")
                    self.layout.addWidget(self.coords_label)
                    
                    # 添加限制文本区域选项
                    self.option_layout = QHBoxLayout()
                    self.text_areas_only_check = QCheckBox("仅限文本区域")
                    self.text_areas_only_check.setChecked(only_text_areas)
                    self.text_areas_only_check.setStyleSheet("color: white;")
                    self.option_layout.addStretch()
                    self.option_layout.addWidget(self.text_areas_only_check)
                    self.option_layout.addStretch()
                    self.layout.addLayout(self.option_layout)
                    
                    # 设置当前鼠标位置
                    self.current_pos = (0, 0)
                    
                    # 保存文本区域
                    self.text_areas = []
                    
                    # 当前是否在有效区域
                    self.is_valid_area = False
                    
                    # 安装事件过滤器以捕获全局鼠标事件
                    self.installEventFilter(self)
                
                def updateCoords(self):
                    """更新坐标显示"""
                    try:
                        # 获取当前鼠标位置
                        self.current_pos = pyautogui.position()
                        x, y = self.current_pos
                        
                        # 检查是否在文本区域内
                        if self.text_areas_only_check.isChecked():
                            self.is_valid_area = self.is_in_text_area(x, y)
                            area_text = "有效区域" if self.is_valid_area else "无效区域"
                            style = "color: #4CAF50;" if self.is_valid_area else "color: #F44336;"
                            self.coords_label.setText(f"当前坐标: ({x}, {y}) - {area_text}")
                            self.coords_label.setStyleSheet(f"font-size: 16px; font-weight: bold; {style}")
                        else:
                            self.is_valid_area = True
                            self.coords_label.setText(f"当前坐标: ({x}, {y})")
                            self.coords_label.setStyleSheet("font-size: 16px; font-weight: bold;")
                        
                        # 更新对话框位置，跟随鼠标
                        screen_geometry = QApplication.desktop().screenGeometry()
                        dialog_x = min(x + 20, screen_geometry.width() - self.width())
                        dialog_y = min(y + 20, screen_geometry.height() - self.height())
                        self.move(dialog_x, dialog_y)
                    except Exception as e:
                        logger.error(f"更新坐标失败: {e}")
                
                def set_text_areas(self, areas):
                    """设置文本区域"""
                    self.text_areas = areas
                
                def is_in_text_area(self, x, y):
                    """检查坐标是否在文本区域内"""
                    for area in self.text_areas:
                        if (area['x'] <= x <= area['x'] + area['width'] and 
                            area['y'] <= y <= area['y'] + area['height']):
                            return True
                    return False
                
                def eventFilter(self, obj, event):
                    """事件过滤器，用于捕获全局鼠标事件"""
                    if event.type() == QEvent.MouseButtonPress:
                        if event.button() == Qt.LeftButton:
                            if self.is_valid_area:
                                self.accept()
                            return True
                    elif event.type() == QEvent.KeyPress:
                        if event.key() == Qt.Key_Escape:
                            self.reject()
                            return True
                    return super().eventFilter(obj, event)
            
            # 获取OCR识别到的文本区域
            text_areas = []
            if main_window and hasattr(main_window, 'ocr_controller'):
                # 获取OCR结果
                ocr_controller = main_window.ocr_controller
                if hasattr(ocr_controller, 'last_ocr_details') and ocr_controller.last_ocr_details:
                    if 'boxes' in ocr_controller.last_ocr_details:
                        text_areas = ocr_controller.last_ocr_details['boxes']
            
            # 创建对话框
            dialog = ClickCaptureDialog(self.monitor_tab)
            dialog.set_text_areas(text_areas)
            
            # 创建并启动更新定时器
            timer = QTimer(dialog)
            timer.timeout.connect(dialog.updateCoords)
            timer.start(50)  # 每50毫秒更新一次
            
            # 显示对话框在当前鼠标位置附近
            cursor_pos = pyautogui.position()
            dialog.move(cursor_pos[0] + 20, cursor_pos[1] + 20)
            
            # 显示对话框
            QApplication.setOverrideCursor(Qt.CrossCursor)  # 设置鼠标为十字光标
            result = dialog.exec_()
            QApplication.restoreOverrideCursor()  # 恢复鼠标光标
            
            # 停止定时器
            timer.stop()
            
            # 处理结果
            if result == QDialog.Accepted:
                x, y = dialog.current_pos
                self.monitor_tab.mouse_x_spin.setValue(x)
                self.monitor_tab.mouse_y_spin.setValue(y)
                
                QMessageBox.information(
                    self.monitor_tab,
                    "坐标已记录",
                    f"已记录鼠标位置: ({x}, {y})"
                )
            
        except Exception as e:
            logger.error(f"选择鼠标位置失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.warning(
                self.monitor_tab,
                "错误",
                f"选择鼠标位置失败: {e}"
            )
    
    @pyqtSlot()
    def on_mouse_settings_changed(self):
        """鼠标点击设置变化事件"""
        try:
            # 保存配置
            self.save_monitor_tab_config()
            
            logger.debug("鼠标点击设置已更新")
                
        except Exception as e:
            logger.error(f"更新鼠标点击设置失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
