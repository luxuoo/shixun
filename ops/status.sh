#!/usr/bin/env bash
# 查看当前发布状态与版本历史（只读，不加锁、不改任何东西）
# 用法: bash ops/status.sh

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

echo "=========================================="
echo "  发布状态"
echo "=========================================="
echo "工作目录 : $APP_DIR"
echo "发布目录 : $DEPLOY_DIR"
echo "当前版本 : $(current_release_name)"
echo "软链指向 : $(current_release)"
echo "服务名   : $SERVICE"
echo "健康检查 : $HEALTH_URL"

if [ -f "$CURRENT_LINK/REVISION" ] || [ -f "$(current_release)/REVISION" ]; then
    echo ""
    echo "--- 当前版本信息 ---"
    cat "$(current_release)/REVISION" 2>/dev/null | sed 's/^/  /'
fi

echo ""
echo "--- 最近一次操作 ---"
"$PYTHON_BIN" "$OPS_DIR/_state.py" show "$STATE_FILE" 2>/dev/null || echo "  （暂无记录）"

echo ""
echo "--- 版本历史（新 → 旧，* 为当前）---"
cur="$(current_release_name)"
count=0
while read -r n; do
    [ -z "$n" ] && continue
    mark="  "
    [ "$n" = "$cur" ] && mark="* "
    size="$(du -sh "$RELEASES_DIR/$n" 2>/dev/null | cut -f1)"
    printf '%s%-28s %s\n' "$mark" "$n" "$size"
    count=$((count + 1))
done < <(list_releases)

[ "$count" -eq 0 ] && echo "  （还没有任何发布，执行 bash ops/deploy.sh 开始）"

echo ""
echo "--- 服务状态 ---"
if command -v systemctl >/dev/null 2>&1 && systemctl list-unit-files 2>/dev/null | grep -q "^${SERVICE}\.service"; then
    systemctl is-active "$SERVICE" 2>/dev/null | sed 's/^/  /'
else
    echo "  （未使用 systemd，或服务名不是 $SERVICE）"
fi

echo ""
echo "--- 健康检查 ---"
if curl -fsS -m 3 "$HEALTH_URL" >/dev/null 2>&1; then
    echo "  ✓ $HEALTH_URL 正常"
else
    echo "  ✗ $HEALTH_URL 无响应"
fi

echo ""
echo "日志: $LOG_FILE"
