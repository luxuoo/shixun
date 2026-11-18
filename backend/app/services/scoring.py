"""成绩计算唯一入口（业务逻辑从路由层下沉到此）。

系统里只有两级成绩，规则固定且可配置：

1. 提交级成绩 submission.final_score
   = AI 评分 与 教师评分 按配置中 ai:teacher 的比例加权。
   只有一方有分时取该方；两者都无分为 None。出勤/加分属于任务级，不参与提交级。

2. 任务级成绩 score.final_score
   = AI×ai% + 教师×teacher% + 出勤×attendance% + 加分(bonus)。
   - 三项权重合计应为 100（配置页强制校验）。
   - 教师未评分时，教师权重并入 AI（避免未复核的任务被凭空扣分）。
   - 加分是「额外累加项」而非权重项：直接加在加权分之上，总分封顶 100。
   - 出勤分入库时已按百分制封顶 100。

所有路由（admin / ai / submissions）一律调用本模块，禁止再写死比例或各自实现。
"""
from typing import Optional

# 唯一默认权重（合计 100）。auth 的默认设置与各处兜底都引用它，避免多套默认值。
DEFAULT_GRADE_WEIGHTS = {"ai": 50, "teacher": 30, "attendance": 20}
WEIGHT_KEYS = ("ai", "teacher", "attendance")

LABELS = {"ai": "AI 评分", "teacher": "教师评分", "attendance": "出勤", "bonus": "加分"}


def normalize_weights(raw) -> dict:
    """把任意输入规整为 {ai,teacher,attendance} 的 0..100 整数权重，并归一到合计 100。

    历史配置可能合计不为 100（如旧默认 40/30/20=90），这里按比例缩放并修正舍入余数，
    保证「权重%」与真实计算一致，避免老数据导致满分只有 90 的困惑。
    """
    raw = raw if isinstance(raw, dict) else {}
    w = {
        k: max(0, min(100, int(raw.get(k, DEFAULT_GRADE_WEIGHTS[k]))))
        for k in WEIGHT_KEYS
    }
    total = sum(w.values())
    if total <= 0:
        return dict(DEFAULT_GRADE_WEIGHTS)
    if total != 100:
        scaled = {k: int(round(v * 100 / total)) for k, v in w.items()}
        diff = 100 - sum(scaled.values())
        if diff:
            biggest = max(scaled, key=lambda k: scaled[k])
            scaled[biggest] = max(0, min(100, scaled[biggest] + diff))
        w = scaled
    return w


def current_weights() -> dict:
    """读取当前生效权重（系统设置），缺失/损坏时回落到唯一默认值"""
    from app.api.auth import _system_settings

    return normalize_weights(_system_settings.get("grade_weights", DEFAULT_GRADE_WEIGHTS))


def submission_final(ai: Optional[float], teacher: Optional[float], w: dict) -> Optional[float]:
    """提交级：AI 与教师按 ai:teacher 比例加权"""
    if ai is None and teacher is None:
        return None
    if teacher is None:
        return round(min(100.0, ai), 1)
    if ai is None:
        return round(min(100.0, teacher), 1)
    wa, wt = w["ai"], w["teacher"]
    total = wa + wt
    if total <= 0:
        return round(min(100.0, (ai + teacher) / 2), 1)
    return round(min(100.0, ai * wa / total + teacher * wt / total), 1)


def task_final(ai, teacher, attendance, bonus, w: dict, teacher_reviewed: bool) -> float:
    """任务级：三项加权 + 加分累加，封顶 100"""
    ai = ai or 0
    attendance = attendance or 0
    bonus = bonus or 0
    wa, wt, watt = w["ai"], w["teacher"], w["attendance"]
    if teacher_reviewed:
        teacher = teacher or 0
    else:
        wa, wt, teacher = wa + wt, 0, 0
    weighted = ai * wa / 100 + teacher * wt / 100 + attendance * watt / 100
    return round(min(100.0, weighted + bonus), 1)


def task_breakdown(ai, teacher, attendance, bonus, w: dict, teacher_reviewed: bool) -> dict:
    """返回可读的成绩构成，供前端展示「这个分是怎么算出来的」"""
    ai = ai or 0
    attendance = attendance or 0
    bonus = bonus or 0
    wa, wt, watt = w["ai"], w["teacher"], w["attendance"]
    if not teacher_reviewed:
        wa, wt = wa + wt, 0
    components = [
        {"key": "ai", "label": LABELS["ai"], "weight": wa, "raw": round(ai, 1),
         "contribution": round(ai * wa / 100, 1)},
        {"key": "teacher", "label": LABELS["teacher"], "weight": wt,
         "raw": round(teacher, 1) if teacher_reviewed else None,
         "contribution": round((teacher or 0) * wt / 100, 1)},
        {"key": "attendance", "label": LABELS["attendance"], "weight": watt,
         "raw": round(attendance, 1), "contribution": round(attendance * watt / 100, 1)},
    ]
    final = task_final(ai, teacher, attendance, bonus, w, teacher_reviewed)
    return {
        "weights": {k: w[k] for k in WEIGHT_KEYS},
        "teacher_reviewed": teacher_reviewed,
        "components": components,
        "bonus": round(bonus, 1),
        "final": final,
    }