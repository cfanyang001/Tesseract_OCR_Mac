import os
import time
import numpy as np
import cv2
import pyautogui
from typing import Dict, Any, List, Tuple, Optional, Union
from PyQt5.QtCore import QObject, pyqtSignal, QRect, QPoint
from loguru import logger

from core.ocr_processor import OCRProcessor
from core.screen_capture import ScreenCapture
from core.text_recognizer import TextRecognizer


class SmartClick(QObject):
    """智能点击功能，支持基于OCR的文本定位点击"""
    
    # 信号
    target_found = pyqtSignal(str, QRect)  # 目标找到信号 (文本, 区域)
    click_performed = pyqtSignal(QPoint, str)  # 点击执行信号 (位置, 类型)
    error_occurred = pyqtSignal(str)  # 错误信号
    
    # 点击类型
    CLICK_TYPE_SINGLE = 'single'  # 单击
    CLICK_TYPE_DOUBLE = 'double'  # 双击
    CLICK_TYPE_RIGHT = 'right'    # 右击
    
    def __init__(self):
        """初始化智能点击功能"""
        super().__init__()
        
        # 创建OCR处理器和屏幕捕获器
        try:
            self.ocr_processor = OCRProcessor()
            self.screen_capture = ScreenCapture()
            self.text_recognizer = TextRecognizer()
            logger.info("智能点击功能初始化成功")
        except Exception as e:
            logger.error(f"智能点击功能初始化失败: {e}")
            raise
        
        # 默认配置
        self.config = {
            'confirm_before_click': True,  # 点击前确认
            'confirmation_timeout': 3.0,   # 确认超时时间 (秒)
            'click_delay': 0.5,            # 点击延迟 (秒)
            'text_match_threshold': 0.8,   # 文本匹配阈值 (0.0-1.0)
            'highlight_target': True,      # 高亮显示目标
            'highlight_color': (0, 255, 0),  # 高亮颜色 (BGR)
            'highlight_duration': 1.0,     # 高亮持续时间 (秒)
            'search_method': 'ocr',        # 搜索方法 ('ocr', 'template', 'hybrid')
            'max_search_attempts': 3,      # 最大搜索尝试次数
        }
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """设置配置"""
        self.config.update(config)
        
        # 更新OCR处理器配置
        if 'ocr' in config:
            self.ocr_processor.set_config(config['ocr'])
        
        # 更新屏幕捕获器配置
        if 'capture' in config:
            self.screen_capture.set_config(config['capture'])
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self.config.copy()
    
    def find_text_location(self, search_text: str, search_area: QRect = None) -> Optional[QRect]:
        """查找文本位置
        
        Args:
            search_text: 要查找的文本
            search_area: 搜索区域，为None时搜索整个屏幕
            
        Returns:
            Optional[QRect]: 文本位置矩形，未找到时返回None
        """
        try:
            # 如果未指定搜索区域，使用整个屏幕
            if search_area is None:
                screen_size = self.screen_capture.get_screen_size()
                search_area = QRect(0, 0, screen_size.width(), screen_size.height())
            
            # 捕获屏幕区域
            image = self.screen_capture.capture_area(search_area)
            
            # OCR识别
            _, details = self.ocr_processor.recognize_text(image)
            
            # 查找匹配的文本框
            for box in details['boxes']:
                text = box['text']
                confidence = self._calculate_text_similarity(text, search_text)
                
                if confidence >= self.config['text_match_threshold']:
                    # 找到匹配的文本，计算绝对位置
                    x = search_area.x() + box['x']
                    y = search_area.y() + box['y']
                    width = box['width']
                    height = box['height']
                    
                    # 创建文本区域矩形
                    text_rect = QRect(x, y, width, height)
                    
                    # 发送信号
                    self.target_found.emit(text, text_rect)
                    
                    logger.info(f"找到文本 '{search_text}' 位置: {text_rect}, 置信度: {confidence:.2f}")
                    return text_rect
            
            logger.info(f"未找到文本 '{search_text}'")
            return None
        
        except Exception as e:
            error_msg = f"查找文本位置失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None
    
    def click_on_text(self, search_text: str, search_area: QRect = None, 
                     click_type: str = CLICK_TYPE_SINGLE, offset: QPoint = None) -> bool:
        """点击文本
        
        Args:
            search_text: 要点击的文本
            search_area: 搜索区域，为None时搜索整个屏幕
            click_type: 点击类型 (single, double, right)
            offset: 相对于文本中心的偏移
            
        Returns:
            bool: 是否成功点击
        """
        try:
            # 查找文本位置
            text_rect = self.find_text_location(search_text, search_area)
            
            if text_rect is None:
                logger.warning(f"无法点击文本 '{search_text}': 未找到")
                return False
            
            # 计算点击位置 (默认为文本中心)
            click_x = text_rect.x() + text_rect.width() // 2
            click_y = text_rect.y() + text_rect.height() // 2
            
            # 应用偏移
            if offset is not None:
                click_x += offset.x()
                click_y += offset.y()
            
            click_point = QPoint(click_x, click_y)
            
            # 点击前确认
            if self.config['confirm_before_click']:
                if not self._confirm_click(click_point, search_text):
                    logger.info(f"用户取消了点击 '{search_text}'")
                    return False
            
            # 执行点击
            self._perform_click(click_point, click_type)
            
            # 发送信号
            self.click_performed.emit(click_point, click_type)
            
            logger.info(f"成功点击文本 '{search_text}', 位置: ({click_x}, {click_y}), 类型: {click_type}")
            return True
        
        except Exception as e:
            error_msg = f"点击文本失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def click_relative_to_text(self, search_text: str, relative_x: float, relative_y: float,
                              search_area: QRect = None, click_type: str = CLICK_TYPE_SINGLE) -> bool:
        """相对于文本位置点击
        
        Args:
            search_text: 参考文本
            relative_x: 相对于文本框的X位置 (0.0-1.0)
            relative_y: 相对于文本框的Y位置 (0.0-1.0)
            search_area: 搜索区域，为None时搜索整个屏幕
            click_type: 点击类型 (single, double, right)
            
        Returns:
            bool: 是否成功点击
        """
        try:
            # 查找文本位置
            text_rect = self.find_text_location(search_text, search_area)
            
            if text_rect is None:
                logger.warning(f"无法执行相对点击: 未找到文本 '{search_text}'")
                return False
            
            # 计算相对位置点击坐标
            click_x = text_rect.x() + int(text_rect.width() * relative_x)
            click_y = text_rect.y() + int(text_rect.height() * relative_y)
            
            click_point = QPoint(click_x, click_y)
            
            # 点击前确认
            if self.config['confirm_before_click']:
                if not self._confirm_click(click_point, f"{search_text} 的相对位置 ({relative_x:.2f}, {relative_y:.2f})"):
                    logger.info("用户取消了相对点击")
                    return False
            
            # 执行点击
            self._perform_click(click_point, click_type)
            
            # 发送信号
            self.click_performed.emit(click_point, click_type)
            
            logger.info(f"成功执行相对点击, 参考文本: '{search_text}', 相对位置: ({relative_x:.2f}, {relative_y:.2f}), 坐标: ({click_x}, {click_y})")
            return True
        
        except Exception as e:
            error_msg = f"相对点击失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def find_element_by_template(self, template_path: str, search_area: QRect = None,
                                threshold: float = 0.8) -> Optional[QRect]:
        """通过模板匹配查找元素
        
        Args:
            template_path: 模板图像路径
            search_area: 搜索区域，为None时搜索整个屏幕
            threshold: 匹配阈值 (0.0-1.0)
            
        Returns:
            Optional[QRect]: 元素位置矩形，未找到时返回None
        """
        try:
            # 检查模板文件是否存在
            if not os.path.exists(template_path):
                logger.error(f"模板文件不存在: {template_path}")
                return None
            
            # 加载模板图像
            template = cv2.imread(template_path)
            if template is None:
                logger.error(f"无法加载模板图像: {template_path}")
                return None
            
            # 如果未指定搜索区域，使用整个屏幕
            if search_area is None:
                screen_size = self.screen_capture.get_screen_size()
                search_area = QRect(0, 0, screen_size.width(), screen_size.height())
            
            # 捕获屏幕区域
            image = self.screen_capture.capture_area(search_area)
            
            # 转换为OpenCV格式
            screen_img = np.array(image)
            
            # 执行模板匹配
            result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 检查匹配度是否达到阈值
            if max_val < threshold:
                logger.info(f"未找到匹配模板, 最佳匹配度: {max_val:.2f}")
                return None
            
            # 计算元素位置
            w, h = template.shape[1], template.shape[0]
            x = search_area.x() + max_loc[0]
            y = search_area.y() + max_loc[1]
            
            # 创建元素区域矩形
            element_rect = QRect(x, y, w, h)
            
            logger.info(f"找到模板匹配元素, 位置: {element_rect}, 匹配度: {max_val:.2f}")
            return element_rect
        
        except Exception as e:
            error_msg = f"模板匹配失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return None
    
    def click_on_element(self, template_path: str, search_area: QRect = None,
                        click_type: str = CLICK_TYPE_SINGLE, offset: QPoint = None) -> bool:
        """点击元素
        
        Args:
            template_path: 模板图像路径
            search_area: 搜索区域，为None时搜索整个屏幕
            click_type: 点击类型 (single, double, right)
            offset: 相对于元素中心的偏移
            
        Returns:
            bool: 是否成功点击
        """
        try:
            # 查找元素位置
            element_rect = self.find_element_by_template(template_path, search_area)
            
            if element_rect is None:
                logger.warning(f"无法点击元素: 未找到匹配模板 {template_path}")
                return False
            
            # 计算点击位置 (默认为元素中心)
            click_x = element_rect.x() + element_rect.width() // 2
            click_y = element_rect.y() + element_rect.height() // 2
            
            # 应用偏移
            if offset is not None:
                click_x += offset.x()
                click_y += offset.y()
            
            click_point = QPoint(click_x, click_y)
            
            # 点击前确认
            if self.config['confirm_before_click']:
                if not self._confirm_click(click_point, f"模板元素 {os.path.basename(template_path)}"):
                    logger.info("用户取消了元素点击")
                    return False
            
            # 执行点击
            self._perform_click(click_point, click_type)
            
            # 发送信号
            self.click_performed.emit(click_point, click_type)
            
            logger.info(f"成功点击元素, 模板: {template_path}, 位置: ({click_x}, {click_y}), 类型: {click_type}")
            return True
        
        except Exception as e:
            error_msg = f"点击元素失败: {e}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度
        
        使用多种算法计算文本相似度，并返回最高的相似度分数
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            
        Returns:
            float: 相似度分数 (0.0-1.0)
        """
        # 如果任一文本为空，返回0
        if not text1 or not text2:
            return 0.0
        
        # 转换为小写进行比较
        text1 = text1.lower()
        text2 = text2.lower()
        
        # 1. 计算精确匹配
        if text1 == text2:
            return 1.0
        
        # 2. 计算包含关系
        if text1 in text2:
            return 0.9
        if text2 in text1:
            return 0.8
        
        # 3. 计算Levenshtein编辑距离
        try:
            import Levenshtein
            lev_similarity = 1.0 - Levenshtein.distance(text1, text2) / max(len(text1), len(text2))
        except ImportError:
            # 如果没有Levenshtein库，使用简化的编辑距离计算
            lev_similarity = self._simple_edit_distance(text1, text2)
        
        # 4. 计算词集合Jaccard相似度
        tokens1 = set(text1.split())
        tokens2 = set(text2.split())
        
        if not tokens1 or not tokens2:
            jaccard_similarity = 0.0
        else:
            intersection = len(tokens1.intersection(tokens2))
            union = len(tokens1.union(tokens2))
            jaccard_similarity = intersection / union if union > 0 else 0.0
        
        # 5. 计算N-gram相似度(字符级)
        ngram_similarity = self._ngram_similarity(text1, text2)
        
        # 返回最高的相似度
        return max([lev_similarity, jaccard_similarity, ngram_similarity])
    
    def _simple_edit_distance(self, s1: str, s2: str) -> float:
        """简化的编辑距离算法
        
        当Levenshtein库不可用时的替代方案
        
        Args:
            s1: 第一个字符串
            s2: 第二个字符串
            
        Returns:
            float: 相似度分数 (0.0-1.0)
        """
        # 创建矩阵
        m, n = len(s1), len(s2)
        if m == 0 or n == 0:
            return 0.0
            
        # 创建矩阵
        matrix = [[0 for _ in range(n + 1)] for _ in range(m + 1)]
        
        # 初始化第一行和第一列
        for i in range(m + 1):
            matrix[i][0] = i
        for j in range(n + 1):
            matrix[0][j] = j
            
        # 计算编辑距离
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    matrix[i][j] = matrix[i-1][j-1]
                else:
                    matrix[i][j] = min(
                        matrix[i-1][j] + 1,    # 删除
                        matrix[i][j-1] + 1,    # 插入
                        matrix[i-1][j-1] + 1   # 替换
                    )
        
        # 计算相似度
        distance = matrix[m][n]
        max_len = max(m, n)
        return 1.0 - (distance / max_len) if max_len > 0 else 0.0
    
    def _ngram_similarity(self, s1: str, s2: str, n: int = 2) -> float:
        """计算N-gram相似度
        
        Args:
            s1: 第一个字符串
            s2: 第二个字符串
            n: N-gram大小，默认为2(bigram)
            
        Returns:
            float: 相似度分数 (0.0-1.0)
        """
        if len(s1) < n or len(s2) < n:
            return 0.0
            
        # 创建n-gram
        s1_ngrams = [s1[i:i+n] for i in range(len(s1) - n + 1)]
        s2_ngrams = [s2[i:i+n] for i in range(len(s2) - n + 1)]
        
        # 计算交集和并集大小
        s1_ngrams_set = set(s1_ngrams)
        s2_ngrams_set = set(s2_ngrams)
        
        intersection = len(s1_ngrams_set.intersection(s2_ngrams_set))
        union = len(s1_ngrams_set.union(s2_ngrams_set))
        
        # 计算相似度
        return intersection / union if union > 0 else 0.0
    
    def _confirm_click(self, point: QPoint, target_desc: str) -> bool:
        """点击前确认
        
        Args:
            point: 点击位置
            target_desc: 目标描述
            
        Returns:
            bool: 是否确认点击
        """
        # TODO: 实现图形界面确认对话框
        # 当前简单实现，实际应用中应替换为图形界面确认
        
        # 高亮显示目标
        if self.config['highlight_target']:
            self._highlight_point(point)
        
        # 模拟确认对话框
        logger.info(f"准备点击 '{target_desc}' 位置: ({point.x()}, {point.y()})")
        
        # 在实际应用中，这里应该显示确认对话框
        # 暂时直接返回确认
        return True
    
    def _perform_click(self, point: QPoint, click_type: str) -> None:
        """执行点击
        
        Args:
            point: 点击位置
            click_type: 点击类型
        """
        # 移动鼠标到点击位置
        pyautogui.moveTo(point.x(), point.y(), duration=0.2)
        
        # 延迟
        time.sleep(self.config['click_delay'])
        
        # 执行点击
        if click_type == self.CLICK_TYPE_SINGLE:
            pyautogui.click()
        elif click_type == self.CLICK_TYPE_DOUBLE:
            pyautogui.doubleClick()
        elif click_type == self.CLICK_TYPE_RIGHT:
            pyautogui.rightClick()
        else:
            raise ValueError(f"不支持的点击类型: {click_type}")
    
    def _highlight_point(self, point: QPoint) -> None:
        """高亮显示点击位置
        
        Args:
            point: 点击位置
        """
        # TODO: 实现高亮显示
        # 在实际应用中，可以使用透明窗口或其他方式高亮显示
        # 当前简单实现，只打印日志
        logger.debug(f"高亮显示点击位置: ({point.x()}, {point.y()})") 