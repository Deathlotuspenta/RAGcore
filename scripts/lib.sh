#!/bin/bash
# 共享：开发者本地一键启动
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
VENV="$BACKEND/.venv"
PORT="${PORT:-8765}"
URL="http://127.0.0.1:${PORT}"
PLIST="$HOME/Library/LaunchAgents/com.ragcore.notes-kb.plist"

list_python_candidates() {
  local -a candidates=()
  local p cmd seen=" "

  add_candidate() {
    local c="$1"
    [[ -z "$c" || ! -x "$c" ]] && return
    [[ "$seen" == *" $c "* ]] && return
    seen+=" $c "
    candidates+=("$c")
  }

  for p in \
    "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3" \
    "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3" \
    "/opt/homebrew/bin/python3.11" \
    "/opt/homebrew/bin/python3" \
    "/usr/local/bin/python3.11" \
    "/usr/local/bin/python3"
  do
    add_candidate "$p"
  done
  for cmd in python3.11 python3 python; do
    command -v "$cmd" &>/dev/null && add_candidate "$(command -v "$cmd")"
  done

  local py
  for py in "${candidates[@]}"; do
    if ! is_conda_python "$py"; then
      echo "$py"
    fi
  done
  for py in "${candidates[@]}"; do
    if is_conda_python "$py"; then
      echo "$py"
    fi
  done
}

find_python() {
  local py
  while IFS= read -r py; do
    [[ -n "$py" ]] && echo "$py" && return 0
  done < <(list_python_candidates)
  return 1
}

is_conda_python() {
  local py="$1"
  local lower
  lower=$(echo "$py" | tr '[:upper:]' '[:lower:]')
  case "$lower" in
    *conda*|*miniconda*|*anaconda*) return 0 ;;
  esac
  "$py" -c "
import sys
p = (sys.prefix + ' ' + getattr(sys, 'base_prefix', '')).lower()
raise SystemExit(1 if any(x in p for x in ('conda', 'miniconda', 'anaconda')) else 0)
" 2>/dev/null
}

check_bundle() {
  local ok=1
  if [[ ! -f "$FRONTEND/dist/index.html" ]]; then
    echo "缺少 frontend/dist（请使用完整安装 zip）"
    ok=0
  fi
  if [[ ! -f "$BACKEND/models/bge-small-zh-v1.5/config.json" ]]; then
    echo "缺少 backend/models/bge-small-zh-v1.5"
    ok=0
  fi
  if [[ ! -f "$BACKEND/models/bge-reranker-base/model.safetensors" ]]; then
    echo "缺少 backend/models/bge-reranker-base"
    ok=0
  fi
  if [[ $ok -eq 0 ]]; then
    read -r -p "按回车退出..."
    exit 1
  fi
}

activate_venv() {
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
}

require_ready() {
  if [[ ! -f "$VENV/bin/uvicorn" ]]; then
    echo "开发者环境未就绪。请在项目根目录执行："
    echo "  cd backend && python3 -m venv .venv && source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    read -r -p "按回车退出..."
    exit 1
  fi
  activate_venv
}

open_browser() {
  local i
  for i in $(seq 1 120); do
    if curl -sf "$URL/health" >/dev/null 2>&1; then
      open "$URL"
      return
    fi
    sleep 0.5
  done
  echo "启动较慢，请稍后在浏览器访问: $URL"
}

start_fast() {
  require_ready
  check_bundle

  if [[ ! -f "$BACKEND/.env" ]]; then
    cp "$BACKEND/.env.example" "$BACKEND/.env"
  fi

  cd "$BACKEND"
  export SERVE_STATIC=true
  export PORT

  if curl -sf "$URL/health" >/dev/null 2>&1; then
    echo "RAGcore 已在运行: $URL"
    open "$URL" 2>/dev/null || true
    read -r -p "按回车关闭..."
    exit 0
  fi

  echo ">> 启动 RAGcore: $URL"
  echo ">> 网页约数秒可用；首次 RAG 问答会加载本地模型"
  open_browser &
  exec "$VENV/bin/uvicorn" server.main:app --host 127.0.0.1 --port "$PORT"
}

start_background() {
  require_ready
  check_bundle
  cd "$BACKEND"
  export SERVE_STATIC=true
  export PORT

  if curl -sf "$URL/health" >/dev/null 2>&1; then
    echo "RAGcore 已在运行: $URL"
    return
  fi

  activate_venv
  mkdir -p "$HOME/Library/Logs"
  nohup "$VENV/bin/uvicorn" server.main:app --host 127.0.0.1 --port "$PORT" \
    >>"$HOME/Library/Logs/ragcore.out.log" 2>>"$HOME/Library/Logs/ragcore.err.log" &
  sleep 2
  open_browser || true
  echo "已在后台启动: $URL"
}

install_autostart() {
  if [[ ! -f "$VENV/bin/uvicorn" ]]; then
    echo "请先配置 backend/.venv（见 README 开发者说明）"
    read -r -p "按回车退出..."
    exit 1
  fi
  local launcher="$ROOT/scripts/start-mac.command"
  chmod +x "$launcher"
  mkdir -p "$HOME/Library/LaunchAgents"
  cat >"$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.ragcore.notes-kb</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-lc</string>
    <string>$launcher autostart</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <false/>
  <key>StandardOutPath</key>
  <string>$HOME/Library/Logs/ragcore.out.log</string>
  <key>StandardErrorPath</key>
  <string>$HOME/Library/Logs/ragcore.err.log</string>
</dict>
</plist>
EOF
  launchctl unload "$PLIST" 2>/dev/null || true
  launchctl load "$PLIST"
  echo "已开启开机自启"
}

uninstall_autostart() {
  if [[ -f "$PLIST" ]]; then
    launchctl unload "$PLIST" 2>/dev/null || true
    rm -f "$PLIST"
    echo "已关闭开机自启"
  else
    echo "未配置开机自启"
  fi
}
