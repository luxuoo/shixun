"""
初始化数据脚本 - 创建测试账号和实训任务
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, async_session, init_db, Base
from app.core.security import get_password_hash
from app.models import User, Class, Task, TaskStep


async def create_init_data():
    """创建初始数据"""
    # 初始化数据库表
    await init_db()

    async with async_session() as session:
        # 检查是否已有数据
        from sqlalchemy import select, func
        result = await session.execute(select(func.count(User.id)))
        count = result.scalar()

        if count > 0:
            print("数据库已有数据，跳过初始化")
            return

        print("开始创建初始数据...")

        # 1. 创建班级
        class1 = Class(name="2024级计算机1班", description="计算机科学与技术专业1班")
        class2 = Class(name="2024级计算机2班", description="计算机科学与技术专业2班")
        class3 = Class(name="2024级人工智能班", description="人工智能专业班级")
        session.add_all([class1, class2, class3])
        await session.flush()
        print("✓ 班级创建完成")

        # 2. 创建管理员账号
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin123"),
            role="admin",
            name="系统管理员",
            email="admin@example.com",
            is_active=True
        )
        session.add(admin)
        await session.flush()
        print("✓ 管理员账号创建完成 (admin/admin123)")

        # 3. 创建教师账号
        teacher1 = User(
            username="teacher1",
            password_hash=get_password_hash("teacher123"),
            role="teacher",
            name="张老师",
            email="teacher1@example.com",
            is_active=True
        )
        teacher2 = User(
            username="teacher2",
            password_hash=get_password_hash("teacher123"),
            role="teacher",
            name="李老师",
            email="teacher2@example.com",
            is_active=True
        )
        session.add_all([teacher1, teacher2])
        await session.flush()

        # 更新班级的教师
        class1.teacher_id = teacher1.id
        class2.teacher_id = teacher1.id
        class3.teacher_id = teacher2.id
        print("✓ 教师账号创建完成 (teacher1/teacher123, teacher2/teacher123)")

        # 4. 创建学生账号
        students = [
            User(
                username="student1",
                password_hash=get_password_hash("student123"),
                role="student",
                name="王小明",
                class_id=class1.id,
                student_id="2024001",
                email="student1@example.com",
                is_active=True
            ),
            User(
                username="student2",
                password_hash=get_password_hash("student123"),
                role="student",
                name="李小红",
                class_id=class1.id,
                student_id="2024002",
                email="student2@example.com",
                is_active=True
            ),
            User(
                username="student3",
                password_hash=get_password_hash("student123"),
                role="student",
                name="张小华",
                class_id=class2.id,
                student_id="2024003",
                email="student3@example.com",
                is_active=True
            ),
            User(
                username="test",
                password_hash=get_password_hash("test123"),
                role="student",
                name="测试学生",
                class_id=class3.id,
                student_id="2024100",
                email="test@example.com",
                is_active=True
            ),
        ]
        session.add_all(students)
        await session.flush()
        print("✓ 学生账号创建完成 (student1/student123, test/test123)")

        # 5. 创建实训任务 - YOLO 智慧交通系统
        task1 = Task(
            title="YOLO 智慧交通系统",
            description="使用 YOLO 目标检测算法实现智慧交通系统，包括视频读取、目标检测、目标跟踪、车速计算、超速检测、碰撞检测等功能。通过本实训，你将掌握计算机视觉和深度学习的实际应用。",
            category="YOLO",
            difficulty=3,
            total_steps=9,
            estimated_hours=20,
            is_active=True,
            created_by=teacher1.id
        )
        session.add(task1)
        await session.flush()

        # 创建任务步骤
        steps_data = [
            {
                "step_order": 1,
                "title": "环境配置",
                "description": "配置 Python 开发环境，安装必要的依赖库。这是完成本实训的基础步骤。",
                "requirements": """1. 安装 Python 3.8 或更高版本
2. 安装 OpenCV 库：pip install opencv-python
3. 安装 YOLO 库：pip install ultralytics
4. 安装其他依赖：pip install numpy torch
5. 验证所有库都能正常导入""",
                "expected_output": "成功导入 cv2、ultralytics、numpy、torch 等库，无报错信息",
                "hints_available": 3
            },
            {
                "step_order": 2,
                "title": "视频读取",
                "description": "实现视频文件的读取和基本处理功能。",
                "requirements": """1. 使用 OpenCV 的 VideoCapture 类读取视频文件
2. 获取视频的基本信息（帧率、分辨率、总帧数）
3. 实现逐帧读取功能
4. 添加视频文件存在性检查
5. 显示视频预览窗口""",
                "expected_output": "能够正常打开并播放视频文件，显示视频基本信息",
                "hints_available": 3
            },
            {
                "step_order": 3,
                "title": "YOLO 模型加载",
                "description": "加载预训练的 YOLO 模型，为后续目标检测做准备。",
                "requirements": """1. 使用 ultralytics 库加载 YOLO 模型
2. 选择合适的模型版本（如 yolo11n.pt）
3. 检测可用的计算设备（CPU/GPU）
4. 对模型进行预热（warmup）
5. 测试模型能否正常进行推理""",
                "expected_output": "模型成功加载，能够对单张图片进行目标检测",
                "hints_available": 3
            },
            {
                "step_order": 4,
                "title": "目标跟踪",
                "description": "在视频中实现目标检测和跟踪功能。",
                "requirements": """1. 使用 YOLO 的 track 方法进行目标跟踪
2. 配置跟踪器（如 ByteTrack）
3. 只检测车辆类别（car, truck, bus）
4. 为每个跟踪目标分配唯一 ID
5. 在画面上绘制跟踪框和 ID""",
                "expected_output": "能够在视频中检测并跟踪车辆，显示跟踪框和 ID",
                "hints_available": 3
            },
            {
                "step_order": 5,
                "title": "车速计算",
                "description": "计算跟踪车辆的行驶速度。",
                "requirements": """1. 记录每帧中车辆的位置信息
2. 计算相邻帧之间的像素距离
3. 实现像素到实际距离的转换（考虑透视变换）
4. 根据帧率计算速度（km/h）
5. 对速度进行平滑处理""",
                "expected_output": "能够显示每辆车的速度（km/h）",
                "hints_available": 3
            },
            {
                "step_order": 6,
                "title": "超速检测",
                "description": "检测超过限速的车辆并发出警告。",
                "requirements": """1. 设置速度阈值（如 80 km/h）
2. 判断车辆是否超速
3. 实现超速持续时间检测（避免误报）
4. 对超速车辆进行标记（红色框）
5. 显示超速警告信息""",
                "expected_output": "能够检测超速车辆并显示警告",
                "hints_available": 3
            },
            {
                "step_order": 7,
                "title": "碰撞检测",
                "description": "检测车辆之间的潜在碰撞风险。",
                "requirements": """1. 计算车辆之间的距离
2. 根据车辆大小动态调整安全距离
3. 实现碰撞风险持续时间检测
4. 对高风险车辆进行标记
5. 显示碰撞警告信息""",
                "expected_output": "能够检测碰撞风险并显示警告",
                "hints_available": 3
            },
            {
                "step_order": 8,
                "title": "UI 绘制",
                "description": "绘制系统界面，显示各种信息。",
                "requirements": """1. 绘制检测框和跟踪信息
2. 显示车辆速度
3. 显示警告信息（超速、碰撞等）
4. 添加统计面板（总车流量等）
5. 优化界面显示效果""",
                "expected_output": "显示完整的系统界面，包含所有检测信息",
                "hints_available": 3
            },
            {
                "step_order": 9,
                "title": "最终运行",
                "description": "整合所有功能，完成系统开发。",
                "requirements": """1. 整合所有功能模块
2. 优化系统性能
3. 添加错误处理机制
4. 编写使用文档
5. 进行完整测试""",
                "expected_output": "系统完整运行，能够实时处理视频并显示检测结果",
                "hints_available": 3
            }
        ]

        for step_data in steps_data:
            step = TaskStep(task_id=task1.id, **step_data)
            session.add(step)

        await session.flush()
        print("✓ YOLO 智慧交通系统任务创建完成 (9个步骤)")

        # 6. 创建第二个实训任务 - Python 数据分析
        task2 = Task(
            title="Python 数据分析实战",
            description="使用 Python 进行数据分析，包括数据清洗、数据可视化、统计分析等。适合初学者入门数据分析。",
            category="Python",
            difficulty=2,
            total_steps=6,
            estimated_hours=12,
            is_active=True,
            created_by=teacher1.id
        )
        session.add(task2)
        await session.flush()

        steps_data2 = [
            {
                "step_order": 1,
                "title": "环境搭建",
                "description": "安装数据分析所需的 Python 库。",
                "requirements": "1. 安装 pandas: pip install pandas\n2. 安装 numpy: pip install numpy\n3. 安装 matplotlib: pip install matplotlib\n4. 安装 seaborn: pip install seaborn\n5. 验证安装",
                "expected_output": "成功导入所有数据分析库",
                "hints_available": 3
            },
            {
                "step_order": 2,
                "title": "数据读取",
                "description": "学习读取各种格式的数据文件。",
                "requirements": "1. 读取 CSV 文件\n2. 读取 Excel 文件\n3. 查看数据基本信息\n4. 查看数据统计描述\n5. 处理缺失值",
                "expected_output": "能够读取并查看数据文件内容",
                "hints_available": 3
            },
            {
                "step_order": 3,
                "title": "数据清洗",
                "description": "对数据进行清洗和预处理。",
                "requirements": "1. 处理缺失值（删除或填充）\n2. 处理重复值\n3. 数据类型转换\n4. 异常值处理\n5. 数据标准化",
                "expected_output": "数据清洗完成，无缺失值和异常值",
                "hints_available": 3
            },
            {
                "step_order": 4,
                "title": "数据可视化",
                "description": "使用图表展示数据分析结果。",
                "requirements": "1. 绘制折线图\n2. 绘制柱状图\n3. 绘制散点图\n4. 绘制饼图\n5. 添加图表标题和标签",
                "expected_output": "能够绘制各种类型的图表",
                "hints_available": 3
            },
            {
                "step_order": 5,
                "title": "统计分析",
                "description": "进行基本的统计分析。",
                "requirements": "1. 计算描述性统计量\n2. 相关性分析\n3. 分组统计\n4. 数据透视表\n5. 结果解读",
                "expected_output": "能够进行基本的统计分析并解读结果",
                "hints_available": 3
            },
            {
                "step_order": 6,
                "title": "项目实战",
                "description": "完成一个完整的数据分析项目。",
                "requirements": "1. 选择分析主题\n2. 数据收集和清洗\n3. 探索性分析\n4. 可视化展示\n5. 撰写分析报告",
                "expected_output": "完成完整的数据分析项目报告",
                "hints_available": 3
            }
        ]

        for step_data in steps_data2:
            step = TaskStep(task_id=task2.id, **step_data)
            session.add(step)

        await session.flush()
        print("✓ Python 数据分析实战任务创建完成 (6个步骤)")

        # 7. 创建第三个实训任务 - Web 前端开发
        task3 = Task(
            title="Web 前端开发入门",
            description="学习 HTML、CSS、JavaScript 基础，完成一个简单的个人网页项目。",
            category="Web",
            difficulty=1,
            total_steps=5,
            estimated_hours=8,
            is_active=True,
            created_by=teacher2.id
        )
        session.add(task3)
        await session.flush()

        steps_data3 = [
            {
                "step_order": 1,
                "title": "HTML 基础",
                "description": "学习 HTML 基本标签和页面结构。",
                "requirements": "1. 创建 HTML 文件\n2. 使用常用标签（h1-p-div）\3. 添加图片和链接\n4. 创建表格\n5. 设计页面结构",
                "expected_output": "能够创建基本的 HTML 页面",
                "hints_available": 3
            },
            {
                "step_order": 2,
                "title": "CSS 样式",
                "description": "使用 CSS 美化页面。",
                "requirements": "1. 内联样式和外部样式表\n2. 选择器使用\n3. 盒模型\n4. 布局（flexbox）\n5. 响应式设计",
                "expected_output": "能够使用 CSS 美化页面",
                "hints_available": 3
            },
            {
                "step_order": 3,
                "title": "JavaScript 基础",
                "description": "学习 JavaScript 基本语法。",
                "requirements": "1. 变量和数据类型\n2. 函数定义\n3. 条件和循环\n4. DOM 操作\n5. 事件处理",
                "expected_output": "能够使用 JavaScript 实现交互功能",
                "hints_available": 3
            },
            {
                "step_order": 4,
                "title": "项目实战",
                "description": "完成个人主页项目。",
                "requirements": "1. 设计页面结构\n2. 实现导航栏\n3. 添加内容区域\n4. 实现响应式布局\n5. 添加动画效果",
                "expected_output": "完成个人主页项目",
                "hints_available": 3
            },
            {
                "step_order": 5,
                "title": "部署上线",
                "description": "将网站部署到服务器。",
                "requirements": "1. 代码优化\n2. 性能优化\n3. 选择托管平台\n4. 部署网站\n5. 测试访问",
                "expected_output": "网站成功部署并可访问",
                "hints_available": 3
            }
        ]

        for step_data in steps_data3:
            step = TaskStep(task_id=task3.id, **step_data)
            session.add(step)

        await session.flush()
        print("✓ Web 前端开发入门任务创建完成 (5个步骤)")

        # 提交事务
        await session.commit()
        print("\n" + "="*50)
        print("初始数据创建完成！")
        print("="*50)
        print("\n账号信息：")
        print("-"*50)
        print(f"{'角色':<10} {'用户名':<15} {'密码':<15} {'姓名':<10}")
        print("-"*50)
        print(f"{'管理员':<10} {'admin':<15} {'admin123':<15} {'系统管理员':<10}")
        print(f"{'教师':<10} {'teacher1':<15} {'teacher123':<15} {'张老师':<10}")
        print(f"{'教师':<10} {'teacher2':<15} {'teacher123':<15} {'李老师':<10}")
        print(f"{'学生':<10} {'student1':<15} {'student123':<15} {'王小明':<10}")
        print(f"{'学生':<10} {'student2':<15} {'student123':<15} {'李小红':<10}")
        print(f"{'学生':<10} {'student3':<15} {'student123':<15} {'张小华':<10}")
        print(f"{'学生':<10} {'test':<15} {'test123':<15} {'测试学生':<10}")
        print("-"*50)
        print("\n实训任务：")
        print("-"*50)
        print("1. YOLO 智慧交通系统 (9步骤, 难度3星)")
        print("2. Python 数据分析实战 (6步骤, 难度2星)")
        print("3. Web 前端开发入门 (5步骤, 难度1星)")
        print("-"*50)


if __name__ == "__main__":
    asyncio.run(create_init_data())
