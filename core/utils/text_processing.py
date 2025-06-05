import re
import string
from typing import Dict, List, Any, Tuple


def clean_text(text: str) -> str:
    """清理文本，移除多余的空白字符
    
    Args:
        text: 输入文本
        
    Returns:
        str: 清理后的文本
    """
    # 移除开头和结尾的空白字符
    text = text.strip()
    
    # 将多个空白字符替换为单个空格
    text = re.sub(r'\s+', ' ', text)
    
    return text


def normalize_text(text: str, lowercase: bool = True, remove_punctuation: bool = False) -> str:
    """规范化文本
    
    Args:
        text: 输入文本
        lowercase: 是否转换为小写
        remove_punctuation: 是否移除标点符号
        
    Returns:
        str: 规范化后的文本
    """
    # 清理文本
    text = clean_text(text)
    
    # 转换为小写
    if lowercase:
        text = text.lower()
    
    # 移除标点符号
    if remove_punctuation:
        text = text.translate(str.maketrans('', '', string.punctuation))
    
    return text


def extract_numbers(text: str) -> List[str]:
    """提取文本中的数字
    
    Args:
        text: 输入文本
        
    Returns:
        List[str]: 提取的数字列表
    """
    # 匹配数字 (整数和小数)
    pattern = r'\d+(?:\.\d+)?'
    numbers = re.findall(pattern, text)
    
    return numbers


def extract_dates(text: str) -> List[str]:
    """提取文本中的日期
    
    Args:
        text: 输入文本
        
    Returns:
        List[str]: 提取的日期列表
    """
    # 匹配常见日期格式
    patterns = [
        r'\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?',  # YYYY-MM-DD, YYYY/MM/DD, YYYY年MM月DD日
        r'\d{1,2}[-/月]\d{1,2}[-/日]?,?\s*\d{4}[年]?',  # MM-DD-YYYY, MM/DD/YYYY
        r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}'  # MM-DD-YY, MM/DD/YY
    ]
    
    dates = []
    for pattern in patterns:
        dates.extend(re.findall(pattern, text))
    
    return dates


def extract_emails(text: str) -> List[str]:
    """提取文本中的电子邮件地址
    
    Args:
        text: 输入文本
        
    Returns:
        List[str]: 提取的电子邮件地址列表
    """
    # 匹配电子邮件地址
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(pattern, text)
    
    return emails


def extract_urls(text: str) -> List[str]:
    """提取文本中的URL
    
    Args:
        text: 输入文本
        
    Returns:
        List[str]: 提取的URL列表
    """
    # 匹配URL
    pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    urls = re.findall(pattern, text)
    
    return urls


def extract_phone_numbers(text: str) -> List[str]:
    """提取文本中的电话号码
    
    Args:
        text: 输入文本
        
    Returns:
        List[str]: 提取的电话号码列表
    """
    # 匹配常见电话号码格式
    patterns = [
        r'\d{3}-\d{3,4}-\d{4}',  # 000-000-0000, 000-0000-0000
        r'\d{3}\.\d{3,4}\.\d{4}',  # 000.000.0000, 000.0000.0000
        r'\(\d{3}\)\s*\d{3,4}[-.]?\d{4}',  # (000) 000-0000, (000)000-0000
        r'\d{3}\s*\d{4}\s*\d{4}',  # 000 0000 0000
        r'\+\d{1,3}\s*\d{3,4}\s*\d{3,4}\s*\d{3,4}'  # +00 000 000 0000
    ]
    
    phone_numbers = []
    for pattern in patterns:
        phone_numbers.extend(re.findall(pattern, text))
    
    return phone_numbers


def split_sentences(text: str) -> List[str]:
    """将文本分割为句子
    
    Args:
        text: 输入文本
        
    Returns:
        List[str]: 句子列表
    """
    # 使用正则表达式分割句子
    pattern = r'(?<=[.!?。！？])\s+'
    sentences = re.split(pattern, text)
    
    # 清理句子
    sentences = [clean_text(sentence) for sentence in sentences if sentence.strip()]
    
    return sentences


def text_contains(text: str, pattern: str, case_sensitive: bool = False) -> bool:
    """检查文本是否包含指定模式
    
    Args:
        text: 输入文本
        pattern: 要查找的模式
        case_sensitive: 是否区分大小写
        
    Returns:
        bool: 是否包含
    """
    if not case_sensitive:
        text = text.lower()
        pattern = pattern.lower()
    
    return pattern in text


def text_matches(text: str, pattern: str, case_sensitive: bool = False) -> bool:
    """检查文本是否完全匹配指定模式
    
    Args:
        text: 输入文本
        pattern: 要匹配的模式
        case_sensitive: 是否区分大小写
        
    Returns:
        bool: 是否匹配
    """
    if not case_sensitive:
        text = text.lower()
        pattern = pattern.lower()
    
    return text == pattern


def text_matches_regex(text: str, pattern: str, case_sensitive: bool = True) -> bool:
    """检查文本是否匹配正则表达式
    
    Args:
        text: 输入文本
        pattern: 正则表达式模式
        case_sensitive: 是否区分大小写
        
    Returns:
        bool: 是否匹配
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    return bool(re.search(pattern, text, flags))


def extract_keywords(text: str, keywords: List[str], case_sensitive: bool = False) -> Dict[str, int]:
    """提取文本中的关键词
    
    Args:
        text: 输入文本
        keywords: 关键词列表
        case_sensitive: 是否区分大小写
        
    Returns:
        Dict[str, int]: 关键词及其出现次数
    """
    if not case_sensitive:
        text = text.lower()
        keywords = [keyword.lower() for keyword in keywords]
    
    result = {}
    for keyword in keywords:
        count = text.count(keyword)
        if count > 0:
            result[keyword] = count
    
    return result
