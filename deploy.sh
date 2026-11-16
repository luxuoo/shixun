#!/bin/bash
# 部署入口（兼容旧用法：bash deploy.sh）
#
# 真正的发布逻辑在 ops/ 下：
#   - 首次安装 / 从旧结构迁移：ops/migrate-from-legacy.sh
#   - 日常更新：              ops/deploy.sh
#   - 版本回滚：              ops/rollback.sh
#
# 本脚本只做转发，避免旧流程把 systemd 单元写回老路径。

set -e
cd "$(cd "$(dirname "$0")" && pwd)"

if [ ! -d .git ]; then
    echo "当前目录不是 git 仓库，请先："
    echo "  git clone https://github.com/luxuoo/shixun.git /www/wwwroot/learning-system"
    exit 1
fi

if [ ! -f ops/migrate-from-legacy.sh ]; then
    echo "未找到 ops/migrate-from-legacy.sh，代码可能还是旧版本，请先："
    echo "  git pull"
    exit 1
fi

echo "=========================================="
echo "  部署入口已改为 ops/ 发布脚本"
if [ -L .deploy/current ] || [ -e .deploy/current ]; then
    echo "  当前版本：$(basename "$(readlink -f .deploy/current 2>/dev/null || echo '')")"
    echo "  日常更新请用：bash ops/deploy.sh"
    echo "  回滚请用：    bash ops/rollback.sh"
    echo "=========================================="
    exit 0
fi

echo "  尚未初始化发布目录，进入安装/迁移流程"
echo "=========================================="
exec bash ops/migrate-from-legacy.sh "$@"
