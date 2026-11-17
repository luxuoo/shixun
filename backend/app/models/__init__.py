from app.models.user import User, Class
from app.models.task import Task, TaskStep
from app.models.submission import Submission
from app.models.attachment import Attachment
from app.models.ai_log import AiLog, Score, RollcallRecord, LoginRecord
from app.models.app_setting import AppSetting
from app.models.evaluation import (
    EvalTemplate, EvalPhase, EvalIndicator,
    EvalScorerConfig, EvalRecord, EvalSnapshot
)

# 高频查询的复合/单列索引：直接绑进 metadata，成为 Alembic 迁移的一部分，
# 不再靠启动时 CREATE INDEX IF NOT EXISTS 补（旧 _ensure_indexes 已移除）。
from sqlalchemy import Index
from app.core.database import Base

_EXTRA_INDEXES = [
    ("idx_ai_logs_user", "ai_logs", ["user_id"]),
    ("idx_ai_logs_task", "ai_logs", ["task_id"]),
    ("idx_ai_logs_step_lookup", "ai_logs", ["user_id", "task_id", "step_id", "request_type"]),
    ("idx_ai_logs_created", "ai_logs", ["created_at"]),
    ("idx_sub_user", "submissions", ["user_id"]),
    ("idx_sub_task", "submissions", ["task_id"]),
    ("idx_sub_step", "submissions", ["step_id"]),
    ("idx_sub_user_task", "submissions", ["user_id", "task_id"]),
    ("idx_sub_submitted", "submissions", ["submitted_at"]),
    ("idx_scores_user_task", "scores", ["user_id", "task_id"]),
    ("idx_rollcall_class", "rollcall_records", ["class_id"]),
    ("idx_rollcall_student", "rollcall_records", ["student_id"]),
    ("idx_login_user", "login_records", ["user_id"]),
    ("idx_steps_task", "task_steps", ["task_id"]),
    ("idx_users_class", "users", ["class_id"]),
    ("idx_users_role", "users", ["role"]),
    ("idx_eval_records_student", "eval_records", ["student_id"]),
    ("idx_eval_records_indicator", "eval_records", ["indicator_id"]),
    ("idx_eval_records_template", "eval_records", ["template_id"]),
    ("idx_eval_snap_student", "eval_snapshots", ["student_id", "template_id"]),
    ("idx_eval_phase_template", "eval_phases", ["template_id"]),
    ("idx_eval_indicator_phase", "eval_indicators", ["phase_id"]),
]

for _name, _table, _cols in _EXTRA_INDEXES:
    _t = Base.metadata.tables.get(_table)
    if _t is not None:
        Index(_name, *[_t.c[c] for c in _cols])

__all__ = [
    'User', 'Class', 'Task', 'TaskStep', 'Submission', 'Attachment',
    'AiLog', 'Score', 'RollcallRecord', 'LoginRecord', 'AppSetting',
    'EvalTemplate', 'EvalPhase', 'EvalIndicator',
    'EvalScorerConfig', 'EvalRecord', 'EvalSnapshot'
]
