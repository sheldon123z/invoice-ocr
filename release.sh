#!/bin/bash

# Invoice OCR 发布脚本
# 用法: ./release.sh <version>
# 例如: ./release.sh v1.0.1

set -e  # 遇到错误立即退出

# 检查是否提供了版本号
if [ -z "$1" ]; then
    echo "错误: 请提供版本号"
    echo "用法: ./release.sh <version>"
    echo "例如: ./release.sh v1.0.1"
    exit 1
fi

VERSION=$1

# 验证版本号格式
if [[ ! $VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "错误: 版本号格式不正确，应该是 vX.Y.Z 格式 (例如: v1.0.1)"
    exit 1
fi

echo "=== Invoice OCR 发布流程 ==="
echo "版本: $VERSION"
echo ""

# 1. 检查是否有未提交的更改
echo "📋 检查 Git 状态..."
if ! git diff-index --quiet HEAD --; then
    echo "⚠️  警告: 存在未提交的更改"
    read -p "是否继续? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 2. 添加所有更改并提交
echo "📦 添加所有更改..."
git add .

read -p "请输入提交信息 (直接回车使用默认信息): " COMMIT_MSG
if [ -z "$COMMIT_MSG" ]; then
    COMMIT_MSG="Release $VERSION"
fi

echo "💾 提交更改..."
git commit -m "$COMMIT_MSG" || echo "没有新的更改需要提交"

# 3. 推送到远程仓库
echo "⬆️  推送代码到 GitHub..."
git push origin main

# 4. 创建并推送标签
echo "🏷️  创建标签 $VERSION..."
git tag -a "$VERSION" -m "Release $VERSION"

echo "⬆️  推送标签到 GitHub..."
git push origin "$VERSION"

# 5. 创建 GitHub Release
echo "🚀 创建 GitHub Release..."

# 生成 Release 说明
read -p "请输入 Release 说明 (直接回车使用默认说明): " RELEASE_NOTES
if [ -z "$RELEASE_NOTES" ]; then
    RELEASE_NOTES="## Invoice OCR GUI Application - $VERSION

### Features
- 发票 OCR 识别 GUI 应用程序
- 支持批量处理发票图片
- 自动提取发票信息并导出到 Excel
- 跨平台支持 (macOS & Windows)

### 安装
请参考 README.md 中的安装说明

### 使用方法
\`\`\`bash
python invoice_ocr_gui.py
\`\`\`"
fi

gh release create "$VERSION" \
    --title "Invoice OCR $VERSION" \
    --notes "$RELEASE_NOTES"

echo ""
echo "✅ 发布完成!"
echo "🔗 查看 Release: https://github.com/sheldon123z/invoice-ocr/releases/tag/$VERSION"
echo ""
echo "💡 提示: 如果需要上传构建的应用程序，运行:"
echo "   gh release upload $VERSION <文件路径>"
