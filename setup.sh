#!/bin/bash
# 环境设置脚本

cd "$(dirname "$0")"

echo "🔧 设置发票 OCR 项目环境..."

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装"
    exit 1
fi

# 检查 pdftoppm
if ! command -v pdftoppm &> /dev/null; then
    echo "📦 安装 pdftoppm (poppler)..."
    brew install poppler
fi

# 创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    if command -v uv &> /dev/null; then
        uv venv
    else
        python3 -m venv .venv
    fi
fi

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
echo "📦 安装依赖..."
pip install -r requirements.txt

echo ""
echo "✅ 环境设置完成！"
echo ""
echo "使用方法："
echo "  ./run.sh              # 启动图形界面"
echo "  ./build_mac.sh        # 打包成 macOS 应用"
echo ""
