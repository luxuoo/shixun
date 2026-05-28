# AI 编程实训辅助教学系统

基于 AI 引导的编程实践教学平台，帮助学生通过分步实训任务掌握编程技能。系统集成 MiMo AI 模型，提供智能提示、代码分析和自动评分功能。

## 系统功能

### 学生端
- **实训任务**：按步骤完成编程任务，支持 Python / Web / YOLO 等多类别
- **AI 助手**：三级渐进式提示（思维引导 -> API 指引 -> 关键代码），避免直接给出答案
- **代码分析**：提交代码后 AI 自动分析，给出改进建议
- **自动评分**：提交代码后 AI 从正确性、代码风格、完成度、创新性四个维度自动评分
- **成绩管理**：查看历史提交、AI 评分、教师评分和最终成绩

### 教师端
- **学生管理**：查看学生信息、学习进度、AI 使用情况
- **班级管理**：创建班级、分配学生
- **任务管理**：创建和编辑实训任务，支持 AI 自动分解任务步骤
- **提交审核**：查看学生提交记录，进行人工评分（与 AI 评分加权计算最终成绩）
- **AI 统计**：查看 AI 调用次数、Token 消耗等统计数据

### 管理员端
- **用户管理**：添加/编辑/禁用用户，支持批量注册学生
- **系统设置**：控制学生自主注册开关、AI 对话功能开关、提示次数上限、自动评分开关
- **数据面板**：系统整体数据概览
- **AI 日志**：查看所有 AI 调用的详细日志

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Naive UI + Monaco Editor |
| 后端 | Python FastAPI + SQLAlchemy (异步) + SQLite |
| AI | MiMo API（OpenAI 兼容格式） |
| 部署 | Nginx + systemd / Docker |

## 项目结构

```
shixun/
├── frontend/               # 前端 Vue 3 项目
│   ├── src/
│   │   ├── api/            # API 接口定义
│   │   ├── components/     # 公共组件（AI对话、代码编辑器等）
│   │   ├── layouts/        # 布局组件（学生端/管理端）
│   │   ├── router/         # 路由配置
│   │   ├── stores/         # Pinia 状态管理
│   │   └── views/          # 页面视图
│   └── vite.config.ts
├── backend/                # 后端 FastAPI 项目
│   ├── app/
│   │   ├── api/            # API 路由（认证、任务、提交、AI、管理）
│   │   ├── core/           # 核心配置（数据库、安全、设置）
│   │   ├── models/         # 数据库模型
│   │   ├── schemas/        # Pydantic 数据模型
│   │   ├── services/       # AI 服务封装
│   │   └── prompts/        # AI 提示词模板
│   ├── init_data.py        # 数据库初始化脚本
│   └── requirements.txt
├── database/               # 数据库 SQL 脚本
├── docker-compose.yml      # Docker 编排
├── nginx.conf              # Nginx 配置参考
├── deploy.sh               # 部署脚本
└── DEPLOY.md               # 部署教程
```

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- Docker（可选）

### 本地开发

**1. 克隆项目**
```bash
git clone http://123.207.45.73:1080/fumeng/shixun.git
cd shixun
```

**2. 配置环境变量**
```bash
cp .env.example backend/.env
# 编辑 backend/.env，填入你的 MiMo API Key
```

**3. 启动后端**
```bash
cd backend
pip install -r requirements.txt
python init_data.py
uvicorn app.main:app --reload --port 8000
```

**4. 启动前端**
```bash
cd frontend
npm install
npm run dev
```

**5. 访问系统**
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### Docker 部署

```bash
cp .env.example backend/.env
# 编辑 backend/.env
docker-compose up -d
```

## 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 教师 | teacher1 | teacher123 |
| 学生 | student1 | student123 |
| 测试学生 | test | test123 |

> 首次部署后请立即修改默认密码。

## AI 功能说明

系统使用 MiMo API（OpenAI 兼容格式）作为 AI 后端。在 `backend/.env` 中配置：

```
MIMO_API_KEY=your-api-key
MIMO_API_URL=https://token-plan-cn.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5-pro
```

### AI 提示分级

| 级别 | 触发条件 | 内容 | 是否包含代码 |
|------|----------|------|-------------|
| 一级（思维引导） | 首次请求 | 解题思路、方法论、引导问题 | 否 |
| 二级（API 指引） | 第二次请求 | 库名、函数名、参数说明 | 仅伪代码 |
| 三级（关键代码） | 第三次及以上 | 关键代码片段（最多15行） | 部分代码，标注 TODO |

### 管理员 AI 控制

管理员可在后台"系统设置"中控制：
- **AI 对话开关**：禁用后学生无法使用提示和代码分析功能
- **提示次数上限**：设置每个步骤的最大提示次数（0 = 使用步骤自带的默认值）
- **自动评分开关**：关闭后提交代码不会自动触发 AI 评分，需教师手动评分

## 评分机制

AI 评分从四个维度进行：

| 维度 | 权重 | 说明 |
|------|------|------|
| 正确性 | 40% | 代码能否运行，是否满足需求 |
| 代码风格 | 20% | 命名规范、注释、格式 |
| 完成度 | 30% | 所有需求是否实现 |
| 创新性 | 10% | 是否有优化、独特思路 |

最终分数计算：
- 仅有 AI 评分时：`最终分数 = AI 总分`
- 教师评分后：`最终分数 = AI 总分 x 0.6 + 教师评分 x 0.4`

## 部署

详细的宝塔面板部署教程请查看 [DEPLOY.md](./DEPLOY.md)

## 许可证

MIT
