#!/bin/sh
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PROJECT_DIR

usage() {
  cat <<EOF
Usage: ./start.sh <command>

Commands:
  start     检查微信登录状态，启动 nanobot gateway
  login     微信扫码登录（首次或登录态过期时使用）
  help      显示帮助信息
EOF
}

# 解析子命令
CMD="${1:-}"
case "$CMD" in
  start|login) ;;
  help|--help|-h|"")
    usage; exit 0 ;;
  *)
    echo "Unknown command: $CMD"; usage; exit 1 ;;
esac

# 加载 .env
if [ -f "$PROJECT_DIR/.env" ]; then
  set -a; . "$PROJECT_DIR/.env"; set +a
else
  echo "Error: .env not found. Copy .env.example to .env and fill in the values."
  exit 1
fi

# 渲染 config.json（仅首次，保留用户后续手动编辑）
if [ ! -f "$PROJECT_DIR/config.json" ]; then
  envsubst '$PROJECT_DIR $DEFAULT_API_KEY $DEFAULT_API_BASE $DEFAULT_MODEL $MEM0_MODEL $MEM0_EMBED_MODEL' \
    < "$PROJECT_DIR/config-example.json" > "$PROJECT_DIR/config.json"
  echo "✓ config.json 已生成：$PROJECT_DIR/config.json"
  echo ""
  echo "下一步："
  echo "  1. 编辑 config.json 启用所需渠道"
  echo "  2. 运行 ./start.sh login   完成微信登录"
  echo "  3. 运行 ./start.sh start   启动服务"
  exit 0
fi

# login 子命令
if [ "$CMD" = "login" ]; then
  uv --directory "$PROJECT_DIR" run python scripts/weixin-login.py
  exit $?
fi

# start 子命令：检查微信登录状态
WEIXIN_STATE_DIR="$(uv --directory "$PROJECT_DIR" run python -c "
import json, pathlib
cfg = json.load(open('$PROJECT_DIR/config.json'))
d = cfg.get('channels', {}).get('weixin', {}).get('stateDir', '~/.nanobot/weixin')
print(pathlib.Path(d).expanduser())
" 2>/dev/null || echo "$HOME/.nanobot/weixin")"

if [ ! -f "$WEIXIN_STATE_DIR/account.json" ]; then
  if [ ! -t 0 ]; then
    echo "Error: 微信未登录，且当前为非交互环境。"
    echo "请先运行：docker compose run --rm -it life-assistant login"
    exit 1
  fi
  echo "微信未登录，开始登录流程..."
  uv --directory "$PROJECT_DIR" run python scripts/weixin-login.py
fi

# 初始化数据库（幂等）
uv --directory "$PROJECT_DIR" run python mcp-server/cli.py init

# 启动 nanobot
exec nanobot gateway --config "$PROJECT_DIR/config.json"
