#!/bin/bash

# Agent Mesh 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Agent Mesh 启动脚本 ===${NC}"

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到python3${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "Python版本: ${PYTHON_VERSION}"

# 创建必要的目录
mkdir -p data logs

# 检查依赖
echo -e "${YELLOW}检查依赖...${NC}"
if ! python3 -c "import websockets" 2>/dev/null; then
    echo -e "${YELLOW}安装依赖...${NC}"
    pip3 install -r requirements.txt --quiet
fi

# 启动服务器
echo -e "${GREEN}启动Agent Mesh服务器...${NC}"
echo -e "WebSocket: ws://127.0.0.1:18800"
echo -e "Web界面: http://127.0.0.1:18801"
echo ""

python3 -m server.main "$@"
