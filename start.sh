#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 输出启动信息
echo -e "${GREEN}正在启动 Tesseract OCR监控软件...${NC}"

# 激活虚拟环境并启动程序
source venv/bin/activate
python main.py

# 如果程序异常退出，显示提示信息
if [ $? -ne 0 ]; then
    echo -e "${RED}程序异常退出，请检查日志获取详细信息${NC}"
    echo -e "${YELLOW}日志位置: $SCRIPT_DIR/logs/${NC}"
    read -p "按任意键退出..." -n1 -s
fi

# 退出虚拟环境
deactivate 