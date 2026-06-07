-- AI 编程辅助教学系统 - 数据库初始化脚本

-- 班级表
CREATE TABLE IF NOT EXISTS classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    teacher_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student',  -- student/teacher/admin
    name VARCHAR(100),
    class_id INTEGER REFERENCES classes(id),
    student_id VARCHAR(20),
    email VARCHAR(100),
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- 任务表
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    difficulty INTEGER DEFAULT 1,
    total_steps INTEGER NOT NULL,
    estimated_hours FLOAT,
    cover_image VARCHAR(255),
    is_active BOOLEAN DEFAULT 1,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 任务步骤表
CREATE TABLE IF NOT EXISTS task_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER REFERENCES tasks(id),
    step_order INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    requirements TEXT,
    reference_code TEXT,
    expected_output TEXT,
    hints_available INTEGER DEFAULT 3,
    UNIQUE(task_id, step_order)
);

-- 提交记录表
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    task_id INTEGER REFERENCES tasks(id),
    step_id INTEGER REFERENCES task_steps(id),
    code TEXT NOT NULL,
    language VARCHAR(20) DEFAULT 'python',
    status VARCHAR(20) DEFAULT 'pending',
    ai_score FLOAT,
    ai_feedback TEXT,
    teacher_score FLOAT,
    teacher_comment TEXT,
    final_score FLOAT,
    file_attachments TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP
);

-- AI 调用记录表
CREATE TABLE IF NOT EXISTS ai_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    task_id INTEGER REFERENCES tasks(id),
    step_id INTEGER REFERENCES task_steps(id),
    request_type VARCHAR(20),
    hint_level INTEGER,
    request_content TEXT,
    response_content TEXT,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 评分表
CREATE TABLE IF NOT EXISTS scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    task_id INTEGER REFERENCES tasks(id),
    ai_total_score FLOAT,
    completion_rate FLOAT,
    teacher_score FLOAT,
    attendance_score FLOAT DEFAULT 0,
    bonus_score FLOAT DEFAULT 0,
    final_score FLOAT,
    ai_hint_count INTEGER,
    total_submissions INTEGER,
    rollcall_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'in_progress',
    completed_at TIMESTAMP,
    reviewed_at TIMESTAMP,
    UNIQUE(user_id, task_id)
);

-- 点名记录表
CREATE TABLE IF NOT EXISTS rollcall_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER REFERENCES users(id),
    class_id INTEGER REFERENCES classes(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 成绩方案表
CREATE TABLE IF NOT EXISTS grade_schemes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    class_id INTEGER REFERENCES classes(id),
    decimal_places INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 计分项目表
CREATE TABLE IF NOT EXISTS grade_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_id INTEGER REFERENCES grade_schemes(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    weight FLOAT NOT NULL,
    max_score FLOAT DEFAULT 100,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 成绩记录表
CREATE TABLE IF NOT EXISTS grade_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER REFERENCES users(id),
    item_id INTEGER REFERENCES grade_items(id),
    score FLOAT,
    remark VARCHAR(200),
    status VARCHAR(20) DEFAULT 'normal',
    recorded_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, item_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_class_id ON users(class_id);
CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_task_id ON submissions(task_id);
CREATE INDEX IF NOT EXISTS idx_ai_logs_user_id ON ai_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_scores_user_id ON scores(user_id);
CREATE INDEX IF NOT EXISTS idx_scores_task_id ON scores(task_id);

-- 插入默认管理员账号 (密码: admin123)
INSERT OR IGNORE INTO users (username, password_hash, role, name)
VALUES ('admin', '$2b$12$LJ3m4ys3Lz0YBNOURq0Y3OjCfKJmKPOJYqDTPVCKzLOBhZMHfSH6e', 'admin', '系统管理员');

-- 插入示例班级
INSERT OR IGNORE INTO classes (name, description, teacher_id)
VALUES ('2024级计算机1班', '计算机科学与技术专业1班', 1);

-- 插入示例任务
INSERT OR IGNORE INTO tasks (title, description, category, difficulty, total_steps, estimated_hours, created_by)
VALUES (
    'YOLO 智慧交通系统',
    '使用 YOLO 目标检测算法实现智慧交通系统，包括车辆检测、速度估计、超速检测等功能。',
    'YOLO',
    3,
    9,
    20,
    1
);

-- 插入示例步骤
INSERT OR IGNORE INTO task_steps (task_id, step_order, title, description, requirements, expected_output, hints_available)
VALUES
(1, 1, '环境配置', '配置 Python 开发环境，安装必要的依赖库。', '1. 安装 Python 3.8+\n2. 安装 OpenCV\n3. 安装 YOLO 相关库\n4. 验证环境配置', '成功导入所有依赖库，无报错', 3),
(1, 2, '视频读取', '实现视频文件的读取和预处理。', '1. 使用 OpenCV 读取视频\n2. 获取视频基本信息\n3. 实现逐帧读取\n4. 显示视频预览', '能够正常播放视频文件', 3),
(1, 3, 'YOLO 模型加载', '加载预训练的 YOLO 模型。', '1. 下载 YOLO 权重文件\n2. 加载模型配置\n3. 初始化检测器\n4. 测试模型加载', '模型成功加载，能够进行简单检测', 3),
(1, 4, '目标跟踪', '实现目标跟踪功能。', '1. 检测视频中的车辆\n2. 为每个检测目标分配 ID\n3. 跟踪目标运动轨迹\n4. 绘制跟踪框', '能够跟踪视频中的车辆', 3),
(1, 5, '车速计算', '计算跟踪车辆的速度。', '1. 获取目标位置信息\n2. 计算帧间位移\n3. 转换为实际速度\n4. 显示速度信息', '能够显示车辆速度', 3),
(1, 6, '超速检测', '检测超速车辆。', '1. 设置速度阈值\n2. 判断是否超速\n3. 标记超速车辆\n4. 记录超速信息', '能够检测并标记超速车辆', 3),
(1, 7, '碰撞检测', '检测潜在的碰撞风险。', '1. 计算车辆间距\n2. 判断碰撞风险\n3. 发出预警\n4. 记录碰撞事件', '能够检测碰撞风险', 3),
(1, 8, 'UI 绘制', '绘制系统界面。', '1. 显示视频画面\n2. 绘制检测框\n3. 显示统计信息\n4. 添加控制按钮', '显示完整的系统界面', 3),
(1, 9, '最终运行', '整合所有功能，完成系统。', '1. 整合所有模块\n2. 优化性能\n3. 测试完整功能\n4. 编写文档', '系统完整运行，功能正常', 3);
