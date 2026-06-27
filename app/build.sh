#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

APP_NAME="Agent Mesh Console"
PROJECT="$SCRIPT_DIR/AgentMeshConsole.xcodeproj"
SCHEME="AgentMeshConsole"
BUILD_DIR="$SCRIPT_DIR/build"
DMG_PATH="$SCRIPT_DIR/dist/$APP_NAME.dmg"
FINAL_DMG="$HOME/Downloads/$APP_NAME.dmg"

echo "=== Agent Mesh Console 构建脚本 ==="

# 清理旧构建
rm -rf "$BUILD_DIR"
rm -f "$DMG_PATH"

# 构建项目
echo "正在构建项目..."
xcodebuild -project "$PROJECT" -scheme "$SCHEME" -configuration Debug -derivedDataPath "$BUILD_DIR" build

# 找到构建产物
APP_PATH=$(find "$BUILD_DIR" -name "$APP_NAME.app" -type d 2>/dev/null | head -1)
if [ -z "$APP_PATH" ]; then
    echo "错误: 未找到构建产物"
    exit 1
fi

echo "构建产物: $APP_PATH"

# 准备 DMG 目录
DIST_DIR="$SCRIPT_DIR/dist/$APP_NAME"
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# 复制 App
cp -R "$APP_PATH" "$DIST_DIR/"

# 创建 Applications 链接
ln -sf /Applications "$DIST_DIR/Applications"

# 创建 DMG
echo "正在创建 DMG..."
hdiutil create -volname "$APP_NAME" -srcfolder "$DIST_DIR" -ov -format UDZO "$DMG_PATH"

# 复制到 Downloads
cp "$DMG_PATH" "$FINAL_DMG"

# 清理
rm -rf "$DIST_DIR"

echo ""
echo "=== 完成 ==="
echo "DMG 路径: $FINAL_DMG"
echo "直接打开: open \"$FINAL_DMG\""
