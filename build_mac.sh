#!/bin/bash
# macOS 打包脚本

set -e  # 遇错退出

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

# 创建虚拟环境
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv "$VENV_DIR"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 安装 Python 依赖
echo "📦 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# 清理旧的构建文件
echo "🧹 清理旧的构建文件..."
rm -rf build dist *.spec

# 准备打包二进制文件
echo "📦 准备 pdftoppm 及依赖库..."
PDFTOPPM_PATH="/opt/homebrew/bin/pdftoppm"
if [ ! -f "$PDFTOPPM_PATH" ]; then
    echo "❌ 未找到 pdftoppm，请先安装: brew install poppler"
    exit 1
fi

# 打包应用（包含 pdftoppm）
echo "🔨 打包应用..."
python -m PyInstaller --name=InvoiceOCR --windowed \
  --hidden-import=invoice_ocr_sum \
  --hidden-import=invoice_ocr_simple \
  --hidden-import=openpyxl \
  --hidden-import=openpyxl.styles \
  --add-binary="$PDFTOPPM_PATH:bin" \
  --osx-bundle-identifier=com.invoiceocr.app \
  --noconfirm \
  invoice_ocr_gui.py

# 手动复制 poppler 库文件
echo "📚 复制 poppler 库文件..."
if [ -d "dist/InvoiceOCR.app" ]; then
    FRAMEWORKS_DIR="dist/InvoiceOCR.app/Contents/Frameworks"
    mkdir -p "$FRAMEWORKS_DIR"
    
    # 复制 poppler 依赖库
    if [ -d "/opt/homebrew/opt/poppler/lib" ]; then
        cp -f /opt/homebrew/opt/poppler/lib/libpoppler*.dylib "$FRAMEWORKS_DIR/" 2>/dev/null || true
    fi
    if [ -d "/opt/homebrew/opt/little-cms2/lib" ]; then
        cp -f /opt/homebrew/opt/little-cms2/lib/liblcms2*.dylib "$FRAMEWORKS_DIR/" 2>/dev/null || true
    fi
    
    # 修复库的 rpath
    if [ -f "dist/InvoiceOCR.app/Contents/MacOS/bin/pdftoppm" ]; then
        install_name_tool -add_rpath "@executable_path/../Frameworks" \
            "dist/InvoiceOCR.app/Contents/MacOS/bin/pdftoppm" 2>/dev/null || true
    fi
fi

# 修复代码签名
echo "🔏 签名应用..."
if [ -d "dist/InvoiceOCR.app" ]; then
    chmod -R u+w dist/InvoiceOCR.app 2>/dev/null || true
    xattr -cr dist/InvoiceOCR.app 2>/dev/null || true
    codesign --force --deep --sign - dist/InvoiceOCR.app 2>/dev/null || echo "⚠️  代码签名可选，忽略错误"
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

    # 非 CI 环境下可选打开应用所在目录
    if [ -z "$CI" ] && [ -t 0 ]; then
        read -p "是否打开应用所在目录？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            open dist
        fi
    fi
else
    echo "❌ 打包失败，请检查错误信息"
    exit 1
fi
