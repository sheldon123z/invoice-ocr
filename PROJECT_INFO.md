# 项目信息

## 📍 项目位置
`/Users/xiaodongzheng/Desktop/InvoiceOCR`

## 🔧 环境配置

### 已创建
- ✅ 项目目录：`/Users/xiaodongzheng/Desktop/InvoiceOCR`
- ✅ uv 虚拟环境：`.venv/` (Python 3.13.5)
- ✅ Git 仓库初始化
- ✅ 依赖已安装：
  - openpyxl (Excel 支持)
  - pyinstaller (打包工具)

### 配置文件
- `pyproject.toml` - uv 项目配置
- `requirements.txt` - pip 依赖列表
- `.gitignore` - Git 忽略文件

## 🚀 快速开始

### 第一次使用
```bash
cd /Users/xiaodongzheng/Desktop/InvoiceOCR
./setup.sh    # 设置环境（如果还没设置）
./run.sh      # 启动应用
```

### 日常使用
```bash
cd /Users/xiaodongzheng/Desktop/InvoiceOCR
./run.sh      # 直接启动
```

## 📦 打包应用

### macOS
```bash
./build_mac.sh
# 生成: dist/InvoiceOCR.app
```

### Windows (在 Windows 系统上)
```bash
build_windows.bat
# 生成: dist\InvoiceOCR.exe
```

## 🔧 虚拟环境管理

### 激活虚拟环境
```bash
source .venv/bin/activate
```

### 安装新依赖
```bash
source .venv/bin/activate
pip install <package-name>
pip freeze > requirements.txt  # 更新依赖列表
```

### 使用 uv 管理（可选）
```bash
# 添加依赖到 pyproject.toml
uv add <package-name>

# 同步依赖
uv sync
```

## 📂 核心文件说明

| 文件 | 说明 |
|------|------|
| `invoice_ocr_gui.py` | 主程序 - 图形界面 |
| `invoice_ocr_sum.py` | 完整模式 - 详细分析 |
| `invoice_ocr_simple.py` | 快速模式 - 仅识别金额 |
| `setup.sh` | 环境设置（首次运行） |
| `run.sh` | 快速启动 |
| `build_mac.sh` | macOS 打包 |

## ⚙️ 配置说明

### 应用配置
运行后配置保存在：`~/.invoice_ocr_config.json`

默认配置：
```json
{
  "ollama_host": "192.168.110.219",
  "ollama_port": 11434,
  "ollama_model": "qwen3-vl:8b",
  "max_retries": 3
}
```

可在应用的"⚙️ 设置"标签页修改。

## 🐛 故障排除

### 虚拟环境问题
```bash
# 删除并重建
rm -rf .venv
./setup.sh
```

### 依赖问题
```bash
source .venv/bin/activate
pip install --upgrade -r requirements.txt
```

### PDF 处理失败
```bash
# 确保安装了 poppler
brew install poppler
which pdftoppm  # 验证安装
```

## 📝 开发说明

### 修改代码后测试
```bash
source .venv/bin/activate
python3 invoice_ocr_gui.py
```

### 更新版本
1. 修改 `pyproject.toml` 中的 `version`
2. 更新 `BUILD_README.md` 中的版本号和更新日志

### 提交代码
```bash
git add .
git commit -m "描述你的修改"
git push
```

## 📞 联系方式

项目创建时间：2025-12-01
环境：macOS (zsh)
Python 版本：3.13.5
