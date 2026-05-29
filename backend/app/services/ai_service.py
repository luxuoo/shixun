"""AI 服务 - 调用 MiMo API 提供编程教学辅助"""
import json
import re
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import settings


class AiService:
    def __init__(self):
        self._client = None
        self.model = settings.MIMO_MODEL

    @property
    def client(self):
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.MIMO_API_KEY,
                base_url=settings.MIMO_API_URL,
                timeout=60.0
            )
        return self._client

    async def _chat(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        force_json: bool = False
    ) -> dict:
        """统一的 chat 调用，处理推理模型的空响应问题"""
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        response = await self.client.chat.completions.create(**kwargs)

        content = response.choices[0].message.content or ""
        tokens_used = response.usage.total_tokens if response.usage else 0

        # 推理模型可能将思考过程作为 reasoning_tokens 消耗，
        # 但 content 为空时尝试从 reasoning_content 提取
        if not content.strip():
            msg = response.choices[0].message
            reasoning = getattr(msg, "reasoning_content", None) or ""
            if reasoning:
                content = reasoning

        if not content.strip():
            content = "AI 暂时没有给出回复，可能是请求复杂度过高，请稍后重试或简化问题。"

        return {"content": content.strip(), "tokens_used": tokens_used}

    async def get_hint(
        self,
        task_title: str,
        step_title: str,
        step_requirements: str,
        hint_count: int,
        student_code: Optional[str] = None,
        question: Optional[str] = None
    ) -> dict:
        """获取分级提示

        hint_count: 当前是第几次请求（从 1 开始）
        - 1: 一级提示（思路引导，无代码）
        - 2: 二级提示（API 引导，可提到函数名）
        - 3+: 三级提示（关键代码片段）
        """
        if hint_count <= 1:
            level = 1
            level_desc = "一级提示（思路引导）"
            level_rule = """请遵守以下规则：
- 只给出解题思路、方法论、所需的核心概念
- 引导学生思考问题的本质
- 提出 1-2 个引导性问题让学生回答
- 绝对不能包含任何代码、函数名、API 名称
- 不能告诉学生具体用什么库"""
        elif hint_count == 2:
            level = 2
            level_desc = "二级提示（API 引导）"
            level_rule = """请遵守以下规则：
- 可以提到相关的库名、函数名、类名
- 解释每个 API 的作用和关键参数
- 给出使用步骤的文字描述
- 仍然不能给出可运行的完整代码
- 可以用伪代码示意流程"""
        else:
            level = 3
            level_desc = "三级提示（关键代码）"
            level_rule = """请遵守以下规则：
- 可以给出关键代码片段（不超过 15 行）
- 必须用 # TODO: 学生补充 标注需要学生自己写的部分
- 只给最核心的部分，不能给完整解决方案
- 解释每段代码的作用"""

        system_prompt = f"""你是一个编程教学助手，正在引导学生完成实训任务。

## 当前任务上下文
- 任务名称：{task_title}
- 当前步骤：{step_title}
- 步骤要求：{step_requirements}
- 学生请求次数：第 {hint_count} 次（{level_desc}）

## 核心原则
1. 绝对不能直接给出完整项目代码
2. 只针对当前步骤进行引导，不能跳到后续步骤
3. 要鼓励学生思考，而不是直接给答案

## 本次提示规则
{level_rule}

## 输出格式
用中文回复，结构清晰，使用 markdown 格式。"""

        parts = []
        if question:
            parts.append(f"学生的问题：{question}")
        if student_code and student_code.strip():
            parts.append(f"学生当前的代码：\n```python\n{student_code}\n```")
        if not parts:
            parts.append("请给我一些提示，帮我理解这个步骤。")
        user_prompt = "\n\n".join(parts)

        result = await self._chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=3000,
            temperature=0.7
        )

        return {
            "hint_level": level,
            "content": result["content"],
            "tokens_used": result["tokens_used"]
        }

    async def analyze_code(
        self,
        code: str,
        step_requirements: str,
        task_title: str,
        step_title: str
    ) -> dict:
        """分析学生代码"""
        system_prompt = """你是一个代码分析助手，帮助学生改进代码。

请用中文回复，使用 markdown 格式。结构如下：

## 代码优点
（列出 2-3 个优点）

## 存在的问题
（列出主要问题，按重要程度排序）

## 改进建议
（具体可行的改进方法）

## 是否满足要求
（明确说明是否完成步骤要求，哪些方面还不够）

不要直接给出完整修改后的代码，只指出问题和方向。"""

        user_prompt = f"""任务：{task_title}
步骤：{step_title}
步骤要求：
{step_requirements}

学生代码：
```python
{code}
```"""

        result = await self._chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=3000,
            temperature=0.3
        )

        # 尝试从分析中提取建议条目
        suggestions = []
        for line in result["content"].split("\n"):
            line = line.strip()
            if re.match(r"^[-*\d]+[.\)、]\s+", line):
                suggestion = re.sub(r"^[-*\d]+[.\)、]\s+", "", line)
                if 10 < len(suggestion) < 200:
                    suggestions.append(suggestion)

        return {
            "analysis": result["content"],
            "suggestions": suggestions[:5],
            "tokens_used": result["tokens_used"]
        }

    async def score_submission(
        self,
        code: str,
        step_requirements: str,
        task_title: str,
        step_title: str
    ) -> dict:
        """对提交的代码进行评分"""
        system_prompt = """你是一个严格但公正的代码评分助手，对学生提交的代码进行评分。

## 评分维度（百分制）
- correctness（正确性 40%）：代码是否能运行、是否满足要求、是否有逻辑错误
- code_style（规范性 20%）：命名、注释、格式、PEP 8
- completion（完成度 30%）：是否完成所有要求、功能完整性
- creativity（创新性 10%）：优化、思路独特、简洁高效

## 评分标准
- 90-100：优秀
- 80-89：良好
- 70-79：中等
- 60-69：及格
- <60：不及格

## 输出要求
必须以严格的 JSON 格式输出，不要任何其它文字，不要 markdown 代码块标记：

{
  "total_score": 数字 0-100,
  "correctness": 数字 0-100,
  "code_style": 数字 0-100,
  "completion": 数字 0-100,
  "creativity": 数字 0-100,
  "feedback": "整体反馈，2-4 句话",
  "suggestions": ["建议1", "建议2", "建议3"]
}

total_score 必须 = correctness*0.4 + code_style*0.2 + completion*0.3 + creativity*0.1（取整）"""

        user_prompt = f"""任务：{task_title}
步骤：{step_title}
步骤要求：
{step_requirements}

学生代码：
```python
{code}
```

请对以上代码进行评分，严格按照 JSON 格式输出，不要包含任何额外文字。"""

        result = await self._chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=4000,
            temperature=0.2
        )

        content = result["content"]
        tokens_used = result["tokens_used"]

        # 提取 JSON
        score_data = self._extract_json(content)

        if score_data:
            try:
                correctness = float(score_data.get("correctness", 60))
                code_style = float(score_data.get("code_style", 60))
                completion = float(score_data.get("completion", 60))
                creativity = float(score_data.get("creativity", 60))
                # 重新计算 total，避免 AI 算错
                total = round(
                    correctness * 0.4 + code_style * 0.2 +
                    completion * 0.3 + creativity * 0.1
                )
                return {
                    "total_score": total,
                    "correctness": correctness,
                    "code_style": code_style,
                    "completion": completion,
                    "creativity": creativity,
                    "feedback": score_data.get("feedback", ""),
                    "suggestions": score_data.get("suggestions", []),
                    "tokens_used": tokens_used
                }
            except (ValueError, TypeError):
                pass

        # 解析失败的兜底
        return {
            "total_score": 60,
            "correctness": 60,
            "code_style": 60,
            "completion": 60,
            "creativity": 60,
            "feedback": "AI 评分解析失败。原始回复：" + content[:300],
            "suggestions": ["请重新提交评分", "可能是代码过长或 AI 模型暂时不可用"],
            "tokens_used": tokens_used
        }

    async def decompose_task(
        self,
        title: str,
        description: str,
        category: str = "",
        difficulty: int = 3,
        detail_level: str = "normal",
        steps_count: int = 0
    ) -> dict:
        """AI 自动分解实训任务为多个步骤"""

        # 根据详细度调整提示词
        detail_instructions = {
            "brief": "每个步骤的要求和描述要简洁明了，每条不超过50字，重点突出核心目标。",
            "normal": "每个步骤的描述适中，要求具体明确，包含必要的技术细节。",
            "detailed": "每个步骤要非常详细，描述要包含具体的技术方案、参考代码思路、常见问题提示，要求要列出每一条检查点。"
        }
        detail_hint = detail_instructions.get(detail_level, detail_instructions["normal"])

        steps_hint = ""
        if steps_count > 0:
            steps_hint = f"\n请将任务分解为恰好 {steps_count} 个步骤。"
        else:
            steps_hint = "\n根据任务复杂度自动决定步骤数量（一般4-10步）。"

        system_prompt = f"""你是一个编程教学课程设计专家。根据用户给出的实训任务描述，自动将其分解为若干个循序渐进的步骤。

{detail_hint}{steps_hint}

## 输出要求
必须以严格的 JSON 格式输出，不要任何其它文字，不要 markdown 代码块标记：

{{
  "title": "优化后的任务标题",
  "description": "优化后的任务描述（更详细）",
  "category": "分类（Python/Web/YOLO/数据分析/机器学习 中选一个）",
  "difficulty": 数字1-5,
  "estimated_hours": 预计完成时长（小时）,
  "steps": [
    {{
      "step_order": 1,
      "title": "步骤标题",
      "description": "步骤详细描述",
      "requirements": "具体要求（学生需要完成什么）",
      "expected_output": "预期输出描述",
      "hints_available": 3
    }}
  ]
}}

## 规则
1. 每个步骤应该是可独立完成的小任务
2. 步骤之间有逻辑递进关系
3. 难度要合理评估"""

        user_prompt = f"""请分解以下实训任务：

任务名称：{title}
任务描述：{description}
{f"任务分类：{category}" if category else ""}
{f"参考难度：{difficulty}星" if difficulty else ""}

请按照 JSON 格式输出分解结果。"""

        result = await self._chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=4000,
            temperature=0.5
        )

        content = result["content"]
        tokens_used = result["tokens_used"]

        # 提取 JSON
        task_data = self._extract_json(content)

        if task_data and "steps" in task_data:
            return {
                "success": True,
                "data": task_data,
                "tokens_used": tokens_used
            }

        # 解析失败
        return {
            "success": False,
            "error": "AI 分解失败，请重试或手动创建任务",
            "raw_content": content[:500],
            "tokens_used": tokens_used
        }

    def _extract_json(self, text: str) -> Optional[dict]:
        """从 AI 文本中提取 JSON 对象"""
        if not text:
            return None
        # 直接尝试
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # 尝试去除 markdown 代码块
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        # 尝试找第一个 { 到最后一个 }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        return None


# 全局实例
ai_service = AiService()
