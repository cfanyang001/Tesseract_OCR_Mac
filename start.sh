#!/bin/bash
# Tesseract OCR监控软件启动脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}   Tesseract OCR监控软件启动脚本     ${NC}"
echo -e "${BLUE}=======================================${NC}"

# 检查Python环境
echo -e "${GREEN}[1/5] 检查Python环境...${NC}"
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
    echo -e "  ${GREEN}✓ 找到Python: $(python3 --version)${NC}"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
    echo -e "  ${GREEN}✓ 找到Python: $(python --version)${NC}"
else
    echo -e "  ${RED}✗ 未找到Python，请安装Python 3.8+${NC}"
    exit 1
fi

# 检查Python版本
PY_VER=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
# 使用Python自身比较版本，避免依赖bc命令
PY_VER_CHECK=$($PYTHON_CMD -c "import sys; print(sys.version_info >= (3, 8))")
if [ "$PY_VER_CHECK" = "False" ]; then
    echo -e "  ${YELLOW}⚠ Python版本过低: $PY_VER，推荐使用Python 3.8+${NC}"
else
    echo -e "  ${GREEN}✓ Python版本符合要求: $PY_VER${NC}"
fi

# 检查虚拟环境
echo -e "${GREEN}[2/5] 检查虚拟环境...${NC}"
if [ -d "venv" ] || [ -d "env" ]; then
    if [ -d "venv/bin" ] || [ -d "venv/Scripts" ]; then
        ENV_DIR="venv"
    elif [ -d "env/bin" ] || [ -d "env/Scripts" ]; then
        ENV_DIR="env"
    fi

    # 激活虚拟环境
    if [ -f "$ENV_DIR/bin/activate" ]; then
        source "$ENV_DIR/bin/activate"
        echo -e "  ${GREEN}✓ 已激活虚拟环境: $ENV_DIR${NC}"
    elif [ -f "$ENV_DIR/Scripts/activate" ]; then
        source "$ENV_DIR/Scripts/activate"
        echo -e "  ${GREEN}✓ 已激活虚拟环境: $ENV_DIR${NC}"
    else
        echo -e "  ${YELLOW}⚠ 发现虚拟环境目录，但无法激活${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ 未检测到虚拟环境，将使用系统Python${NC}"
fi

# 检查系统环境
echo -e "${GREEN}[3/5] 检查系统环境...${NC}"

# 检测操作系统
OS=$(uname -s)
if [ "$OS" = "Darwin" ]; then
    echo -e "  ${GREEN}✓ 检测到macOS系统${NC}"
    
    # 检测Apple Silicon
    ARCH=$(uname -m)
    if [ "$ARCH" = "arm64" ]; then
        echo -e "  ${GREEN}✓ 检测到Apple Silicon架构${NC}"
        
        # 检查Rosetta状态
        if [ -x "$(command -v arch)" ]; then
            if [ "$(arch)" = "arm64" ]; then
                echo -e "  ${GREEN}✓ 使用原生ARM64模式${NC}"
            else
                echo -e "  ${YELLOW}⚠ 使用Rosetta 2模拟运行，性能可能受影响${NC}"
            fi
        fi
        
        # 设置M系列芯片优化环境变量
        export PYTHONUNBUFFERED=1
        export VECLIB_MAXIMUM_THREADS=4
        export NUMEXPR_MAX_THREADS=4
        
        # 检查Tesseract是否是原生ARM64版本
        if command -v tesseract &>/dev/null; then
            TESSERACT_BIN=$(which tesseract)
            if file "$TESSERACT_BIN" | grep -q "arm64"; then
                echo -e "  ${GREEN}✓ 检测到原生ARM64 Tesseract OCR${NC}"
            else
                echo -e "  ${YELLOW}⚠ Tesseract OCR可能不是ARM64原生版本，性能可能受影响${NC}"
            fi
        fi
    else
        echo -e "  ${GREEN}✓ 检测到Intel架构${NC}"
    fi
elif [ "$OS" = "Linux" ]; then
    echo -e "  ${GREEN}✓ 检测到Linux系统${NC}"
else
    echo -e "  ${GREEN}✓ 检测到${OS}系统${NC}"
fi

# 检查Tesseract
echo -e "${GREEN}[4/5] 检查Tesseract OCR...${NC}"
if command -v tesseract &>/dev/null; then
    TESSERACT_VERSION=$(tesseract --version 2>&1 | head -n1)
    echo -e "  ${GREEN}✓ 找到Tesseract: $TESSERACT_VERSION${NC}"
else
    echo -e "  ${RED}✗ 未找到Tesseract OCR${NC}"
    
    # 提供安装建议
    if [ "$OS" = "Darwin" ]; then
        echo -e "  ${YELLOW}推荐安装命令: brew install tesseract${NC}"
    elif [ "$OS" = "Linux" ]; then
        echo -e "  ${YELLOW}推荐安装命令: sudo apt-get install tesseract-ocr${NC}"
    else
        echo -e "  ${YELLOW}请安装Tesseract OCR后再运行${NC}"
    fi
    
    echo -e "  ${YELLOW}是否继续? (y/n)${NC}"
    read -r answer
    if [[ "$answer" != "y" && "$answer" != "Y" ]]; then
        echo -e "${RED}退出安装${NC}"
        exit 1
    fi
fi

# 检查依赖
echo -e "${GREEN}[5/5] 检查依赖项...${NC}"
$PYTHON_CMD -c "import PyQt6" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "  ${YELLOW}⚠ 缺少PyQt6依赖${NC}"
    echo -e "  ${YELLOW}是否安装依赖? (y/n)${NC}"
    read -r answer
    if [[ "$answer" = "y" || "$answer" = "Y" ]]; then
        echo -e "  ${GREEN}正在安装依赖...${NC}"
        pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo -e "  ${RED}✗ 依赖安装失败${NC}"
            exit 1
        else
            echo -e "  ${GREEN}✓ 依赖安装完成${NC}"
        fi
    fi
else
    echo -e "  ${GREEN}✓ PyQt6依赖已安装${NC}"
fi

# 检查main.py文件是否存在
if [ ! -f "main.py" ]; then
    echo -e "${RED}错误：main.py文件不存在，无法启动程序${NC}"
    exit 1
fi

# 确保main.py有执行权限
chmod +x main.py

echo -e "${BLUE}=======================================${NC}"
echo -e "${GREEN}所有检查完成，正在启动应用程序...${NC}"
echo -e "${BLUE}=======================================${NC}"

# 创建日志目录
mkdir -p logs

# 启动应用程序
$PYTHON_CMD main.py "$@" 