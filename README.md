# Tesseract OCR监控软件

基于Python 3.9和Tesseract OCR的屏幕监控软件，可以监控屏幕指定区域的文字内容，当识别到特定文本时触发预设动作。

## 功能特点

- 基于Tesseract OCR的文字识别
- 屏幕区域选择与截图
- 自定义监控规则与触发条件
- 多种自动化动作（键盘输入、鼠标点击等）
- 多线程后台任务管理
- 用户友好的GUI界面

## 系统要求

- macOS系统（适配M系列芯片）
- Python 3.9
- Tesseract OCR 5.5.1+

## 安装指南

1. 安装Tesseract OCR:
```bash
brew install tesseract
```

2. 克隆仓库:
```bash
git clone https://github.com/yourusername/Tesseract_OCR.git
cd Tesseract_OCR
```

3. 创建并激活Python虚拟环境:
```bash
python3.9 -m venv venv
source venv/bin/activate
```

4. 安装依赖:
```bash
pip install -r requirements.txt
```

## 使用方法

1. 启动应用:
```bash
python main.py
```

2. 在OCR标签页中选择屏幕区域
3. 设置监控规则与触发条件
4. 配置自动化动作
5. 启动监控任务

## 项目结构

- `core/`: 核心功能模块
  - `ocr_processor.py`: OCR文字识别处理
  - `screen_capture.py`: 屏幕捕获功能
  - `action_executor.py`: 动作执行系统
  - `monitor_engine.py`: 监控引擎
  - `task_manager.py`: 任务管理器
  - `utils/`: 工具函数
- `ui/`: 用户界面
  - `components/`: UI组件
  - `controllers/`: 控制器
  - `resources/`: 资源文件
- `config/`: 配置管理
- `tests/`: 测试用例

## 许可证

MIT

## 贡献指南

欢迎提交问题和拉取请求。
