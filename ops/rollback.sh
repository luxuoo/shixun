#!/usr/bin/env bash
# 一键回滚：把 current 软链切回历史版本并重启（纯切换，不重新构建，几秒完成）
#
# 用法:
#   bash ops/rollback.sh                  # 回到上一个版本
#   bash ops/rollback.sh --to 20261116-101500-1d36261
#   bash ops/rollback.sh --list           # 查看可用版本

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

TARGET=""
ACTOR="${OPS_ACTOR:-$(whoami 2>/dev/null || echo unknown)}"
while [ $# -gt 0 ]; do
    case "$1" in
        --to) TARGET="${2:?--to 需要版本名}"; shift 2 ;;
        --actor) ACTOR="${2:?--actor 需要参数}"; shift 2 ;;
        --list)
            echo "可用版本（新 → 旧，* 为当前）:"
            cur="$(current_release_name)"
            list_releases | while read -r n; do
                mark="  "
                [ "$n" = "$cur" ] && mark="* "
                printf '%s%s\n' "$mark" "$n"
            done
            exit 0 ;;
        -h|--help) sed -n '2,9p' "$0"; exit 0 ;;
        *)
            # 兼容版本错位：后端可能比脚本新，传了旧脚本不认识的参数。
            # 这里只告警并忽略，不要直接退出（否则面板一按就失败）。
            log "  ⚠ 忽略未知参数：$1（ops 脚本可能比后端旧，建议 git pull）"
            shift
            ;;
    esac
done

acquire_lock
rotate_log
START_TS="$(date +%s)"

CURRENT_NAME="$(current_release_name)"
CURRENT_DIR="$(current_release)"

if [ -z "$TARGET" ]; then
    # 取「当前版本的下一个」，即上一次发布。
    # 不能简单取列表第一个非当前版本 —— 发布失败会留下未切换的版本目录。
    TARGET="$(previous_release "$CURRENT_NAME" || true)"
    if [ -z "$TARGET" ]; then
        die "没有可回滚的历史版本（当前: ${CURRENT_NAME:-无}；用 --to 指定版本）"
    fi
fi

TARGET_DIR="$RELEASES_DIR/$TARGET"
[ -d "$TARGET_DIR" ] || die "版本不存在: $TARGET（用 --list 查看可用版本）"

if [ "$TARGET" = "$CURRENT_NAME" ]; then
    log "当前已经是 $TARGET，无需回滚"
    exit 0
fi

state_set \
    "status=running" "action=rollback" "step=started" "pid=$$" "actor=$ACTOR" "error=" \
    "release=$CURRENT_NAME" "target_release=$TARGET" \
    "started_at=$(date '+%Y-%m-%d %H:%M:%S')" "finished_at=" "log=$LOG_FILE"

log "========== 开始回滚：${CURRENT_NAME:-无} → $TARGET =========="

SW=0
switch_to "$TARGET_DIR" || SW=$?

if [ "$SW" -eq 1 ]; then
    # 软链已经切过去了，只是服务没重启：不要切回原版本（同样起不来）
    DUR="$(($(date +%s) - START_TS))"
    state_set "status=failed" "step=已切换但未重启" \
              "error=服务未能重启，请执行：sudo systemctl restart $SERVICE" \
              "release=$TARGET" "finished_at=$(date '+%Y-%m-%d %H:%M:%S')" "duration_sec=$DUR"
    history_add rollback "$TARGET" "" failed "$ACTOR" "已切换，服务重启失败"
    log "软链已切到 $TARGET，但服务没重启。手动执行：sudo systemctl restart $SERVICE"
    exit 1
fi

if [ "$SW" -ne 0 ]; then
    log "回滚后的版本未通过健康检查"
    if [ -n "$CURRENT_DIR" ] && [ -d "$CURRENT_DIR" ]; then
        log "  尝试切回原版本 $(basename "$CURRENT_DIR")…"
        switch_to "$CURRENT_DIR" || log "  ✗ 原版本也未通过健康检查，需要人工介入"
    fi
    state_set \
        "status=failed" "step=回滚失败" "release=$CURRENT_NAME" \
        "error=目标版本 $TARGET 启动失败，已切回原版本" \
        "finished_at=$(date '+%Y-%m-%d %H:%M:%S')"
    history_add rollback "$TARGET" "" failed "$ACTOR" "启动失败，已切回 $CURRENT_NAME"
    exit 1
fi

# 回滚后从 REVISION 取回提交号，供界面显示
SHA=""
SUBJECT=""
if [ -f "$TARGET_DIR/REVISION" ]; then
    SHA="$(grep -m1 '^commit=' "$TARGET_DIR/REVISION" | cut -d= -f2)"
    SUBJECT="$(grep -m1 '^subject=' "$TARGET_DIR/REVISION" | cut -d= -f2-)"
fi

DUR="$(($(date +%s) - START_TS))"
state_set \
    "status=success" "step=完成" "release=$TARGET" "sha=$SHA" \
    "subject=$SUBJECT" "prev_release=$CURRENT_NAME" \
    "finished_at=$(date '+%Y-%m-%d %H:%M:%S')" "duration_sec=$DUR"
history_add rollback "$TARGET" "$SHA" success "$ACTOR" "来自 $CURRENT_NAME，耗时 ${DUR}s"

log "========== 回滚完成：现在运行 $TARGET（耗时 ${DUR}s）=========="
log "如需回到回滚前的版本，执行：bash ops/rollback.sh --to $CURRENT_NAME"
