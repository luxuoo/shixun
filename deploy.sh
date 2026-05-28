#!/bin/bash
# 宝塔面板部署脚本
# 使用方法: bash deploy.sh

set -e

PROJECT_DIR="/www/wwwroot/learning-system"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "=========================================="
echo "  AI 编程实训辅助教学系统 - 部署脚本"
echo "=========================================="

# 1. 构建前端
echo "[1/4] 构建前端..."
cd "$FRONTEND_DIR"
npm install
npm run build
echo "✓ 前端构建完成"

# 2. 安装后端依赖
echo "[2/4] 安装后端依赖..."
cd "$BACKEND_DIR"
pip install -r requirements.txt
echo "✓ 后端依赖安装完成"

# 3. 初始化数据库
echo "[3/4] 初始化数据库..."
cd "$BACKEND_DIR"
python init_data.py
echo "✓ 数据库初始化完成"

# 4. 创建 systemd 服务
echo "[4/4] 创建系统服务..."
cat > /etc/systemd/system/learning-system.service << EOF
[Unit]
Description=AI Learning System Backend
After=network.target

[Service]
Type=simple
User=www
WorkingDirectory=$BACKEND_DIR
ExecStart=$(which python) -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5
Environment=PYTHONPATH=$BACKEND_DIR

[Install]
WantedBy=multi-user-group
EOF

systemctl daemon-reload
systemctl enable learning-system
systemctl start learning-system
echo "✓ 后端服务已启动"

echo ""
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo ""
echo "接下来请在宝塔面板配置 Nginx（见下方说明）"
echo ""
