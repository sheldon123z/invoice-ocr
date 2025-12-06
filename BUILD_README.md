# 发票 OCR 图形界面应用程序打包指南

## 📦 功能特性

- 🖥️ 跨平台支持（macOS 和 Windows）
- 🎨 简洁的图形界面
- 🚀 快速模式和完整分析模式
- ⚙️ 灵活的配置选项
- 📊 Excel 报告生成
- 🔄 自动文件重命名
- 💾 配置自动保存

## 🛠️ 环境准备

### 系统依赖

#### macOS
```bash
# 安装 pdftoppm (通过 poppler)
brew install poppler

# 确保有 Python 3.8+
python3 --version
```

#### Windows
```bash
# 下载并安装 poppler-utils for Windows
# 下载地址: https://github.com/oschwartz10612/poppler-windows/releases
# 将 poppler/bin 目录添加到系统 PATH

# 确保有 Python 3.8+
python --version
```

### Python 依赖

```bash
# 安装依赖包
pip install -r requirements.txt
```

## 🚀 打包步骤

### 方法 1: 使用 spec 配置文件（推荐）

#### macOS
```bash
# 打包为 .app 应用
pyinstaller invoice_ocr_gui.spec

# 生成的应用位置：dist/InvoiceOCR.app
# 可以直接拖拽到"应用程序"文件夹使用
```

#### Windows
```bash
# 使用相同的 spec 文件打包
pyinstaller invoice_ocr_gui.spec

# 生成的应用位置：dist\InvoiceOCR.exe
```

### 方法 2: 使用命令行参数

#### macOS
```bash
pyinstaller --name="InvoiceOCR" \
  --windowed \
  --onefile \
  --add-data "invoice_ocr_sum.py:." \
  --add-data "invoice_ocr_simple.py:." \
  --hidden-import=openpyxl \
  --hidden-import=openpyxl.styles \
  invoice_ocr_gui.py
```

#### Windows
```bash
pyinstaller --name="InvoiceOCR" ^
  --windowed ^
  --onefile ^
  --add-data "invoice_ocr_sum.py;." ^
  --add-data "invoice_ocr_simple.py;." ^
  --hidden-import=openpyxl ^
  --hidden-import=openpyxl.styles ^
  invoice_ocr_gui.py
```

## 📝 打包说明

### 参数解释

- `--windowed`: 不显示控制台窗口（GUI 应用）
- `--onefile`: 打包成单个可执行文件
- `--name`: 应用名称
- `--add-data`: 包含额外的数据文件
- `--hidden-import`: 包含隐式导入的模块
- `--icon`: 应用图标（可选）

### 文件结构

打包后的目录结构：

```
dist/
├── InvoiceOCR.app (macOS)
└── InvoiceOCR.exe (Windows)

build/  # 临时构建文件，可以删除
```

## 🎯 使用说明

### 启动应用

#### macOS
1. 双击 `InvoiceOCR.app`
2. 如遇到"无法打开"的提示，右键点击选择"打开"
3. 或在终端运行：`open dist/InvoiceOCR.app`

#### Windows
1. 双击 `InvoiceOCR.exe`
2. 如遇到 Windows Defender 警告，选择"仍要运行"

### 界面操作

1. **设置标签页**
   - 配置 Ollama 服务器地址（默认：192.168.110.219）
   - 设置端口（默认：11434）
   - 选择模型（默认：qwen3-vl:8b）
   - 点击"测试连接"确保服务器可用
   - 点击"保存设置"保存配置

2. **处理发票标签页**
   - 点击"浏览"选择发票所在目录
   - 选择处理模式：
     - 🚀 快速模式：仅识别金额
     - 📊 完整模式：提取完整信息并分析
   - 勾选需要的选项：
     - 生成 Excel 报告
     - 文件重命名
     - 验证发票
   - 点击"开始处理"

3. **查看结果**
   - 实时查看处理进度和日志
   - 处理完成后在发票目录查看生成的报告

## 🔧 配置文件

应用配置保存在：
- macOS: `~/.invoice_ocr_config.json`
- Windows: `C:\Users\<用户名>\.invoice_ocr_config.json`

配置内容包括：
```json
{
  "ollama_host": "192.168.110.219",
  "ollama_port": 11434,
  "ollama_model": "qwen3-vl:8b",
  "max_retries": 3,
  "scan_directory": "",
  "mode": "simple",
  "enable_excel": true,
  "enable_rename": false,
  "enable_validate": true
}
```

## ⚠️ 注意事项

### macOS
1. 首次运行可能需要在"系统偏好设置 > 安全性与隐私"中允许运行
2. 确保 `pdftoppm` 已安装且在 PATH 中
3. 如需签名发布，需要 Apple Developer 账号

### Windows
1. 确保 poppler 工具已安装并添加到 PATH
2. 可能需要安装 Visual C++ Redistributable
3. 杀毒软件可能会误报，需要添加信任

### 通用
1. 必须能访问 Ollama 服务器
2. 需要网络权限（访问 Ollama API）
3. 需要文件系统读写权限

## 🐛 故障排除

### 问题 1: 无法启动应用
- 检查是否有 Python 运行时错误
- 尝试在终端运行查看错误信息：
  - macOS: `./dist/InvoiceOCR.app/Contents/MacOS/InvoiceOCR`
  - Windows: 在 cmd 中运行 `InvoiceOCR.exe`

### 问题 2: 无法连接 Ollama
- 检查服务器地址和端口是否正确
- 确保防火墙允许连接
- 使用"测试连接"功能验证

### 问题 3: PDF 处理失败
- 检查 pdftoppm/poppler 是否已安装
- 验证 PATH 环境变量

### 问题 4: Excel 导出失败
- 确保 openpyxl 已正确打包
- 检查目标目录是否有写权限

## 📄 许可证

本项目仅供学习和内部使用。

## 🔄 更新日志

### v1.0.0 (2025-12-01)
- 初始版本
- 支持快速和完整两种识别模式
- 跨平台 GUI 界面
- 配置管理功能u
