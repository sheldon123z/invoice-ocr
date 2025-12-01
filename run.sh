#!/bin/bash
# 快速启动脚本

cd "$(dirname "$0")"

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 setup.sh"
    exit 1
fi

# 激活虚拟环境并运行
echo "🚀 启动发票 OCR 图形界面..."
source .venv/bin/activate
python3 invoice_ocr_gui.py
