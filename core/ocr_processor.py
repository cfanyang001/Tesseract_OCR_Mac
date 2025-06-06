import os
import pytesseract
from PIL import Image
import numpy as np
import cv2
import hashlib
import time
from typing import Dict, Any, Optional, Tuple, List, Union
from functools import lru_cache
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
            'custom_config': '',           # 自定义配置
            'use_cache': True,             # 是否使用缓存
            'cache_size': 50,              # 缓存大小
            'cache_ttl': 60                # 缓存有效期(秒)
        }
        
        # 初始化缓存
        self._cache = {}
        self._cache_timestamps = {}
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """设置OCR配置"""
        old_cache_size = self.config.get('cache_size', 50)
        self.config.update(config)
        
        # 如果缓存大小变小，清理多余的缓存
        if self.config['cache_size'] < old_cache_size:
            self._clean_cache()
    
    def get_config(self) -> Dict[str, Any]:
        """获取OCR配置"""
        return self.config.copy()
    
    def get_available_languages(self) -> List[str]:
        """获取可用的OCR语言"""
        return list(self.LANGUAGE_MAPPING.values())
    
    def _image_hash(self, image: np.ndarray) -> str:
        """计算图像的哈希值，用于缓存键"""
        # 将图像调整为固定大小以加速哈希计算
        small_img = cv2.resize(image, (32, 32))
        # 计算图像的md5哈希
        return hashlib.md5(small_img.tobytes()).hexdigest()
    
    def _clean_cache(self) -> None:
        """清理过期和多余的缓存"""
        if not self.config['use_cache']:
            self._cache = {}
            self._cache_timestamps = {}
            return
            
        # 清理过期缓存
        current_time = time.time()
        expired_keys = [
            k for k, t in self._cache_timestamps.items() 
            if current_time - t > self.config['cache_ttl']
        ]
        
        for key in expired_keys:
            if key in self._cache:
                del self._cache[key]
            if key in self._cache_timestamps:
                del self._cache_timestamps[key]
        
        # 如果缓存仍然太大，删除最旧的条目
        if len(self._cache) > self.config['cache_size']:
            # 按时间戳排序
            sorted_keys = sorted(
                self._cache_timestamps.keys(), 
                key=lambda k: self._cache_timestamps[k]
            )
            
            # 删除最旧的条目，直到达到缓存大小
            for key in sorted_keys[:len(self._cache) - self.config['cache_size']]:
                if key in self._cache:
                    del self._cache[key]
                if key in self._cache_timestamps:
                    del self._cache_timestamps[key]
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """预处理图像，提高OCR识别率
        
        使用多种预处理方法，根据图像特性自动选择最佳方法
        """
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
            
            # 创建多种预处理结果，稍后选择最佳结果
            processed_images = [gray]  # 原始灰度图
            
            # 1. 高斯模糊 + 自适应阈值二值化
            if accuracy < 90:
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                binary = cv2.adaptiveThreshold(
                    blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 11, 2
                )
                processed_images.append(binary)
            
            # 2. 锐化
            if accuracy < 85:
                kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                sharpened = cv2.filter2D(gray, -1, kernel)
                processed_images.append(sharpened)
            
            # 3. 直方图均衡化
            if accuracy < 80:
                equalized = cv2.equalizeHist(gray)
                processed_images.append(equalized)
            
            # 4. Otsu二值化
            if accuracy < 75:
                _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                processed_images.append(otsu)
            
            # 为了提高性能，仅在需要时返回多种预处理结果
            # 在实际应用中，可以通过测试选择最佳预处理方法
            
            # 如果精度要求较低，直接返回最适合一般情况的预处理结果
            if accuracy < 70:
                return processed_images[1]  # 返回自适应阈值二值化结果
            
            return processed_images[0]  # 返回灰度图
            
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
            # 检查缓存
            if self.config['use_cache']:
                # 清理过期缓存
                self._clean_cache()
                
                # 计算图像哈希
                img_hash = self._image_hash(image)
                
                # 构建缓存键
                cache_key = f"{img_hash}_{self.config['language']}_{self.config['psm']}_{self.config['oem']}"
                
                # 检查缓存
                if cache_key in self._cache:
                    # 更新时间戳
                    self._cache_timestamps[cache_key] = time.time()
                    logger.debug(f"使用缓存的OCR结果: {cache_key}")
                    return self._cache[cache_key]
            
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
            
            result = (text, details)
            
            # 保存到缓存
            if self.config['use_cache']:
                self._cache[cache_key] = result
                self._cache_timestamps[cache_key] = time.time()
            
            logger.debug(f"OCR识别成功: {len(text)} 字符, 置信度: {details['confidence']}%")
            return result
        
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
            'languages': self.get_available_languages(),
            'config': self.get_config()
        }
