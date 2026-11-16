#!/usr/bin/env bash
# 应急恢复：服务起不来、页面打不开时用
#
# 与 rollback.sh 的区别：不做「失败就切回去」的二次折腾，也不因健康检查失败而中止，
# 只负责把软链指到一个可用的版本并把服务拉起来，然后如实报告状态。
#
# 用法:
#   bash ops/recover.sh                  # 切到上一个版本并重启
#   bash ops/recover.sh --list           # 看有哪些版本可选
#   bash ops/recover.sh --to 20261116-203914-1d36261
#   bash ops/recover.sh --no-restart     # 只修软链（服务重启你自己来）
#   bash ops/recover.sh --fix-unit       # 重装 systemd 单元（需 root）

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

TARGET=""
DO_RESTART=1
FIX_UNIT=0
while [ $# -gt 0 ]; do
    case "$1" in
        --to) TARGET="${2:?--to 需要版本名}"; shift 2 ;;
        --no-restart) DO_RESTART=0; shift ;;
        --fix-unit) FIX_UNIT=1; shift ;;
        --list)
            cur="$(current_release_name)"
            echo "可用版本（新 → 旧，* 为当前）:"
            list_releases | while read -r n; do
                mark="  "
                [ "$n" = "$cur" ] && mark="* "
                health=""
                [ -x "$RELEASES_DIR/$n/backend/venv/bin/python" ] || health="  （缺少 venv，不可用）"
                printf '%s%s%s\n' "$mark" "$n" "$health"
            done
            exit 0 ;;
        -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
        *) echo "未知参数: $1"; exit 2 ;;
    esac
done

echo "=========================================="
echo "  发布状态"
echo "=========================================="
echo "当前版本 : $(current_release_name)"
echo "服务名   : $SERVICE"
echo ""

# 没有可用版本时，多半还没发布过
if [ -z "$(list_releases)" ]; then
    echo "没有任何版本目录，先执行：bash ops/deploy.sh"
    exit 1
fi

if [ "$FIX_UNIT" = "1" ]; then
    echo "→ 重装 systemd 单元"
    if [ "$(id -u)" = "0" ]; then
        bash "$OPS_DIR/install-service.sh" || exit 1
    else
        sudo bash "$OPS_DIR/install-service.sh" || exit 1
    fi
    echo ""
fi

# 优先选「历史上发布成功过的最近版本」，而不是简单取列表里的前一个
# （发布失败会留下版本目录，那些版本不该被当成恢复目标）
last_good_release() {
    local cur="$1"
    [ -f "$HISTORY_FILE" ] || return 0
    awk -F' *\\| *' -v cur="$cur" '
        $2 == "deploy" && $5 == "success" && $3 != cur { last = $3 }
        END { if (last != "") print last }
    ' "$HISTORY_FILE"
}

CURRENT_NAME="$(current_release_name)"
if [ -z "$TARGET" ]; then
    GOOD="$(last_good_release "$CURRENT_NAME" || true)"
    if [ -n "$GOOD" ] && [ -d "$RELEASES_DIR/$GOOD" ]; then
        TARGET="$GOOD"
        echo "→ 依据发布历史，选择最近一次成功发布的版本"
    else
        TARGET="$(previous_release "$CURRENT_NAME" || true)"
        [ -z "$TARGET" ] && TARGET="$(list_releases | head -1)"
    fi
fi

TARGET_DIR="$RELEASES_DIR/$TARGET"
if [ ! -d "$TARGET_DIR" ]; then
    echo "版本不存在: $TARGET"
    echo "用 bash ops/recover.sh --list 查看可用版本"
    exit 1
fi

echo "→ 目标版本: $TARGET"
if [ ! -x "$TARGET_DIR/backend/venv/bin/python" ]; then
    echo "  ✗ 该版本缺少虚拟环境，换一个版本，或先执行 bash ops/deploy.sh --force"
    exit 1
fi

# 直接改软链，不走 switch_to 的失败回退逻辑
ln -sfn "$TARGET_DIR" "$CURRENT_LINK"
echo "  ✓ 软链已指向 $TARGET"

if [ "$DO_RESTART" = "1" ]; then
    echo "→ 重启服务 $SERVICE"
    if do_restart; then
        echo "  ✓ 已下发重启"
    else
        echo "  ✗ 重启失败，手动执行：sudo systemctl restart $SERVICE"
    fi
fi

echo ""
echo "→ 等待服务就绪（最多 20 秒）"
HEALTH_TIMEOUT=20
if wait_health; then
    RUN_COMMIT="$(curl -fsS -m 3 "$HEALTH_URL" 2>/dev/null | "$PYTHON_BIN" -c 'import json,sys;print(json.load(sys.stdin).get("commit",""))' 2>/dev/null || true)"
    echo "  ✓ $HEALTH_URL 已就绪（运行版本 ${RUN_COMMIT:-未知}）"
    state_set "status=success" "action=recover" "step=完成" "release=$TARGET" "sha=${RUN_COMMIT:-}" \
              "error=" "finished_at=$(date '+%Y-%m-%d %H:%M:%S')"
    history_add recover "$TARGET" "${RUN_COMMIT:-}" success "$(whoami 2>/dev/null || echo unknown)" "应急恢复"
    echo ""
    echo "恢复完成。若页面仍打不开，检查 Nginx：root 是否指向 $CURRENT_LINK/frontend/dist"
else
    echo "  ✗ 服务仍未响应，看错误日志："
    echo "    sudo journalctl -u $SERVICE -n 50 --no-pager"
    echo "    tail -n 60 $LOG_FILE"
    state_set "status=failed" "action=recover" "step=恢复后仍未就绪" "release=$TARGET" \
              "error=服务未响应，需查看 journalctl" "finished_at=$(date '+%Y-%m-%d %H:%M:%S')"
    exit 1
fi
