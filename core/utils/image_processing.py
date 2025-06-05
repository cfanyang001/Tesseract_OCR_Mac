import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple, List


def resize_image(image: np.ndarray, width: int = None, height: int = None) -> np.ndarray:
    """调整图像大小
    
    Args:
        image: 输入图像
        width: 目标宽度，为None时按比例缩放
        height: 目标高度，为None时按比例缩放
        
    Returns:
        np.ndarray: 调整大小后的图像
    """
    # 获取原始尺寸
    h, w = image.shape[:2]
    
    # 计算缩放比例
    if width is None and height is None:
        return image
    
    if width is None:
        ratio = height / float(h)
        width = int(w * ratio)
    elif height is None:
        ratio = width / float(w)
        height = int(h * ratio)
    
    # 调整大小
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)


def denoise_image(image: np.ndarray, method: str = 'gaussian', strength: int = 3) -> np.ndarray:
    """图像去噪
    
    Args:
        image: 输入图像
        method: 去噪方法 ('gaussian', 'median', 'bilateral')
        strength: 去噪强度
        
    Returns:
        np.ndarray: 去噪后的图像
    """
    if method == 'gaussian':
        return cv2.GaussianBlur(image, (strength, strength), 0)
    elif method == 'median':
        return cv2.medianBlur(image, strength)
    elif method == 'bilateral':
        return cv2.bilateralFilter(image, strength, 75, 75)
    else:
        return image


def binarize_image(image: np.ndarray, method: str = 'adaptive', threshold: int = 127) -> np.ndarray:
    """图像二值化
    
    Args:
        image: 输入图像
        method: 二值化方法 ('simple', 'adaptive', 'otsu')
        threshold: 二值化阈值 (0-255)
        
    Returns:
        np.ndarray: 二值化后的图像
    """
    # 确保图像为灰度图
    if len(image.shape) > 2:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    if method == 'simple':
        _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    elif method == 'adaptive':
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
    elif method == 'otsu':
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        binary = gray
    
    return binary


def enhance_contrast(image: np.ndarray, method: str = 'clahe', clip_limit: float = 2.0) -> np.ndarray:
    """增强图像对比度
    
    Args:
        image: 输入图像
        method: 增强方法 ('clahe', 'histogram', 'stretch')
        clip_limit: CLAHE方法的限制对比度
        
    Returns:
        np.ndarray: 增强后的图像
    """
    # 确保图像为灰度图
    if len(image.shape) > 2:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    if method == 'clahe':
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
    elif method == 'histogram':
        enhanced = cv2.equalizeHist(gray)
    elif method == 'stretch':
        # 对比度拉伸
        min_val, max_val = gray.min(), gray.max()
        enhanced = np.uint8(255 * (gray - min_val) / (max_val - min_val))
    else:
        enhanced = gray
    
    return enhanced


def deskew_image(image: np.ndarray, max_angle: float = 45.0) -> np.ndarray:
    """图像倾斜校正
    
    Args:
        image: 输入图像
        max_angle: 最大校正角度
        
    Returns:
        np.ndarray: 校正后的图像
    """
    # 确保图像为灰度图
    if len(image.shape) > 2:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # 二值化
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 计算倾斜角度
    coords = np.column_stack(np.where(binary > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    # 校正角度
    if angle < -max_angle:
        angle = -(90 + angle)
    elif angle > max_angle:
        angle = 90 - angle
    else:
        angle = -angle
    
    # 旋转图像
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, 
                            borderMode=cv2.BORDER_REPLICATE)
    
    return rotated


def remove_noise(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """去除噪点
    
    Args:
        image: 输入图像
        kernel_size: 形态学操作的核大小
        
    Returns:
        np.ndarray: 处理后的图像
    """
    # 创建核
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    
    # 开运算 (先腐蚀后膨胀)，去除小噪点
    opening = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)
    
    return opening


def preprocess_for_ocr(image: np.ndarray, preprocessing_steps: List[str] = None) -> np.ndarray:
    """OCR图像预处理
    
    Args:
        image: 输入图像
        preprocessing_steps: 预处理步骤列表
            可选值: 'resize', 'denoise', 'binarize', 'enhance', 'deskew', 'remove_noise'
            
    Returns:
        np.ndarray: 预处理后的图像
    """
    if preprocessing_steps is None:
        preprocessing_steps = ['resize', 'denoise', 'binarize', 'remove_noise']
    
    processed = image.copy()
    
    for step in preprocessing_steps:
        if step == 'resize':
            # 调整到合适的大小
            processed = resize_image(processed, width=1000)
        elif step == 'denoise':
            # 去噪
            processed = denoise_image(processed, method='gaussian', strength=3)
        elif step == 'binarize':
            # 二值化
            processed = binarize_image(processed, method='adaptive')
        elif step == 'enhance':
            # 增强对比度
            processed = enhance_contrast(processed, method='clahe')
        elif step == 'deskew':
            # 倾斜校正
            processed = deskew_image(processed)
        elif step == 'remove_noise':
            # 去除噪点
            processed = remove_noise(processed)
    
    return processed
