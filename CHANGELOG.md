# 更新日志

## v1.2.0 (2025-12-01)

### 🐛 Bug 修复
- **火山引擎 API 修复**
  - 修复默认 endpoint 配置
  - 添加 Endpoint ID 说明注释
  - 改进错误处理和错误信息
  
- **OpenRouter API 优化**
  - 添加推荐的 HTTP-Referer 和 X-Title headers
  - 支持自动检测图片 MIME 类型
  - 更详细的 HTTP 错误和网络错误处理

- **API 错误处理增强**
  - 所有 provider 均添加 HTTPError 和 URLError 的具体处理
  - 错误消息包含类型名和详细信息
  - 检测并报告空内容响应

### ✨ 改进
- **界面优化**
  - 窗口尺寸从 900x700 增加到 1200x900
  - 更大更清晰的显示区域
  
- **配置说明改进**
  - 更详细的 API 提供商使用说明
  - 每个 provider 的具体配置步骤
  - 添加火山引擎和 OpenRouter 的特点说明
  
- **日志输出优化**
  - 显示当前使用的 API 提供商
  - 根据 provider 显示相应的配置信息
  - Ollama：服务器和模型
  - 火山引擎：Endpoint ID
  - OpenRouter：模型名称

### 🚀 新功能
- **Linux 平台支持**
  - 新增 build_linux.sh 编译脚本
  - 支持多种 Linux 包管理器（apt-get, yum, dnf）
  - 自动安装 poppler-utils 依赖
  - 生成单文件可执行程序

### 📚 文档更新
- 更新 README 添加 Linux 编译说明
- 添加三个 API 提供商的详细配置指南
- 更新系统要求，包含所有平台
- 更新特性列表，强调跨平台和多 API 支持

## v1.1.0 (2025-12-01)

### 🚀 新功能
- **多 API 提供商支持**
  - Ollama (本地/局域网)
  - 火山引擎豆包视觉模型
  - OpenRouter 多模型平台

- **Markdown 报告生成**
  - 快速模式和完整模式都生成 Markdown 报告
  - 可选择是否生成报告

### 🐛 Bug 修复
- 修复快速模式处理逻辑错误
- 修复 Markdown 报告未正确生成的问题
- 改进网络错误提示信息

### ✨ 改进
- 统一的 API 抽象层 (ocr_api.py)
- 更友好的错误提示和故障排除指南
- PDF 文件处理支持(打包 pdftoppm)
- 优化的打包脚本和代码签名

### 📦 依赖更新
- 打包完整的 poppler 工具链
- 支持多种 API 提供商

## v1.0.0 (2025-12-01)

### 初始版本
- 发票 OCR 识别基本功能
- Ollama 视觉模型支持
- 快速模式和完整模式
- Excel 报告生成
- 文件重命名功能
