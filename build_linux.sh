#!/bin/bash
# Linux 打包脚本

echo "🚀 开始打包发票 OCR 应用 (Linux)..."

# 检查依赖
echo "📦 检查依赖..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装"
    exit 1
fi

if ! command -v pdftoppm &> /dev/null; then
    echo "⚠️  未找到 pdftoppm，正在尝试安装..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y poppler-utils
    elif command -v yum &> /dev/null; then
        sudo yum install -y poppler-utils
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y poppler-utils
    else
        echo "❌ 无法自动安装 poppler-utils，请手动安装"
        exit 1
    fi
fi

# 安装 Python 依赖
echo "📦 安装 Python 依赖..."
python3 -m pip install --user -r requirements.txt

# 清理旧的构建文件
echo "🧹 清理旧的构建文件..."
rm -rf build dist

# 查找 pdftoppm 路径
PDFTOPPM_PATH=$(which pdftoppm)
if [ -z "$PDFTOPPM_PATH" ]; then
    echo "❌ 未找到 pdftoppm，请先安装: sudo apt-get install poppler-utils"
    exit 1
fi

echo "📝 找到 pdftoppm: $PDFTOPPM_PATH"

# 打包应用（包含 pdftoppm）
echo "🔨 打包应用..."
python3 -m PyInstaller \
  --name=InvoiceOCR \
  --onefile \
  --windowed \
  --hidden-import=invoice_ocr_sum \
  --hidden-import=invoice_ocr_simple \
  --hidden-import=ocr_api \
  --hidden-import=openpyxl \
  --hidden-import=openpyxl.styles \
  --add-binary="$PDFTOPPM_PATH:bin" \
  --collect-all=poppler \
  invoice_ocr_gui.py

# 检查是否成功
if [ -f "dist/InvoiceOCR" ]; then
    echo "✅ 打包成功！"
    echo "📂 应用位置：dist/InvoiceOCR"
    echo ""
    echo "使用方法："
    echo "  1. 运行: ./dist/InvoiceOCR"
    echo "  2. 或复制到系统路径: sudo cp dist/InvoiceOCR /usr/local/bin/"
    echo ""
    
    # 设置可执行权限
    chmod +x dist/InvoiceOCR
    
    # 可选：打开应用所在目录
    read -p "是否打开应用所在目录？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        xdg-open dist 2>/dev/null || nautilus dist 2>/dev/null || dolphin dist 2>/dev/null || echo "请手动打开 dist 目录"
    fi
else
    echo "❌ 打包失败，请检查错误信息"
    exit 1
fi
