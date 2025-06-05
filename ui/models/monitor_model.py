from typing import Dict, List, Any, Tuple
from PyQt5.QtCore import QRect

from ui.models.base_model import BaseModel


class Rule:
    """规则类，表示一个文本匹配规则"""
    
    TYPE_CONTAINS = 'contains'       # 包含文本
    TYPE_EXACT = 'exact'             # 精确匹配
    TYPE_REGEX = 'regex'             # 正则表达式
    TYPE_NUMERIC = 'numeric'         # 数值比较
    
    def __init__(self, rule_id: str, rule_type: str, content: str, 
                 case_sensitive: bool = False, trim: bool = True):
        self.id = rule_id                      # 规则ID
        self.type = rule_type                  # 规则类型
        self.content = content                 # 规则内容
        self.case_sensitive = case_sensitive   # 是否区分大小写
        self.trim = trim                       # 是否忽略首尾空格
    
    def to_dict(self) -> Dict[str, Any]:
        """将规则转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'case_sensitive': self.case_sensitive,
            'trim': self.trim
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """从字典创建规则"""
        return cls(
            rule_id=data['id'],
            rule_type=data['type'],
            content=data['content'],
            case_sensitive=data.get('case_sensitive', False),
            trim=data.get('trim', True)
        )


class Action:
    """动作类，表示一个自动化动作"""
    
    TYPE_NOTIFICATION = 'notification'   # 系统通知
    TYPE_KEYBOARD = 'keyboard'           # 键盘输入
    TYPE_MOUSE = 'mouse'                 # 鼠标点击
    TYPE_SCRIPT = 'script'               # 运行脚本
    TYPE_CUSTOM = 'custom'               # 自定义动作
    
    def __init__(self, action_id: str, action_type: str, name: str, 
                 params: Dict[str, Any] = None, description: str = ''):
        self.id = action_id              # 动作ID
        self.type = action_type          # 动作类型
        self.name = name                 # 动作名称
        self.params = params or {}       # 动作参数
        self.description = description   # 动作描述
    
    def to_dict(self) -> Dict[str, Any]:
        """将动作转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'params': self.params,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        """从字典创建动作"""
        return cls(
            action_id=data['id'],
            action_type=data['type'],
            name=data['name'],
            params=data.get('params', {}),
            description=data.get('description', '')
        )


class MonitorModel(BaseModel):
    """监控模型类，存储监控规则和动作"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化默认数据
        self._data = {
            'rules': {},                  # 规则字典 {rule_id: Rule}
            'actions': {},                # 动作字典 {action_id: Action}
            'rule_combination': 'AND',    # 规则组合方式 (AND, OR, CUSTOM)
            'custom_expression': '',      # 自定义规则表达式
            'trigger_condition': 'match', # 触发条件 (match, unmatch, change)
            'trigger_delay': 0,           # 触发延迟 (秒)
            'trigger_actions': []         # 触发动作ID列表
        }
    
    def add_rule(self, rule: Rule) -> None:
        """添加规则"""
        rules = self.get('rules').copy()
        rules[rule.id] = rule
        self.set('rules', rules)
    
    def remove_rule(self, rule_id: str) -> None:
        """移除规则"""
        rules = self.get('rules').copy()
        if rule_id in rules:
            del rules[rule_id]
            self.set('rules', rules)
    
    def get_rule(self, rule_id: str) -> Rule:
        """获取规则"""
        return self.get('rules').get(rule_id)
    
    def get_all_rules(self) -> Dict[str, Rule]:
        """获取所有规则"""
        return self.get('rules')
    
    def add_action(self, action: Action) -> None:
        """添加动作"""
        actions = self.get('actions').copy()
        actions[action.id] = action
        self.set('actions', actions)
    
    def remove_action(self, action_id: str) -> None:
        """移除动作"""
        actions = self.get('actions').copy()
        if action_id in actions:
            del actions[action_id]
            self.set('actions', actions)
    
    def get_action(self, action_id: str) -> Action:
        """获取动作"""
        return self.get('actions').get(action_id)
    
    def get_all_actions(self) -> Dict[str, Action]:
        """获取所有动作"""
        return self.get('actions')
    
    def set_rule_combination(self, combination: str) -> None:
        """设置规则组合方式"""
        self.set('rule_combination', combination)
    
    def get_rule_combination(self) -> str:
        """获取规则组合方式"""
        return self.get('rule_combination')
    
    def set_custom_expression(self, expression: str) -> None:
        """设置自定义规则表达式"""
        self.set('custom_expression', expression)
    
    def get_custom_expression(self) -> str:
        """获取自定义规则表达式"""
        return self.get('custom_expression')
    
    def set_trigger_condition(self, condition: str) -> None:
        """设置触发条件"""
        self.set('trigger_condition', condition)
    
    def get_trigger_condition(self) -> str:
        """获取触发条件"""
        return self.get('trigger_condition')
    
    def set_trigger_delay(self, delay: int) -> None:
        """设置触发延迟 (秒)"""
        self.set('trigger_delay', max(0, min(60, delay)))
    
    def get_trigger_delay(self) -> int:
        """获取触发延迟 (秒)"""
        return self.get('trigger_delay')
    
    def set_trigger_actions(self, action_ids: List[str]) -> None:
        """设置触发动作ID列表"""
        self.set('trigger_actions', action_ids)
    
    def get_trigger_actions(self) -> List[str]:
        """获取触发动作ID列表"""
        return self.get('trigger_actions')
    
    def add_trigger_action(self, action_id: str) -> None:
        """添加触发动作ID"""
        actions = self.get('trigger_actions').copy()
        if action_id not in actions:
            actions.append(action_id)
            self.set('trigger_actions', actions)
    
    def remove_trigger_action(self, action_id: str) -> None:
        """移除触发动作ID"""
        actions = self.get('trigger_actions').copy()
        if action_id in actions:
            actions.remove(action_id)
            self.set('trigger_actions', actions) 