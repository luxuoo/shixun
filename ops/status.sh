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
if service_exists; then
    state="$(systemctl is-active "$SERVICE" 2>/dev/null || true)"
    echo "  ${state:-unknown}（$SERVICE）"
else
    echo "  （未找到服务单元 $SERVICE，或未使用 systemd）"
fi

echo ""
echo "--- 健康检查与版本一致性 ---"
HEALTH_JSON="$(curl -fsS -m 3 "$HEALTH_URL" 2>/dev/null || true)"
if [ -z "$HEALTH_JSON" ]; then
    echo "  ✗ $HEALTH_URL 无响应"
else
    RUN_COMMIT="$(printf '%s' "$HEALTH_JSON" | "$PYTHON_BIN" -c \
        'import json,sys;print(json.load(sys.stdin).get("commit",""))' 2>/dev/null || true)"
    RUN_STARTED="$(printf '%s' "$HEALTH_JSON" | "$PYTHON_BIN" -c \
        'import json,sys;print(json.load(sys.stdin).get("started_at",""))' 2>/dev/null || true)"
    CUR_DIR="$(current_release)"
    CUR_COMMIT=""
    [ -f "$CUR_DIR/REVISION" ] && CUR_COMMIT="$(grep -m1 '^commit=' "$CUR_DIR/REVISION" | cut -d= -f2)"

    echo "  ✓ 服务在线（启动于 ${RUN_STARTED:-未知}）"
    echo "  运行版本: ${RUN_COMMIT:-未知（旧版本没有上报）}"
    echo "  软链版本: ${CUR_COMMIT:-未知}"
    if [ -n "$RUN_COMMIT" ] && [ -n "$CUR_COMMIT" ] && [ "$RUN_COMMIT" != "$CUR_COMMIT" ]; then
        echo "  ⚠ 两者不一致：进程还在跑 $RUN_COMMIT，重启服务或检查 systemd 单元是否指向 .deploy/current"
    fi
fi

echo ""
echo "--- 最近操作记录 ---"
if [ -f "$HISTORY_FILE" ]; then
    tail -6 "$HISTORY_FILE" | sed 's/^/  /'
else
    echo "  （暂无记录）"
fi

echo ""
echo "日志: $LOG_FILE"
echo "历史: $HISTORY_FILE"
