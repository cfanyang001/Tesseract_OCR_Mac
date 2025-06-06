import os
import sys
import json
import time
import platform
import tempfile
import shutil
import urllib.request
import urllib.error
import zipfile
import subprocess
from typing import Dict, Any, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal
from loguru import logger

class UpdateChecker(QObject):
    """更新检查器，用于检查和安装软件更新"""
    
    # 信号
    update_available = pyqtSignal(dict)  # 有更新可用 (更新信息)
    update_progress = pyqtSignal(int, str)  # 更新进度 (百分比, 消息)
    update_error = pyqtSignal(str)  # 更新错误 (错误信息)
    update_complete = pyqtSignal(bool, str)  # 更新完成 (成功与否, 消息)
    
    def __init__(self):
        """初始化更新检查器"""
        super().__init__()
        
        # 当前版本
        self.current_version = "1.0.0"
        
        # 更新服务器URL
        self.update_url = "https://api.github.com/repos/yourusername/Tesseract_OCR/releases/latest"
        
        # 临时目录
        self.temp_dir = os.path.join(tempfile.gettempdir(), "tesseract_ocr_update")
        
        # 系统信息
        self.system = platform.system().lower()
        self.is_mac = self.system == "darwin"
        self.is_windows = self.system == "windows"
        self.is_linux = self.system == "linux"
        
        # Apple Silicon检测
        self.is_apple_silicon = False
        if self.is_mac:
            self.is_apple_silicon = platform.machine() == 'arm64'
    
    def check_for_updates(self) -> Tuple[bool, Dict[str, Any]]:
        """检查更新
        
        Returns:
            Tuple[bool, Dict[str, Any]]: (是否有更新, 更新信息)
        """
        try:
            logger.info("检查软件更新...")
            
            # 获取最新版本信息
            with urllib.request.urlopen(self.update_url, timeout=10) as response:
                data = json.loads(response.read().decode())
            
            latest_version = data.get("tag_name", "").lstrip("v")
            if not latest_version:
                logger.warning("无法获取最新版本号")
                return False, {}
            
            logger.debug(f"当前版本: {self.current_version}, 最新版本: {latest_version}")
            
            # 比较版本号
            if self._compare_versions(latest_version, self.current_version) <= 0:
                logger.info("已经是最新版本")
                return False, {}
            
            # 获取更新信息
            update_info = {
                "version": latest_version,
                "release_date": data.get("published_at", ""),
                "release_notes": data.get("body", "无更新说明"),
                "download_url": None,
                "is_prerelease": data.get("prerelease", False)
            }
            
            # 获取下载URL
            assets = data.get("assets", [])
            for asset in assets:
                name = asset.get("name", "")
                
                # 根据系统选择合适的安装包
                if self.is_windows and name.endswith(".zip") and "win" in name.lower():
                    update_info["download_url"] = asset.get("browser_download_url")
                    break
                elif self.is_mac and name.endswith(".zip") and "mac" in name.lower():
                    # 针对Apple Silicon的特殊处理
                    if self.is_apple_silicon and "arm64" in name.lower():
                        update_info["download_url"] = asset.get("browser_download_url")
                        break
                    elif not self.is_apple_silicon and "x86_64" in name.lower():
                        update_info["download_url"] = asset.get("browser_download_url")
                        break
                    # 如果没有找到特定架构的包，使用通用包
                    elif "universal" in name.lower():
                        update_info["download_url"] = asset.get("browser_download_url")
                elif self.is_linux and name.endswith(".zip") and "linux" in name.lower():
                    update_info["download_url"] = asset.get("browser_download_url")
                    break
            
            if not update_info["download_url"]:
                logger.warning("未找到适用于当前系统的更新包")
                return False, update_info
            
            logger.info(f"发现新版本: {latest_version}")
            
            # 发送信号
            self.update_available.emit(update_info)
            
            return True, update_info
            
        except urllib.error.URLError as e:
            logger.error(f"检查更新失败 (网络错误): {e}")
            return False, {"error": f"网络错误: {str(e)}"}
            
        except json.JSONDecodeError as e:
            logger.error(f"检查更新失败 (解析错误): {e}")
            return False, {"error": f"解析错误: {str(e)}"}
            
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
            return False, {"error": str(e)}
    
    def download_update(self, download_url: str) -> bool:
        """下载更新
        
        Args:
            download_url: 下载URL
            
        Returns:
            bool: 是否下载成功
        """
        try:
            logger.info(f"开始下载更新: {download_url}")
            
            # 创建临时目录
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir, exist_ok=True)
            
            # 下载文件路径
            download_file = os.path.join(self.temp_dir, "update.zip")
            
            # 发送进度信号
            self.update_progress.emit(0, "开始下载更新...")
            
            # 下载文件
            def report_progress(blocknum, blocksize, totalsize):
                """报告下载进度"""
                if totalsize > 0:
                    percent = min(int(blocknum * blocksize * 100 / totalsize), 100)
                    self.update_progress.emit(percent, f"下载更新: {percent}%")
            
            urllib.request.urlretrieve(download_url, download_file, report_progress)
            
            # 检查下载文件
            if not os.path.exists(download_file) or os.path.getsize(download_file) == 0:
                logger.error("下载更新失败: 文件不存在或为空")
                self.update_error.emit("下载更新失败: 文件不存在或为空")
                return False
            
            logger.info(f"更新下载完成: {download_file}")
            self.update_progress.emit(100, "下载完成")
            
            return True
            
        except urllib.error.URLError as e:
            logger.error(f"下载更新失败 (网络错误): {e}")
            self.update_error.emit(f"下载更新失败: 网络错误 - {str(e)}")
            return False
            
        except Exception as e:
            logger.error(f"下载更新失败: {e}")
            self.update_error.emit(f"下载更新失败: {str(e)}")
            return False
    
    def install_update(self) -> bool:
        """安装更新
        
        Returns:
            bool: 是否安装成功
        """
        try:
            logger.info("开始安装更新...")
            self.update_progress.emit(0, "准备安装更新...")
            
            # 检查临时目录
            download_file = os.path.join(self.temp_dir, "update.zip")
            if not os.path.exists(download_file):
                logger.error("安装更新失败: 更新文件不存在")
                self.update_error.emit("安装更新失败: 更新文件不存在")
                return False
            
            # 创建解压目录
            extract_dir = os.path.join(self.temp_dir, "extract")
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir)
            os.makedirs(extract_dir, exist_ok=True)
            
            # 解压文件
            self.update_progress.emit(10, "解压更新文件...")
            with zipfile.ZipFile(download_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # 获取应用目录
            app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            
            # 检查是否有安装脚本
            install_script = None
            if self.is_mac or self.is_linux:
                install_script = os.path.join(extract_dir, "install.sh")
            elif self.is_windows:
                install_script = os.path.join(extract_dir, "install.bat")
            
            # 运行安装脚本
            if install_script and os.path.exists(install_script):
                self.update_progress.emit(30, "运行安装脚本...")
                
                # 添加执行权限
                if self.is_mac or self.is_linux:
                    os.chmod(install_script, 0o755)
                
                # 运行脚本
                proc = subprocess.Popen(
                    install_script,
                    cwd=extract_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True
                )
                stdout, stderr = proc.communicate()
                
                if proc.returncode != 0:
                    logger.error(f"安装脚本执行失败: {stderr.decode('utf-8', errors='ignore')}")
                    self.update_error.emit("安装脚本执行失败，请查看日志获取详细信息")
                    return False
                    
                logger.info(f"安装脚本执行成功: {stdout.decode('utf-8', errors='ignore')}")
                self.update_progress.emit(90, "安装脚本执行完成")
                
            else:
                # 如果没有安装脚本，执行默认安装流程
                self.update_progress.emit(30, "复制更新文件...")
                
                # 获取更新文件列表
                files_to_update = []
                for root, dirs, files in os.walk(extract_dir):
                    for file in files:
                        src_file = os.path.join(root, file)
                        rel_path = os.path.relpath(src_file, extract_dir)
                        dst_file = os.path.join(app_dir, rel_path)
                        files_to_update.append((src_file, dst_file))
                
                # 备份原始文件
                backup_dir = os.path.join(self.temp_dir, "backup")
                os.makedirs(backup_dir, exist_ok=True)
                
                self.update_progress.emit(40, "备份原始文件...")
                for _, dst_file in files_to_update:
                    if os.path.exists(dst_file):
                        rel_path = os.path.relpath(dst_file, app_dir)
                        backup_file = os.path.join(backup_dir, rel_path)
                        os.makedirs(os.path.dirname(backup_file), exist_ok=True)
                        shutil.copy2(dst_file, backup_file)
                
                # 复制更新文件
                self.update_progress.emit(60, "应用更新...")
                for i, (src_file, dst_file) in enumerate(files_to_update):
                    os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                    
                    # 更新进度
                    progress = 60 + int((i / len(files_to_update)) * 30)
                    self.update_progress.emit(progress, f"应用更新: {progress}%")
            
            # 更新完成
            self.update_progress.emit(100, "更新完成")
            self.update_complete.emit(True, "更新安装成功，请重启应用程序")
            
            logger.info("更新安装成功")
            return True
            
        except Exception as e:
            logger.error(f"安装更新失败: {e}")
            self.update_error.emit(f"安装更新失败: {str(e)}")
            self.update_complete.emit(False, f"更新失败: {str(e)}")
            return False
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """比较版本号
        
        Args:
            version1: 版本号1
            version2: 版本号2
            
        Returns:
            int: 1 如果version1>version2, -1 如果version1<version2, 0 如果相等
        """
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        # 补齐版本号长度
        while len(v1_parts) < len(v2_parts):
            v1_parts.append(0)
        while len(v2_parts) < len(v1_parts):
            v2_parts.append(0)
        
        # 比较版本号
        for i in range(len(v1_parts)):
            if v1_parts[i] > v2_parts[i]:
                return 1
            elif v1_parts[i] < v2_parts[i]:
                return -1
        
        return 0
    
    def cleanup(self):
        """清理临时文件"""
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            logger.debug("清理更新临时文件完成")
        except Exception as e:
            logger.error(f"清理更新临时文件失败: {e}")


# 全局单例
_instance = None

def get_updater() -> UpdateChecker:
    """获取更新检查器单例"""
    global _instance
    if _instance is None:
        _instance = UpdateChecker()
    return _instance 