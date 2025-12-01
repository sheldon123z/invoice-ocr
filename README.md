# 发票 OCR 识别工具

## 📝 简介

一个简单易用的发票 OCR 识别工具，支持图形界面操作，可以批量识别发票并生成统计报告。

## ✨ 特性

- 🖥️ **跨平台**：支持 macOS、Windows 和 Linux
- 🎨 **图形界面**：无需命令行，简单易用
- 🚀 **双模式**：
  - 快速模式：仅识别金额
  - 完整模式：提取详细信息并统计分析
- 🔌 **多 API 支持**：支持 Ollama、火山引擎和 OpenRouter （400+ 模型）
- ⚙️ **灵活配置**：可自定义服务器地址、API Key、模型等
- 📊 **智能分析**：按月份、供应商、金额区间统计
- 📈 **报告导出**：生成 Markdown 和 Excel 报告
- 🔄 **自动重命名**：按“金额-购买方”格式重命名文件

## 🚀 快速开始

### 方式一：使用打包好的应用（推荐）

从 [Releases](https://github.com/sheldon123z/invoice-ocr/releases) 下载对应平台的应用：
- **macOS**: 下载 `InvoiceOCR-macOS.zip`，解压后运行 `InvoiceOCR.app`
- **Windows**: 下载 `InvoiceOCR-Windows.zip`，解压后运行 `InvoiceOCR.exe`

### 方式二：从源码运行

#### macOS

```bash
# 1. 设置开发环境（首次）
./setup_dev.sh

# 2. 运行应用
/opt/homebrew/bin/python3.13 invoice_ocr_gui.py
```

### 方式三：自己打包应用

#### macOS

```bash
# 运行打包脚本
./build_mac.sh

# 打包好的应用在 dist/InvoiceOCR.app
```

#### Windows

```bash
# 1. 安装打包工具
pip install pyinstaller openpyxl

# 2. 运行打包脚本
build_windows.bat

# 3. 使用应用
# 在 dist\InvoiceOCR.exe 找到打包好的应用
```

#### Linux

```bash
# 运行打包脚本
chmod +x build_linux.sh
./build_linux.sh

# 打包好的应用在 dist/InvoiceOCR
# 可以直接运行或复制到系统路径
```

## 📖 使用说明

### 1. 配置 API 提供商（首次使用）

1. 打开应用，切换到“⚙️ 设置”标签
2. 选择 API 提供商：
   - **Ollama**：本地/局域网服务器
     - 配置服务器地址、端口和模型名
   - **火山引擎**：字节跳动的 AI 服务
     - 需要 API Key 和 Endpoint ID（从火山方舟控制台获取）
   - **OpenRouter**：聚合 400+ 模型的统一 API
     - 需要 API Key 和模型名（如 google/gemini-2.0-flash-exp:free）
3. 点击“🔌 测试连接”验证配置
4. 点击“💾 保存设置”

### 2. 处理发票

1. 切换到"📋 处理发票"标签
2. 点击"浏览..."选择发票所在目录
3. 选择处理模式：
   - **🚀 快速模式**：仅识别金额，速度快
   - **📊 完整模式**：提取完整信息，支持详细分析
4. 勾选需要的选项：
   - ✅ 生成 Excel 报告
   - ✅ 文件重命名
   - ✅ 验证发票
5. 点击"🚀 开始处理"

### 3. 查看结果

- 实时日志显示在界面中
- 处理完成后，在发票目录查看：
  - `invoice_summary.md` - Markdown 报告
  - `invoice_summary.xlsx` - Excel 详细报告（如启用）
  - 重命名的发票文件（如启用）

## 📂 项目文件

```
.
├── invoice_ocr_gui.py          # 图形界面程序（主程序）
├── invoice_ocr_sum.py          # 完整模式核心逻辑
├── invoice_ocr_simple.py       # 快速模式核心逻辑
├── invoice_ocr_gui.spec        # PyInstaller 打包配置
├── pyproject.toml             # uv 项目配置
├── requirements.txt            # Python 依赖
├── setup.sh                   # 环境设置脚本（推荐）
├── run.sh                     # 快速启动脚本（推荐）
├── build_mac.sh               # macOS 打包脚本
├── build_windows.bat          # Windows 打包脚本
├── BUILD_README.md            # 详细打包说明
├── README.md                  # 本文件
└── .venv/                     # 虚拟环境目录
```

## 🔧 系统要求

### 必需
- Python 3.8+
- 以下之一：
  - Ollama 服务器（本地/局域网）+ 视觉模型（如 qwen3-vl）
  - 火山引擎 API Key + Endpoint ID
  - OpenRouter API Key
- pdftoppm（处理 PDF）
  - macOS: `brew install poppler`
  - Windows: 下载 poppler-utils
  - Linux: `sudo apt-get install poppler-utils`

### 可选
- openpyxl（Excel 报告功能）

## 📊 支持的文件格式

- PDF（自动转换首页为图片）
- PNG、JPG、JPEG
- WebP、BMP
- TIF、TIFF

## ⚠️ 注意事项

1. **网络连接**：需要能够访问 Ollama 服务器
2. **文件命名**：
   - 自动跳过包含"行程单"关键词的文件
   - 支持中文和长文件名
3. **处理时间**：取决于文件数量和 Ollama 服务器性能
4. **配置保存**：配置自动保存到 `~/.invoice_ocr_config.json`

## 🐛 故障排除

### 无法连接服务器
- 检查服务器地址和端口
- 确保防火墙允许连接
- 使用"测试连接"功能验证

### PDF 处理失败
- 确保已安装 pdftoppm
- 检查 PDF 文件是否损坏

### Excel 导出失败
- 确保已安装 openpyxl：`pip install openpyxl`
- 检查目标目录是否有写权限

## 📝 命令行版本

如果需要命令行版本，可以直接使用：

```bash
# 快速模式
python3 invoice_ocr_simple.py /path/to/invoices

# 完整模式（带分析和报告）
python3 invoice_ocr_sum.py /path/to/invoices --excel --rename
```

## 📄 许可证

本项目仅供学习和内部使用。

## 🙋 技术支持

如有问题，请查阅 `BUILD_README.md` 中的详细说明。
