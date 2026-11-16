#!/usr/bin/env bash
# 一键更新：拉取最新代码 → 构建到独立版本目录 → 切换软链 → 重启 → 健康检查
# 构建失败或健康检查不通过时，自动切回上一个版本。
#
# 用法:
#   bash ops/deploy.sh                  # 更新到 origin/main 最新
#   bash ops/deploy.sh --ref v1.2.0     # 指定分支/标签/提交
#   bash ops/deploy.sh --force          # 版本号相同也强制重建
#   bash ops/deploy.sh --no-restart --skip-health   # 只准备版本（迁移时用）

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

REF="$REMOTE/$BRANCH"
FORCE=0
NO_RESTART="${NO_RESTART:-0}"
SKIP_HEALTH="${SKIP_HEALTH:-0}"
while [ $# -gt 0 ]; do
    case "$1" in
        --ref) REF="${2:?--ref 需要参数}"; shift 2 ;;
        --force) FORCE=1; shift ;;
        --no-restart) NO_RESTART=1; shift ;;
        --skip-health) SKIP_HEALTH=1; shift ;;
        -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
        *) die "未知参数: $1" ;;
    esac
done
export NO_RESTART SKIP_HEALTH

acquire_lock

STARTED="$(date '+%Y-%m-%d %H:%M:%S')"
PREV_DIR="$(current_release)"
PREV_NAME="$(current_release_name)"

state_set \
    "status=running" "action=deploy" "step=started" "pid=$$" \
    "error=" "ref=$REF" "release=" "sha=" \
    "prev_release=$PREV_NAME" "started_at=$STARTED" "finished_at=" "log=$LOG_FILE"

log "========== 开始发布（$REF）=========="
log "工作目录: $APP_DIR"

# ---------- 1. 准备共享数据 ----------
step "准备共享数据"
prepare_shared

# ---------- 2. 拉取代码 ----------
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
    state_set "status=success" "step=已是最新" "sha=$SHORT" \
              "release=$PREV_NAME" "finished_at=$(date '+%Y-%m-%d %H:%M:%S')"
    exit 0
fi

# ---------- 3. 导出代码到独立版本目录 ----------
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
subject=$SUBJECT
EOF

# ---------- 4. 构建 ----------
step "安装后端依赖"
build_backend "$RELEASE"

step "构建前端"
build_frontend "$RELEASE"

# ---------- 5. 切换并验证 ----------
step "切换版本"
if ! switch_to "$RELEASE"; then
    log "新版本启动失败，尝试回滚到上一个版本…"
    if [ -n "$PREV_DIR" ] && [ -d "$PREV_DIR" ]; then
        switch_to "$PREV_DIR" || log "  ✗ 回滚后仍未通过健康检查，需要人工介入"
        state_set "status=failed" "step=已自动回滚" \
                  "error=新版本健康检查失败，已切回 $(basename "$PREV_DIR")" \
                  "release=$PREV_NAME" "sha=$CURRENT_SHA" \
                  "finished_at=$(date '+%Y-%m-%d %H:%M:%S')"
        log "已回滚到 $(basename "$PREV_DIR")，新版本目录保留在 $RELEASE 供排查"
    else
        die "新版本健康检查失败，且没有可回滚的历史版本"
    fi
    exit 1
fi

state_set \
    "status=success" "step=完成" "sha=$SHORT" "release=$NAME" \
    "prev_release=$PREV_NAME" "subject=$SUBJECT" \
    "finished_at=$(date '+%Y-%m-%d %H:%M:%S')"

# ---------- 6. 清理旧版本 ----------
step "清理旧版本"
prune_releases

log "========== 发布完成：$NAME =========="
