#!/usr/bin/env bash
# 发布流程公共函数：目录约定、日志、状态、健康检查、切换软链
# 由 deploy.sh / rollback.sh / status.sh 引用，不单独执行。

set -euo pipefail

OPS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${APP_DIR:-$(cd "$OPS_DIR/.." && pwd)}"

# 发布产物与运行数据都放在 .deploy 下（已在 .gitignore 忽略）
DEPLOY_DIR="${DEPLOY_DIR:-$APP_DIR/.deploy}"
RELEASES_DIR="$DEPLOY_DIR/releases"
CURRENT_LINK="$DEPLOY_DIR/current"
SHARED_DIR="$DEPLOY_DIR/shared"
STATE_FILE="$DEPLOY_DIR/state.json"
LOCK_FILE="$DEPLOY_DIR/ops.lock"
LOG_FILE="$DEPLOY_DIR/ops.log"
HISTORY_FILE="$DEPLOY_DIR/history.log"

# 可通过环境变量覆盖
REMOTE="${REMOTE:-origin}"
BRANCH="${BRANCH:-main}"
SERVICE="${SERVICE:-learning-system}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-40}"
RELEASE_KEEP="${RELEASE_KEEP:-5}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
NPM_BIN="${NPM_BIN:-npm}"
# 没有 systemd 时（如宝塔「Python 项目管理器」）可用自定义重启命令
RESTART_CMD="${RESTART_CMD:-}"

mkdir -p "$RELEASES_DIR" "$SHARED_DIR"

# ---------------- 日志 ----------------

log() {
    local line
    line="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    printf '%s\n' "$line"
    printf '%s\n' "$line" >>"$LOG_FILE"
}

step() {
    log "▶ $*"
    state_set "step=$*"
}

# 发布日志超过 2MB 就轮转，避免长期运行把磁盘吃满
rotate_log() {
    local max=2097152
    if [ -f "$LOG_FILE" ] && [ "$(wc -c <"$LOG_FILE" 2>/dev/null || echo 0)" -gt "$max" ]; then
        mv -f "$LOG_FILE" "$LOG_FILE.1" 2>/dev/null || true
        log "（日志已轮转到 ops.log.1）"
    fi
}

# 追加一条历史记录，供运维页面展示「谁在什么时候发布了什么」
# 格式: 时间 | 动作 | 版本 | 提交 | 结果 | 操作者 | 补充说明
history_add() {
    local action="$1" release="$2" sha="$3" result="$4" actor="$5" detail="${6:-}"
    printf '%s | %s | %s | %s | %s | %s | %s\n' \
        "$(date '+%Y-%m-%d %H:%M:%S')" "$action" "${release:--}" "${sha:--}" \
        "$result" "${actor:--}" "$detail" >>"$HISTORY_FILE"
}

die() {
    log "✗ $*"
    state_set "status=failed" "error=$*" "finished_at=$(date '+%Y-%m-%d %H:%M:%S')"
    exit 1
}

# ---------------- 状态 ----------------

state_set() {
    "$PYTHON_BIN" "$OPS_DIR/_state.py" set "$STATE_FILE" "$@" >/dev/null 2>&1 || true
}

# ---------------- 并发锁 ----------------

acquire_lock() {
    # macOS 默认没有 flock，此时退化为无锁，只影响并发保护不影响发布
    if ! command -v flock >/dev/null 2>&1; then
        log "  ⚠ 系统无 flock，跳过并发锁（请勿同时执行两个发布）"
        return 0
    fi
    exec 9>"$LOCK_FILE"
    if ! flock -n 9; then
        log "另一个发布/回滚正在进行（锁: $LOCK_FILE）"
        exit 3
    fi
}

# ---------------- 版本信息 ----------------

# 从新到旧列出所有版本（只用 basename + sort，不依赖 GNU find）
list_releases() {
    local d
    for d in "$RELEASES_DIR"/*/; do
        [ -d "$d" ] || continue
        basename "$d"
    done | sort -r
}

current_release() {
    # -L 覆盖「软链但目标已删除」，-e 覆盖「被误建成普通文件/目录」，两者都要判
    if [ -L "$CURRENT_LINK" ] || [ -e "$CURRENT_LINK" ]; then
        readlink -f "$CURRENT_LINK" 2>/dev/null || true
    fi
}

current_release_name() {
    local dir
    dir="$(current_release)"
    if [ -n "$dir" ]; then basename "$dir"; else echo ""; fi
}

# 当前版本的下一个（即上一个发布）。注意不能用「列表里第一个非当前」，
# 因为发布失败会留下一个未被切换的版本，那个版本不该被当作回滚目标。
previous_release() {
    local cur="$1" seen=0 n
    while read -r n; do
        [ -z "$n" ] && continue
        if [ "$seen" = "1" ]; then
            echo "$n"
            return 0
        fi
        [ "$n" = "$cur" ] && seen=1
    done < <(list_releases)
    return 1
}

# ---------------- 共享数据 ----------------

prepare_shared() {
    # 先把老数据搬过来，再建空目录（顺序反了会导致「目录非空」判断失效）
    if [ ! -f "$SHARED_DIR/.env" ]; then
        if [ -f "$APP_DIR/backend/.env" ]; then
            cp "$APP_DIR/backend/.env" "$SHARED_DIR/.env"
            log "  已把现有 backend/.env 搬到 $SHARED_DIR/.env（后续只维护这一份）"
        elif [ -f "$APP_DIR/.env" ]; then
            cp "$APP_DIR/.env" "$SHARED_DIR/.env"
            log "  已把现有 .env 搬到 $SHARED_DIR/.env"
        elif [ -f "$APP_DIR/.env.example" ]; then
            cp "$APP_DIR/.env.example" "$SHARED_DIR/.env"
            log "  ⚠ 未找到 .env，已用 .env.example 生成，请尽快填写密钥：$SHARED_DIR/.env"
        fi
    fi

    if [ -f "$APP_DIR/backend/data/teaching.db" ] && [ ! -f "$SHARED_DIR/data/teaching.db" ]; then
        mkdir -p "$SHARED_DIR/data"
        cp -a "$APP_DIR/backend/data/." "$SHARED_DIR/data/" 2>/dev/null || true
        log "  已迁移旧数据库到 $SHARED_DIR/data"
    fi

    if [ -d "$APP_DIR/backend/uploads" ] && [ -z "$(ls -A "$SHARED_DIR/uploads" 2>/dev/null)" ]; then
        cp -a "$APP_DIR/backend/uploads/." "$SHARED_DIR/uploads/" 2>/dev/null || true
    fi

    mkdir -p "$SHARED_DIR/data" "$SHARED_DIR/uploads/images" "$SHARED_DIR/uploads/videos"
}

# 把共享数据挂进某个 release
# 注意：git archive 里若已存在同名目录，直接 ln -s 会把软链建到目录内部，
# 所以先删掉目标位置再建软链。
link_shared() {
    local release="$1"
    local target
    for name in .env data uploads; do
        target="$release/backend/$name"
        rm -rf "$target"
        ln -s "$SHARED_DIR/$name" "$target"
    done
}

# ---------------- 前置检查 ----------------

# 构建前把「缺依赖」这类问题提前暴露，避免跑到一半才失败
preflight() {
    log "  检查构建环境…"

    if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
        die "找不到 $PYTHON_BIN，无法创建虚拟环境"
    fi
    if ! "$PYTHON_BIN" -c 'import venv' >/dev/null 2>&1; then
        die "缺少 python3-venv，执行：apt install -y python3-venv（CentOS: yum install -y python3）"
    fi

    if ! command -v "$NPM_BIN" >/dev/null 2>&1; then
        die "找不到 $NPM_BIN，无法构建前端（宝塔可在 Node 管理器装好后用 NPM_BIN=/path/to/npm 指定）"
    fi
    local node_major
    node_major="$("$NPM_BIN" -v 2>/dev/null | cut -d. -f1)"
    if [ -n "$node_major" ] && [ "$node_major" -lt 18 ] 2>/dev/null; then
        die "Node 版本为 $node_major，Vite 构建需要 >= 18"
    fi

    if command -v df >/dev/null 2>&1; then
        local avail_kb
        avail_kb="$(df -Pk "$DEPLOY_DIR" 2>/dev/null | awk 'NR==2 {print $4}')"
        if [ -n "${avail_kb:-}" ] && [ "$avail_kb" -lt 1048576 ] 2>/dev/null; then
            die "磁盘剩余不足 1GB（$(($avail_kb / 1024))MB），先清理再发布"
        fi
    fi

    if ! command -v curl >/dev/null 2>&1; then
        log "  ⚠ 未安装 curl，发布后将跳过健康检查"
    fi
    log "  环境检查通过"
}

# 构建产物自检：少文件就别切换，免得把线上切到坏的版本
check_build() {
    local release="$1"
    [ -f "$release/backend/app/main.py" ] || { log "  ✗ 缺少后端入口 app/main.py"; return 1; }
    [ -x "$release/backend/venv/bin/python" ] || { log "  ✗ 缺少后端虚拟环境"; return 1; }
    if [ -f "$release/frontend/package.json" ]; then
        [ -f "$release/frontend/dist/index.html" ] || { log "  ✗ 前端产物 dist/index.html 不存在"; return 1; }
    fi
    return 0
}

# ---------------- 构建 ----------------

build_backend() {
    local release="$1"
    local backend="$release/backend"
    log "  创建虚拟环境…"
    "$PYTHON_BIN" -m venv "$backend/venv" >>"$LOG_FILE" 2>&1 \
        || die "虚拟环境创建失败（确认已安装 python3-venv）"
    "$backend/venv/bin/pip" install --upgrade pip -q >>"$LOG_FILE" 2>&1 || true
    log "  安装 Python 依赖…"
    "$backend/venv/bin/pip" install -q -r "$backend/requirements.txt" >>"$LOG_FILE" 2>&1 \
        || die "Python 依赖安装失败，详见 $LOG_FILE"
}

build_frontend() {
    local release="$1"
    local frontend="$release/frontend"
    if [ ! -f "$frontend/package.json" ]; then
        log "  跳过前端（无 package.json）"
        return 0
    fi

    log "  安装前端依赖…"
    if [ -f "$frontend/package-lock.json" ]; then
        (cd "$frontend" && "$NPM_BIN" ci --no-audit --no-fund) >>"$LOG_FILE" 2>&1 \
            || die "npm ci 失败（检查 Node 是否 >= 18）"
    else
        (cd "$frontend" && "$NPM_BIN" install --no-audit --no-fund) >>"$LOG_FILE" 2>&1 \
            || die "npm install 失败（检查 Node 是否 >= 18）"
    fi

    log "  构建前端产物…"
    (cd "$frontend" && "$NPM_BIN" run build) >>"$LOG_FILE" 2>&1 \
        || die "前端构建失败，详见 $LOG_FILE"

    # node_modules 只用于构建，留着会让每个版本多占几百 MB
    rm -rf "$frontend/node_modules"
}

# ---------------- 切换与重启 ----------------

do_restart() {
    if [ -n "$RESTART_CMD" ]; then
        log "  执行自定义重启命令：$RESTART_CMD"
        bash -c "$RESTART_CMD" >>"$LOG_FILE" 2>&1 || log "  ⚠ 自定义重启命令返回非零"
        return 0
    fi

    if ! command -v systemctl >/dev/null 2>&1; then
        log "  ⚠ 没有 systemd，无法自动重启，请手动重启后端（或设置 RESTART_CMD）"
        return 0
    fi

    if ! systemctl list-unit-files 2>/dev/null | grep -q "^${SERVICE}\.service"; then
        log "  ⚠ 未找到服务 ${SERVICE}.service，先执行 ops/install-service.sh"
        return 0
    fi

    if [ "$(id -u)" = "0" ]; then
        systemctl restart "$SERVICE" >>"$LOG_FILE" 2>&1 || return 1
    else
        sudo -n systemctl restart "$SERVICE" >>"$LOG_FILE" 2>&1 || return 1
    fi
    log "  服务 ${SERVICE} 已重启"
    return 0
}

wait_health() {
    if ! command -v curl >/dev/null 2>&1; then
        log "  ⚠ 未安装 curl，跳过健康检查"
        return 0
    fi
    # HEALTH_TIMEOUT 是总等待秒数，不是循环次数
    local deadline=$((SECONDS + HEALTH_TIMEOUT))
    while [ "$SECONDS" -lt "$deadline" ]; do
        if curl -fsS -m 2 "$HEALTH_URL" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    return 1
}

# 切换软链 → 重启 → 健康检查；成功返回 0，失败返回 1（由调用方决定是否回滚）
switch_to() {
    local target="$1"
    [ -d "$target" ] || die "目标版本不存在：$target"
    [ -f "$target/backend/app/main.py" ] || die "目标版本缺少后端代码：$target"
    if [ ! -x "$target/backend/venv/bin/python" ]; then
        die "版本 $(basename "$target") 缺少虚拟环境，无法启动。可执行 bash ops/deploy.sh --force 重新构建"
    fi

    # current 若被误建成真实目录，先清掉，避免软链建到目录内部
    if [ -e "$CURRENT_LINK" ] && [ ! -L "$CURRENT_LINK" ]; then
        rm -rf "$CURRENT_LINK"
    fi

    log "  切换软链 current → $(basename "$target")"
    ln -sfn "$target" "$CURRENT_LINK"

    # 首次从旧结构迁移时，服务单元可能还指向老路径，
    # 这两个开关让发布只「准备好版本」，重启与校验交给迁移脚本后续处理
    if [ "${NO_RESTART:-0}" = "1" ]; then
        log "  （按要求跳过重启）"
    else
        step "重启服务"
        if ! do_restart; then
            log "  ✗ 服务重启失败"
            return 1
        fi
    fi

    if [ "${SKIP_HEALTH:-0}" = "1" ]; then
        log "  （按要求跳过健康检查）"
        return 0
    fi

    step "健康检查"
    if wait_health; then
        log "  ✓ 健康检查通过"
        return 0
    fi
    log "  ✗ 健康检查失败（${HEALTH_TIMEOUT}s 内 $HEALTH_URL 未就绪）"
    return 1
}

# 清理旧版本：保留最近 N 个，且永不删除当前版本
prune_releases() {
    local keep="${1:-$RELEASE_KEEP}"
    local current i=0 name
    current="$(current_release_name)"
    while read -r name; do
        [ -z "$name" ] && continue
        i=$((i + 1))
        [ "$i" -le "$keep" ] && continue
        [ "$name" = "$current" ] && continue
        log "  清理旧版本 $name"
        rm -rf "${RELEASES_DIR:?}/$name"
    done < <(list_releases)
}
