#!/bin/bash
# 开发环境设置脚本

echo "🔧 设置开发环境..."

# 检查 Python 3.13
if ! command -v /opt/homebrew/bin/python3.13 &> /dev/null; then
    echo "❌ 未找到 Python 3.13"
    echo "请运行: brew install python@3.13"
    exit 1
fi

# 检查 python-tk
if ! /opt/homebrew/bin/python3.13 -c "import tkinter" 2>/dev/null; then
    echo "❌ 未找到 tkinter"
    echo "正在安装 python-tk..."
    brew install python-tk@3.13
fi

# 安装依赖到用户目录
echo "📦 安装 Python 依赖..."
/opt/homebrew/bin/python3.13 -m pip install --user --break-system-packages -r requirements.txt

# 创建运行别名
echo ""
echo "✅ 开发环境设置完成！"
echo ""
echo "使用以下命令运行应用："
echo "  /opt/homebrew/bin/python3.13 invoice_ocr_gui.py"
echo ""
echo "或者添加别名到 ~/.zshrc:"
echo "  alias python=/opt/homebrew/bin/python3.13"
