import os
import sys
import importlib
import pkg_resources
from loguru import logger

def check_qt_compatibility():
    """检查并确保项目中使用的PyQt版本保持一致
    
    检查已安装的PyQt版本，对比requirements.txt中指定的版本，
    如果不一致，打印警告日志。
    """
    try:
        # 获取已安装的PyQt版本
        pyqt5_version = pkg_resources.get_distribution("PyQt5").version
        logger.info(f"检测到PyQt5版本: {pyqt5_version}")
        
        # 检查运行时Qt版本
        from PyQt5.QtCore import QT_VERSION_STR
        logger.info(f"Qt版本: {QT_VERSION_STR}")
        
        # 检查PyQt与Qt版本是否匹配
        from PyQt5.QtCore import PYQT_VERSION_STR
        if PYQT_VERSION_STR != pyqt5_version:
            logger.warning(f"PyQt5版本不匹配: 包版本 {pyqt5_version}, 运行时版本 {PYQT_VERSION_STR}")
        
        # 检查项目导入是否一致
        try:
            import importlib_metadata
            if hasattr(importlib_metadata, 'packages_distributions'):
                dists = importlib_metadata.packages_distributions()
                qt_packages = [d for pkg in dists for d in dists[pkg] if d.lower().startswith('pyqt')]
                if len(set(qt_packages)) > 1:
                    logger.warning(f"检测到多个Qt包: {set(qt_packages)}")
        except ImportError:
            pass
    
    except Exception as e:
        logger.error(f"PyQt版本检查失败: {e}")
        
def check_package_versions(required_file='requirements.txt'):
    """检查已安装的包与requirements.txt中指定的版本是否一致"""
    try:
        # 读取requirements.txt
        req_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), required_file)
        if not os.path.exists(req_path):
            logger.warning(f"找不到依赖文件: {req_path}")
            return
            
        with open(req_path, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
        # 检查版本
        mismatches = []
        for req in requirements:
            if '==' in req:
                package, version = req.split('==', 1)
                try:
                    installed = pkg_resources.get_distribution(package).version
                    if installed != version:
                        mismatches.append(f"{package}: 需要 {version}, 已安装 {installed}")
                except pkg_resources.DistributionNotFound:
                    mismatches.append(f"{package}: 需要 {version}, 未安装")
                    
        # 报告结果
        if mismatches:
            logger.warning("以下包版本与requirements.txt不匹配:")
            for mismatch in mismatches:
                logger.warning(f"  - {mismatch}")
            logger.warning("建议运行: pip install -r requirements.txt")
        else:
            logger.info("所有包版本与requirements.txt匹配")
    
    except Exception as e:
        logger.error(f"依赖检查失败: {e}")

# 初始化时自动检查
check_qt_compatibility()
