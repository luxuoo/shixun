"""AI 服务 - 调用大模型 API 提供编程教学辅助

支持多服务商（MiMo / DeepSeek），二者均为 OpenAI 兼容接口，
通过 settings.AI_PROVIDER 或运行时切换决定当前使用哪一家。
"""
import asyncio
import json
import re
from typing import Optional

from openai import AsyncOpenAI
import openai

from app.core.config import settings
from app.services import app_settings


# 各服务商的能力差异
PROVIDER_CAPS = {
    "mimo": {"json_mode": False},
    # DeepSeek 新一代模型（deepseek-flash / deepseek-v4-pro）默认开启思考模式
    # （thinking=enabled, effort=high），评分/问答类任务不需要思维链，
    # 显式关闭以保持旧版 deepseek-chat 的低延迟低成本行为
    "deepseek": {"json_mode": True, "disable_thinking": True},
}


class AiServiceError(Exception):
    """AI 服务异常，携带可直接返回给前端的提示"""

    def __init__(self, detail: str, status_code: int = 502):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class AiService:
    def __init__(self):
        self._clients: dict = {}
        self._provider_override: Optional[str] = None
        self._fallback_warned = False

    # ---------------- 服务商管理 ----------------

    @property
    def provider(self) -> str:
        """当前生效的服务商名称

        若首选服务商没配 API Key，而另一家配置了，则自动回退，
        避免改了 AI_PROVIDER 却忘了填密钥导致整个 AI 功能不可用。
        """
        requested = self._provider_override or app_settings.default_provider()
        if app_settings.provider_config(requested)["api_key"]:
            return requested
        for name in ("deepseek", "mimo"):
            if name != requested and app_settings.provider_config(name)["api_key"]:
                if not self._fallback_warned:
                    print(f"[AI] {requested} 未配置 API Key，已自动回退到 {name}")
                    self._fallback_warned = True
                return name
        return requested

    @property
    def model(self) -> str:
        return app_settings.provider_config(self.provider)["model"]

    def set_provider(self, name: str) -> dict:
        """运行时切换服务商（重启后回到数据库/.env 里配置的默认值）"""
        name = (name or "").strip().lower()
        if name not in PROVIDER_CAPS:
            raise AiServiceError(f"不支持的 AI 服务商：{name}", status_code=400)
        conf = app_settings.provider_config(name)
        if not conf["api_key"]:
            label = conf["label"]
            raise AiServiceError(
                f"{label} 未配置 API Key，请先在管理后台「AI 服务配置」里填写",
                status_code=400,
            )
        self._provider_override = name
        return self.describe()

    def describe(self) -> dict:
        """返回当前服务商信息（不含密钥）"""
        conf = app_settings.provider_config(self.provider)
        return {
            "provider": conf["name"],
            "label": conf["label"],
            "model": conf["model"],
            "api_url": conf["api_url"],
            "configured": bool(conf["api_key"]),
            "providers": app_settings.available_providers(),
        }

    @property
    def client(self) -> AsyncOpenAI:
        """按 (api_url, api_key) 复用客户端，避免重复建连"""
        conf = app_settings.provider_config(self.provider)
        if not conf["api_key"]:
            raise AiServiceError(
                f"{conf['label']} 未配置 API Key，请联系管理员在「AI 服务配置」页面设置",
                status_code=503,
            )
        cache_key = (conf["api_url"], conf["api_key"])
        client = self._clients.get(cache_key)
        if client is None:
            client = AsyncOpenAI(
                api_key=conf["api_key"],
                base_url=conf["api_url"],
                timeout=settings.AI_TIMEOUT,
                max_retries=0,  # 重试逻辑自己控制，便于记录日志
            )
            self._clients[cache_key] = client
        return client

    # ---------------- 核心调用 ----------------

    async def _chat(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        force_json: bool = False,
    ) -> dict:
        """统一的 chat 调用：带重试、JSON 模式与推理模型兼容"""
        provider = self.provider
        kwargs = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if force_json and PROVIDER_CAPS.get(provider, {}).get("json_mode"):
            kwargs["response_format"] = {"type": "json_object"}
        # DeepSeek 官方文档：思考模式需通过 extra_body 传入 thinking 参数关闭；
        # MiMo 不识别该参数，仅对 deepseek 附加
        if PROVIDER_CAPS.get(provider, {}).get("disable_thinking"):
            kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

        response = await self._request_with_retry(kwargs)

        msg = response.choices[0].message
        content = (msg.content or "").strip()
        tokens_used = response.usage.total_tokens if getattr(response, "usage", None) else 0

        # 官方文档警告：JSON Output 模式下输出无法识别为 JSON 时，
        # 非法内容会被替换成空格（content 可能为空但 finish_reason=stop），建议重试
        if not content and force_json:
            response = await self._request_with_retry(kwargs)
            msg = response.choices[0].message
            content = (msg.content or "").strip()
            tokens_used += response.usage.total_tokens if getattr(response, "usage", None) else 0

        # 推理模型（mimo-v2.5-pro / 手动开启思考的 DeepSeek）会先输出 reasoning_content，
        # 若最终 content 为空则退回使用思考内容，避免前端拿到空白回复
        if not content:
            content = (self._extract_reasoning(msg) or "").strip()

        if not content:
            content = "AI 暂时没有给出回复，可能是请求复杂度过高，请稍后重试或简化问题。"

        return {"content": content, "tokens_used": tokens_used, "provider": provider}

    async def _request_with_retry(self, kwargs: dict):
        """对限流、超时、5xx 做指数退避重试"""
        retries = max(0, settings.AI_MAX_RETRIES)
        last_exc: Optional[Exception] = None

        for attempt in range(retries + 1):
            try:
                return await self.client.chat.completions.create(**kwargs)
            except (
                openai.RateLimitError,
                openai.APITimeoutError,
                openai.APIConnectionError,
                openai.InternalServerError,
            ) as e:
                last_exc = e
                if attempt >= retries:
                    break
                await asyncio.sleep(min(1.5 * (2 ** attempt), 8))
            except openai.APIStatusError as e:
                # 429 / 5xx 可重试，其余（401/400）直接抛出
                status = getattr(e, "status_code", 0)
                last_exc = e
                if status not in (429, 500, 502, 503, 504) or attempt >= retries:
                    break
                await asyncio.sleep(min(1.5 * (2 ** attempt), 8))

        raise last_exc  # type: ignore[misc]

    @staticmethod
    def _extract_reasoning(msg) -> Optional[str]:
        """兼容不同 SDK 版本获取 reasoning_content"""
        reasoning = getattr(msg, "reasoning_content", None)
        if not reasoning and hasattr(msg, "model_extra"):
            reasoning = (msg.model_extra or {}).get("reasoning_content")
        if not reasoning and hasattr(msg, "to_dict"):
            reasoning = (msg.to_dict() or {}).get("reasoning_content")
        return reasoning

    # ---------------- 业务能力 ----------------

    async def get_hint(
        self,
        task_title: str,
        step_title: str,
        step_requirements: str,
        hint_count: int,
        student_code: Optional[str] = None,
        question: Optional[str] = None,
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

        system_prompt = f"""你是一个编程教学助手，正在引导学生完成教学任务。

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
            temperature=0.7,
        )

        return {
            "hint_level": level,
            "content": result["content"],
            "tokens_used": result["tokens_used"],
        }

    async def analyze_code(
        self,
        code: str,
        step_requirements: str,
        task_title: str,
        step_title: str,
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
            temperature=0.3,
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
            "tokens_used": result["tokens_used"],
        }

    async def score_submission(
        self,
        code: str,
        step_requirements: str,
        task_title: str,
        step_title: str,
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
            temperature=0.2,
            force_json=True,
        )

        content = result["content"]
        tokens_used = result["tokens_used"]

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
                    "tokens_used": tokens_used,
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
            "tokens_used": tokens_used,
        }

    async def decompose_task(
        self,
        title: str,
        description: str,
        category: str = "",
        difficulty: int = 3,
        detail_level: str = "normal",
        steps_count: int = 0,
    ) -> dict:
        """AI 自动分解教学任务为多个步骤"""

        detail_instructions = {
            "brief": "每个步骤的要求和描述要简洁明了，每条不超过50字，重点突出核心目标。",
            "normal": "每个步骤的描述适中，要求具体明确，包含必要的技术细节。",
            "detailed": "每个步骤要非常详细，描述要包含具体的技术方案、参考代码思路、常见问题提示，要求要列出每一条检查点。",
        }
        detail_hint = detail_instructions.get(detail_level, detail_instructions["normal"])

        if steps_count > 0:
            steps_hint = f"\n请将任务分解为恰好 {steps_count} 个步骤。"
        else:
            steps_hint = "\n根据任务复杂度自动决定步骤数量（一般4-10步）。"

        system_prompt = f"""你是一个编程教学课程设计专家。根据用户给出的教学任务描述，自动将其分解为若干个循序渐进的步骤。

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

        user_prompt = f"""请分解以下教学任务：

任务名称：{title}
任务描述：{description}
{f"任务分类：{category}" if category else ""}
{f"参考难度：{difficulty}星" if difficulty else ""}

请按照 JSON 格式输出分解结果。"""

        result = await self._chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=4000,
            temperature=0.5,
            force_json=True,
        )

        content = result["content"]
        tokens_used = result["tokens_used"]

        task_data = self._extract_json(content)

        if task_data and "steps" in task_data:
            return {"success": True, "data": task_data, "tokens_used": tokens_used}

        return {
            "success": False,
            "error": "AI 分解失败，请重试或手动创建任务",
            "raw_content": content[:500],
            "tokens_used": tokens_used,
        }

    async def generate_eval_template(
        self,
        course_name: str,
        course_description: str,
        category: str = "",
        student_count: int = 0,
        task_count: int = 0,
    ) -> dict:
        """AI 生成评价方案模板"""
        from app.prompts.evaluation import GENERATE_TEMPLATE_SYSTEM, GENERATE_TEMPLATE_USER

        user_prompt = GENERATE_TEMPLATE_USER.format(
            course_name=course_name,
            course_description=course_description,
            category=category or "通用",
            student_count=student_count,
            task_count=task_count,
        )

        result = await self._chat(
            system_prompt=GENERATE_TEMPLATE_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=4000,
            temperature=0.5,
            force_json=True,
        )

        data = self._extract_json(result["content"])
        if data and "phases" in data:
            return {"success": True, "data": data, "tokens_used": result["tokens_used"]}
        return {
            "success": False,
            "error": "AI 生成失败，请重试",
            "raw_content": result["content"][:500],
            "tokens_used": result["tokens_used"],
        }

    async def suggest_indicators(
        self,
        phase_name: str,
        phase_weight: float,
        existing_indicators: str = "",
        category: str = "",
        other_phases: str = "",
    ) -> dict:
        """AI 推荐评价指标"""
        from app.prompts.evaluation import SUGGEST_INDICATORS_SYSTEM, SUGGEST_INDICATORS_USER

        user_prompt = SUGGEST_INDICATORS_USER.format(
            phase_name=phase_name,
            phase_weight=phase_weight,
            existing_indicators=existing_indicators or "无",
            category=category or "通用",
            other_phases=other_phases or "无",
        )

        result = await self._chat(
            system_prompt=SUGGEST_INDICATORS_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=3000,
            temperature=0.5,
            force_json=True,
        )

        data = self._extract_json(result["content"])
        if data and "indicators" in data:
            return {"success": True, "data": data["indicators"], "tokens_used": result["tokens_used"]}
        return {
            "success": False,
            "error": "AI 推荐失败，请重试",
            "raw_content": result["content"][:500],
            "tokens_used": result["tokens_used"],
        }

    async def diagnose_student(
        self,
        student_name: str,
        class_name: str,
        template_name: str,
        total_score: float,
        phase_details: str,
        dim_details: str,
        trend_data: str,
    ) -> dict:
        """AI 学生个体诊断"""
        from app.prompts.evaluation import DIAGNOSE_STUDENT_SYSTEM, DIAGNOSE_STUDENT_USER

        user_prompt = DIAGNOSE_STUDENT_USER.format(
            student_name=student_name,
            class_name=class_name,
            template_name=template_name,
            total_score=total_score,
            phase_details=phase_details,
            dim_details=dim_details,
            trend_data=trend_data or "暂无历史数据",
        )

        result = await self._chat(
            system_prompt=DIAGNOSE_STUDENT_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=3000,
            temperature=0.6,
        )

        return {"report": result["content"], "tokens_used": result["tokens_used"]}

    async def class_insight(
        self,
        class_name: str,
        template_name: str,
        student_count: int,
        avg_score: float,
        pass_rate: float,
        excellent_rate: float,
        score_distribution: str,
        dim_averages: str,
        top_students: str,
    ) -> dict:
        """AI 班级学情洞察"""
        from app.prompts.evaluation import CLASS_INSIGHT_SYSTEM, CLASS_INSIGHT_USER

        user_prompt = CLASS_INSIGHT_USER.format(
            class_name=class_name,
            template_name=template_name,
            student_count=student_count,
            avg_score=avg_score,
            pass_rate=pass_rate,
            excellent_rate=excellent_rate,
            score_distribution=score_distribution,
            dim_averages=dim_averages,
            top_students=top_students,
        )

        result = await self._chat(
            system_prompt=CLASS_INSIGHT_SYSTEM,
            user_prompt=user_prompt,
            max_tokens=4000,
            temperature=0.6,
        )

        return {"report": result["content"], "tokens_used": result["tokens_used"]}

    async def health_check(self, provider: Optional[str] = None, timeout: float = 20.0) -> dict:
        """连通性自检：返回耗时与模型回复片段"""
        import time

        original = self._provider_override
        started = time.perf_counter()
        try:
            if provider:
                self.set_provider(provider)
            resp = await self._chat(
                system_prompt="你是一个测试助手，请只回复一句简短的中文问候。",
                user_prompt="请用中文回复：你好",
                max_tokens=200,
                temperature=0.3,
            )
            elapsed = round((time.perf_counter() - started) * 1000)
            return {
                "success": True,
                "provider": self.provider,
                "model": self.model,
                "latency_ms": elapsed,
                "reply": resp["content"][:120],
                "tokens_used": resp["tokens_used"],
            }
        except Exception as e:
            detail, _ = ai_error_detail(e)
            return {
                "success": False,
                "provider": self.provider,
                "model": self.model,
                "latency_ms": round((time.perf_counter() - started) * 1000),
                "error": detail,
            }
        finally:
            if provider:
                self._provider_override = original

    def _extract_json(self, text: str) -> Optional[dict]:
        """从 AI 文本中提取 JSON 对象"""
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        return None


def ai_error_detail(exc: Exception) -> tuple:
    """把 AI 调用异常翻译成 (HTTP 状态码, 用户可读提示)

    401/403 认证问题、余额不足、限流、超时分别给出针对性提示，
    避免前端只看到一坨 SDK 原始报错。
    """
    if isinstance(exc, AiServiceError):
        return exc.detail, exc.status_code

    raw = str(exc)
    text = raw.lower()

    if isinstance(exc, openai.AuthenticationError) or "401" in text or "invalid api key" in text:
        return "AI 服务认证失败，请管理员检查 API Key 是否正确或已过期", 502
    if isinstance(exc, openai.PermissionDeniedError) or "403" in text:
        return "AI 服务拒绝访问，请检查 API Key 权限或账户状态", 502
    if isinstance(exc, openai.RateLimitError) or "429" in text:
        return "AI 服务请求过于频繁或额度已用尽，请稍后重试", 429
    if "insufficient" in text or "balance" in text or "quota" in text:
        return "AI 账户余额不足，请管理员充值后重试", 502
    if isinstance(exc, openai.APITimeoutError) or "timeout" in text or "timed out" in text:
        return "AI 服务响应超时，请稍后重试或简化问题", 504
    if isinstance(exc, openai.APIConnectionError):
        return "无法连接 AI 服务，请检查网络或 API 地址配置", 502
    if isinstance(exc, openai.BadRequestError) or "400" in text:
        return f"AI 请求参数有误：{raw[:200]}", 502
    return f"AI 服务错误：{raw[:300]}", 502


# 全局实例
ai_service = AiService()
