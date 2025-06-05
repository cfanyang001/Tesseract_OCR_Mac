from PyQt5.QtCore import QObject, pyqtSlot, Qt, QTimer
from PyQt5.QtWidgets import QMessageBox, QPushButton, QLabel, QComboBox, QLineEdit, QCheckBox, QTableWidgetItem, QTableWidget, QSpinBox
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
                # 开始监控
                success = ocr_controller.start_monitoring()
                if success:
                    self.is_monitoring = True
                    self.monitor_button.setText("停止监控")
                    self.monitor_button.setStyleSheet("background-color: #F44336; color: white; border-radius: 4px;")
                    self.status_label.setText("监控状态: 正在监控")
                    logger.info("监控已启动")
                else:
                    QMessageBox.warning(
                        self.monitor_tab, 
                        "警告", 
                        "无法启动监控，请先在OCR设置中选择一个区域"
                    )
            else:
                # 停止监控
                success = ocr_controller.stop_monitoring()
                if success:
                    self.is_monitoring = False
                    self.monitor_button.setText("开始监控")
                    self.monitor_button.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 4px;")
                    self.status_label.setText("监控状态: 已停止")
                    logger.info("监控已停止")
        
        except Exception as e:
            logger.error(f"切换监控状态失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.warning(
                self.monitor_tab, 
                "错误", 
                f"切换监控状态失败: {e}"
            )
    
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
            
            options_item = QTableWidgetItem(", ".join(options))
            table.setItem(row, 4, options_item)
            
        except Exception as e:
            logger.error(f"添加规则到表格失败: {e}")
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
            rule_list_group = self.monitor_tab.rule_list_group
            rule_table = rule_list_group.findChild(QTableWidget, "rule_table")
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
            # 创建消息框提示用户
            QMessageBox.information(
                self.monitor_tab,
                "选择鼠标位置",
                "请将鼠标移动到目标位置，然后按下 Ctrl+Shift+P 键记录坐标。\n\n" +
                "按下 Esc 键取消选择。"
            )
            
            # 创建一个全局键盘监听器
            import keyboard
            import pyautogui
            
            # 定义回调函数
            def on_hotkey_pressed():
                try:
                    # 获取当前鼠标位置
                    x, y = pyautogui.position()
                    
                    # 更新坐标输入框
                    self.monitor_tab.mouse_x_spin.setValue(x)
                    self.monitor_tab.mouse_y_spin.setValue(y)
                    
                    # 移除键盘监听器
                    keyboard.unhook_all()
                    
                    # 显示成功消息
                    QMessageBox.information(
                        self.monitor_tab,
                        "坐标已记录",
                        f"已记录鼠标位置: ({x}, {y})"
                    )
                except Exception as e:
                    logger.error(f"记录鼠标位置失败: {e}")
                    QMessageBox.warning(
                        self.monitor_tab,
                        "错误",
                        f"记录鼠标位置失败: {e}"
                    )
            
            # 定义取消函数
            def on_cancel():
                # 移除键盘监听器
                keyboard.unhook_all()
                
                # 显示取消消息
                QMessageBox.information(
                    self.monitor_tab,
                    "已取消",
                    "已取消选择鼠标位置"
                )
            
            # 注册热键
            keyboard.add_hotkey('ctrl+shift+p', on_hotkey_pressed)
            keyboard.add_hotkey('esc', on_cancel)
            
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
