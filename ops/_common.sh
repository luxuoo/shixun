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

# 从 .env 读取运维相关配置（命令行执行时不会自动带上 .env）
# 只认白名单键，避免把整个文件 source 进来
load_ops_env() {
    local file line key val
    for file in "$SHARED_DIR/.env" "$APP_DIR/backend/.env" "$APP_DIR/.env"; do
        [ -f "$file" ] || continue
        while IFS= read -r line || [ -n "$line" ]; do
            case "$line" in
                ''|'#'*) continue ;;
            esac
            line="${line#export }"
            key="${line%%=*}"
            val="${line#*=}"
            key="$(printf '%s' "$key" | tr -d '[:space:]')"
            case "$key" in
                PIP_INDEX_URL|NPM_REGISTRY|INSTALL_TIMEOUT|RELEASE_KEEP|RESTART_CMD|HEALTH_TIMEOUT|SERVICE|PYTHON_BIN|NPM_BIN) ;;
                *) continue ;;
            esac
            # 已经显式设置的环境变量优先
            [ -n "${!key:-}" ] && continue
            # 去掉包裹的引号
            case "$val" in
                \"*\") val="${val#\"}"; val="${val%\"}" ;;
                \'*\') val="${val#\'}"; val="${val%\'}" ;;
            esac
            export "$key=$val"
        done <"$file"
    done
}

load_ops_env

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

# 依赖源：国内服务器直连 PyPI / npmjs 经常卡住，默认走镜像；改成 official 即用官方源
PIP_INDEX_URL="${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}"
NPM_REGISTRY="${NPM_REGISTRY:-https://registry.npmmirror.com}"
# 单步安装超时（秒），超时即判定失败，不会无限卡住
INSTALL_TIMEOUT="${INSTALL_TIMEOUT:-900}"

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

# ---------------- 构建辅助 ----------------

# 带超时执行，避免网络卡住时发布永远停在「安装依赖」
run_limited() {
    local secs="$1"
    shift
    if command -v timeout >/dev/null 2>&1; then
        timeout "$secs" "$@"
        local code=$?
        [ "$code" -eq 124 ] && return 124
        return "$code"
    fi
    "$@"
}

# pip 源参数
pip_index_args() {
    case "$PIP_INDEX_URL" in
        ""|official|OFFICIAL)
            return 0 ;;
    esac
    local host
    host="$(printf '%s' "$PIP_INDEX_URL" | sed -E 's#^https?://([^/]+).*#\1#')"
    printf '%s\n%s\n%s\n' "--index-url" "$PIP_INDEX_URL" "--trusted-host $host"
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
    local venv="$backend/venv"

    # requirements.txt 没变就直接复用上一版 venv：省掉最容易卡住的一步
    if [ "${REUSE_VENV:-0}" = "1" ] && [ -n "${PREV_DIR:-}" ] && [ -x "$PREV_DIR/backend/venv/bin/python" ]; then
        log "  依赖未变更，复用上一版虚拟环境（跳过 pip 安装）"
        cp -a "$PREV_DIR/backend/venv" "$venv" 2>>"$LOG_FILE" && return 0
        log "  ⚠ 复用失败，改为重新安装依赖"
        rm -rf "$venv"
    fi

    log "  创建虚拟环境…"
    "$PYTHON_BIN" -m venv "$venv" >>"$LOG_FILE" 2>&1 || {
        log "  ✗ venv 创建失败（安装 python3-venv 后重试）"
        return 1
    }

    local idx_desc="官方 PyPI"
    case "$PIP_INDEX_URL" in
        ""|official|OFFICIAL) ;;
        *) idx_desc="$PIP_INDEX_URL" ;;
    esac
    log "  安装 Python 依赖（源：$idx_desc，超时 ${INSTALL_TIMEOUT}s）"

    local args=(install -q --disable-pip-version-check --timeout 30 --retries 3)
    # 用 python -m pip，避免复制过来的 venv 里 pip 脚本 shebang 指向旧路径
    local pip_cmd=("$venv/bin/python" -m pip)
    if [ "$idx_desc" != "官方 PyPI" ]; then
        local host
        host="$(printf '%s' "$PIP_INDEX_URL" | sed -E 's#^https?://([^/]+).*#\1#')"
        args+=(--index-url "$PIP_INDEX_URL" --trusted-host "$host")
    fi

    run_limited "$INSTALL_TIMEOUT" "${pip_cmd[@]}" "${args[@]}" -r "$backend/requirements.txt" >>"$LOG_FILE" 2>&1
    local code=$?
    if [ "$code" -eq 124 ]; then
        log "  ✗ 依赖安装超时（${INSTALL_TIMEOUT}s），多半是源太慢"
        log "    可在 .env 里设置 PIP_INDEX_URL 换源，或 PIP_INDEX_URL=official 用官方源"
        return 1
    fi
    if [ "$code" -ne 0 ]; then
        log "  ✗ 依赖安装失败，详见 $LOG_FILE"
        return 1
    fi
    return 0
}

build_frontend() {
    local release="$1"
    local frontend="$release/frontend"
    if [ ! -f "$frontend/package.json" ]; then
        log "  跳过前端（无 package.json）"
        return 0
    fi

    # 前端源码没变就直接复用上一版 dist：省掉 npm install + vite build
    if [ "${REUSE_DIST:-0}" = "1" ] && [ -n "${PREV_DIR:-}" ] && [ -f "$PREV_DIR/frontend/dist/index.html" ]; then
        log "  前端未变更，复用上一版构建产物（跳过 npm）"
        mkdir -p "$frontend"
        cp -a "$PREV_DIR/frontend/dist" "$frontend/dist" 2>>"$LOG_FILE" && return 0
        log "  ⚠ 复用失败，改为重新构建"
        rm -rf "$frontend/dist"
    fi

    local registry_desc="官方 npm"
    case "$NPM_REGISTRY" in
        ""|official|OFFICIAL) ;;
        *) registry_desc="$NPM_REGISTRY" ;;
    esac
    local reg_args=()
    if [ "$registry_desc" != "官方 npm" ]; then
        reg_args=(--registry "$NPM_REGISTRY")
    fi
    local common_args=(--no-audit --no-fund --fetch-timeout=60000 --fetch-retries=3)

    log "  安装前端依赖（源：$registry_desc，超时 ${INSTALL_TIMEOUT}s）"
    if [ -f "$frontend/package-lock.json" ]; then
        (cd "$frontend" && run_limited "$INSTALL_TIMEOUT" "$NPM_BIN" ci "${common_args[@]}" "${reg_args[@]}") >>"$LOG_FILE" 2>&1
    else
        (cd "$frontend" && run_limited "$INSTALL_TIMEOUT" "$NPM_BIN" install "${common_args[@]}" "${reg_args[@]}") >>"$LOG_FILE" 2>&1
    fi
    local code=$?
    if [ "$code" -eq 124 ]; then
        log "  ✗ 前端依赖安装超时（${INSTALL_TIMEOUT}s），多半是 registry 太慢"
        log "    可在 .env 里设置 NPM_REGISTRY 换源"
        return 1
    fi
    if [ "$code" -ne 0 ]; then
        log "  ✗ 前端依赖安装失败，详见 $LOG_FILE"
        return 1
    fi

    log "  构建前端产物…"
    (cd "$frontend" && run_limited "$INSTALL_TIMEOUT" "$NPM_BIN" run build) >>"$LOG_FILE" 2>&1
    if [ $? -ne 0 ]; then
        log "  ✗ 前端构建失败，详见 $LOG_FILE"
        return 1
    fi

    # node_modules 只用于构建，留着会让每个版本多占几百 MB
    rm -rf "$frontend/node_modules"
    return 0
}

# ---------------- 切换与重启 ----------------

# 判断服务单元是否存在
# 注意：不能用 `systemctl list-unit-files | grep -q ...` —— grep -q 命中后立即退出，
# systemctl 收到 SIGPIPE 返回 141，pipefail 下整条管道判为失败，
# 于是「服务明明存在」却被当成不存在，发布时直接跳过重启（线上仍是旧代码）。
service_exists() {
    command -v systemctl >/dev/null 2>&1 || return 1

    local state
    state="$(systemctl show -p LoadState --value "$SERVICE" 2>/dev/null || true)"
    if [ -n "$state" ]; then
        if [ "$state" = "not-found" ] || [ "$state" = "masked" ]; then
            return 1
        fi
        return 0
    fi

    # 老版本 systemd 不支持 show --value：先把列表落到文件，再对文件 grep（无管道）
    local tmp found=1
    tmp="$(mktemp 2>/dev/null || echo "/tmp/ops-units.$$")"
    systemctl list-unit-files >"$tmp" 2>/dev/null || true
    grep -q "^${SERVICE}\.service" "$tmp" && found=0
    rm -f "$tmp"
    return "$found"
}

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

    if ! service_exists; then
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
            SWITCH_FAIL="restart"
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
    SWITCH_FAIL="health"
    return 2
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
