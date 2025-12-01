# macOS "应用已损坏" 错误修复指南

## 问题描述
在 macOS 上打开 `InvoiceOCR.app` 时，可能会提示：
- "应用已损坏，无法打开"
- "来自身份不明开发者"

这是因为应用没有通过 Apple 公证（Notarization）。

## 快速解决方法

### 方法 1: 使用修复脚本（推荐）

在项目目录下运行：

```bash
./fix_app.sh
```

或指定应用路径：

```bash
./fix_app.sh dist/InvoiceOCR.app
```

### 方法 2: 右键打开

1. 在 Finder 中找到 `InvoiceOCR.app`
2. **按住 Control 键**点击应用（或右键点击）
3. 选择 "打开"
4. 在弹出的对话框中点击 "打开"

第一次打开后，以后就可以正常双击打开了。

### 方法 3: 使用终端命令

```bash
# 移除隔离属性
xattr -cr dist/InvoiceOCR.app

# 直接打开
open dist/InvoiceOCR.app
```

### 方法 4: 临时禁用 Gatekeeper（不推荐）

```bash
# 禁用 Gatekeeper
sudo spctl --master-disable

# 打开应用
open dist/InvoiceOCR.app

# 重新启用 Gatekeeper（重要！）
sudo spctl --master-enable
```

## 为什么会出现这个问题？

macOS 的 Gatekeeper 安全机制要求：
1. 应用必须由已识别的开发者签名
2. 应用必须通过 Apple 公证

我们的应用使用了自签名（ad-hoc signing），没有开发者证书，也没有公证。

## 长期解决方案

如果要发布给其他用户，需要：
1. 注册 Apple Developer Program ($99/年)
2. 使用开发者证书签名
3. 提交给 Apple 公证

## 安全性说明

本应用是开源的，您可以：
- 查看完整源代码: https://github.com/sheldon123z/invoice-ocr
- 自己从源码构建应用
- 检查应用内容

应用不会：
- 收集个人信息
- 上传您的发票数据
- 执行任何恶意操作

所有 OCR 处理都在本地或您配置的服务器上进行。

## 常见问题

**Q: 为什么要移除隔离属性？**  
A: macOS 对下载的文件添加隔离属性，这会触发更严格的安全检查。移除这个属性相当于告诉系统这个应用是您信任的。

**Q: 这样做安全吗？**  
A: 如果您是从官方 GitHub 仓库下载或自己构建的应用，是安全的。不要对不信任来源的应用执行这些操作。

**Q: 每次更新都要重新操作吗？**  
A: 是的，每次下载新版本都需要重新执行这些步骤。

## 需要帮助？

- GitHub Issues: https://github.com/sheldon123z/invoice-ocr/issues
- 查看源码: https://github.com/sheldon123z/invoice-ocr
