@echo off
REM Windows 打包脚本

echo 开始打包发票 OCR 应用...

REM 检查 Python
echo 检查依赖...
python --version >nul 2>&1
if errorlevel 1 (
    echo 未找到 Python，请先安装
    if not defined CI pause
    exit /b 1
)

REM 安装 Python 依赖
echo 安装 Python 依赖...
pip install -r requirements.txt
pip install pyinstaller

REM 清理旧的构建文件
echo 清理旧的构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 打包应用（使用 Windows 专用 spec 文件）
echo 打包应用...
pyinstaller InvoiceOCR_windows.spec

REM 检查是否成功
if exist "dist\InvoiceOCR.exe" (
    echo 打包成功！
    echo 应用位置：dist\InvoiceOCR.exe
    echo.
    echo 使用方法：
    echo   双击 dist\InvoiceOCR.exe 运行
    echo.

    REM 非 CI 环境下打开应用所在目录
    if not defined CI explorer dist
) else (
    echo 打包失败，请检查错误信息
    if not defined CI pause
    exit /b 1
)

if not defined CI pause
