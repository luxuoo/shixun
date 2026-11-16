# 宝塔面板部署教程

本文档详细介绍如何将 AI 编程实训辅助教学系统部署到云服务器。

---

## 一、服务器准备

### 1.1 购买云服务器

推荐配置：
- CPU：2核
- 内存：4GB
- 硬盘：40GB SSD
- 系统：Ubuntu 22.04 LTS 或 CentOS 7+
- 带宽：3Mbps 以上

### 1.2 开放端口

在云服务器控制台的安全组中放行以下端口：

| 端口 | 用途 |
|------|------|
| 22 | SSH 远程连接 |
| 80 | HTTP 访问 |
| 443 | HTTPS 访问 |

### 1.3 安装宝塔面板

SSH 登录服务器后执行：

**Ubuntu / Debian：**
```bash
wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh
```

**CentOS：**
```bash
yum install -y wget && wget -O install.sh https://download.bt.cn/install/install_6.0.sh && bash install.sh
```

安装完成后会显示：
```
外网面板地址: http://xxx.xxx.xxx.xxx:8888/xxxxx
内网面板地址: http://xxx.xxx.xxx.xxx:8888/xxxxx
username: xxxxxxxx
password: xxxxxxxx
```

请务必保存好这些信息。

---

## 二、宝塔面板安装软件

登录宝塔面板后，进入 **软件商店**，搜索并安装以下软件：

| 软件 | 版本 | 说明 |
|------|------|------|
| Nginx | 1.24+ | Web 服务器和反向代理 |
| Node.js 版本管理器 | - | 用于构建前端（安装 Node.js 18） |
| Python 项目管理器 | - | 可选，用于管理 Python 环境 |

如果不用 Python 项目管理器，也可以直接安装系统自带的 Python 3。

---

## 三、上传项目

### 方式一：使用 Git（推荐）

```bash
cd /www/wwwroot
git clone http://123.207.45.73:1080/fumeng/shixun.git learning-system
```

### 方式二：宝塔文件管理器上传

1. 在宝塔面板点击 **文件**
2. 进入 `/www/wwwroot/` 目录
3. 点击 **上传**，将整个项目文件夹压缩为 zip 后上传
4. 上传完成后解压，重命名为 `learning-system`

### 方式三：SCP 命令上传

```bash
# 在本地电脑执行
scp -r /path/to/项目 root@服务器IP:/www/wwwroot/learning-system
```

---

## 四、部署后端

### 4.1 安装 Python 依赖

```bash
cd /www/wwwroot/learning-system/backend
pip3 install -r requirements.txt
```

如果提示 pip3 不存在，先安装：
```bash
# Ubuntu
apt install python3-pip -y

# CentOS
yum install python3-pip -y
```

### 4.2 配置环境变量

```bash
cp /www/wwwroot/learning-system/.env.example /www/wwwroot/learning-system/backend/.env
```

编辑 `/www/wwwroot/learning-system/backend/.env`：

```ini
# 应用配置
APP_NAME=AI编程实训辅助教学系统
DEBUG=false

# 数据库配置（SQLite，无需修改）
DATABASE_URL=sqlite+aiosqlite:///./data/teaching.db

# AI 服务商：deepseek 或 mimo（二选一，填哪家的密钥就选哪家）
AI_PROVIDER=deepseek

# DeepSeek API（推荐）
DEEPSEEK_API_KEY=sk-你的密钥
DEEPSEEK_API_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# 小米 MiMo API（备选，留空则不启用）
MIMO_API_KEY=
MIMO_API_URL=https://token-plan-cn.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5-pro

# 超时（秒）与失败重试次数
AI_TIMEOUT=120
AI_MAX_RETRIES=2

# 安全配置（务必修改为随机字符串）
SECRET_KEY=改成一个很长的随机字符串比如用openssl生成
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 文件上传配置
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760

# CORS 配置（改成你的域名或服务器IP）
CORS_ORIGINS=["http://你的域名或IP"]
```

生成随机 SECRET_KEY：
```bash
openssl rand -hex 32
```

### 4.3 初始化数据库

```bash
cd /www/wwwroot/learning-system/backend
python3 init_data.py
```

成功后会显示默认账号信息。

### 4.4 创建 systemd 服务

执行以下命令创建后端服务：

```bash
cat > /etc/systemd/system/learning-system.service << 'EOF'
[Unit]
Description=AI Learning System Backend
After=network.target

[Service]
Type=simple
User=www
WorkingDirectory=/www/wwwroot/learning-system/backend
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5
Environment=PYTHONPATH=/www/wwwroot/learning-system/backend

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable learning-system
systemctl start learning-system
```

验证后端是否启动成功：
```bash
# 查看服务状态
systemctl status learning-system

# 测试接口
curl http://127.0.0.1:8000/docs
```

如果看到 HTML 输出说明后端启动成功。

---

## 五、构建前端

### 5.1 安装 Node.js

在宝塔面板的 **Node.js 版本管理器** 中安装 Node.js 18。

或者命令行安装：
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install nodejs -y
```

### 5.2 构建前端

```bash
cd /www/wwwroot/learning-system/frontend
npm install
npm run build
```

构建完成后会生成 `frontend/dist/` 目录，这就是前端的静态文件。

> 如果构建过程中报内存不足，可以使用：`NODE_OPTIONS="--max-old-space-size=2048" npm run build`

---

## 六、配置 Nginx

### 6.1 添加站点

在宝塔面板：**网站** -> **添加站点**

- 域名：填写你的域名（如 `learn.example.com`），如果没有域名就填服务器 IP
- PHP 版本：选择 **纯静态**
- 根目录：默认即可（会自动创建）

### 6.2 配置反向代理

点击站点名称 -> **设置** -> **配置文件**，将内容替换为：

```nginx
server {
    listen 80;
    server_name 你的域名或IP;  # 改成你的域名或服务器IP

    # 前端静态文件
    location / {
        root /www/wwwroot/learning-system/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;   # AI 接口响应较慢，超时设长一些
        proxy_connect_timeout 10s;
    }

    # API 文档页面（调试用，正式上线可删除）
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000;
    }

    # 上传文件静态服务
    location /uploads/ {
        alias /www/wwwroot/learning-system/backend/uploads/;
    }
}
```

保存后点击 **重载配置**。

### 6.3 删除默认站点

如果宝塔自动创建了一个默认站点，建议删除它，避免冲突。

---

## 七、配置 HTTPS（推荐）

在宝塔面板：**网站** -> 点击站点 -> **设置** -> **SSL**

1. 选择 **Let's Encrypt**
2. 勾选你的域名
3. 点击 **申请**
4. 开启 **强制 HTTPS**

申请成功后，将 Nginx 配置中的 `listen 80` 改为 `listen 443 ssl`，并添加证书路径（宝塔会自动处理）。

---

## 八、验证部署

打开浏览器访问你的域名或服务器 IP，应该能看到登录页面。

测试步骤：
1. 使用默认管理员账号 `admin / admin123` 登录
2. 进入管理后台，检查各功能是否正常
3. 切换到学生账号 `student1 / student123`，测试 AI 助手功能
4. 提交一段代码，确认自动评分功能正常

---

## 九、常用运维命令

```bash
# 后端服务管理
systemctl start learning-system     # 启动
systemctl stop learning-system      # 停止
systemctl restart learning-system   # 重启
systemctl status learning-system    # 查看状态

# 查看后端日志
journalctl -u learning-system -f

# 查看端口占用
lsof -i :8000

# 重新构建前端（更新代码后）
cd /www/wwwroot/learning-system/frontend
npm install
npm run build
systemctl restart learning-system
```

---

## 十、更新部署（一键更新 + 一键回滚）

更新不再直接改工作目录，而是「构建到新版本目录 → 切换软链 → 重启」。
好处是**构建失败不影响线上**，切换失败**自动回滚**，历史版本可随时切回。

### 10.1 目录结构（了解即可，不用手动建）

```
/www/wwwroot/learning-system/          # git 仓库，只负责拉代码
├── .deploy/
│   ├── releases/
│   │   ├── 20261116-201533-1d36261/   # 每个版本独立目录（含各自 venv 与 dist）
│   │   ├── 20261115-143022-9a2c1f0/
│   │   └── ...
│   ├── current -> releases/20261116-201533-1d36261   # 软链，切换即生效
│   ├── shared/
│   │   ├── .env                       # 环境变量（只维护这一份）
│   │   ├── data/teaching.db           # 数据库
│   │   └── uploads/                   # 上传文件
│   ├── state.json                     # 最近一次发布状态（后台页面读它）
│   └── ops.log                        # 发布日志
└── ops/                               # 发布脚本
```

首次发布会自动把老的 `backend/data`、`backend/uploads`、`backend/.env` 迁到 `.deploy/shared`。

> 服务器上已经是老结构（服务直接跑 `backend/`）？先看 **10.5**，迁移一次后本节步骤自然完成。

### 10.2 一次性准备（3 步）

```bash
cd /www/wwwroot/learning-system

# 1) 先跑一次发布，生成 current 软链与共享目录
git config --global --add safe.directory /www/wwwroot/learning-system   # 非 root 用户需要
bash ops/deploy.sh

# 2) 注册 systemd 服务（脚本自动指向 .deploy/current，并提供免密重启）
sudo bash ops/install-service.sh

# 3) 把 Nginx 指到发布目录（片段见 ops/nginx.snippet.conf）
#    root /www/wwwroot/learning-system/.deploy/current/frontend/dist;
#    location /uploads/ { alias /www/wwwroot/learning-system/.deploy/shared/uploads/; }
nginx -t && nginx -s reload
```

> 用宝塔「Python 项目管理器」启动后端的话，跳过第 2 步，改为在 `.env` 里设置
> `RESTART_CMD="bt restart 你的项目名"`，发布脚本会调它重启。

### 10.3 日常更新（三种方式任选）

**方式 A：命令行（最稳）**

```bash
cd /www/wwwroot/learning-system
bash ops/deploy.sh              # 更新到 origin/main
bash ops/deploy.sh --ref v1.2   # 更新到指定分支/标签/提交
bash ops/status.sh              # 看当前版本与历史
```

**方式 B：管理后台点按钮**

服务器 `.env` 里设置 `OPS_ENABLED=true` 并重启后端，然后
管理后台 → 系统设置 → **部署运维** → 「一键更新」。页面会实时显示进度、构建日志和历史版本。

**方式 C：git push 后自动发布**

```bash
# 在服务器上，用 .env 里的密钥启动 webhook 接收器
set -a; . /www/wwwroot/learning-system/.deploy/shared/.env; set +a
python3 /www/wwwroot/learning-system/ops/webhook.py

# 建议做成常驻服务（可选）
# /etc/systemd/system/learning-webhook.service
#   [Service]
#   EnvironmentFile=/www/wwwroot/learning-system/.deploy/shared/.env
#   ExecStart=/usr/bin/python3 /www/wwwroot/learning-system/ops/webhook.py
#   Restart=always
```

然后在 GitHub 仓库 → Settings → Webhooks 添加：

| 项 | 值 |
|---|---|
| Payload URL | `https://你的域名/hooks/github` |
| Content type | `application/json` |
| Secret | 与 `.env` 的 `OPS_WEBHOOK_SECRET` 一致 |
| Events | Just the push event |

之后 `git push origin main` 就会自动发布（同分支连续推送会合并，不会并发打架）。

> 私有仓库需要服务器有拉取权限：`git remote set-url origin git@github.com:用户名/仓库.git`
> 并把部署公钥（`~/.ssh/id_ed25519.pub`）加到仓库 Deploy keys。

### 10.4 回滚

```bash
bash ops/rollback.sh                    # 回到上一个版本（不重建，约 5 秒）
bash ops/rollback.sh --list             # 列出所有可用版本
bash ops/rollback.sh --to 20261115-143022-9a2c1f0   # 回到指定版本
```

后台「部署运维」页面同样可以点「一键回滚」，或在版本历史里对某个版本点「回滚到此版本」。

回滚只是切换软链 + 重启，**不重新构建**，所以很快；回滚后若想回到最新版，再点一次「一键更新」即可。

### 10.5 从旧版升级到发布体系（老服务器必看）

如果服务器上还是「`git pull` + 直接构建」的老结构（`backend/` 与 `frontend/dist` 被服务和 Nginx 直接引用），
先迁移一次，之后才能用一键更新。

**直接 `git pull` 后执行 `ops/deploy.sh` 是不行的**：旧 systemd 单元的 `WorkingDirectory` 还指着
`.../learning-system/backend`，脚本重启的仍是老代码，而健康检查（读 8000 端口）会照常通过，
看起来「发布成功」但页面没变。

正确做法：

```bash
cd /www/wwwroot/learning-system

# 1) 先拿到新代码（远端不是 GitHub 的话，先加一个）
git remote -v
# 若 origin 还是自建地址，执行：
#   git remote add github https://github.com/luxuoo/shixun.git
#   git fetch github main && git reset --hard github/main
git pull

# 2) 一条命令完成迁移（构建 → 迁移数据 → 改写服务单元 → 重启 → 校验）
bash ops/migrate-from-legacy.sh

# 根目录的 bash deploy.sh 已改为转发入口，效果相同；
# 迁移完成后再执行它只会提示当前版本，不会覆盖服务配置
```

脚本会做这些事，全程线上不中断：

| 步骤 | 说明 |
|---|---|
| 自检 | 检查 git 仓库、python3-venv、npm/Node 版本 |
| 备份 | `.env`、`data/`、`uploads/` 复制到 `.deploy/backup/<时间戳>/` |
| 构建 | 新版本构建到 `.deploy/releases/`，此时线上仍跑老代码 |
| 迁数据 | 老 `.env` / 数据库 / 上传文件搬到 `.deploy/shared`，版本间共享 |
| 改服务 | 把 systemd 单元重写到 `.deploy/current/backend` 并重启 |
| 校验 | 健康检查 + 打印 Nginx 需要改的两行 |

最后手动改 Nginx 并 reload：

```nginx
root /www/wwwroot/learning-system/.deploy/current/frontend/dist;
location /uploads/ { alias /www/wwwroot/learning-system/.deploy/shared/uploads/; }
```

```bash
nginx -t && nginx -s reload
```

用宝塔「Python 项目管理器」启动后端（没有 systemd 单元）的话，迁移脚本会跳过改服务这一步，
请改为在 `.env` 里设置 `RESTART_CMD="bt restart 你的项目名"`，并在面板里把项目目录改成
`/www/wwwroot/learning-system/.deploy/current/backend`。

> 迁移脚本以 root 执行时，会自动把 `.deploy` 归属改成 `www`，否则运行用户写不了数据库和上传目录。

### 10.6 手动流程（不使用脚本时）

```bash
cd /www/wwwroot/learning-system
git pull origin main
cd frontend && npm ci && npm run build
cd ../backend && pip3 install -r requirements.txt
systemctl restart learning-system
```

---

## 十一、数据备份

重要数据目录：

| 路径 | 内容 |
|------|------|
| `backend/data/teaching.db` | SQLite 数据库（所有业务数据） |
| `backend/uploads/` | 用户上传的文件 |
| `backend/.env` | 环境配置（含 API Key） |

建议定期备份：
```bash
# 创建备份脚本
cat > /www/wwwroot/learning-system/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/www/backup/learning-system"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# 备份数据库
cp /www/wwwroot/learning-system/backend/data/teaching.db $BACKUP_DIR/teaching_$DATE.db

# 备份上传文件
tar czf $BACKUP_DIR/uploads_$DATE.tar.gz -C /www/wwwroot/learning-system/backend uploads/

# 只保留最近 30 天的备份
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "备份完成: $DATE"
EOF

chmod +x /www/wwwroot/learning-system/backup.sh
```

设置定时备份（每天凌晨 3 点）：
```bash
crontab -e
# 添加以下行
0 3 * * * /www/wwwroot/learning-system/backup.sh >> /var/log/backup.log 2>&1
```

---

## 十二、常见问题

### 1. 后端启动失败
```bash
# 查看错误日志
journalctl -u learning-system -n 50
# 常见原因：端口被占用、Python 依赖缺失、.env 配置错误
```

### 2. AI 功能不工作
- 先到「AI 使用统计 → AI 服务商」点「测试选中」，看具体报错（认证失败 / 超时 / 余额不足会分别提示）
- 检查 `backend/.env`：`AI_PROVIDER` 与对应服务商的 `*_API_KEY` 是否都填了
- 确认服务器能访问 `api.deepseek.com`（或 `token-plan-cn.xiaomimimo.com`）
- 在后台设置中确认"AI 对话功能"已开启
- 密钥错误时重启服务，日志会打印 `[AI] 服务商=... 密钥=已配置/未配置`

### 3. 前端页面空白
- 确认 `frontend/dist/` 目录存在且有文件
- 检查 Nginx 配置中的 `root` 路径是否正确
- 检查浏览器控制台是否有报错

### 4. CORS 跨域错误
- 确认 `backend/.env` 中的 `CORS_ORIGINS` 包含你的访问地址
- 格式：`["http://你的域名"]` 或 `["http://你的IP"]`

### 5. 上传文件失败
- 检查 `backend/uploads/` 目录权限：`chmod 755 backend/uploads/`
- 检查 Nginx 的 `/uploads/` location 配置是否正确

### 6. 后台「部署运维」提示未开启
- 服务器 `.env`（实际读的是 `.deploy/shared/.env`）里设置 `OPS_ENABLED=true`，然后 `systemctl restart learning-system`
- 页面右上角状态卡应显示「服务状态：运行中」；若显示「无响应」，检查 `OPS_HEALTH_URL` 是否指向真实端口

### 7. 一键更新报「服务重启失败」
发布脚本用非 root 用户跑，需要免密 sudo：

```bash
# 重新执行安装脚本会自动配置；或手动添加
echo 'www ALL=(root) NOPASSWD: /bin/systemctl restart learning-system, /bin/systemctl is-active learning-system' \
  | sudo tee /etc/sudoers.d/learning-system-deploy
sudo chmod 440 /etc/sudoers.d/learning-system-deploy
```

### 8. 更新后页面还是旧版本
- 浏览器缓存：`Ctrl+F5` 强刷；Nginx 里 `index.html` 应为 `no-store`（见 `nginx.conf`）
- Nginx 仍指向老路径：确认 `root` 已改为 `.deploy/current/frontend/dist` 并 `nginx -s reload`
- 软链未生效：`readlink -f /www/wwwroot/learning-system/.deploy/current` 看指向哪个版本

### 9. 发布失败怎么排查
```bash
tail -50 /www/wwwroot/learning-system/.deploy/ops.log   # 发布日志
bash ops/status.sh                                      # 当前版本与健康状态
journalctl -u learning-system -n 50                     # 后端启动报错
```
构建失败时线上仍跑旧版本，`.deploy/releases/` 里会留下失败版本的目录，确认无用可手动删掉。
