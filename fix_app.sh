#!/bin/bash
# 修复 macOS "应用已损坏" 错误

APP_PATH="$1"

if [ -z "$APP_PATH" ]; then
    APP_PATH="dist/InvoiceOCR.app"
fi

if [ ! -d "$APP_PATH" ]; then
    echo "❌ 找不到应用: $APP_PATH"
    exit 1
fi

echo "🔧 修复 macOS 应用签名和权限..."
echo "应用路径: $APP_PATH"
echo ""

# 1. 修复权限
echo "📝 步骤 1: 修复文件权限..."
chmod -R u+w "$APP_PATH"

# 2. 清理元数据
echo "📝 步骤 2: 清理元数据..."
find "$APP_PATH" -name ".DS_Store" -delete 2>/dev/null || true
find "$APP_PATH" -name "._*" -delete 2>/dev/null || true

# 3. 移除隔离属性
echo "📝 步骤 3: 移除隔离属性..."
xattr -cr "$APP_PATH" 2>/dev/null || true

# 4. 移除特定的隔离标记
echo "📝 步骤 4: 移除 com.apple.quarantine 属性..."
xattr -d com.apple.quarantine "$APP_PATH" 2>/dev/null || true

# 5. 尝试签名
echo "📝 步骤 5: 签名应用..."
codesign --force --deep --sign - "$APP_PATH" 2>/dev/null || echo "⚠️ 签名失败（可忽略）"

echo ""
echo "✅ 修复完成！"
echo ""
echo "如果应用仍然无法打开，请尝试以下方法："
echo ""
echo "方法 1: 使用右键打开"
echo "  1. 在 Finder 中找到应用"
echo "  2. 按住 Control 键点击应用"
echo "  3. 选择 \"打开\""
echo "  4. 在弹出的对话框中点击 \"打开\""
echo ""
echo "方法 2: 使用终端命令"
echo "  sudo spctl --master-disable"
echo "  (打开应用后可以用 sudo spctl --master-enable 恢复)"
echo ""
echo "方法 3: 直接运行"
echo "  open \"$APP_PATH\""
echo ""
