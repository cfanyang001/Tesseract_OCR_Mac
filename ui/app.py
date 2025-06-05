import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from ui.components.main_window import MainWindow


class App:
    """应用程序主类，负责初始化和启动应用程序"""
    
    def __init__(self):
        # 创建QApplication实例
        self.app = QApplication(sys.argv)
        
        # 设置应用程序样式
        self.setup_style()
        
        # 创建主窗口
        self.main_window = MainWindow()
    
    def setup_style(self):
        """设置应用程序样式"""
        # 设置应用程序属性
        self.app.setApplicationName("Tesseract OCR监控软件")
        self.app.setApplicationVersion("1.0.0")
        self.app.setOrganizationName("Tesseract OCR")
        
        # 设置全局样式
        self.app.setStyle("Fusion")
    
    def run(self):
        """运行应用程序"""
        # 显示主窗口
        self.main_window.show()
        
        # 进入应用程序主循环
        return self.app.exec_()


def run_app():
    """启动应用程序的便捷函数"""
    app = App()
    return app.run()


if __name__ == "__main__":
    sys.exit(run_app())
