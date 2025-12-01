@echo off
REM Windows 打包脚本

echo 🚀 开始打包发票 OCR 应用...

REM 检查 Python
echo 📦 检查依赖...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装
    pause
    exit /b 1
)

REM 检查 pdftoppm
pdftoppm -v >nul 2>&1
if errorlevel 1 (
    echo ⚠️  未找到 pdftoppm，请确保已安装 poppler-utils
    echo 下载地址: https://github.com/oschwartz10612/poppler-windows/releases
    pause
)

REM 安装 Python 依赖
echo 📦 安装 Python 依赖...
pip install -r requirements.txt

REM 清理旧的构建文件
echo 🧹 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 打包应用
echo 🔨 打包应用...
pyinstaller invoice_ocr_gui.spec

REM 检查是否成功
if exist "dist\InvoiceOCR.exe" (
    echo ✅ 打包成功！
    echo 📂 应用位置：dist\InvoiceOCR.exe
    echo.
    echo 使用方法：
    echo   双击 dist\InvoiceOCR.exe 运行
    echo.
    
    REM 打开应用所在目录
    explorer dist
) else (
    echo ❌ 打包失败，请检查错误信息
    pause
    exit /b 1
)

pause
