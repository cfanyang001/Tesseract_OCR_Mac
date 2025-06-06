#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tesseract OCR监控软件
基于Python 3.9和Tesseract OCR的屏幕监控软件，可以监控屏幕指定区域的文字内容，
当识别到特定文本时触发预设动作。
"""

import os
import sys
import platform
import argparse
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTranslator, QLocale
from loguru import logger

# 导入自定义模块
from ui.main_window import MainWindow
from config.mac_compatibility import MacCompatibility


def setup_logging(debug=False):
    """设置日志记录
    
    Args:
        debug: 是否为调试模式
    """
    log_level = "DEBUG" if debug else "INFO"
    
    # 清除默认处理器
    logger.remove()
    
    # 添加标准输出处理器
    logger.add(sys.stderr, level=log_level, 
               format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    # 添加文件处理器
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    logger.add(os.path.join(log_dir, "app_{time}.log"), rotation="10 MB", 
               retention="1 week", level=log_level)
    
    logger.info(f"日志级别设置为: {log_level}")


def check_environment():
    """检查环境并设置优化参数
    
    Returns:
        bool: 环境是否适合运行应用
    """
    # 记录基本系统信息
    logger.info(f"操作系统: {platform.system()} {platform.release()} ({platform.machine()})")
    logger.info(f"Python版本: {platform.python_version()}")
    
    # 检查是否为Mac M系列芯片
    is_apple_silicon = False
    mac_model = ""
    
    if platform.system() == "Darwin":
        try:
            mac_compat = MacCompatibility()
            is_apple_silicon = mac_compat.is_apple_silicon()
            
            if is_apple_silicon:
                chip_info = mac_compat.get_chip_info()
                mac_model = chip_info.get("model", "")
                logger.info(f"检测到Apple Silicon芯片: {mac_model}")
                
                # 设置优化环境变量
                os.environ["PYTHONUNBUFFERED"] = "1"  # 禁用输出缓冲
                os.environ["VECLIB_MAXIMUM_THREADS"] = "4"  # 限制veclib线程
                os.environ["NUMEXPR_MAX_THREADS"] = "4"  # 限制numexpr线程
                
                # M4芯片特定优化
                if "M4" in mac_model:
                    logger.info("应用M4芯片特定优化")
                    os.environ["PYTESSERACT_M_OPTIMIZE"] = "1"
                
            else:
                logger.info("运行在Intel Mac上")
                
        except Exception as e:
            logger.warning(f"检查Mac兼容性失败: {e}")
    
    # 检查Tesseract
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        logger.info(f"Tesseract版本: {version}")
    except Exception as e:
        logger.warning(f"Tesseract检测失败: {e}")
        
    # 检查其他依赖项
    try:
        import PIL
        logger.debug(f"Pillow版本: {PIL.__version__}")
    except Exception as e:
        logger.warning(f"Pillow检测失败: {e}")
    
    try:
        import cv2
        logger.debug(f"OpenCV版本: {cv2.__version__}")
    except Exception as e:
        logger.warning(f"OpenCV检测失败: {e}")
    
    return True


def main():
    """应用程序主入口"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Tesseract OCR监控软件")
    parser.add_argument("-d", "--debug", action="store_true", help="调试模式")
    parser.add_argument("--no-update-check", action="store_true", help="禁用更新检查")
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.debug)
    
    # 记录启动信息
    logger.info("="*40)
    logger.info("Tesseract OCR监控软件启动")
    logger.info("="*40)
    
    # 检查环境
    check_environment()
    
    try:
        # 创建QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("Tesseract OCR监控软件")
        app.setOrganizationName("YourCompany")
        app.setOrganizationDomain("example.com")
        
        # 主窗口
        window = MainWindow()
        window.show()
        
        # 执行应用程序
        return app.exec_()
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {e}")
        return 1
    finally:
        logger.info("应用程序退出")


if __name__ == "__main__":
    sys.exit(main())
