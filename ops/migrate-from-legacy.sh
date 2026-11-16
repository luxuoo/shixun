#!/usr/bin/env bash
# 从旧结构迁移到「版本目录 + 软链」发布体系
#
# 旧结构（deploy.sh 直接 git pull 那种）：
#   /www/wwwroot/learning-system/{backend,frontend/dist}
#   systemd 的 WorkingDirectory 指向 .../learning-system/backend
#   Nginx root 指向 .../learning-system/frontend/dist
#
# 迁移后：
#   .deploy/current -> .deploy/releases/<版本>，服务与 Nginx 都指向 current
#
# 用法（在服务器上、项目根目录执行，已经 git pull 到含 ops/ 的新代码）：
#   bash ops/migrate-from-legacy.sh
#
# 整个过程线上不会中断：先在后台把新版本构建好，最后才切服务与 Nginx。

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

RUN_USER="${RUN_USER:-www}"
UNIT="/etc/systemd/system/${SERVICE}.service"
ASSUME_YES=0
[ "${1:-}" = "--yes" ] && ASSUME_YES=1

hint() { printf '\n\033[1m%s\033[0m\n' "$*"; }
is_root() { [ "$(id -u)" = "0" ]; }

# ---------------- 0. 环境自检 ----------------

hint "① 环境自检"

[ -d "$APP_DIR/.git" ] || die "$APP_DIR 不是 git 仓库，迁移脚本需在项目根目录执行"
[ -f "$APP_DIR/ops/deploy.sh" ] || die "未找到 ops/deploy.sh，请先 git pull 到最新代码"
log "  仓库: $APP_DIR"

if "$PYTHON_BIN" -c 'import venv' >/dev/null 2>&1; then
    log "  python3-venv: 可用"
else
    die "缺少 python3-venv，先安装：apt install -y python3-venv（CentOS: yum install -y python3）"
fi

if command -v "$NPM_BIN" >/dev/null 2>&1; then
    log "  npm: $("$NPM_BIN" -v 2>/dev/null)"
    NODE_MAJOR="$(node_major_of)"
    if [ -n "$NODE_MAJOR" ] && [ "$NODE_MAJOR" -lt 18 ] 2>/dev/null; then
        log "  ⚠ Node 版本为 $NODE_MAJOR，Vite 构建需要 >= 18，构建可能失败"
    fi
else
    die "找不到 npm，前端无法构建（宝塔可在「Node 版本管理器」里安装后重试，或用 NPM_BIN=/path/to/npm 指定）"
fi

if [ -L "$CURRENT_LINK" ] || [ -e "$CURRENT_LINK" ]; then
    log "  已存在 .deploy/current（当前版本 $(current_release_name)）"
    log "  这看起来已经迁移过了，直接更新请用：bash ops/deploy.sh"
    [ "$ASSUME_YES" = "1" ] || exit 0
fi

# 旧 systemd 单元是否还指着老路径
NEED_UNIT_FIX=0
if [ -f "$UNIT" ]; then
    OLD_WD="$(grep -E '^WorkingDirectory=' "$UNIT" | head -1 | cut -d= -f2-)"
    log "  现有服务单元 WorkingDirectory: ${OLD_WD:-（未设置）}"
    case "$OLD_WD" in
        *.deploy/current*) log "  服务已指向 current，无需改写" ;;
        *) NEED_UNIT_FIX=1; log "  → 需要改写到 .deploy/current/backend" ;;
    esac
else
    log "  未找到 systemd 单元 $UNIT，稍后会创建（首次安装）"
    NEED_UNIT_FIX=1
fi

# ---------------- 1. 备份老数据 ----------------

hint "② 备份现有配置与数据（首次安装时会跳过）"
BACKUP="$DEPLOY_DIR/backup/$(date '+%Y%m%d-%H%M%S')"
mkdir -p "$BACKUP"
for item in .env data uploads; do
    src="$APP_DIR/backend/$item"
    if [ -e "$src" ]; then
        cp -a "$src" "$BACKUP/" 2>/dev/null && log "  已备份 backend/$item → $BACKUP/$item"
    fi
done
log "  备份目录: $BACKUP"

# ---------------- 2. 构建并切换（先不动线上） ----------------

hint "③ 构建新版本（此时线上仍跑老代码，不会中断）"
log "  说明：共享数据（.env / 数据库 / 上传文件）会自动迁移到 .deploy/shared"

if ! NO_RESTART=1 SKIP_HEALTH=1 bash "$OPS_DIR/deploy.sh" --force; then
    die "构建失败，线上未受影响。排查：tail -50 $LOG_FILE"
fi
log "  新版本已就绪：$(current_release_name)"

# root 执行时，把发布目录交给运行用户，否则 www 无法写数据库与上传目录
if is_root && id "$RUN_USER" >/dev/null 2>&1; then
    chown -R "$RUN_USER:$RUN_USER" "$DEPLOY_DIR"
    log "  已将 $DEPLOY_DIR 归属改为 $RUN_USER"
fi

# ---------------- 3. 切换服务单元 ----------------

hint "④ 让服务运行新版本"
if [ "$NEED_UNIT_FIX" = "1" ]; then
    if is_root; then
        RUN_USER="$RUN_USER" bash "$OPS_DIR/install-service.sh" || die "服务单元安装失败"
    elif sudo -n true 2>/dev/null; then
        RUN_USER="$RUN_USER" sudo -n bash "$OPS_DIR/install-service.sh" || die "服务单元安装失败"
    else
        log "  ⚠ 需要 root 改写服务单元，请执行："
        log "    sudo bash ops/install-service.sh"
        log "  完成后再执行：bash ops/status.sh 确认版本"
        exit 1
    fi
else
    log "  服务单元无需改写，直接重启"
    do_restart || die "重启失败，排查：journalctl -u $SERVICE -n 50"
fi

# ---------------- 4. 校验 ----------------

hint "⑤ 校验"
if wait_health; then
    log "  ✓ 后端健康检查通过（$HEALTH_URL）"
else
    log "  ✗ 后端未就绪，查看日志：journalctl -u $SERVICE -n 50"
    log "  回滚到迁移前：cd $APP_DIR && git checkout <旧提交> && systemctl restart $SERVICE"
    exit 1
fi

# ---------------- 5. Nginx 提示 ----------------

hint "⑥ 最后一步：Nginx 指到新目录"
NEW_ROOT="$CURRENT_LINK/frontend/dist"
FOUND_CONF=0
for conf in /www/server/panel/vhost/nginx/*.conf /etc/nginx/conf.d/*.conf /etc/nginx/sites-enabled/*; do
    [ -f "$conf" ] || continue
    if grep -q "$APP_DIR/frontend/dist" "$conf" 2>/dev/null; then
        FOUND_CONF=1
        log "  发现仍指向老路径的配置：$conf"
        log "    需要把 root $APP_DIR/frontend/dist; 改成："
        log "    root $NEW_ROOT;"
        log "    并把 uploads 指向：alias ${SHARED_DIR}/uploads/;"
    fi
done

if [ "$FOUND_CONF" = "0" ]; then
    log "  未自动发现旧的 root 配置，请手动确认 Nginx 中："
    log "    root $NEW_ROOT;"
    log "    location /uploads/ { alias ${SHARED_DIR}/uploads/; }"
fi
log "  改完执行：nginx -t && nginx -s reload"

cat <<EOF

==========================================
迁移完成，后续日常操作：
  bash ops/deploy.sh        # 更新到最新代码
  bash ops/rollback.sh      # 回滚上一版
  bash ops/status.sh        # 查看当前版本
后台也能用：管理端 → 系统设置 → 部署运维（.env 设 OPS_ENABLED=true）
==========================================
EOF
