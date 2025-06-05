import re
import uuid
from typing import Dict, Any, List, Callable, Optional, Union
from datetime import datetime

from core.utils.text_processing import (
    text_contains, text_matches, text_matches_regex,
    extract_numbers, extract_dates, extract_emails, extract_urls
)
from loguru import logger


class Rule:
    """规则类，表示一个文本匹配规则"""
    
    # 规则类型
    TYPE_CONTAINS = 'contains'       # 包含文本
    TYPE_EXACT = 'exact'             # 精确匹配
    TYPE_REGEX = 'regex'             # 正则表达式
    TYPE_NUMERIC = 'numeric'         # 数值比较
    TYPE_NOT_CONTAINS = 'not_contains'  # 不包含文本
    TYPE_CHANGED = 'changed'         # 文本变化
    
    # 数值比较操作符
    OP_EQ = 'eq'    # 等于
    OP_NE = 'ne'    # 不等于
    OP_GT = 'gt'    # 大于
    OP_GE = 'ge'    # 大于等于
    OP_LT = 'lt'    # 小于
    OP_LE = 'le'    # 小于等于
    
    def __init__(self, rule_id: str = None, rule_type: str = TYPE_CONTAINS, 
                 content: str = '', params: Dict[str, Any] = None):
        """初始化规则
        
        Args:
            rule_id: 规则ID，为None时自动生成
            rule_type: 规则类型
            content: 规则内容
            params: 规则参数
        """
        self.id = rule_id or str(uuid.uuid4())
        self.type = rule_type
        self.content = content
        self.params = params or {}
        self.last_match_time = None  # 上次匹配时间
        self.last_match_text = None  # 上次匹配文本
    
    def match(self, text: str) -> bool:
        """匹配文本
        
        Args:
            text: 要匹配的文本
            
        Returns:
            bool: 是否匹配
        """
        result = False
        case_sensitive = self.params.get('case_sensitive', False)
        
        try:
            # 根据规则类型进行匹配
            if self.type == self.TYPE_CONTAINS:
                result = text_contains(text, self.content, case_sensitive)
                
            elif self.type == self.TYPE_EXACT:
                result = text_matches(text, self.content, case_sensitive)
                
            elif self.type == self.TYPE_REGEX:
                result = text_matches_regex(text, self.content, case_sensitive)
                
            elif self.type == self.TYPE_NUMERIC:
                # 提取文本中的数字
                numbers = extract_numbers(text)
                if not numbers:
                    return False
                
                # 获取第一个数字进行比较
                try:
                    num = float(numbers[0])
                    target = float(self.content)
                    operator = self.params.get('operator', self.OP_EQ)
                    
                    if operator == self.OP_EQ:
                        result = num == target
                    elif operator == self.OP_NE:
                        result = num != target
                    elif operator == self.OP_GT:
                        result = num > target
                    elif operator == self.OP_GE:
                        result = num >= target
                    elif operator == self.OP_LT:
                        result = num < target
                    elif operator == self.OP_LE:
                        result = num <= target
                except (ValueError, IndexError):
                    result = False
                    
            elif self.type == self.TYPE_NOT_CONTAINS:
                result = not text_contains(text, self.content, case_sensitive)
                
            elif self.type == self.TYPE_CHANGED:
                # 检查文本是否变化
                if self.last_match_text is None:
                    result = True  # 首次匹配，视为变化
                else:
                    result = text != self.last_match_text
            
            # 更新匹配状态
            if result:
                self.last_match_time = datetime.now()
                self.last_match_text = text
            
            return result
            
        except Exception as e:
            logger.error(f"规则匹配异常: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """将规则转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'params': self.params,
            'last_match_time': self.last_match_time.isoformat() if self.last_match_time else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """从字典创建规则"""
        rule = cls(
            rule_id=data['id'],
            rule_type=data['type'],
            content=data['content'],
            params=data.get('params', {})
        )
        
        if data.get('last_match_time'):
            rule.last_match_time = datetime.fromisoformat(data['last_match_time'])
        
        return rule


class RuleMatcher:
    """规则匹配器，用于匹配文本规则"""
    
    # 规则组合方式
    COMBINE_AND = 'AND'  # 所有规则都匹配
    COMBINE_OR = 'OR'    # 任一规则匹配
    COMBINE_CUSTOM = 'CUSTOM'  # 自定义表达式
    
    def __init__(self):
        """初始化规则匹配器"""
        self.rules = {}  # 规则字典 {rule_id: Rule}
        self.rule_combination = self.COMBINE_AND  # 规则组合方式
        self.custom_expression = ""  # 自定义规则表达式
        self.last_result = False  # 上次匹配结果
        self.last_match_time = None  # 上次匹配时间
    
    def add_rule(self, rule: Rule) -> None:
        """添加规则
        
        Args:
            rule: 规则对象
        """
        self.rules[rule.id] = rule
    
    def remove_rule(self, rule_id: str) -> bool:
        """移除规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 是否成功移除
        """
        if rule_id in self.rules:
            del self.rules[rule_id]
            return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """获取规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            Optional[Rule]: 规则对象，不存在时返回None
        """
        return self.rules.get(rule_id)
    
    def get_all_rules(self) -> Dict[str, Rule]:
        """获取所有规则
        
        Returns:
            Dict[str, Rule]: 规则字典
        """
        return self.rules.copy()
    
    def set_rule_combination(self, combination: str) -> None:
        """设置规则组合方式
        
        Args:
            combination: 规则组合方式 (AND, OR, CUSTOM)
        """
        if combination in (self.COMBINE_AND, self.COMBINE_OR, self.COMBINE_CUSTOM):
            self.rule_combination = combination
    
    def set_custom_expression(self, expression: str) -> None:
        """设置自定义规则表达式
        
        Args:
            expression: 自定义规则表达式
        """
        self.custom_expression = expression
    
    def match(self, text: str) -> bool:
        """匹配文本
        
        Args:
            text: 要匹配的文本
            
        Returns:
            bool: 是否匹配
        """
        if not self.rules:
            return False
        
        try:
            # 根据组合方式进行匹配
            if self.rule_combination == self.COMBINE_AND:
                result = self._match_and(text)
            elif self.rule_combination == self.COMBINE_OR:
                result = self._match_or(text)
            elif self.rule_combination == self.COMBINE_CUSTOM:
                result = self._match_custom(text)
            else:
                result = False
            
            # 更新匹配状态
            self.last_result = result
            if result:
                self.last_match_time = datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"规则匹配异常: {e}")
            return False
    
    def _match_and(self, text: str) -> bool:
        """AND匹配
        
        Args:
            text: 要匹配的文本
            
        Returns:
            bool: 是否匹配
        """
        return all(rule.match(text) for rule in self.rules.values())
    
    def _match_or(self, text: str) -> bool:
        """OR匹配
        
        Args:
            text: 要匹配的文本
            
        Returns:
            bool: 是否匹配
        """
        return any(rule.match(text) for rule in self.rules.values())
    
    def _match_custom(self, text: str) -> bool:
        """自定义表达式匹配
        
        Args:
            text: 要匹配的文本
            
        Returns:
            bool: 是否匹配
        """
        if not self.custom_expression:
            return False
        
        try:
            # 创建规则匹配结果字典
            rule_results = {f"r{rule.id}": rule.match(text) for rule in self.rules.values()}
            
            # 替换表达式中的规则ID
            expr = self.custom_expression
            for rule_id, result in rule_results.items():
                expr = expr.replace(rule_id, str(result).lower())
            
            # 执行表达式
            return bool(eval(expr))
            
        except Exception as e:
            logger.error(f"自定义表达式匹配异常: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """将规则匹配器转换为字典"""
        return {
            'rules': {rule_id: rule.to_dict() for rule_id, rule in self.rules.items()},
            'rule_combination': self.rule_combination,
            'custom_expression': self.custom_expression,
            'last_result': self.last_result,
            'last_match_time': self.last_match_time.isoformat() if self.last_match_time else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RuleMatcher':
        """从字典创建规则匹配器"""
        matcher = cls()
        
        # 加载规则
        rules_data = data.get('rules', {})
        for rule_data in rules_data.values():
            rule = Rule.from_dict(rule_data)
            matcher.add_rule(rule)
        
        # 设置规则组合方式
        matcher.rule_combination = data.get('rule_combination', cls.COMBINE_AND)
        matcher.custom_expression = data.get('custom_expression', '')
        
        # 设置匹配状态
        matcher.last_result = data.get('last_result', False)
        if data.get('last_match_time'):
            matcher.last_match_time = datetime.fromisoformat(data['last_match_time'])
        
        return matcher 