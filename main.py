#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tesseract OCR监控软件
基于Python 3.9和Tesseract OCR的屏幕监控软件，可以监控屏幕指定区域的文字内容，
当识别到特定文本时触发预设动作。
"""

import sys
import os
import traceback
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

# 初始化错误处理器
def init_error_handler():
    """初始化全局错误处理器"""
    try:
        from core.error_handler import get_error_handler
        error_handler = get_error_handler()
        logger.info("全局错误处理器已初始化")
        return error_handler
    except Exception as e:
        logger.warning(f"初始化错误处理器失败: {e}")
        return None

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

# 检查系统环境
def check_environment():
    """检查系统环境"""
    try:
        import platform
        
        # 检查操作系统
        system = platform.system()
        release = platform.release()
        machine = platform.machine()
        logger.info(f"操作系统: {system} {release} ({machine})")
        
        # 检查Python版本
        python_version = platform.python_version()
        logger.info(f"Python版本: {python_version}")
        
        # 检查依赖版本
        from config import check_package_versions
        check_package_versions()
        
        # 检查PyQt兼容性
        from config import check_qt_compatibility
        check_qt_compatibility()
        
        # 检查Mac M4芯片兼容性（如果是Mac系统）
        if system == "Darwin":
            try:
                from config.mac_compatibility import MacCompatibility
                mac_compat = MacCompatibility()
                report = mac_compat.get_compatibility_report()
                
                # 记录基本信息
                chip_info = report.get('hardware', {})
                if chip_info.get('is_apple_silicon', False):
                    logger.info(f"检测到Apple Silicon芯片: {chip_info.get('model', 'Unknown')}")
                    
                    # M4芯片特定优化
                    if "M4" in chip_info.get('model', ''):
                        logger.info("检测到M4芯片，应用M系列芯片优化...")
                        
                        # 记录Tesseract兼容性信息
                        tesseract_info = report.get('tesseract', {})
                        if tesseract_info.get('is_native', False):
                            logger.info("Tesseract OCR为原生ARM64版本，性能最佳")
                        else:
                            logger.warning("Tesseract OCR非原生ARM64版本，性能可能受影响")
                
                # 记录优化建议
                if report.get('recommendations'):
                    logger.info("系统兼容性建议:")
                    for recommendation in report.get('recommendations', []):
                        logger.info(f"  - {recommendation}")
                        
                # 设置Mac专有环境变量
                if chip_info.get('is_apple_silicon', False):
                    # 设置环境变量以优化性能
                    os.environ['PYTHONUNBUFFERED'] = '1'
                    os.environ['VECLIB_MAXIMUM_THREADS'] = '4'
                    os.environ['NUMEXPR_MAX_THREADS'] = '4'
                    
                    # 对于M4芯片，增加额外优化
                    if "M4" in chip_info.get('model', ''):
                        # M4芯片特定优化
                        os.environ['PYTESSERACT_M_OPTIMIZE'] = '1'
            except ImportError as e:
                logger.warning(f"无法加载Mac兼容性检查模块: {e}")
            except Exception as e:
                logger.warning(f"Mac兼容性检查失败: {e}")
        
        return True
    except Exception as e:
        logger.error(f"环境检查失败: {e}")
        return True  # 继续运行，不阻止应用启动

# 使用全局错误处理器
def handle_exception(exc_type, exc_value, exc_traceback):
    """处理未捕获的异常"""
    # 尝试使用我们的错误处理器
    try:
        from core.error_handler import get_error_handler
        error_handler = get_error_handler()
        if error_handler:
            # 让错误处理器处理异常
            error_handler.global_exception_handler(exc_type, exc_value, exc_traceback)
            return
    except:
        pass
    
    # 如果错误处理器不可用，回退到基本处理
    logger.error("发生未捕获的异常:")
    logger.error("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    
    # 如果存在GUI，可以显示错误对话框
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox
        if QApplication.instance():
            QMessageBox.critical(
                None,
                "错误",
                f"应用程序发生错误:\n{exc_value}\n\n请查看日志获取详细信息。"
            )
    except:
        pass

# 主函数
def main():
    """程序入口函数"""
    # 创建日志目录
    os.makedirs("logs", exist_ok=True)
    
    # 初始化错误处理器
    error_handler = init_error_handler()
    
    # 设置异常处理
    if not error_handler:
        sys.excepthook = handle_exception
    
    logger.info("启动Tesseract OCR监控软件")
    
    # 检查环境
    check_environment()
    
    # 检查Tesseract OCR
    if not check_tesseract():
        logger.error("Tesseract OCR未安装或配置错误，请安装后重试")
        print("错误: Tesseract OCR未安装或配置错误，请安装后重试")
        print("可以通过以下命令安装: brew install tesseract")
        sys.exit(1)
    
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
