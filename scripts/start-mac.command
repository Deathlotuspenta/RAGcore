#!/bin/bash
# 日常秒开启动（离线，不装依赖）
# 用法:
#   start-mac.command
#   start-mac.command autostart
#   start-mac.command install-autostart
#   start-mac.command uninstall-autostart
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib.sh
source "$SCRIPT_DIR/lib.sh"

case "${1:-start}" in
  install-autostart) install_autostart ;;
  uninstall-autostart) uninstall_autostart ;;
  autostart) start_background ;;
  start | "") start_fast ;;
  *)
    echo "用法: $0 [start|autostart|install-autostart|uninstall-autostart]"
    read -r -p "按回车退出..."
    exit 1
    ;;
esac
