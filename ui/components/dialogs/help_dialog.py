from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QTextBrowser,
    QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap
import platform
from loguru import logger

from ui.components.shortcut_manager import get_shortcut_manager


class HelpDialog(QDialog):
    """帮助对话框"""
    
    def __init__(self, parent=None):
        """初始化帮助对话框
        
        Args:
            parent: 父窗口
        """
        super().__init__(parent)
        
        # 设置窗口属性
        self.setWindowTitle("帮助")
        self.setMinimumSize(600, 400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # 检查平台和硬件
        self.is_mac = platform.system() == "darwin"
        self.is_apple_silicon = False
        self.mac_model = ""
        
        if self.is_mac:
            try:
                if platform.machine() == 'arm64':
                    self.is_apple_silicon = True
                    
                    # 尝试获取型号信息
                    try:
                        from config.mac_compatibility import MacCompatibility
                        mac_compat = MacCompatibility()
                        chip_info = mac_compat.get_chip_info()
                        self.mac_model = chip_info.get('model', '')
                    except:
                        pass
            except:
                pass
        
        # 设置UI
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建标签页
        tab_widget = QTabWidget()
        
        # 快捷键标签页
        shortcuts_tab = self._create_shortcuts_tab()
        tab_widget.addTab(shortcuts_tab, "快捷键")
        
        # 使用帮助标签页
        usage_tab = self._create_usage_tab()
        tab_widget.addTab(usage_tab, "使用帮助")
        
        # 优化提示标签页
        optimization_tab = self._create_optimization_tab()
        tab_widget.addTab(optimization_tab, "优化提示")
        
        # 关于标签页
        about_tab = self._create_about_tab()
        tab_widget.addTab(about_tab, "关于")
        
        layout.addWidget(tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
    
    def _create_shortcuts_tab(self):
        """创建快捷键标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 说明标签
        label = QLabel("以下是可用的键盘快捷键:")
        layout.addWidget(label)
        
        # 快捷键表格
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["功能", "快捷键"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # 获取快捷键列表
        shortcuts = get_shortcut_manager().get_shortcut_help()
        table.setRowCount(len(shortcuts))
        
        for i, shortcut in enumerate(shortcuts):
            description_item = QTableWidgetItem(shortcut["description"])
            key_item = QTableWidgetItem(shortcut["key_sequence"])
            
            table.setItem(i, 0, description_item)
            table.setItem(i, 1, key_item)
        
        layout.addWidget(table)
        
        # Mac特有提示
        if self.is_mac:
            note_label = QLabel("注: 在Mac系统上，Ctrl键对应Command (⌘) 键")
            note_label.setStyleSheet("color: gray; font-style: italic;")
            layout.addWidget(note_label)
        
        return tab
    
    def _create_usage_tab(self):
        """创建使用帮助标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 使用帮助文本浏览器
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        
        html_content = """
        <h2>Tesseract OCR监控软件使用帮助</h2>
        
        <h3>基本功能</h3>
        <ol>
            <li><b>OCR识别</b>: 选择屏幕区域，软件将识别区域内的文字。</li>
            <li><b>监控规则</b>: 设置文字匹配规则，当识别结果符合规则时触发动作。</li>
            <li><b>自动动作</b>: 可以设置键盘输入、鼠标点击等自动响应动作。</li>
            <li><b>多任务管理</b>: 支持同时运行多个监控任务，每个任务可以有不同的设置。</li>
        </ol>
        
        <h3>开始使用</h3>
        <ol>
            <li>在OCR标签页中选择屏幕区域</li>
            <li>设置监控规则与匹配条件</li>
            <li>配置当规则匹配时要执行的动作</li>
            <li>启动监控任务</li>
        </ol>
        
        <h3>常见问题</h3>
        <p><b>问题</b>: OCR识别不准确怎么办？</p>
        <p><b>解答</b>: 可以尝试调整OCR参数，如PSM模式、OEM引擎等，或者使用图像预处理功能提高识别率。</p>
        
        <p><b>问题</b>: 如何提高监控性能？</p>
        <p><b>解答</b>: 可以减少监控区域大小，调整刷新频率，或使用优化模式。</p>
        """
        
        # 为Mac M系列芯片添加特殊说明
        if self.is_apple_silicon:
            html_content += """
            <h3>M系列芯片专属功能</h3>
            <p>检测到您正在使用Apple Silicon芯片，以下是一些专属功能:</p>
            <ul>
                <li><b>优化性能</b>: 使用Ctrl+Shift+P快捷键可快速切换性能优化模式</li>
                <li><b>高效OCR</b>: 针对M系列芯片优化的文本识别流程</li>
                <li><b>智能缓存</b>: 自适应缓存策略，减少内存占用</li>
            </ul>
            """
        
        html_content += """
        <h3>更多帮助</h3>
        <p>如需更多帮助，请查看 <a href="https://github.com/yourusername/Tesseract_OCR">项目文档</a>。</p>
        """
        
        text_browser.setHtml(html_content)
        layout.addWidget(text_browser)
        
        return tab
    
    def _create_optimization_tab(self):
        """创建优化提示标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 优化提示文本浏览器
        text_browser = QTextBrowser()
        
        html_content = """
        <h2>软件优化提示</h2>
        
        <h3>通用优化建议</h3>
        <ul>
            <li><b>减少监控区域</b>: 较小的区域可以提高OCR识别速度和准确率</li>
            <li><b>调整刷新频率</b>: 根据实际需要设置合适的刷新频率，避免不必要的资源消耗</li>
            <li><b>使用缓存</b>: 启用OCR结果缓存可以减少重复识别，提高响应速度</li>
            <li><b>优化规则</b>: 精简规则设计，避免复杂的条件组合</li>
            <li><b>正确选择OCR引擎</b>: 根据识别内容选择合适的OCR引擎和参数</li>
        </ul>
        """
        
        # 根据系统平台添加特定优化建议
        if self.is_mac:
            html_content += """
            <h3>Mac系统优化建议</h3>
            <ul>
                <li><b>授予必要权限</b>: 确保应用有屏幕录制和辅助功能权限</li>
                <li><b>使用原生Tesseract</b>: 安装ARM64原生编译的Tesseract OCR</li>
                <li><b>关闭不必要的后台任务</b>: 减少系统资源占用</li>
            </ul>
            """
            
            if self.is_apple_silicon:
                # M系列芯片特定优化建议
                html_content += """
                <h3>Apple Silicon优化建议</h3>
                <ul>
                    <li><b>安装原生ARM64 Python</b>: 确保使用原生编译的Python和依赖库</li>
                    <li><b>使用优化模式</b>: 在设置中启用"M系列芯片优化"选项</li>
                    <li><b>更新系统</b>: 保持macOS系统为最新版本，获取性能改进</li>
                    <li><b>监控资源使用</b>: 使用Activity Monitor监控CPU和内存使用情况</li>
                </ul>
                """
                
                # M4芯片特定优化
                if "M4" in self.mac_model:
                    html_content += """
                    <h3>M4芯片特定优化</h3>
                    <ul>
                        <li><b>启用高级缓存</b>: M4芯片拥有更大的缓存，适合增加OCR缓存大小</li>
                        <li><b>开启Neural Engine加速</b>: 在设置中启用Neural Engine支持</li>
                        <li><b>并行任务</b>: M4芯片可以高效处理多个并行监控任务</li>
                    </ul>
                    """
        else:
            # 其他系统的优化建议
            html_content += """
            <h3>Windows/Linux优化建议</h3>
            <ul>
                <li><b>更新显卡驱动</b>: 最新的显卡驱动可以提高屏幕捕获性能</li>
                <li><b>关闭视觉特效</b>: 减少系统视觉特效可以提高响应速度</li>
                <li><b>使用独立显卡</b>: 如有独立显卡，建议设置程序使用独立显卡运行</li>
            </ul>
            """
        
        text_browser.setHtml(html_content)
        layout.addWidget(text_browser)
        
        return tab
    
    def _create_about_tab(self):
        """创建关于标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 应用标题
        title_label = QLabel("Tesseract OCR监控软件")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 版本信息
        version_label = QLabel("版本: 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # 应用描述
        desc_label = QLabel("基于Python 3.9和Tesseract OCR的屏幕监控软件，可以监控屏幕指定区域的文字内容，当识别到特定文本时触发预设动作。")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        # 系统信息
        sys_info = f"系统: {platform.system()} {platform.release()}"
        if self.is_mac and self.is_apple_silicon:
            sys_info += f" (Apple Silicon{' ' + self.mac_model if self.mac_model else ''})"
        sys_label = QLabel(sys_info)
        sys_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(sys_label)
        
        # Python信息
        py_label = QLabel(f"Python: {platform.python_version()}")
        py_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(py_label)
        
        # 版权信息
        copyright_label = QLabel("© 2025 Your Company")
        copyright_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright_label)
        
        # 许可证信息
        license_label = QLabel("本软件基于MIT许可证发布")
        license_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(license_label)
        
        layout.addStretch()
        
        return tab 