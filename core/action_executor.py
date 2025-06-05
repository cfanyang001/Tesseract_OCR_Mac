import os
import time
import subprocess
import threading
import pyautogui
import keyboard
import sys
from typing import Dict, Any, List, Callable, Optional, Union
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
from loguru import logger


class Action:
    """动作类，表示一个自动化动作"""
    
    # 动作类型
    TYPE_KEYBOARD = 'keyboard'        # 键盘动作
    TYPE_MOUSE = 'mouse'              # 鼠标动作
    TYPE_DELAY = 'delay'              # 延迟动作
    TYPE_COMMAND = 'command'          # 命令动作
    TYPE_SCRIPT = 'script'            # 脚本动作
    TYPE_SCREENSHOT = 'screenshot'    # 截图动作
    TYPE_NOTIFICATION = 'notification'  # 通知动作
    
    # 鼠标动作类型
    MOUSE_CLICK = 'click'             # 单击
    MOUSE_DOUBLE_CLICK = 'double_click'  # 双击
    MOUSE_RIGHT_CLICK = 'right_click'  # 右键单击
    MOUSE_MOVE = 'move'               # 移动
    MOUSE_DRAG = 'drag'               # 拖拽
    MOUSE_SCROLL = 'scroll'           # 滚动
    
    # 键盘动作类型
    KEYBOARD_TYPE = 'type'            # 输入文本
    KEYBOARD_PRESS = 'press'          # 按下按键
    KEYBOARD_HOTKEY = 'hotkey'        # 快捷键
    
    def __init__(self, action_id: str = None, action_type: str = None, 
                 params: Dict[str, Any] = None, name: str = ''):
        """初始化动作
        
        Args:
            action_id: 动作ID，为None时自动生成
            action_type: 动作类型
            params: 动作参数
            name: 动作名称
        """
        from uuid import uuid4
        self.id = action_id or str(uuid4())
        self.type = action_type
        self.params = params or {}
        self.name = name or f"动作 {self.id[:8]}"
        self.last_executed = None  # 上次执行时间
    
    def to_dict(self) -> Dict[str, Any]:
        """将动作转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'params': self.params,
            'name': self.name,
            'last_executed': self.last_executed.isoformat() if self.last_executed else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """从字典创建动作"""
        action = cls(
            action_id=data['id'],
            action_type=data['type'],
            params=data.get('params', {}),
            name=data.get('name', '')
        )
        
        if data.get('last_executed'):
            action.last_executed = datetime.fromisoformat(data['last_executed'])
        
        return action


class ActionExecutor(QObject):
    """动作执行器，用于执行自动化动作"""
    
    # 信号
    action_started = pyqtSignal(str, dict)  # 动作开始信号 (动作ID, 参数)
    action_completed = pyqtSignal(str, bool, str)  # 动作完成信号 (动作ID, 是否成功, 结果)
    action_sequence_completed = pyqtSignal(bool, str)  # 动作序列完成信号 (是否成功, 结果)
    
    def __init__(self):
        """初始化动作执行器"""
        super().__init__()
        
        # 动作字典
        self.actions = {}  # {action_id: Action}
        
        # 动作序列
        self.sequences = {}  # {sequence_id: List[str]}
        
        # 执行状态
        self._running = False
        self._stop_event = threading.Event()
        self._current_sequence = None
        self._current_action = None
        
        # 配置
        self.config = {
            'default_delay': 0.5,  # 默认延迟 (秒)
            'mouse_speed': 1.0,    # 鼠标移动速度
            'safe_mode': True,     # 安全模式（防止危险操作）
            'screenshot_dir': './screenshots',  # 截图保存目录
            'allow_commands': False,  # 是否允许执行命令
            'command_timeout': 10.0   # 命令超时时间 (秒)
        }
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """设置配置"""
        self.config.update(config)
    
    def add_action(self, action: Action) -> None:
        """添加动作
        
        Args:
            action: 动作对象
        """
        self.actions[action.id] = action
    
    def remove_action(self, action_id: str) -> bool:
        """移除动作
        
        Args:
            action_id: 动作ID
            
        Returns:
            bool: 是否成功移除
        """
        if action_id in self.actions:
            del self.actions[action_id]
            # 从所有序列中移除
            for sequence_id, action_ids in self.sequences.items():
                if action_id in action_ids:
                    self.sequences[sequence_id].remove(action_id)
            return True
        return False
    
    def get_action(self, action_id: str) -> Optional[Action]:
        """获取动作
        
        Args:
            action_id: 动作ID
            
        Returns:
            Optional[Action]: 动作对象，不存在时返回None
        """
        return self.actions.get(action_id)
    
    def get_all_actions(self) -> Dict[str, Action]:
        """获取所有动作
        
        Returns:
            Dict[str, Action]: 动作字典
        """
        return self.actions.copy()
    
    def create_sequence(self, sequence_id: str, action_ids: List[str] = None) -> None:
        """创建动作序列
        
        Args:
            sequence_id: 序列ID
            action_ids: 动作ID列表
        """
        self.sequences[sequence_id] = action_ids or []
    
    def remove_sequence(self, sequence_id: str) -> bool:
        """移除动作序列
        
        Args:
            sequence_id: 序列ID
            
        Returns:
            bool: 是否成功移除
        """
        if sequence_id in self.sequences:
            del self.sequences[sequence_id]
            return True
        return False
    
    def add_to_sequence(self, sequence_id: str, action_id: str) -> bool:
        """添加动作到序列
        
        Args:
            sequence_id: 序列ID
            action_id: 动作ID
            
        Returns:
            bool: 是否成功添加
        """
        if sequence_id in self.sequences and action_id in self.actions:
            self.sequences[sequence_id].append(action_id)
            return True
        return False
    
    def remove_from_sequence(self, sequence_id: str, action_id: str) -> bool:
        """从序列中移除动作
        
        Args:
            sequence_id: 序列ID
            action_id: 动作ID
            
        Returns:
            bool: 是否成功移除
        """
        if sequence_id in self.sequences and action_id in self.sequences[sequence_id]:
            self.sequences[sequence_id].remove(action_id)
            return True
        return False
    
    def reorder_sequence(self, sequence_id: str, action_ids: List[str]) -> bool:
        """重新排序序列
        
        Args:
            sequence_id: 序列ID
            action_ids: 新的动作ID列表
            
        Returns:
            bool: 是否成功重排序
        """
        if (sequence_id in self.sequences and 
                all(action_id in self.actions for action_id in action_ids)):
            self.sequences[sequence_id] = action_ids
            return True
        return False
    
    def execute_action(self, action_id: str) -> bool:
        """执行单个动作
        
        Args:
            action_id: 动作ID
            
        Returns:
            bool: 是否成功执行
        """
        action = self.get_action(action_id)
        if not action:
            logger.error(f"动作不存在: {action_id}")
            return False
        
        try:
            # 设置当前动作
            self._current_action = action_id
            
            # 发送动作开始信号
            self.action_started.emit(action_id, action.params)
            
            # 执行动作
            result = self._execute_action_by_type(action)
            
            # 更新执行时间
            action.last_executed = datetime.now()
            
            # 发送动作完成信号
            self.action_completed.emit(action_id, True, result)
            
            logger.info(f"动作执行成功: {action.name}")
            return True
            
        except Exception as e:
            logger.error(f"动作执行失败: {e}")
            self.action_completed.emit(action_id, False, str(e))
            return False
        finally:
            self._current_action = None
    
    def execute_sequence(self, sequence_id: str) -> bool:
        """执行动作序列
        
        Args:
            sequence_id: 序列ID
            
        Returns:
            bool: 是否成功执行
        """
        if sequence_id not in self.sequences:
            logger.error(f"序列不存在: {sequence_id}")
            return False
        
        if self._running:
            logger.warning("已有序列正在执行")
            return False
        
        try:
            # 设置执行状态
            self._running = True
            self._current_sequence = sequence_id
            self._stop_event.clear()
            
            # 创建并启动执行线程
            thread = threading.Thread(
                target=self._execute_sequence_thread,
                args=(sequence_id,),
                daemon=True
            )
            thread.start()
            
            logger.info(f"序列开始执行: {sequence_id}")
            return True
            
        except Exception as e:
            logger.error(f"序列执行失败: {e}")
            self._running = False
            self._current_sequence = None
            self.action_sequence_completed.emit(False, str(e))
            return False
    
    def stop_execution(self) -> None:
        """停止执行"""
        if self._running:
            self._stop_event.set()
            logger.info("正在停止执行...")
    
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running
    
    def get_current_sequence(self) -> Optional[str]:
        """获取当前正在执行的序列ID"""
        return self._current_sequence
    
    def get_current_action(self) -> Optional[str]:
        """获取当前正在执行的动作ID"""
        return self._current_action
    
    def _execute_sequence_thread(self, sequence_id: str) -> None:
        """执行序列线程
        
        Args:
            sequence_id: 序列ID
        """
        success = True
        result = "序列执行完成"
        
        try:
            # 获取动作ID列表
            action_ids = self.sequences[sequence_id]
            
            # 执行每个动作
            for i, action_id in enumerate(action_ids):
                # 检查是否停止
                if self._stop_event.is_set():
                    success = False
                    result = "序列执行被中断"
                    break
                
                # 执行动作
                if not self.execute_action(action_id):
                    success = False
                    result = f"动作 {i+1}/{len(action_ids)} 执行失败"
                    break
                
                # 延迟
                if i < len(action_ids) - 1:
                    time.sleep(self.config['default_delay'])
                    
        except Exception as e:
            success = False
            result = f"序列执行异常: {e}"
            logger.error(result)
        
        finally:
            # 重置执行状态
            self._running = False
            self._current_sequence = None
            
            # 发送完成信号
            self.action_sequence_completed.emit(success, result)
    
    def _execute_action_by_type(self, action: Action) -> str:
        """根据类型执行动作
        
        Args:
            action: 动作对象
            
        Returns:
            str: 执行结果
        """
        # 根据动作类型执行
        if action.type == Action.TYPE_KEYBOARD:
            return self._execute_keyboard_action(action)
        elif action.type == Action.TYPE_MOUSE:
            return self._execute_mouse_action(action)
        elif action.type == Action.TYPE_DELAY:
            return self._execute_delay_action(action)
        elif action.type == Action.TYPE_COMMAND:
            return self._execute_command_action(action)
        elif action.type == Action.TYPE_SCRIPT:
            return self._execute_script_action(action)
        elif action.type == Action.TYPE_SCREENSHOT:
            return self._execute_screenshot_action(action)
        elif action.type == Action.TYPE_NOTIFICATION:
            return self._execute_notification_action(action)
        else:
            raise ValueError(f"不支持的动作类型: {action.type}")
    
    def _execute_keyboard_action(self, action: Action) -> str:
        """执行键盘动作
        
        Args:
            action: 动作对象
            
        Returns:
            str: 执行结果
        """
        params = action.params
        keyboard_type = params.get('keyboard_type', Action.KEYBOARD_TYPE)
        
        if keyboard_type == Action.KEYBOARD_TYPE:
            # 输入文本
            text = params.get('text', '')
            interval = params.get('interval', 0.0)
            pyautogui.write(text, interval=interval)
            return f"输入文本: {text}"
            
        elif keyboard_type == Action.KEYBOARD_PRESS:
            # 按下按键
            key = params.get('key', '')
            pyautogui.press(key)
            return f"按下按键: {key}"
            
        elif keyboard_type == Action.KEYBOARD_HOTKEY:
            # 快捷键
            keys = params.get('keys', [])
            if not keys:
                raise ValueError("未指定快捷键")
            pyautogui.hotkey(*keys)
            return f"使用快捷键: {'+'.join(keys)}"
            
        else:
            raise ValueError(f"不支持的键盘动作类型: {keyboard_type}")
    
    def _execute_mouse_action(self, action: Action) -> str:
        """执行鼠标动作
        
        Args:
            action: 动作对象
            
        Returns:
            str: 执行结果
        """
        params = action.params
        mouse_type = params.get('mouse_type', Action.MOUSE_CLICK)
        
        # 获取鼠标位置
        x = params.get('x', None)
        y = params.get('y', None)
        
        # 如果指定了位置，先移动鼠标
        if x is not None and y is not None:
            duration = params.get('duration', 0.5) * self.config['mouse_speed']
            pyautogui.moveTo(x, y, duration=duration)
        
        if mouse_type == Action.MOUSE_CLICK:
            # 单击
            button = params.get('button', 'left')
            clicks = params.get('clicks', 1)
            interval = params.get('interval', 0.0)
            pyautogui.click(button=button, clicks=clicks, interval=interval)
            return f"鼠标单击: 位置({x}, {y}), 按钮={button}, 次数={clicks}, 间隔={interval}秒"
            
        elif mouse_type == Action.MOUSE_DOUBLE_CLICK:
            # 双击
            button = params.get('button', 'left')
            pyautogui.doubleClick(button=button)
            return f"鼠标双击: 位置({x}, {y}), 按钮={button}"
            
        elif mouse_type == Action.MOUSE_RIGHT_CLICK:
            # 右键单击
            pyautogui.rightClick()
            return f"鼠标右击: 位置({x}, {y})"
            
        elif mouse_type == Action.MOUSE_MOVE:
            # 移动（已在前面处理）
            return f"鼠标移动: 位置({x}, {y})"
            
        elif mouse_type == Action.MOUSE_DRAG:
            # 拖拽
            to_x = params.get('to_x', x)
            to_y = params.get('to_y', y)
            button = params.get('button', 'left')
            duration = params.get('duration', 0.5) * self.config['mouse_speed']
            pyautogui.dragTo(to_x, to_y, duration=duration, button=button)
            return f"鼠标拖拽: 从({x}, {y})到({to_x}, {to_y})"
            
        elif mouse_type == Action.MOUSE_SCROLL:
            # 滚动
            amount = params.get('amount', 10)
            pyautogui.scroll(amount)
            return f"鼠标滚动: 数量={amount}, 位置({x}, {y})"
            
        else:
            raise ValueError(f"不支持的鼠标动作类型: {mouse_type}")
    
    def _execute_delay_action(self, action: Action) -> str:
        """执行延迟动作
        
        Args:
            action: 动作对象
            
        Returns:
            str: 执行结果
        """
        # 获取延迟时间
        delay = action.params.get('delay', self.config['default_delay'])
        
        # 执行延迟
        time.sleep(delay)
        
        return f"延迟: {delay}秒"
    
    def _execute_command_action(self, action: Action) -> str:
        """执行命令动作
        
        Args:
            action: 动作对象
            
        Returns:
            str: 执行结果
        """
        # 检查是否允许执行命令
        if not self.config['allow_commands']:
            raise PermissionError("禁止执行命令，请在配置中启用")
        
        # 获取命令
        command = action.params.get('command', '')
        shell = action.params.get('shell', True)
        
        # 检查安全模式
        if self.config['safe_mode']:
            # 禁止执行危险命令
            dangerous_commands = ['rm', 'mkfs', 'dd', 'format', 'del', 'rd']
            if any(cmd in command.lower() for cmd in dangerous_commands):
                raise PermissionError(f"禁止执行危险命令: {command}")
        
        # 执行命令
        timeout = action.params.get('timeout', self.config['command_timeout'])
        result = subprocess.run(
            command, 
            shell=shell, 
            capture_output=True, 
            text=True,
            timeout=timeout
        )
        
        # 检查结果
        if result.returncode != 0:
            logger.warning(f"命令执行返回非零值: {result.returncode}, 错误: {result.stderr}")
        
        return f"命令执行: {command}, 返回码: {result.returncode}, 输出: {result.stdout[:200]}"
    
    def _execute_script_action(self, action: Action) -> str:
        """执行脚本动作
        
        Args:
            action: 脚本动作对象
            
        Returns:
            str: 执行结果
        """
        try:
            script_content = action.params.get('content')
            if not script_content:
                return "脚本内容为空"
            
            # 检查是否是路径
            is_file = action.params.get('is_file', False)
            if is_file:
                # 作为文件路径处理
                if not os.path.exists(script_content):
                    return f"脚本文件不存在: {script_content}"
                
                # 检查文件后缀
                if not script_content.endswith('.py'):
                    return f"不支持的脚本类型: {script_content}"
                
                # 执行脚本文件
                try:
                    result = subprocess.check_output(
                        [sys.executable, script_content],
                        stderr=subprocess.STDOUT,
                        timeout=self.config.get('command_timeout', 10.0),
                        universal_newlines=True
                    )
                    return f"脚本执行成功: {result}"
                except subprocess.CalledProcessError as e:
                    return f"脚本执行失败: {e.output}"
                except subprocess.TimeoutExpired:
                    return "脚本执行超时"
            else:
                # 作为脚本内容处理
                try:
                    # 创建临时执行环境
                    local_vars = {}
                    # 增加访问动作执行器的能力
                    local_vars['executor'] = self
                    local_vars['pyautogui'] = pyautogui
                    local_vars['keyboard'] = keyboard
                    local_vars['time'] = time
                    local_vars['os'] = os
                    
                    # 执行脚本
                    exec(script_content, {}, local_vars)
                    
                    # 获取结果
                    result = local_vars.get('result', '脚本执行成功')
                    return str(result)
                except Exception as e:
                    return f"脚本执行异常: {str(e)}"
        except Exception as e:
            logger.error(f"执行脚本动作异常: {e}")
            return f"执行脚本动作异常: {str(e)}"
    
    def _execute_screenshot_action(self, action: Action) -> str:
        """执行截图动作
        
        Args:
            action: 动作对象
            
        Returns:
            str: 执行结果
        """
        # 获取参数
        region = action.params.get('region', None)  # (x, y, width, height)
        path = action.params.get('path', None)
        
        # 设置默认路径
        if not path:
            os.makedirs(self.config['screenshot_dir'], exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = os.path.join(self.config['screenshot_dir'], f'screenshot_{timestamp}.png')
        
        # 截图
        screenshot = pyautogui.screenshot(region=region)
        screenshot.save(path)
        
        return f"截图保存: {path}"
    
    def _execute_notification_action(self, action: Action) -> str:
        """执行通知动作
        
        Args:
            action: 动作对象
            
        Returns:
            str: 执行结果
        """
        # 获取参数
        title = action.params.get('title', '通知')
        message = action.params.get('message', '')
        sound = action.params.get('sound', True)
        
        # 发送通知
        try:
            # 在macOS上使用osascript
            if os.name == 'posix':
                script = f'display notification "{message}" with title "{title}"'
                if sound:
                    script += ' sound name "Ping"'
                subprocess.run(['osascript', '-e', script], capture_output=True)
            # 在Windows上使用toast
            elif os.name == 'nt':
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=5, threaded=True)
            else:
                logger.warning(f"不支持的操作系统: {os.name}")
                
            return f"通知: {title} - {message}"
            
        except Exception as e:
            logger.error(f"通知失败: {e}")
            return f"通知失败: {e}"
    
    def to_dict(self) -> Dict[str, Any]:
        """将动作执行器转换为字典"""
        return {
            'actions': {action_id: action.to_dict() for action_id, action in self.actions.items()},
            'sequences': self.sequences.copy(),
            'config': self.config.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionExecutor':
        """从字典创建动作执行器"""
        executor = cls()
        
        # 设置配置
        if 'config' in data:
            executor.set_config(data['config'])
        
        # 加载动作
        actions_data = data.get('actions', {})
        for action_data in actions_data.values():
            action = Action.from_dict(action_data)
            executor.add_action(action)
        
        # 加载序列
        sequences_data = data.get('sequences', {})
        for sequence_id, action_ids in sequences_data.items():
            executor.create_sequence(sequence_id, action_ids)
        
        return executor
