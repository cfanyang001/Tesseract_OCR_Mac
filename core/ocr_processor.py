import os
import pytesseract
from PIL import Image
import numpy as np
import cv2
from typing import Dict, Any, Optional, Tuple, List
from loguru import logger


class OCRProcessor:
    """OCR处理模块，集成Tesseract OCR引擎"""
    
    # 语言映射
    LANGUAGE_MAPPING = {
        'chi_sim': '中文简体',
        'chi_tra': '中文繁体',
        'eng': '英语',
        'jpn': '日语',
        'kor': '韩语'
    }
    
    # 反向语言映射
    LANGUAGE_MAPPING_REVERSE = {
        '中文简体': 'chi_sim',
        '中文繁体': 'chi_tra',
        '英语': 'eng',
        '日语': 'jpn',
        '韩语': 'kor'
    }
    
    def __init__(self):
        """初始化OCR处理器"""
        # 检查Tesseract是否安装
        try:
            self.tesseract_version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract OCR版本: {self.tesseract_version}")
        except Exception as e:
            logger.error(f"Tesseract OCR检测失败: {e}")
            raise RuntimeError("Tesseract OCR未安装或配置错误")
        
        # 默认OCR配置
        self.config = {
            'language': 'chi_sim',         # OCR语言
            'accuracy': 80,                # 精度 (0-100)
            'preprocess': True,            # 是否启用图像预处理
            'autocorrect': False,          # 是否启用文本自动修正
            'psm': 3,                      # 页面分割模式 (3=自动)
            'oem': 3,                      # OCR引擎模式 (3=默认)
            'custom_config': ''            # 自定义配置
        }
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """设置OCR配置"""
        self.config.update(config)
    
    def get_config(self) -> Dict[str, Any]:
        """获取OCR配置"""
        return self.config.copy()
    
    def get_available_languages(self) -> List[str]:
        """获取可用的OCR语言"""
        return list(self.LANGUAGE_MAPPING.values())
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """预处理图像，提高OCR识别率"""
        if not self.config['preprocess']:
            return image
        
        try:
            # 确保图像是RGB或BGR格式
            if len(image.shape) == 3:
                if image.shape[2] == 4:  # RGBA格式
                    image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
                # 现在图像应该是3通道RGB或BGR格式
            
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                # 已经是灰度图
                gray = image.copy()
            
            # 根据精度调整预处理强度
            accuracy = self.config['accuracy']
            
            # 应用高斯模糊减少噪点
            if accuracy < 70:
                gray = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # 应用自适应阈值二值化
            if accuracy < 90:
                gray = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 11, 2
                )
            
            # 应用形态学操作
            if accuracy < 80:
                kernel = np.ones((1, 1), np.uint8)
                gray = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
            
            return gray
            
        except Exception as e:
            logger.error(f"图像预处理失败: {e}")
            # 如果预处理失败，返回原始图像
            return image
    
    def recognize_text(self, image: np.ndarray, config: str = None) -> Tuple[str, Dict[str, Any]]:
        """识别图像中的文本
        
        Args:
            image: 图像数组
            config: 可选的自定义Tesseract配置，覆盖默认配置
            
        Returns:
            Tuple[str, Dict[str, Any]]: 识别的文本和详细信息
        """
        try:
            # 预处理图像
            processed_image = self.preprocess_image(image)
            
            # 构建Tesseract配置
            if config is None:
                config = f'--psm {self.config["psm"]} --oem {self.config["oem"]}'
                if self.config['custom_config']:
                    config += f' {self.config["custom_config"]}'
            
            # 识别文本
            text = pytesseract.image_to_string(
                processed_image,
                lang=self.config['language'],
                config=config
            )
            
            # 获取详细信息
            data = pytesseract.image_to_data(
                processed_image,
                lang=self.config['language'],
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            # 文本自动修正
            if self.config['autocorrect']:
                text = self.autocorrect_text(text)
            
            # 构建详细信息
            details = {
                'confidence': self._calculate_avg_confidence(data),
                'word_count': len(data['text']),
                'char_count': sum(len(word) for word in data['text'] if word.strip()),
                'boxes': self._extract_text_boxes(data)
            }
            
            logger.debug(f"OCR识别成功: {len(text)} 字符, 置信度: {details['confidence']}%")
            return text, details
        
        except Exception as e:
            logger.error(f"OCR识别失败: {e}")
            return "", {'confidence': 0, 'word_count': 0, 'char_count': 0, 'boxes': []}
    
    def autocorrect_text(self, text: str) -> str:
        """自动修正文本
        
        简单的文本修正，可以根据需要扩展
        """
        # TODO: 实现更复杂的文本修正
        # 移除多余的空格和换行符
        text = ' '.join(text.split())
        return text
    
    def _calculate_avg_confidence(self, data: Dict[str, Any]) -> float:
        """计算平均置信度"""
        confidences = [conf for conf in data['conf'] if conf > 0]
        if not confidences:
            return 0
        return round(sum(confidences) / len(confidences), 2)
    
    def _extract_text_boxes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取文本框信息"""
        boxes = []
        for i in range(len(data['text'])):
            if not data['text'][i].strip():
                continue
                
            boxes.append({
                'text': data['text'][i],
                'conf': data['conf'][i],
                'x': data['left'][i],
                'y': data['top'][i],
                'width': data['width'][i],
                'height': data['height'][i]
            })
        return boxes
    
    def get_tesseract_info(self) -> Dict[str, Any]:
        """获取Tesseract信息"""
        return {
            'version': self.tesseract_version,
            'available_languages': self.get_available_languages()
        }
