#!/bin/bash
# macOS 打包脚本

echo "🚀 开始打包发票 OCR 应用..."

# 检查依赖
echo "📦 检查依赖..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装"
    exit 1
fi

if ! command -v pdftoppm &> /dev/null; then
    echo "❌ 未找到 pdftoppm，正在安装..."
    brew install poppler
fi

# 安装 Python 依赖
echo "📦 安装 Python 依赖..."
/opt/homebrew/bin/python3.13 -m pip install --user -r requirements.txt

# 清理旧的构建文件
echo "🧹 清理旧的构建文件..."
rm -rf build dist

# 打包应用
echo "🔨 打包应用..."
/opt/homebrew/bin/python3.13 -m PyInstaller --name=InvoiceOCR --windowed \
  --hidden-import=invoice_ocr_sum \
  --hidden-import=invoice_ocr_simple \
  --hidden-import=openpyxl \
  --hidden-import=openpyxl.styles \
  --osx-bundle-identifier=com.invoiceocr.app \
  invoice_ocr_gui.py

# 修复代码签名
echo "🔏 签名应用..."
if [ -d "dist/InvoiceOCR.app" ]; then
    xattr -cr dist/InvoiceOCR.app
    codesign --force --deep --sign - dist/InvoiceOCR.app
fi

# 检查是否成功
if [ -d "dist/InvoiceOCR.app" ]; then
    echo "✅ 打包成功！"
    echo "📂 应用位置：dist/InvoiceOCR.app"
    echo ""
    echo "使用方法："
    echo "  1. 双击 dist/InvoiceOCR.app 运行"
    echo "  2. 或拖拽到\"应用程序\"文件夹"
    echo ""
    
    # 可选：打开应用所在目录
    read -p "是否打开应用所在目录？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open dist
    fi
else
    echo "❌ 打包失败，请检查错误信息"
    exit 1
fi
