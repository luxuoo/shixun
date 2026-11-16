#!/usr/bin/env bash
# 一键更新：拉取最新代码 → 构建到独立版本目录 → 切换软链 → 重启 → 健康检查
# 构建失败或健康检查不通过时，自动切回上一个版本。
#
# 用法:
#   bash ops/deploy.sh                  # 更新到 origin/main 最新
#   bash ops/deploy.sh --ref v1.2.0     # 指定分支/标签/提交
#   bash ops/deploy.sh --force          # 版本号相同也强制重建
#   bash ops/deploy.sh --actor 张三      # 记录操作者（后台触发时自动传）
#   bash ops/deploy.sh --no-restart --skip-health   # 只准备版本（迁移时用）

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

REF="$REMOTE/$BRANCH"
FORCE=0
KEEP_FAILED=0
FORCE_REBUILD=0
ACTOR="${OPS_ACTOR:-$(whoami 2>/dev/null || echo unknown)}"
NO_RESTART="${NO_RESTART:-0}"
SKIP_HEALTH="${SKIP_HEALTH:-0}"

while [ $# -gt 0 ]; do
    case "$1" in
        --ref) REF="${2:?--ref 需要参数}"; shift 2 ;;
        --force) FORCE=1; shift ;;
        --actor) ACTOR="${2:?--actor 需要参数}"; shift 2 ;;
        --keep-failed) KEEP_FAILED=1; shift ;;
        --force-rebuild) FORCE_REBUILD=1; shift ;;
        --no-restart) NO_RESTART=1; shift ;;
        --skip-health) SKIP_HEALTH=1; shift ;;
        -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
        *) die "未知参数: $1" ;;
    esac
done
export NO_RESTART SKIP_HEALTH

# 构建失败时清理未完成的版本目录（日志里已有全部输出，留着只会占磁盘）
cleanup_failed() {
    local release="$1"
    if [ "$KEEP_FAILED" = "1" ]; then
        log "  保留失败版本目录（--keep-failed）：$release"
        return 0
    fi
    [ -d "$release" ] && rm -rf "$release" && log "  已清理未完成的版本目录：$(basename "$release")"
}

# die 会直接退出，所以清理放在 EXIT 兜底里；
# 已切换成功或明确要求保留时不动该目录
RELEASE=""
KEEP_RELEASE=0
FAIL_REASON="构建失败"
cleanup_on_exit() {
    local code=$?
    [ "$KEEP_RELEASE" = "1" ] && return 0
    [ -n "$RELEASE" ] && [ -d "$RELEASE" ] || return 0
    [ "$code" -eq 0 ] && return 0
    # 已切到这个版本（说明它在正常跑）就不要删
    [ "$(current_release_name)" = "$(basename "$RELEASE")" ] && return 0
    cleanup_failed "$RELEASE"
    # 构建类失败也要进历史，否则页面看不到这次尝试
    if [ -n "${NAME:-}" ] && [ -n "${SHORT:-}" ]; then
        history_add deploy "$NAME" "$SHORT" failed "$ACTOR" "$FAIL_REASON"
    fi
}
trap cleanup_on_exit EXIT

acquire_lock
rotate_log

START_TS="$(date +%s)"
STARTED="$(date '+%Y-%m-%d %H:%M:%S')"
PREV_DIR="$(current_release)"
PREV_NAME="$(current_release_name)"

state_set \
    "status=running" "action=deploy" "step=started" "pid=$$" "actor=$ACTOR" \
    "error=" "ref=$REF" "release=" "sha=" \
    "prev_release=$PREV_NAME" "started_at=$STARTED" "finished_at=" "duration_sec=" "log=$LOG_FILE"

log "========== 开始发布（$REF）=========="
log "工作目录: $APP_DIR"
log "操作者  : $ACTOR"

# ---------- 1. 环境自检 ----------
step "环境自检"
preflight

# ---------- 2. 准备共享数据 ----------
step "准备共享数据"
prepare_shared

# ---------- 3. 拉取代码 ----------
step "拉取代码"
if [ ! -d "$APP_DIR/.git" ]; then
    die "$APP_DIR 不是 git 仓库，请先 git clone"
fi

git -C "$APP_DIR" fetch --prune --tags "$REMOTE" >>"$LOG_FILE" 2>&1 || die "git fetch 失败（检查网络或仓库权限）"
SHA="$(git -C "$APP_DIR" rev-parse "$REF" 2>/dev/null)" || die "找不到引用 $REF"
SHORT="$(git -C "$APP_DIR" rev-parse --short=7 "$SHA")"
SUBJECT="$(git -C "$APP_DIR" log -1 --pretty=%s "$SHA" | cut -c1-80)"
log "  目标提交: $SHORT  $SUBJECT"

CURRENT_SHA=""
if [ -n "$PREV_NAME" ]; then
    CURRENT_SHA="${PREV_NAME##*-}"
fi
if [ "$SHORT" = "$CURRENT_SHA" ] && [ "$FORCE" -eq 0 ]; then
    log "已是最新版本（$SHORT），无需发布。加 --force 可强制重建。"
    state_set "status=success" "step=已是最新" "sha=$SHORT" "release=$PREV_NAME" \
              "finished_at=$(date '+%Y-%m-%d %H:%M:%S')" "duration_sec=0"
    history_add deploy "$PREV_NAME" "$SHORT" skipped "$ACTOR" "已是最新，未重建"
    exit 0
fi

# ---------- 4. 导出代码到独立版本目录 ----------
step "导出代码"
NAME="$(date '+%Y%m%d-%H%M%S')-$SHORT"
RELEASE="$RELEASES_DIR/$NAME"
mkdir -p "$RELEASE"
git -C "$APP_DIR" archive "$SHA" | tar -x -C "$RELEASE" || die "代码导出失败"
link_shared "$RELEASE"
log "  版本目录: $RELEASE"

cat >"$RELEASE/REVISION" <<EOF
commit=$SHORT
ref=$REF
built_at=$(date '+%Y-%m-%d %H:%M:%S')
actor=$ACTOR
subject=$SUBJECT
EOF

# ---------- 5. 增量判断 ----------
# requirements / 前端源码没变就复用上一版产物，把最容易卡住的 pip / npm 整段跳过
REUSE_VENV=0
REUSE_DIST=0
if [ -n "$PREV_DIR" ] && [ -d "$PREV_DIR" ] && [ "${FORCE_REBUILD:-0}" != "1" ] && [ -n "$CURRENT_SHA" ]; then
    CHANGED="$(git -C "$APP_DIR" diff --name-only "${CURRENT_SHA}..${SHA}" 2>/dev/null || true)"
    if [ -n "$CHANGED" ]; then
        TOTAL_CHANGES="$(printf '%s\n' "$CHANGED" | grep -c . || true)"
        log "  本次变更 $TOTAL_CHANGES 个文件"
        printf '%s\n' "$CHANGED" | grep -qE '^backend/requirements\.txt$' || REUSE_VENV=1
        printf '%s\n' "$CHANGED" | grep -qE '^frontend/' || REUSE_DIST=1
    else
        log "  未检测到文件差异，全部复用上一版产物"
        REUSE_VENV=1
        REUSE_DIST=1
    fi
    [ "$REUSE_VENV" = "1" ] && log "  后端依赖无变化"
    [ "$REUSE_DIST" = "1" ] && log "  前端源码无变化"
fi
[ "${FORCE_REBUILD:-0}" = "1" ] && log "  已指定 --force-rebuild，全部重新构建"
export REUSE_VENV REUSE_DIST

# ---------- 6. 构建 ----------
step "安装后端依赖"
if ! build_backend "$RELEASE"; then
    FAIL_REASON="后端依赖安装失败"
    die "后端依赖安装失败（线上仍是 ${PREV_NAME:-未发布}）"
fi

step "构建前端"
if ! build_frontend "$RELEASE"; then
    FAIL_REASON="前端构建失败"
    die "前端构建失败（线上仍是 ${PREV_NAME:-未发布}）"
fi

# ---------- 6. 产物自检 ----------
step "校验构建产物"
if ! check_build "$RELEASE"; then
    FAIL_REASON="构建产物不完整"
    die "构建产物不完整，已放弃本次发布（线上仍是 $PREV_NAME）"
fi
log "  ✓ 产物完整"

# ---------- 7. 切换并验证 ----------
step "切换版本"
SW=0
switch_to "$RELEASE" || SW=$?

if [ "$SW" -eq 1 ]; then
    # 重启失败：版本已经切过去了，回滚同样需要重启，所以不回滚
    KEEP_RELEASE=1
    DUR="$(($(date +%s) - START_TS))"
    state_set "status=failed" "step=已切换但未重启" \
              "error=服务未能重启，请执行：sudo systemctl restart $SERVICE" \
              "release=$NAME" "sha=$SHORT" \
              "finished_at=$(date '+%Y-%m-%d %H:%M:%S')" "duration_sec=$DUR"
    history_add deploy "$NAME" "$SHORT" failed "$ACTOR" "已切换，服务重启失败"
    log "版本已切换，但服务没能重启。手动执行：sudo systemctl restart $SERVICE"
    exit 1
fi

if [ "$SW" -ne 0 ]; then
    log "新版本启动失败，尝试回滚到上一个版本…"
    if [ -n "$PREV_DIR" ] && [ -d "$PREV_DIR" ]; then
        switch_to "$PREV_DIR" || log "  ✗ 回滚后仍未通过健康检查，需要人工介入"
        DUR="$(($(date +%s) - START_TS))"
        state_set "status=failed" "step=已自动回滚" \
                  "error=新版本健康检查失败，已切回 $(basename "$PREV_DIR")" \
                  "release=$PREV_NAME" "sha=$CURRENT_SHA" \
                  "finished_at=$(date '+%Y-%m-%d %H:%M:%S')" "duration_sec=$DUR"
        KEEP_RELEASE=1
        history_add deploy "$NAME" "$SHORT" failed "$ACTOR" "启动失败，已回滚到 $(basename "$PREV_DIR")"
        log "已回滚到 $(basename "$PREV_DIR")，失败版本保留在 $RELEASE 供排查"
    else
        history_add deploy "$NAME" "$SHORT" failed "$ACTOR" "启动失败，无可回滚版本"
        die "新版本健康检查失败，且没有可回滚的历史版本"
    fi
    exit 1
fi

DUR="$(($(date +%s) - START_TS))"
state_set \
    "status=success" "step=完成" "sha=$SHORT" "release=$NAME" \
    "prev_release=$PREV_NAME" "subject=$SUBJECT" \
    "finished_at=$(date '+%Y-%m-%d %H:%M:%S')" "duration_sec=$DUR"
history_add deploy "$NAME" "$SHORT" success "$ACTOR" "耗时 ${DUR}s"

# ---------- 8. 清理旧版本 ----------
step "清理旧版本"
prune_releases

log "========== 发布完成：$NAME（耗时 ${DUR}s）=========="
