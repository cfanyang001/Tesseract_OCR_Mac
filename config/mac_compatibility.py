import os
import platform
import subprocess
from typing import Dict, Any, Optional, Tuple
from loguru import logger


class MacCompatibility:
    """Mac兼容性检查类，专门针对M系列芯片优化"""
    
    def __init__(self):
        """初始化Mac兼容性检查类"""
        self._is_mac = platform.system() == "Darwin"
        self._chip_info = None
        self._rosetta_status = None
        
    def is_mac(self) -> bool:
        """检查是否为Mac系统"""
        return self._is_mac
    
    def get_mac_version(self) -> Optional[str]:
        """获取Mac系统版本
        
        Returns:
            Optional[str]: Mac系统版本，非Mac系统返回None
        """
        if not self._is_mac:
            return None
        
        return platform.mac_ver()[0]
    
    def is_apple_silicon(self) -> bool:
        """检查是否为Apple Silicon芯片
        
        Returns:
            bool: 是否为Apple Silicon芯片
        """
        if not self._is_mac:
            return False
            
        arch = platform.machine()
        return arch == 'arm64'
    
    def get_chip_info(self) -> Dict[str, Any]:
        """获取芯片详细信息
        
        Returns:
            Dict[str, Any]: 芯片信息字典
        """
        if self._chip_info is not None:
            return self._chip_info
            
        if not self._is_mac:
            return {"error": "Not a Mac system"}
        
        try:
            # 使用系统命令获取芯片信息
            cmd = ["sysctl", "-n", "machdep.cpu.brand_string"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = proc.communicate()
            
            brand = output.decode('utf-8').strip()
            
            # 检查是否为M系列芯片
            is_apple_silicon = self.is_apple_silicon()
            
            # 获取详细信息
            result = {
                "brand": brand,
                "architecture": platform.machine(),
                "is_apple_silicon": is_apple_silicon,
                "model": "Unknown"
            }
            
            # 如果是Apple Silicon，尝试确定具体型号
            if is_apple_silicon:
                # 使用system_profiler获取更详细信息
                cmd = ["system_profiler", "SPHardwareDataType"]
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output, error = proc.communicate()
                output_str = output.decode('utf-8')
                
                # 解析输出查找芯片型号
                for line in output_str.split('\n'):
                    if "Chip" in line and "Apple" in line:
                        result["model"] = line.split(':')[1].strip()
                        break
            
            self._chip_info = result
            return result
            
        except Exception as e:
            logger.error(f"获取芯片信息失败: {e}")
            return {"error": str(e)}
    
    def is_using_rosetta(self) -> bool:
        """检查是否使用Rosetta 2运行
        
        Returns:
            bool: 是否使用Rosetta 2
        """
        if not self._is_mac or not self.is_apple_silicon():
            return False
            
        if self._rosetta_status is not None:
            return self._rosetta_status
            
        try:
            # 检查当前进程是否通过Rosetta 2运行
            cmd = ["sysctl", "-n", "sysctl.proc_translated"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = proc.communicate()
            
            if proc.returncode == 0:
                status = output.strip() == b'1'
            else:
                # 如果命令失败，可能不是在Rosetta下运行
                status = False
                
            self._rosetta_status = status
            return status
            
        except Exception as e:
            logger.error(f"检查Rosetta状态失败: {e}")
            return False
    
    def check_tesseract_compatibility(self) -> Dict[str, Any]:
        """检查Tesseract OCR与当前系统的兼容性
        
        Returns:
            Dict[str, Any]: 兼容性信息
        """
        result = {
            "is_mac": self._is_mac,
            "is_apple_silicon": self.is_apple_silicon(),
            "using_rosetta": self.is_using_rosetta() if self._is_mac else False,
            "tesseract_installed": False,
            "tesseract_version": None,
            "is_native": False,
            "recommendations": []
        }
        
        try:
            # 检查Tesseract是否安装
            cmd = ["tesseract", "--version"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output, error = proc.communicate()
            
            if proc.returncode == 0:
                # 提取版本号
                version_line = output.decode('utf-8').split('\n')[0]
                result["tesseract_installed"] = True
                result["tesseract_version"] = version_line.strip()
                
                # 检查是否为原生编译版本
                if self.is_apple_silicon() and not self.is_using_rosetta():
                    # 检查tesseract是否为arm64架构
                    cmd = ["file", "$(which tesseract)"]
                    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    output, error = proc.communicate()
                    output_str = output.decode('utf-8').lower()
                    
                    if "arm64" in output_str:
                        result["is_native"] = True
                    else:
                        result["recommendations"].append(
                            "Tesseract OCR未针对Apple Silicon优化。建议重新安装原生ARM64版本以获得更好性能。"
                        )
            else:
                result["recommendations"].append(
                    "未检测到Tesseract OCR。请使用'brew install tesseract'安装。"
                )
        except Exception as e:
            logger.error(f"检查Tesseract兼容性失败: {e}")
            result["recommendations"].append(f"检查Tesseract失败: {e}")
        
        # 针对M4芯片的特殊优化建议
        if self.is_apple_silicon():
            chip_info = self.get_chip_info()
            if "model" in chip_info and "M4" in chip_info["model"]:
                result["recommendations"].append(
                    "检测到M4芯片。建议使用最新版Tesseract OCR (5.5.1+)以获得最佳性能。"
                )
        
        return result
    
    def get_compatibility_report(self) -> Dict[str, Any]:
        """获取完整的兼容性报告
        
        Returns:
            Dict[str, Any]: 兼容性报告
        """
        report = {
            "system": {
                "os": platform.system(),
                "os_version": self.get_mac_version() if self._is_mac else platform.version(),
                "architecture": platform.machine(),
                "python_version": platform.python_version(),
                "python_implementation": platform.python_implementation()
            },
            "hardware": self.get_chip_info() if self._is_mac else {"error": "Not a Mac system"},
            "tesseract": self.check_tesseract_compatibility(),
            "recommendations": []
        }
        
        # 合并来自Tesseract检查的建议
        if "recommendations" in report["tesseract"]:
            report["recommendations"].extend(report["tesseract"]["recommendations"])
        
        # 针对M系列芯片的Python优化建议
        if self.is_apple_silicon():
            if not report["system"]["python_implementation"] == "CPython":
                report["recommendations"].append(
                    "建议使用CPython解释器以获得最佳性能和兼容性。"
                )
            
            # 检查是否为原生ARM64版Python
            if platform.machine() != 'arm64':
                report["recommendations"].append(
                    "当前Python解释器不是Apple Silicon原生版本。建议安装ARM64版Python以获得最佳性能。"
                )
        
        return report


# 简单使用示例
if __name__ == "__main__":
    compatibility = MacCompatibility()
    report = compatibility.get_compatibility_report()
    
    print(f"系统信息: {report['system']['os']} {report['system']['os_version']} ({report['system']['architecture']})")
    print(f"Python版本: {report['system']['python_version']} ({report['system']['python_implementation']})")
    
    if compatibility.is_mac():
        chip_info = report['hardware']
        print(f"芯片信息: {chip_info.get('brand', 'Unknown')} {chip_info.get('model', '')}")
        print(f"是否为Apple Silicon: {chip_info.get('is_apple_silicon', False)}")
        print(f"是否使用Rosetta 2: {compatibility.is_using_rosetta()}")
    
    print("\nTesseract OCR信息:")
    tesseract_info = report['tesseract']
    print(f"  已安装: {tesseract_info['tesseract_installed']}")
    if tesseract_info['tesseract_installed']:
        print(f"  版本: {tesseract_info['tesseract_version']}")
        print(f"  原生优化: {tesseract_info['is_native']}")
    
    if report['recommendations']:
        print("\n优化建议:")
        for recommendation in report['recommendations']:
            print(f"- {recommendation}") 