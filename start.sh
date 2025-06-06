#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查系统类型
echo -e "${BLUE}检查系统环境...${NC}"
OS_TYPE=$(uname -s)
ARCH_TYPE=$(uname -m)

# 检查是否为Apple Silicon
if [[ "$OS_TYPE" == "Darwin" && "$ARCH_TYPE" == "arm64" ]]; then
    echo -e "${GREEN}检测到Apple Silicon芯片，应用性能优化...${NC}"
    
    # 检查Tesseract是否安装
    if ! command -v tesseract &> /dev/null; then
        echo -e "${RED}未检测到Tesseract OCR。${NC}"
        echo -e "${YELLOW}请使用以下命令安装: brew install tesseract${NC}"
        read -p "是否继续启动程序? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        TESSERACT_VERSION=$(tesseract --version 2>&1 | head -n 1)
        echo -e "${GREEN}检测到$TESSERACT_VERSION${NC}"
        
        # 检查是否为原生ARM64版本
        TESSERACT_FILE=$(which tesseract)
        if file "$TESSERACT_FILE" | grep -q "arm64"; then
            echo -e "${GREEN}Tesseract已针对Apple Silicon优化${NC}"
        else
            echo -e "${YELLOW}Tesseract非原生ARM64版本，可能影响性能${NC}"
            echo -e "${YELLOW}建议使用Homebrew重新安装: brew reinstall tesseract${NC}"
        fi
    fi
    
    # 检查是否存在python-Levenshtein库
    if ! python3 -c "import Levenshtein" &> /dev/null; then
        echo -e "${YELLOW}未检测到python-Levenshtein库，将使用备用算法${NC}"
        echo -e "${YELLOW}建议安装以提高性能: pip install python-Levenshtein${NC}"
    fi
    
    # 设置Apple Silicon优化环境变量
    export PYTHONUNBUFFERED=1
    export VECLIB_MAXIMUM_THREADS=4
    export NUMEXPR_MAX_THREADS=4
fi

# 输出启动信息
echo -e "${GREEN}正在启动 Tesseract OCR监控软件...${NC}"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}未检测到虚拟环境，创建新的虚拟环境...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# 启动程序
python main.py

# 如果程序异常退出，显示提示信息
if [ $? -ne 0 ]; then
    echo -e "${RED}程序异常退出，请检查日志获取详细信息${NC}"
    echo -e "${YELLOW}日志位置: $SCRIPT_DIR/logs/${NC}"
    read -p "按任意键退出..." -n1 -s
fi

# 退出虚拟环境
deactivate 