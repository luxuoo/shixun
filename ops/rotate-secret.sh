#!/usr/bin/env bash
# 轮换 SECRET_KEY（JWT 签名密钥）
#
# 注意：换掉之后所有已签发的 token 立即失效，**所有用户需要重新登录一次**。
# 默认密钥是公开的（源码里就有），任何拿到仓库的人都能伪造管理员身份，生产环境必须换。
#
# 用法:
#   bash ops/rotate-secret.sh            # 生成新密钥并写入，提示重启
#   bash ops/rotate-secret.sh --restart  # 写入后顺带重启服务
#   bash ops/rotate-secret.sh --show     # 只看当前状态（不修改）

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

DO_RESTART=0
SHOW_ONLY=0
for arg in "$@"; do
    case "$arg" in
        --restart) DO_RESTART=1 ;;
        --show) SHOW_ONLY=1 ;;
        -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
        *) echo "未知参数: $arg"; exit 2 ;;
    esac
done

# 找出实际生效的 .env（发布体系下是 shared/.env）
ENV_FILE=""
for f in "$SHARED_DIR/.env" "$APP_DIR/backend/.env" "$APP_DIR/.env"; do
    [ -f "$f" ] && ENV_FILE="$f" && break
done

if [ -z "$ENV_FILE" ]; then
    echo "没有找到 .env：$SHARED_DIR/.env 或 $APP_DIR/backend/.env"
    exit 1
fi

read_secret() {
    "$PYTHON_BIN" - "$ENV_FILE" <<'PY'
import sys

path = sys.argv[1]
value = ""
try:
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("SECRET_KEY="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
except OSError:
    pass
print(value)
PY
}

CURRENT="$(read_secret)"
DEFAULT_KEYS=("" "your-secret-key-change-in-production" "changeme" "secret")

is_default=0
for d in "${DEFAULT_KEYS[@]}"; do
    [ "$CURRENT" = "$d" ] && is_default=1
done

echo "=========================================="
echo "  SECRET_KEY 状态"
echo "=========================================="
echo "配置文件 : $ENV_FILE"
if [ -z "$CURRENT" ]; then
    echo "当前值   : （未设置，使用代码默认值 —— 可被伪造）"
elif [ "$is_default" -eq 1 ]; then
    echo "当前值   : ${CURRENT}（公开默认值 —— 可被伪造）"
else
    echo "当前值   : ${CURRENT:0:8}…（长度 ${#CURRENT}）"
fi
echo ""

if [ "$SHOW_ONLY" = "1" ]; then
    [ "$is_default" -eq 1 ] && echo "建议执行：bash ops/rotate-secret.sh --restart"
    exit 0
fi

echo "⚠ 提醒：更换后所有已登录用户会被登出，需要重新登录一次。"
echo ""

# 备份
BACKUP_DIR="$DEPLOY_DIR/backup/secret-$(date '+%Y%m%d-%H%M%S')"
mkdir -p "$BACKUP_DIR"
cp -a "$ENV_FILE" "$BACKUP_DIR/.env"
echo "✓ 已备份原配置：$BACKUP_DIR/.env"

# 生成新密钥（48 字节 → 64 字符左右的 urlsafe 串）
NEW_KEY="$("$PYTHON_BIN" -c 'import secrets; print(secrets.token_urlsafe(48))' 2>/dev/null || true)"
if [ -z "$NEW_KEY" ]; then
    NEW_KEY="$(openssl rand -base64 48 2>/dev/null | tr -d '\n/+=' | cut -c1-64)"
fi
if [ -z "$NEW_KEY" ]; then
    echo "✗ 无法生成密钥（缺少 python3 / openssl）"
    exit 1
fi

# 写回（有则替换，无则追加）
"$PYTHON_BIN" - "$ENV_FILE" "$NEW_KEY" <<'PY'
import sys

path, key = sys.argv[1], sys.argv[2]
with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

found = False
out = []
for line in lines:
    if line.strip().startswith("SECRET_KEY="):
        out.append(f"SECRET_KEY={key}\n")
        found = True
    else:
        out.append(line)
if not found:
    if out and not out[-1].endswith("\n"):
        out[-1] += "\n"
    out.append(f"SECRET_KEY={key}\n")

with open(path, "w", encoding="utf-8") as f:
    f.writelines(out)
PY

echo "✓ 已写入新密钥：${NEW_KEY:0:8}…（长度 ${#NEW_KEY}）"
echo "  备份文件里仍是旧密钥，需要时可据此恢复"

if [ "$DO_RESTART" = "1" ]; then
    echo ""
    echo "→ 重启服务使新密钥生效"
    if do_restart; then
        if wait_health; then
            echo "  ✓ 服务已用新密钥启动，请重新登录"
        else
            echo "  ⚠ 服务未在预期时间内响应，检查：journalctl -u $SERVICE -n 50"
        fi
    else
        echo "  ✗ 重启失败，手动执行：sudo systemctl restart $SERVICE"
        exit 1
    fi
else
    echo ""
    echo "下一步（二选一）："
    echo "  sudo systemctl restart $SERVICE     # 手动重启"
    echo "  bash ops/rotate-secret.sh --restart # 或重跑并带 --restart"
fi
