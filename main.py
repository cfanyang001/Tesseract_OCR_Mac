#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tesseract OCR监控软件
基于Python 3.9和Tesseract OCR的屏幕监控软件，可以监控屏幕指定区域的文字内容，
当识别到特定文本时触发预设动作。
"""

import sys
import os
from loguru import logger

# 配置日志
logger.remove()  # 移除默认处理器
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # 每天零点创建新文件
    retention="30 days",  # 保留30天的日志
    level="DEBUG",
    encoding="utf-8",
    enqueue=True  # 线程安全
)
logger.add(sys.stderr, level="INFO")  # 添加标准错误输出

# 检查Tesseract OCR是否安装
def check_tesseract():
    """检查Tesseract OCR是否安装"""
    try:
        import pytesseract
        tesseract_version = pytesseract.get_tesseract_version()
        logger.info(f"Tesseract OCR版本: {tesseract_version}")
        return True
    except Exception as e:
        logger.error(f"Tesseract OCR检测失败: {e}")
        return False

# 主函数
def main():
    """程序入口函数"""
    logger.info("启动Tesseract OCR监控软件")
    
    # 检查环境
    if not check_tesseract():
        logger.error("Tesseract OCR未安装或配置错误，请安装后重试")
        print("错误: Tesseract OCR未安装或配置错误，请安装后重试")
        print("可以通过以下命令安装: brew install tesseract")
        sys.exit(1)
    
    # 创建日志目录
    os.makedirs("logs", exist_ok=True)
    
    # 导入应用程序
    try:
        from ui.app import run_app
        sys.exit(run_app())
    except Exception as e:
        logger.exception(f"应用程序启动失败: {e}")
        print(f"错误: 应用程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
