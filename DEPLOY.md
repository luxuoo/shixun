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

# MiMo API 配置（必须填写你自己的 API Key）
MIMO_API_KEY=你的API密钥
MIMO_API_URL=https://token-plan-cn.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5-pro

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

## 十、更新部署

当代码有更新时：

```bash
cd /www/wwwroot/learning-system
git pull origin main

# 重新构建前端
cd frontend
npm install
npm run build

# 重启后端
cd ../backend
pip3 install -r requirements.txt  # 如果有新依赖
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
- 检查 `backend/.env` 中的 `MIMO_API_KEY` 是否正确
- 确认服务器能访问 `token-plan-cn.xiaomimimo.com`
- 在后台设置中确认"AI 对话功能"已开启

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
