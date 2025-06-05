from PyQt5.QtCore import QObject, pyqtSlot, Qt
from PyQt5.QtWidgets import QComboBox, QLineEdit
from loguru import logger

from config.config_manager import ConfigManager

class ConfigController(QObject):
    """配置控制器，连接配置面板和配置管理器"""
    
    def __init__(self, config_panel):
        """初始化配置控制器
        
        Args:
            config_panel: 配置面板组件
        """
        super().__init__()
        self.config_panel = config_panel
        self.config_manager = ConfigManager()
        self.tab_widgets = {}  # 存储标签页组件的引用
        
        # 连接信号
        self.connect_signals()
        
        # 初始化配置面板
        self.init_config_panel()
    
    def connect_signals(self):
        """连接信号"""
        # 配置面板信号
        self.config_panel.config_changed.connect(self.on_config_changed)
        self.config_panel.config_saved.connect(self.on_config_saved)
    
    def init_config_panel(self):
        """初始化配置面板"""
        try:
            # 获取所有配置名称
            config_names = self.config_manager.get_all_config_names()
            
            # 清除现有项
            self.config_panel.config_combo.clear()
            
            # 添加配置名称到下拉框
            for name in config_names:
                self.config_panel.config_combo.addItem(name)
            
            # 设置当前配置
            current_config = self.config_manager.current_config
            self.config_panel.config_combo.setCurrentText(current_config)
            
            # 更新配置面板显示
            self.config_panel.current_config = current_config
            self.config_panel.configs = {name: self.config_manager.get_config(name) for name in config_names}
            self.config_panel.update_config_display()
            
            logger.info("配置面板初始化完成")
        
        except Exception as e:
            logger.error(f"初始化配置面板失败: {e}")
    
    def register_tab(self, tab_name, tab_widget):
        """注册标签页组件
        
        Args:
            tab_name: 标签页名称
            tab_widget: 标签页组件
        """
        self.tab_widgets[tab_name] = tab_widget
        logger.info(f"注册标签页: {tab_name}")
    
    @pyqtSlot(str)
    def on_config_changed(self, config_name):
        """当选择的配置改变时
        
        Args:
            config_name: 配置名称
        """
        try:
            # 设置配置管理器的当前配置
            self.config_manager.set_current_config(config_name)
            
            # 确保配置面板的当前配置与配置管理器同步
            self.config_panel.current_config = config_name
            
            # 更新配置面板显示
            self.update_config_display()
            
            # 应用配置到所有已注册的标签页
            self.apply_config_to_all_tabs()
            
            logger.info(f"切换到配置: {config_name}")
        
        except Exception as e:
            logger.error(f"切换配置失败: {e}")
    
    @pyqtSlot(str, dict)
    def on_config_saved(self, config_name, config_data):
        """当配置保存时
        
        Args:
            config_name: 配置名称
            config_data: 配置数据
        """
        try:
            # 保存配置
            success = self.config_manager.save_config(config_name, config_data)
            
            if success:
                # 更新配置面板中的配置数据
                self.config_panel.configs[config_name] = config_data.copy()
                
                # 确保配置管理器的当前配置与配置面板同步
                if self.config_manager.current_config != config_name:
                    self.config_manager.set_current_config(config_name)
                
                logger.info(f"配置 {config_name} 已保存")
            else:
                logger.error(f"保存配置 {config_name} 失败")
        
        except Exception as e:
            logger.error(f"保存配置时发生错误: {e}")
    
    def update_config_display(self):
        """更新配置面板显示"""
        # 获取当前配置
        config = self.config_manager.get_config()
        
        # 更新配置面板
        self.config_panel.configs[self.config_panel.current_config] = config
        self.config_panel.update_config_display()
    
    def apply_config_to_all_tabs(self):
        """应用配置到所有已注册的标签页"""
        try:
            for tab_name, tab_widget in self.tab_widgets.items():
                self.apply_config_to_tab(tab_name, tab_widget)
            logger.info("已将配置应用到所有标签页")
        except Exception as e:
            logger.error(f"应用配置到所有标签页失败: {e}")
    
    def apply_config_to_tab(self, tab_name, tab_widget):
        """应用配置到指定标签页
        
        Args:
            tab_name: 标签页名称
            tab_widget: 标签页组件
        """
        try:
            # 获取当前配置
            config = self.config_manager.get_config()
            
            # 应用全局配置
            self.apply_global_config(tab_widget, config.get("global", {}))
            
            # 根据标签页类型应用特定配置
            if tab_name == "OCR设置":
                self.apply_ocr_config(tab_widget, config.get("ocr", {}))
            elif tab_name == "监控设置":
                self.apply_monitor_config(tab_widget, config.get("monitor", {}))
            elif tab_name == "任务管理":
                self.apply_task_config(tab_widget, config.get("task", {}))
            elif tab_name == "动作配置":
                self.apply_actions_config(tab_widget, config.get("actions", {}))
            elif tab_name == "日志":
                self.apply_logs_config(tab_widget, config.get("logs", {}))
            
        except Exception as e:
            logger.error(f"应用配置到标签页 {tab_name} 失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def apply_global_config(self, tab_widget, config):
        """应用全局配置到标签页
        
        Args:
            tab_widget: 标签页组件
            config: 全局配置
        """
        # 全局配置应用于所有标签页
        try:
            # 这里可以应用主题、语言等全局配置
            logger.info(f"已应用全局配置: {config}")
        except Exception as e:
            logger.error(f"应用全局配置失败: {e}")
    
    def apply_ocr_config(self, tab_widget, config):
        """应用OCR配置到标签页
        
        Args:
            tab_widget: OCR标签页组件
            config: OCR配置
        """
        try:
            # 获取左侧面板，OCRTab中的组件都在left_panel中
            left_panel = tab_widget.left_panel if hasattr(tab_widget, 'left_panel') else tab_widget
            
            # 设置语言
            if 'language' in config:
                # 获取语言显示文本
                from core.ocr_processor import OCRProcessor
                language_code = config['language']
                language_text = OCRProcessor.LANGUAGE_MAPPING.get(language_code, '中文简体')
                
                # 设置语言下拉框
                lang_combo = left_panel.findChild(QObject, "lang_combo")
                if lang_combo:
                    index = lang_combo.findText(language_text)
                    if index >= 0:
                        lang_combo.setCurrentIndex(index)
                        logger.debug(f"设置语言为: {language_text}")
            
            # 设置PSM模式
            if 'psm' in config:
                psm_combo = left_panel.findChild(QObject, "psm_combo")
                if psm_combo:
                    psm_value = int(config['psm'])
                    if 0 <= psm_value < psm_combo.count():
                        psm_combo.setCurrentIndex(psm_value)
                        logger.debug(f"设置PSM模式为: {psm_value}")
            
            # 设置OEM引擎
            if 'oem' in config:
                oem_combo = left_panel.findChild(QObject, "oem_combo")
                if oem_combo:
                    oem_value = int(config['oem'])
                    if 0 <= oem_value < oem_combo.count():
                        oem_combo.setCurrentIndex(oem_value)
                        logger.debug(f"设置OEM引擎为: {oem_value}")
            
            # 设置精度
            if 'accuracy' in config:
                accuracy_slider = left_panel.findChild(QObject, "accuracy_slider")
                if accuracy_slider:
                    accuracy_slider.setValue(config['accuracy'])
                    logger.debug(f"设置精度为: {config['accuracy']}")
                    
                    # 同时更新精度显示值
                    accuracy_value = left_panel.findChild(QObject, "accuracy_value")
                    if accuracy_value:
                        accuracy_value.setText(f"{config['accuracy']}%")
            
            # 设置预处理选项
            if 'preprocess' in config:
                preprocess_check = left_panel.findChild(QObject, "preprocess_check")
                if preprocess_check:
                    preprocess_check.setChecked(config['preprocess'])
                    logger.debug(f"设置预处理为: {config['preprocess']}")
            
            # 设置文本修正选项
            if 'autocorrect' in config:
                autocorrect_check = left_panel.findChild(QObject, "autocorrect_check")
                if autocorrect_check:
                    autocorrect_check.setChecked(config['autocorrect'])
                    logger.debug(f"设置自动修正为: {config['autocorrect']}")
            
            # 设置屏幕区域
            if 'screen_area' in config:
                screen_area = config['screen_area']
                
                # 设置屏幕区域坐标
                x_spin = left_panel.findChild(QObject, "x_spin")
                if x_spin:
                    x_spin.setValue(screen_area.get('x', 0))
                
                y_spin = left_panel.findChild(QObject, "y_spin")
                if y_spin:
                    y_spin.setValue(screen_area.get('y', 0))
                
                width_spin = left_panel.findChild(QObject, "width_spin")
                if width_spin:
                    width_spin.setValue(screen_area.get('width', 1))
                
                height_spin = left_panel.findChild(QObject, "height_spin")
                if height_spin:
                    height_spin.setValue(screen_area.get('height', 1))
                
                # 如果有控制器，更新其区域
                if hasattr(tab_widget, 'controller') and tab_widget.controller:
                    if screen_area.get('is_selected', False):
                        from PyQt5.QtCore import QRect
                        rect = QRect(
                            screen_area.get('x', 0),
                            screen_area.get('y', 0),
                            screen_area.get('width', 1),
                            screen_area.get('height', 1)
                        )
                        tab_widget.controller.current_rect = rect
                        logger.debug(f"设置控制器区域为: {rect}")
                        
                        # 如果有预览图像，尝试更新预览
                        if hasattr(tab_widget, 'preview'):
                            tab_widget.controller.update_preview()
            
            # 如果有控制器，更新其OCR处理器配置
            if hasattr(tab_widget, 'controller') and tab_widget.controller and hasattr(tab_widget.controller, 'ocr_processor'):
                tab_widget.controller.ocr_processor.set_config(config)
                logger.debug("已更新OCR处理器配置")
            
            logger.info(f"已应用OCR配置: {config}")
        except Exception as e:
            logger.error(f"应用OCR配置失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def apply_monitor_config(self, tab_widget, config):
        """应用监控配置到标签页
        
        Args:
            tab_widget: 监控标签页组件
            config: 监控配置
        """
        try:
            # 设置监控间隔
            if hasattr(tab_widget, 'interval_combo') and 'interval' in config:
                interval = str(config['interval'])
                index = tab_widget.interval_combo.findText(interval)
                if index >= 0:
                    tab_widget.interval_combo.setCurrentIndex(index)
                else:
                    # 如果找不到精确匹配，选择最接近的值
                    tab_widget.interval_combo.setCurrentText(interval)
            
            # 设置匹配模式
            if hasattr(tab_widget, 'match_mode_combo') and 'match_mode' in config:
                match_mode = config['match_mode']
                index = tab_widget.match_mode_combo.findText(match_mode)
                if index >= 0:
                    tab_widget.match_mode_combo.setCurrentIndex(index)
            
            # 设置规则组合方式
            if hasattr(tab_widget, 'rule_list_group'):
                rule_list_group = tab_widget.rule_list_group
                combination_combo = rule_list_group.findChild(QComboBox, "combination_combo")
                if combination_combo and 'rule_combination' in config:
                    rule_combination = config['rule_combination']
                    combo_text = ""
                    
                    if rule_combination == "AND":
                        combo_text = "全部满足 (AND)"
                    elif rule_combination == "OR":
                        combo_text = "任一满足 (OR)"
                    elif rule_combination == "CUSTOM":
                        combo_text = "自定义组合"
                    
                    if combo_text:
                        index = combination_combo.findText(combo_text)
                        if index >= 0:
                            combination_combo.setCurrentIndex(index)
                
                # 设置自定义表达式
                custom_expr_edit = rule_list_group.findChild(QLineEdit, "custom_expr_edit")
                if custom_expr_edit and 'custom_expression' in config:
                    custom_expr_edit.setText(config['custom_expression'])
                    # 如果是自定义组合，则启用自定义表达式输入框
                    if config.get('rule_combination') == "CUSTOM":
                        custom_expr_edit.setEnabled(True)
            
            # 设置触发条件、延迟和执行动作
            if hasattr(tab_widget, 'action_group'):
                action_group = tab_widget.action_group
                
                # 设置触发条件
                trigger_combo = action_group.findChild(QComboBox, "trigger_combo")
                if trigger_combo and 'trigger_condition' in config:
                    index = trigger_combo.findText(config['trigger_condition'])
                    if index >= 0:
                        trigger_combo.setCurrentIndex(index)
                
                # 设置延迟
                delay_spin = action_group.findChild(QComboBox, "delay_spin")
                if delay_spin and 'trigger_delay' in config:
                    delay_spin.setValue(int(config['trigger_delay']))
                
                # 设置执行动作
                action_combo = action_group.findChild(QComboBox, "action_combo")
                if action_combo and 'action_type' in config:
                    index = action_combo.findText(config['action_type'])
                    if index >= 0:
                        action_combo.setCurrentIndex(index)
            
            # 加载规则列表
            main_window = tab_widget.window()
            if main_window and hasattr(main_window, 'monitor_engine') and 'rules' in config:
                monitor_engine = main_window.monitor_engine
                if monitor_engine and hasattr(monitor_engine, 'rule_matcher'):
                    # 导入规则
                    from core.rule_matcher import Rule
                    
                    # 清空现有规则
                    monitor_engine.rule_matcher.rules = {}
                    
                    # 加载规则
                    if 'rules' in config and isinstance(config['rules'], dict):
                        for rule_id, rule_data in config['rules'].items():
                            if isinstance(rule_data, dict):
                                rule = Rule.from_dict(rule_data)
                                monitor_engine.rule_matcher.add_rule(rule)
                    
                    # 设置规则组合方式
                    if 'rule_combination' in config:
                        monitor_engine.rule_matcher.set_rule_combination(config['rule_combination'])
                    
                    # 设置自定义表达式
                    if 'custom_expression' in config:
                        monitor_engine.rule_matcher.set_custom_expression(config['custom_expression'])
                    
                    # 更新规则表格
                    if hasattr(tab_widget, 'controller'):
                        tab_widget.controller.update_rule_table()
            
            logger.info(f"已应用监控配置: {config}")
        except Exception as e:
            logger.error(f"应用监控配置失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def apply_task_config(self, tab_widget, config):
        """应用任务配置到标签页
        
        Args:
            tab_widget: 任务标签页组件
            config: 任务配置
        """
        try:
            # 设置最大并发任务数
            if hasattr(tab_widget, 'max_concurrent_combo') and 'max_concurrent' in config:
                index = tab_widget.max_concurrent_combo.findText(config['max_concurrent'])
                if index >= 0:
                    tab_widget.max_concurrent_combo.setCurrentIndex(index)
            
            # 设置优先级模式
            if hasattr(tab_widget, 'priority_mode_combo') and 'priority_mode' in config:
                index = tab_widget.priority_mode_combo.findText(config['priority_mode'])
                if index >= 0:
                    tab_widget.priority_mode_combo.setCurrentIndex(index)
            
            # 设置自动重启
            if hasattr(tab_widget, 'auto_restart_check') and 'auto_restart' in config:
                tab_widget.auto_restart_check.setChecked(config['auto_restart'])
            
            logger.info(f"已应用任务配置: {config}")
        except Exception as e:
            logger.error(f"应用任务配置失败: {e}")
    
    def apply_actions_config(self, tab_widget, config):
        """应用动作配置到标签页
        
        Args:
            tab_widget: 动作标签页组件
            config: 动作配置
        """
        try:
            # 设置动作延迟
            if hasattr(tab_widget, 'delay_combo') and 'delay' in config:
                index = tab_widget.delay_combo.findText(config['delay'])
                if index >= 0:
                    tab_widget.delay_combo.setCurrentIndex(index)
            
            # 设置重试次数
            if hasattr(tab_widget, 'retries_combo') and 'retries' in config:
                index = tab_widget.retries_combo.findText(config['retries'])
                if index >= 0:
                    tab_widget.retries_combo.setCurrentIndex(index)
            
            # 设置超时时间
            if hasattr(tab_widget, 'timeout_combo') and 'timeout' in config:
                index = tab_widget.timeout_combo.findText(config['timeout'])
                if index >= 0:
                    tab_widget.timeout_combo.setCurrentIndex(index)
            
            # 设置确认动作
            if hasattr(tab_widget, 'confirm_action_check') and 'confirm_action' in config:
                tab_widget.confirm_action_check.setChecked(config['confirm_action'])
            
            logger.info(f"已应用动作配置: {config}")
        except Exception as e:
            logger.error(f"应用动作配置失败: {e}")
    
    def apply_logs_config(self, tab_widget, config):
        """应用日志配置到标签页
        
        Args:
            tab_widget: 日志标签页组件
            config: 日志配置
        """
        try:
            # 设置保留天数
            if hasattr(tab_widget, 'retention_days_combo') and 'retention_days' in config:
                index = tab_widget.retention_days_combo.findText(config['retention_days'])
                if index >= 0:
                    tab_widget.retention_days_combo.setCurrentIndex(index)
            
            # 设置最大大小
            if hasattr(tab_widget, 'max_size_combo') and 'max_size' in config:
                index = tab_widget.max_size_combo.findText(config['max_size'])
                if index >= 0:
                    tab_widget.max_size_combo.setCurrentIndex(index)
            
            # 设置导出格式
            if hasattr(tab_widget, 'export_format_combo') and 'export_format' in config:
                index = tab_widget.export_format_combo.findText(config['export_format'])
                if index >= 0:
                    tab_widget.export_format_combo.setCurrentIndex(index)
            
            logger.info(f"已应用日志配置: {config}")
        except Exception as e:
            logger.error(f"应用日志配置失败: {e}")
    
    def get_config_from_tab(self, tab_name, tab_widget):
        """从标签页获取配置
        
        Args:
            tab_name: 标签页名称
            tab_widget: 标签页组件
            
        Returns:
            dict: 配置数据
        """
        # 获取当前配置的完整副本
        config = self.config_manager.get_config().copy()
        
        # 根据标签页类型更新特定部分
        if tab_name == "OCR设置":
            config["ocr"] = self.get_ocr_config(tab_widget)
        elif tab_name == "监控设置":
            config["monitor"] = self.get_monitor_config(tab_widget)
        elif tab_name == "任务管理":
            config["task"] = self.get_task_config(tab_widget)
        elif tab_name == "动作配置":
            config["actions"] = self.get_actions_config(tab_widget)
        elif tab_name == "日志":
            config["logs"] = self.get_logs_config(tab_widget)
        
        return config
    
    def get_monitor_config(self, tab_widget):
        """从监控标签页获取配置
        
        Args:
            tab_widget: 监控标签页组件
            
        Returns:
            dict: 监控配置
        """
        # 获取当前监控配置的副本
        config = self.config_manager.get_section_config("monitor").copy()
        
        try:
            # 获取监控间隔
            if hasattr(tab_widget, 'interval_combo'):
                config['interval'] = tab_widget.interval_combo.currentText()
            
            # 获取匹配模式
            if hasattr(tab_widget, 'match_mode_combo'):
                config['match_mode'] = tab_widget.match_mode_combo.currentText()
            
            # 获取规则组合方式
            if hasattr(tab_widget, 'rule_list_group'):
                rule_list_group = tab_widget.rule_list_group
                combination_combo = rule_list_group.findChild(QComboBox, "combination_combo")
                if combination_combo:
                    combo_text = combination_combo.currentText()
                    rule_combination = ""
                    
                    if combo_text == "全部满足 (AND)":
                        rule_combination = "AND"
                    elif combo_text == "任一满足 (OR)":
                        rule_combination = "OR"
                    elif combo_text == "自定义组合":
                        rule_combination = "CUSTOM"
                    
                    if rule_combination:
                        config['rule_combination'] = rule_combination
                
                # 获取自定义表达式
                custom_expr_edit = rule_list_group.findChild(QLineEdit, "custom_expr_edit")
                if custom_expr_edit:
                    config['custom_expression'] = custom_expr_edit.text()
            
            # 获取触发条件、延迟和执行动作
            if hasattr(tab_widget, 'action_group'):
                action_group = tab_widget.action_group
                
                # 获取触发条件
                trigger_combo = action_group.findChild(QComboBox, "trigger_combo")
                if trigger_combo:
                    config['trigger_condition'] = trigger_combo.currentText()
                
                # 获取延迟
                delay_spin = action_group.findChild(QComboBox, "delay_spin")
                if delay_spin:
                    config['trigger_delay'] = delay_spin.value()
                
                # 获取执行动作
                action_combo = action_group.findChild(QComboBox, "action_combo")
                if action_combo:
                    config['action_type'] = action_combo.currentText()
            
            # 获取规则列表 - 从主窗口的监控引擎中获取
            main_window = tab_widget.window()
            if main_window and hasattr(main_window, 'monitor_engine'):
                monitor_engine = main_window.monitor_engine
                if monitor_engine and hasattr(monitor_engine, 'rule_matcher'):
                    # 保存规则列表
                    rules_data = {}
                    for rule_id, rule in monitor_engine.rule_matcher.get_all_rules().items():
                        rules_data[rule_id] = rule.to_dict()
                    config['rules'] = rules_data
                    
                    # 保存规则组合方式
                    config['rule_combination'] = monitor_engine.rule_matcher.rule_combination
                    config['custom_expression'] = monitor_engine.rule_matcher.custom_expression
            
        except Exception as e:
            logger.error(f"获取监控配置失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return config
    
    def get_task_config(self, tab_widget):
        """从任务标签页获取配置
        
        Args:
            tab_widget: 任务标签页组件
            
        Returns:
            dict: 任务配置
        """
        # 获取当前任务配置的副本
        config = self.config_manager.get_section_config("task").copy()
        
        try:
            # 获取最大并发任务数
            if hasattr(tab_widget, 'max_concurrent_combo'):
                config['max_concurrent'] = tab_widget.max_concurrent_combo.currentText()
            
            # 获取优先级模式
            if hasattr(tab_widget, 'priority_mode_combo'):
                config['priority_mode'] = tab_widget.priority_mode_combo.currentText()
            
            # 获取自动重启
            if hasattr(tab_widget, 'auto_restart_check'):
                config['auto_restart'] = tab_widget.auto_restart_check.isChecked()
        except Exception as e:
            logger.error(f"获取任务配置失败: {e}")
        
        return config
    
    def get_actions_config(self, tab_widget):
        """从动作标签页获取配置
        
        Args:
            tab_widget: 动作标签页组件
            
        Returns:
            dict: 动作配置
        """
        # 获取当前动作配置的副本
        config = self.config_manager.get_section_config("actions").copy()
        
        try:
            # 获取动作延迟
            if hasattr(tab_widget, 'delay_combo'):
                config['delay'] = tab_widget.delay_combo.currentText()
            
            # 获取重试次数
            if hasattr(tab_widget, 'retries_combo'):
                config['retries'] = tab_widget.retries_combo.currentText()
            
            # 获取超时时间
            if hasattr(tab_widget, 'timeout_combo'):
                config['timeout'] = tab_widget.timeout_combo.currentText()
            
            # 获取确认动作
            if hasattr(tab_widget, 'confirm_action_check'):
                config['confirm_action'] = tab_widget.confirm_action_check.isChecked()
        except Exception as e:
            logger.error(f"获取动作配置失败: {e}")
        
        return config
    
    def get_logs_config(self, tab_widget):
        """从日志标签页获取配置
        
        Args:
            tab_widget: 日志标签页组件
            
        Returns:
            dict: 日志配置
        """
        # 获取当前日志配置的副本
        config = self.config_manager.get_section_config("logs").copy()
        
        try:
            # 获取保留天数
            if hasattr(tab_widget, 'retention_days_combo'):
                config['retention_days'] = tab_widget.retention_days_combo.currentText()
            
            # 获取最大大小
            if hasattr(tab_widget, 'max_size_combo'):
                config['max_size'] = tab_widget.max_size_combo.currentText()
            
            # 获取导出格式
            if hasattr(tab_widget, 'export_format_combo'):
                config['export_format'] = tab_widget.export_format_combo.currentText()
        except Exception as e:
            logger.error(f"获取日志配置失败: {e}")
        
        return config
    
    def get_ocr_config(self, tab_widget):
        """从OCR标签页获取配置
        
        Args:
            tab_widget: OCR标签页组件
            
        Returns:
            dict: OCR配置
        """
        # 获取当前OCR配置的副本
        config = self.config_manager.get_section_config("ocr").copy()
        
        try:
            # 获取左侧面板，OCRTab中的组件都在left_panel中
            left_panel = tab_widget.left_panel if hasattr(tab_widget, 'left_panel') else tab_widget
            
            # 获取语言
            lang_combo = left_panel.findChild(QObject, "lang_combo")
            if lang_combo:
                selected_lang = lang_combo.currentText()
                # 将语言显示文本转换为语言代码
                from core.ocr_processor import OCRProcessor
                lang_code = OCRProcessor.LANGUAGE_MAPPING_REVERSE.get(selected_lang, 'chi_sim')
                config['language'] = lang_code
                logger.debug(f"获取语言设置: {selected_lang} -> {lang_code}")
            
            # 获取PSM模式
            psm_combo = left_panel.findChild(QObject, "psm_combo")
            if psm_combo:
                psm_index = psm_combo.currentIndex()
                config['psm'] = str(psm_index)
                logger.debug(f"获取PSM模式: {psm_index}")
            
            # 获取OEM引擎
            oem_combo = left_panel.findChild(QObject, "oem_combo")
            if oem_combo:
                oem_index = oem_combo.currentIndex()
                config['oem'] = str(oem_index)
                logger.debug(f"获取OEM引擎: {oem_index}")
            
            # 获取精度设置
            accuracy_slider = left_panel.findChild(QObject, "accuracy_slider")
            if accuracy_slider:
                accuracy_value = accuracy_slider.value()
                config['accuracy'] = accuracy_value
                logger.debug(f"获取精度设置: {accuracy_value}")
            
            # 获取预处理选项
            preprocess_check = left_panel.findChild(QObject, "preprocess_check")
            if preprocess_check:
                preprocess_value = preprocess_check.isChecked()
                config['preprocess'] = preprocess_value
                logger.debug(f"获取预处理选项: {preprocess_value}")
            
            # 获取文本修正选项
            autocorrect_check = left_panel.findChild(QObject, "autocorrect_check")
            if autocorrect_check:
                autocorrect_value = autocorrect_check.isChecked()
                config['autocorrect'] = autocorrect_value
                logger.debug(f"获取文本修正选项: {autocorrect_value}")
            
            # 获取屏幕区域
            screen_area = {
                'x': 0,
                'y': 0,
                'width': 1,
                'height': 1,
                'is_selected': False
            }
            
            # 从控制器获取区域
            if hasattr(tab_widget, 'controller') and tab_widget.controller and tab_widget.controller.current_rect:
                rect = tab_widget.controller.current_rect
                screen_area = {
                    'x': rect.x(),
                    'y': rect.y(),
                    'width': rect.width(),
                    'height': rect.height(),
                    'is_selected': True
                }
                logger.debug(f"从控制器获取区域: {rect}")
            else:
                # 从UI组件获取区域
                x_spin = left_panel.findChild(QObject, "x_spin")
                if x_spin:
                    screen_area['x'] = x_spin.value()
                
                y_spin = left_panel.findChild(QObject, "y_spin")
                if y_spin:
                    screen_area['y'] = y_spin.value()
                
                width_spin = left_panel.findChild(QObject, "width_spin")
                if width_spin and width_spin.value() > 0:
                    screen_area['width'] = width_spin.value()
                    screen_area['is_selected'] = True
                
                height_spin = left_panel.findChild(QObject, "height_spin")
                if height_spin and height_spin.value() > 0:
                    screen_area['height'] = height_spin.value()
                    screen_area['is_selected'] = True
                
                logger.debug(f"从UI组件获取区域: {screen_area}")
            
            config['screen_area'] = screen_area
            
        except Exception as e:
            logger.error(f"获取OCR配置失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return config 