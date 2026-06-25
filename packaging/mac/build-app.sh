#!/usr/bin/env bash
# 维护者：构建 RAGcore.app（内置 Python + 模型 + 前端）
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
DIST="$ROOT/dist"
PACKAGING="$ROOT/packaging"

ARCH="$(uname -m)"
case "$ARCH" in
  arm64) APP_BASENAME="RAGcore-mac-arm64" ;;
  x86_64) APP_BASENAME="RAGcore-mac-x64" ;;
  *) echo "不支持的 Mac 架构: $ARCH"; exit 1 ;;
esac

APP_NAME="${APP_BASENAME}.app"
ZIP_NAME="${APP_BASENAME}.zip"

find_python() {
  local cmd ver
  for cmd in python3.11 python3; do
    if command -v "$cmd" >/dev/null 2>&1; then
      ver="$("$cmd" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
      if [[ "$ver" == "3.11" || "$ver" == "3.12" ]]; then
        printf '%s\n' "$cmd"
        return 0
      fi
    fi
  done
  return 1
}

echo "==> RAGcore Mac 桌面应用构建 ($ARCH)"
echo "    项目目录: $ROOT"

PYTHON="$(find_python)" || {
  echo "错误: 需要 Python 3.11+（python3.11 或 python3）"
  exit 1
}
echo "    使用 Python: $PYTHON ($("$PYTHON" --version))"

echo ""
echo "==> 构建前端..."
cd "$FRONTEND"
if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi
npm run build
[[ -f dist/index.html ]] || { echo "错误: frontend/dist 构建失败"; exit 1; }

echo ""
echo "==> 校验模型..."
EMBED="$BACKEND/models/bge-small-zh-v1.5"
RERANK="$BACKEND/models/bge-reranker-base"
[[ -f "$EMBED/config.json" ]] || { echo "缺少 $EMBED"; exit 1; }
if [[ ! -f "$RERANK/model.safetensors" ]]; then
  echo "缺少 reranker，正在下载..."
  bash "$BACKEND/scripts/download_reranker.sh"
fi

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

APP="$STAGE/$APP_NAME"
CONTENTS="$APP/Contents"
RES="$CONTENTS/Resources"
MACOS="$CONTENTS/MacOS"

mkdir -p "$RES" "$MACOS"

echo ""
echo "==> 创建内置 Python 环境（约 5–15 分钟）..."
"$PYTHON" -m venv --copies "$STAGE/python"
"$STAGE/python/bin/pip" install --upgrade pip
"$STAGE/python/bin/pip" install -r "$BACKEND/requirements-lock.txt"

echo ""
echo "==> 组装应用资源..."
cp -R "$STAGE/python" "$RES/python"
mkdir -p "$RES/backend"
cp -R "$BACKEND/server" "$RES/backend/server"
cp -R "$BACKEND/models" "$RES/backend/models"
cp "$BACKEND/.env.example" "$RES/backend/"
cp "$BACKEND/requirements-lock.txt" "$RES/backend/"
mkdir -p "$RES/frontend"
cp -R "$FRONTEND/dist" "$RES/frontend/dist"
cp "$PACKAGING/launcher.py" "$RES/launcher.py"
cp "$PACKAGING/mac/Info.plist" "$CONTENTS/Info.plist"
cp "$PACKAGING/mac/ragcore" "$MACOS/ragcore"
chmod +x "$MACOS/ragcore"

if [[ -f "$PACKAGING/mac/RAGcore.icns" ]]; then
  mkdir -p "$RES"
  cp "$PACKAGING/mac/RAGcore.icns" "$RES/AppIcon.icns"
  /usr/libexec/PlistBuddy -c "Add :CFBundleIconFile string AppIcon" "$CONTENTS/Info.plist" 2>/dev/null \
    || /usr/libexec/PlistBuddy -c "Set :CFBundleIconFile AppIcon" "$CONTENTS/Info.plist"
fi

mkdir -p "$DIST"
rm -rf "$DIST/$APP_NAME" "$DIST/$ZIP_NAME"
cp -R "$APP" "$DIST/$APP_NAME"

echo ""
echo "==> 打包 $ZIP_NAME ..."
cp "$PACKAGING/用户安装说明.txt" "$DIST/安装说明.txt"
cd "$DIST"
zip -r -y "$ZIP_NAME" "$APP_NAME" "安装说明.txt" -x "*.DS_Store" -x "*__pycache__*"
rm -f "$DIST/安装说明.txt"

echo ""
echo "完成:"
echo "  应用: $DIST/$APP_NAME"
echo "  压缩包: $DIST/$ZIP_NAME"
echo "  大小: $(du -sh "$DIST/$APP_NAME" | cut -f1)"
echo ""
echo "用户：解压后将 .app 拖入「应用程序」，双击即可。"
