#!/usr/bin/env bash
# 首次安装：把后端注册为 systemd 服务，指向 .deploy/current（随发布自动切换）
# 只需执行一次：sudo bash ops/install-service.sh
#
# 若你用的是宝塔「Python 项目管理器」，不要跑这个脚本，
# 而是在 .env 里设置 RESTART_CMD="bt restart 你的项目名" 让发布脚本调用面板重启。

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

if [ "$(id -u)" != "0" ]; then
    echo "请用 root 执行：sudo bash ops/install-service.sh"
    exit 1
fi

# 允许以哪个用户身份运行后端（默认 www，宝塔环境就是 www）
RUN_USER="${RUN_USER:-www}"
if ! id "$RUN_USER" >/dev/null 2>&1; then
    echo "用户 $RUN_USER 不存在，可用 RUN_USER=root 重新执行"
    exit 1
fi

CURRENT_BACKEND="$CURRENT_LINK/backend"
if [ ! -d "$CURRENT_BACKEND" ]; then
    echo "还没有任何发布版本，先执行一次：bash ops/deploy.sh"
    echo "（首次发布会把代码导出到 $RELEASES_DIR 并建立 current 软链）"
    exit 1
fi

UNIT="/etc/systemd/system/${SERVICE}.service"
cat >"$UNIT" <<EOF
[Unit]
Description=AI Learning System Backend
After=network.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${CURRENT_BACKEND}
ExecStart=${CURRENT_BACKEND}/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5
Environment=PYTHONPATH=${CURRENT_BACKEND}
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "✓ 已写入 $UNIT"
systemctl daemon-reload
systemctl enable "$SERVICE" >/dev/null 2>&1 || true
systemctl restart "$SERVICE"
sleep 2
systemctl is-active --quiet "$SERVICE" && echo "✓ 服务已启动" || echo "✗ 服务未启动，查看：journalctl -u $SERVICE -n 50"

# 发布脚本需要用非 root 用户重启服务，配置免密 sudo
DEPLOY_USER="${DEPLOY_USER:-$RUN_USER}"
SUDOERS="/etc/sudoers.d/${SERVICE}-deploy"
SYSTEMCTL="$(command -v systemctl)"
cat >"$SUDOERS" <<EOF
# 允许发布脚本重启本服务（仅此一个命令，风险可控）
${DEPLOY_USER} ALL=(root) NOPASSWD: ${SYSTEMCTL} restart ${SERVICE}, ${SYSTEMCTL} is-active ${SERVICE}
EOF
chmod 440 "$SUDOERS"
visudo -cf "$SUDOERS" >/dev/null 2>&1 && echo "✓ 已配置免密重启：$SUDOERS" || {
    rm -f "$SUDOERS"
    echo "⚠ sudoers 校验失败，已回滚。请手动为 $DEPLOY_USER 配置："
    echo "  $DEPLOY_USER ALL=(root) NOPASSWD: $SYSTEMCTL restart $SERVICE"
}

echo ""
echo "=========================================="
echo "后续 Nginx 需要指向发布目录（改完 reload）："
echo "  root /www/wwwroot/learning-system/.deploy/current/frontend/dist;"
echo "  location /uploads/ { alias /www/wwwroot/learning-system/.deploy/shared/uploads/; }"
echo ""
echo "之后每次更新：bash ops/deploy.sh   （回滚：bash ops/rollback.sh）"
echo "=========================================="
