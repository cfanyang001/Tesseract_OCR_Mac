import os
import json
import time
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QRect

from core.text_recognizer import TextRecognizer
from core.rule_matcher import RuleMatcher, Rule
from core.action_executor import ActionExecutor, Action
from core.task_scheduler import TaskScheduler, Task
from loguru import logger


class MonitorArea:
    """监控区域，表示一个需要监控的屏幕区域"""
    
    def __init__(self, area_id: str = None, name: str = '',
                 rect: QRect = None, enabled: bool = True):
        """初始化监控区域
        
        Args:
            area_id: 区域ID，为None时自动生成
            name: 区域名称
            rect: 区域矩形
            enabled: 是否启用
        """
        from uuid import uuid4
        self.id = area_id or str(uuid4())
        self.name = name or f"区域 {self.id[:8]}"
        self.rect = rect or QRect(0, 0, 400, 300)
        self.enabled = enabled
        
        # 关联的规则ID列表
        self.rule_ids = []
        
        # 监控配置
        self.config = {
            'refresh_rate': 1000,  # 刷新频率 (毫秒)
            'ocr_language': 'chi_sim',  # OCR语言
            'preprocessing': True,  # 是否启用预处理
            'save_images': False,  # 是否保存图像
            'save_dir': './captures',  # 保存目录
        }
        
        # 状态数据
        self.last_text = ""
        self.last_capture_time = None
        self.match_count = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """将监控区域转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'rect': {
                'x': self.rect.x(),
                'y': self.rect.y(),
                'width': self.rect.width(),
                'height': self.rect.height()
            },
            'enabled': self.enabled,
            'rule_ids': self.rule_ids.copy(),
            'config': self.config.copy(),
            'last_text': self.last_text,
            'last_capture_time': self.last_capture_time.isoformat() if self.last_capture_time else None,
            'match_count': self.match_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MonitorArea':
        """从字典创建监控区域"""
        # 创建矩形
        rect_data = data.get('rect', {})
        rect = QRect(
            rect_data.get('x', 0),
            rect_data.get('y', 0),
            rect_data.get('width', 400),
            rect_data.get('height', 300)
        )
        
        # 创建监控区域
        area = cls(
            area_id=data.get('id'),
            name=data.get('name', ''),
            rect=rect,
            enabled=data.get('enabled', True)
        )
        
        # 设置其他属性
        area.rule_ids = data.get('rule_ids', [])
        area.config = data.get('config', area.config)
        area.last_text = data.get('last_text', '')
        area.match_count = data.get('match_count', 0)
        
        if data.get('last_capture_time'):
            area.last_capture_time = datetime.fromisoformat(data['last_capture_time'])
            
        return area


class MonitorEngine(QObject):
    """监控引擎，集成所有核心组件，提供完整的OCR监控功能"""
    
    # 信号
    text_recognized = pyqtSignal(str, str, dict)  # 文本识别信号 (区域ID, 文本, 详细信息)
    rule_matched = pyqtSignal(str, str, dict)     # 规则匹配信号 (区域ID, 规则ID, 匹配信息)
    area_added = pyqtSignal(str)                  # 区域添加信号 (区域ID)
    area_removed = pyqtSignal(str)                # 区域移除信号 (区域ID)
    area_enabled = pyqtSignal(str, bool)          # 区域启用/禁用信号 (区域ID, 是否启用)
    engine_started = pyqtSignal()                 # 引擎启动信号
    engine_stopped = pyqtSignal()                 # 引擎停止信号
    error_occurred = pyqtSignal(str)              # 错误信号 (错误信息)
    
    def __init__(self, config_dir: str = './config'):
        """初始化监控引擎
        
        Args:
            config_dir: 配置目录
        """
        super().__init__()
        
        # 配置目录
        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)
        
        # 创建核心组件
        try:
            self.text_recognizer = TextRecognizer()
            self.rule_matcher = RuleMatcher()
            self.action_executor = ActionExecutor()
            self.task_scheduler = TaskScheduler()
            logger.info("监控引擎组件初始化成功")
        except Exception as e:
            logger.error(f"监控引擎组件初始化失败: {e}")
            raise
        
        # 监控区域字典
        self.areas = {}  # {area_id: MonitorArea}
        
        # 运行状态
        self._running = False
        self._stop_event = threading.Event()
        self._monitor_threads = {}  # {area_id: Thread}
        
        # 设置任务调度器关联
        self.task_scheduler.set_action_executor(self.action_executor)
        self.task_scheduler.set_rule_matcher(self.rule_matcher)
        
        # 注册回调函数
        self.task_scheduler.register_callback('start_monitor', self.start)
        self.task_scheduler.register_callback('stop_monitor', self.stop)
        self.task_scheduler.register_callback('capture_area', self._capture_area_callback)
        
        # 连接信号
        self.text_recognizer.text_recognized.connect(self._on_text_recognized)
        self.text_recognizer.error_occurred.connect(self._on_error)
        
        # 配置
        self.config = {
            'auto_start': False,      # 是否自动启动
            'auto_save': True,        # 是否自动保存配置
            'save_interval': 300,     # 自动保存间隔 (秒)
            'log_level': 'INFO',      # 日志级别
            'max_log_files': 10,      # 最大日志文件数
            'enable_notification': True,  # 是否启用通知
        }
        
        # 加载配置
        self._load_config()
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """设置配置
        
        Args:
            config: 配置字典
        """
        self.config.update(config)
        
        # 更新日志级别
        logger.remove()
        logger.add(
            os.path.join(self.config_dir, 'logs', 'ocr_monitor_{time}.log'),
            rotation='10 MB',
            retention=self.config['max_log_files'],
            level=self.config['log_level']
        )
        
        # 如果启用了自动保存，更新保存定时器
        if self.config['auto_save']:
            # 这里可以实现自动保存定时器
            pass

    def add_area(self, area: MonitorArea) -> None:
        """添加监控区域
        
        Args:
            area: 监控区域对象
        """
        self.areas[area.id] = area
        self.area_added.emit(area.id)
        logger.info(f"监控区域已添加: {area.name}")
        
        # 自动保存配置
        if self.config['auto_save']:
            self._save_config()
    
    def remove_area(self, area_id: str) -> bool:
        """移除监控区域
        
        Args:
            area_id: 区域ID
            
        Returns:
            bool: 是否成功移除
        """
        if area_id in self.areas:
            # 如果区域正在监控中，先停止
            if area_id in self._monitor_threads:
                self.stop_monitor_area(area_id)
            
            del self.areas[area_id]
            self.area_removed.emit(area_id)
            logger.info(f"监控区域已移除: {area_id}")
            
            # 自动保存配置
            if self.config['auto_save']:
                self._save_config()
                
            return True
        return False
    
    def get_area(self, area_id: str) -> Optional[MonitorArea]:
        """获取监控区域
        
        Args:
            area_id: 区域ID
            
        Returns:
            Optional[MonitorArea]: 监控区域对象，不存在时返回None
        """
        if not area_id:
            return None
        return self.areas.get(area_id)
    
    def get_all_areas(self) -> Dict[str, MonitorArea]:
        """获取所有监控区域
        
        Returns:
            Dict[str, MonitorArea]: 监控区域字典
        """
        return self.areas.copy()
    
    def enable_area(self, area_id: str) -> bool:
        """启用监控区域
        
        Args:
            area_id: 区域ID
            
        Returns:
            bool: 是否成功启用
        """
        area = self.get_area(area_id)
        if area:
            area.enabled = True
            self.area_enabled.emit(area_id, True)
            logger.info(f"监控区域已启用: {area.name}")
            
            # 如果引擎正在运行，启动该区域的监控
            if self._running:
                self.start_monitor_area(area_id)
            
            # 自动保存配置
            if self.config['auto_save']:
                self._save_config()
                
            return True
        return False
    
    def disable_area(self, area_id: str) -> bool:
        """禁用监控区域
        
        Args:
            area_id: 区域ID
            
        Returns:
            bool: 是否成功禁用
        """
        area = self.get_area(area_id)
        if area:
            area.enabled = False
            self.area_enabled.emit(area_id, False)
            logger.info(f"监控区域已禁用: {area.name}")
            
            # 如果该区域正在监控中，停止监控
            if area_id in self._monitor_threads:
                self.stop_monitor_area(area_id)
            
            # 自动保存配置
            if self.config['auto_save']:
                self._save_config()
                
            return True
        return False
    
    def add_rule_to_area(self, area_id: str, rule_id: str) -> bool:
        """向监控区域添加规则
        
        Args:
            area_id: 区域ID
            rule_id: 规则ID
            
        Returns:
            bool: 是否成功添加
        """
        area = self.get_area(area_id)
        if area and rule_id in self.rule_matcher.get_all_rules():
            if rule_id not in area.rule_ids:
                area.rule_ids.append(rule_id)
                logger.info(f"规则已添加到区域: {rule_id} -> {area.name}")
                
                # 自动保存配置
                if self.config['auto_save']:
                    self._save_config()
                    
                return True
        return False
    
    def remove_rule_from_area(self, area_id: str, rule_id: str) -> bool:
        """从监控区域移除规则
        
        Args:
            area_id: 区域ID
            rule_id: 规则ID
            
        Returns:
            bool: 是否成功移除
        """
        area = self.get_area(area_id)
        if area and rule_id in area.rule_ids:
            area.rule_ids.remove(rule_id)
            logger.info(f"规则已从区域移除: {rule_id} -> {area.name}")
            
            # 自动保存配置
            if self.config['auto_save']:
                self._save_config()
                
            return True
        return False
    
    def start(self) -> bool:
        """启动监控引擎"""
        if self._running:
            logger.warning("监控引擎已在运行")
            return False
        
        try:
            # 设置运行状态
            self._running = True
            self._stop_event.clear()
            
            # 启动任务调度器
            self.task_scheduler.start()
            
            # 启动所有启用的监控区域
            for area_id, area in self.areas.items():
                if area.enabled:
                    self.start_monitor_area(area_id)
            
            # 发送启动信号
            self.engine_started.emit()
            
            logger.info("监控引擎已启动")
            return True
            
        except Exception as e:
            self._running = False
            error_msg = f"启动监控引擎失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def stop(self) -> bool:
        """停止监控引擎"""
        if not self._running:
            logger.warning("监控引擎未在运行")
            return False
        
        try:
            # 设置停止事件
            self._stop_event.set()
            
            # 停止所有监控线程
            for area_id in list(self._monitor_threads.keys()):
                self.stop_monitor_area(area_id)
            
            # 停止任务调度器
            self.task_scheduler.stop()
            
            # 重置状态
            self._running = False
            
            # 发送停止信号
            self.engine_stopped.emit()
            
            logger.info("监控引擎已停止")
            return True
            
        except Exception as e:
            error_msg = f"停止监控引擎失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running
    
    def start_monitor_area(self, area_id: str) -> bool:
        """启动监控区域
        
        Args:
            area_id: 区域ID
            
        Returns:
            bool: 是否成功启动
        """
        # 检查区域是否存在且启用
        area = self.get_area(area_id)
        if not area or not area.enabled:
            return False
        
        # 检查是否已在监控
        if area_id in self._monitor_threads and self._monitor_threads[area_id].is_alive():
            logger.warning(f"区域已在监控中: {area.name}")
            return False
        
        try:
            # 创建并启动监控线程
            thread = threading.Thread(
                target=self._monitor_area_thread,
                args=(area_id,),
                daemon=True
            )
            
            # 记录线程
            self._monitor_threads[area_id] = thread
            
            # 启动线程
            thread.start()
            
            logger.info(f"区域监控已启动: {area.name}")
            return True
            
        except Exception as e:
            error_msg = f"启动区域监控失败: {area.name}, {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def stop_monitor_area(self, area_id: str) -> bool:
        """停止监控区域
        
        Args:
            area_id: 区域ID
            
        Returns:
            bool: 是否成功停止
        """
        # 检查是否在监控
        if area_id not in self._monitor_threads:
            return False
        
        try:
            # 获取线程
            thread = self._monitor_threads[area_id]
            
            # 移除线程记录
            del self._monitor_threads[area_id]
            
            # 线程会自动检测停止事件
            logger.info(f"区域监控已停止: {area_id}")
            return True
            
        except Exception as e:
            error_msg = f"停止区域监控失败: {area_id}, {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def save_config(self) -> bool:
        """保存配置"""
        return self._save_config()
    
    def reload_config(self) -> bool:
        """重新加载配置"""
        return self._load_config()
    
    def _save_config(self) -> bool:
        """保存配置到文件"""
        try:
            # 保存监控引擎配置
            engine_config = {
                'config': self.config,
                'areas': {area_id: area.to_dict() for area_id, area in self.areas.items()},
            }
            
            # 保存到文件
            with open(os.path.join(self.config_dir, 'engine_config.json'), 'w', encoding='utf-8') as f:
                json.dump(engine_config, f, ensure_ascii=False, indent=2)
            
            # 保存规则配置
            rule_config = {
                'rules': {rule_id: rule.to_dict() for rule_id, rule in self.rule_matcher.get_all_rules().items()},
                'rule_combination': self.rule_matcher.rule_combination,
                'custom_expression': self.rule_matcher.custom_expression,
            }
            
            with open(os.path.join(self.config_dir, 'rule_config.json'), 'w', encoding='utf-8') as f:
                json.dump(rule_config, f, ensure_ascii=False, indent=2)
            
            # 保存动作配置
            action_config = self.action_executor.to_dict()
            
            with open(os.path.join(self.config_dir, 'action_config.json'), 'w', encoding='utf-8') as f:
                json.dump(action_config, f, ensure_ascii=False, indent=2)
            
            # 保存任务配置
            task_config = self.task_scheduler.to_dict()
            
            with open(os.path.join(self.config_dir, 'task_config.json'), 'w', encoding='utf-8') as f:
                json.dump(task_config, f, ensure_ascii=False, indent=2)
            
            logger.info("配置已保存")
            return True
            
        except Exception as e:
            error_msg = f"保存配置失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def _load_config(self) -> bool:
        """从文件加载配置"""
        try:
            # 加载监控引擎配置
            engine_config_path = os.path.join(self.config_dir, 'engine_config.json')
            if os.path.exists(engine_config_path):
                with open(engine_config_path, 'r', encoding='utf-8') as f:
                    engine_config = json.load(f)
                
                # 更新配置
                if 'config' in engine_config:
                    self.set_config(engine_config['config'])
                
                # 加载监控区域
                if 'areas' in engine_config:
                    for area_data in engine_config['areas'].values():
                        area = MonitorArea.from_dict(area_data)
                        self.areas[area.id] = area
            
            # 加载规则配置
            rule_config_path = os.path.join(self.config_dir, 'rule_config.json')
            if os.path.exists(rule_config_path):
                with open(rule_config_path, 'r', encoding='utf-8') as f:
                    rule_config = json.load(f)
                
                # 加载规则
                if 'rules' in rule_config:
                    for rule_data in rule_config['rules'].values():
                        rule = Rule.from_dict(rule_data)
                        self.rule_matcher.add_rule(rule)
                
                # 设置规则组合方式
                if 'rule_combination' in rule_config:
                    self.rule_matcher.set_rule_combination(rule_config['rule_combination'])
                
                # 设置自定义表达式
                if 'custom_expression' in rule_config:
                    self.rule_matcher.set_custom_expression(rule_config['custom_expression'])
            
            # 加载动作配置
            action_config_path = os.path.join(self.config_dir, 'action_config.json')
            if os.path.exists(action_config_path):
                with open(action_config_path, 'r', encoding='utf-8') as f:
                    action_config = json.load(f)
                
                # 从字典创建动作执行器
                executor = ActionExecutor.from_dict(action_config)
                
                # 更新配置
                self.action_executor.set_config(executor.config)
                
                # 加载动作
                for action_id, action in executor.get_all_actions().items():
                    self.action_executor.add_action(action)
                
                # 加载序列
                for sequence_id, action_ids in executor.sequences.items():
                    self.action_executor.create_sequence(sequence_id, action_ids)
            
            # 加载任务配置
            task_config_path = os.path.join(self.config_dir, 'task_config.json')
            if os.path.exists(task_config_path):
                with open(task_config_path, 'r', encoding='utf-8') as f:
                    task_config = json.load(f)
                
                # 从字典创建任务调度器
                scheduler = TaskScheduler.from_dict(task_config)
                
                # 更新配置
                self.task_scheduler.set_config(scheduler.config)
                
                # 加载任务
                for task_id, task in scheduler.get_all_tasks().items():
                    self.task_scheduler.add_task(task)
            
            logger.info("配置已加载")
            
            # 如果配置为自动启动，则启动引擎
            if self.config.get('auto_start', False):
                self.start()
                
            return True
            
        except Exception as e:
            error_msg = f"加载配置失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def _monitor_area_thread(self, area_id: str) -> None:
        """监控区域线程
        
        Args:
            area_id: 区域ID
        """
        area = self.get_area(area_id)
        if not area:
            return
        
        logger.info(f"区域监控线程已启动: {area.name}")
        
        while not self._stop_event.is_set():
            try:
                # 获取配置
                refresh_rate = area.config.get('refresh_rate', 1000)
                
                # 设置OCR配置
                ocr_config = {
                    'language': area.config.get('ocr_language', 'chi_sim'),
                    'preprocess': area.config.get('preprocessing', True),
                }
                self.text_recognizer.set_config({'ocr': ocr_config})
                
                # 识别文本
                text, details = self.text_recognizer.recognize_area(area.rect)
                
                # 更新状态
                area.last_text = text
                area.last_capture_time = datetime.now()
                
                # 发送信号
                self.text_recognized.emit(area_id, text, details)
                
                # 检查规则匹配
                self._check_rules(area, text)
                
                # 保存图像
                if area.config.get('save_images', False):
                    self._save_area_image(area)
                
                # 等待下一次刷新
                self._stop_event.wait(refresh_rate / 1000)
                
            except Exception as e:
                error_msg = f"区域监控异常: {area.name}, {e}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                time.sleep(1.0)  # 发生错误时短暂暂停
        
        logger.info(f"区域监控线程已退出: {area.name}")
    
    def _check_rules(self, area: MonitorArea, text: str) -> None:
        """检查规则匹配
        
        Args:
            area: 监控区域
            text: 识别的文本
        """
        # 检查规则匹配
        for rule_id in area.rule_ids:
            rule = self.rule_matcher.get_rule(rule_id)
            if rule and rule.match(text):
                # 匹配成功，记录并发送信号
                area.match_count += 1
                
                # 匹配信息
                match_info = {
                    'area_id': area.id,
                    'rule_id': rule_id,
                    'text': text,
                    'time': datetime.now().isoformat(),
                    'count': area.match_count
                }
                
                # 发送信号
                self.rule_matched.emit(area.id, rule_id, match_info)
                
                # 触发事件
                self.task_scheduler.trigger_event('rule_matched', {
                    'area_id': area.id,
                    'rule_id': rule_id,
                    'text': text
                })
                
                logger.info(f"规则匹配成功: {rule_id} in {area.name}")
    
    def _save_area_image(self, area: MonitorArea) -> None:
        """保存区域图像
        
        Args:
            area: 监控区域
        """
        try:
            # 确保保存目录存在
            save_dir = area.config.get('save_dir', './captures')
            os.makedirs(save_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{area.id}_{timestamp}.png"
            filepath = os.path.join(save_dir, filename)
            
            # 捕获图像
            image = self.text_recognizer.screen_capture.capture_area(area.rect)
            
            # 保存图像
            self.text_recognizer.screen_capture.save_image(image, filepath)
            
            logger.debug(f"区域图像已保存: {filepath}")
            
        except Exception as e:
            logger.error(f"保存区域图像失败: {e}")
    
    def _capture_area_callback(self, area_id: str = None) -> Dict[str, Any]:
        """捕获区域回调函数
        
        Args:
            area_id: 区域ID，为None时捕获所有区域
            
        Returns:
            Dict[str, Any]: 捕获结果
        """
        results = {}
        
        if area_id:
            # 捕获指定区域
            area = self.get_area(area_id)
            if area:
                text, details = self.text_recognizer.recognize_area(area.rect)
                results[area_id] = {
                    'text': text,
                    'details': details,
                    'time': datetime.now().isoformat()
                }
        else:
            # 捕获所有区域
            for area_id, area in self.areas.items():
                if area.enabled:
                    text, details = self.text_recognizer.recognize_area(area.rect)
                    results[area_id] = {
                        'text': text,
                        'details': details,
                        'time': datetime.now().isoformat()
                    }
        
        return results
    
    def _on_text_recognized(self, text: str, details: Dict[str, Any]) -> None:
        """文本识别信号处理
        
        Args:
            text: 识别的文本
            details: 详细信息
        """
        # 这里处理文本识别器发出的信号
        pass
    
    def _on_error(self, error: str) -> None:
        """错误信号处理
        
        Args:
            error: 错误信息
        """
        # 转发错误信号
        self.error_occurred.emit(error)
