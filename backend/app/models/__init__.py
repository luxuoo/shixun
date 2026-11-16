from app.models.user import User, Class
from app.models.task import Task, TaskStep
from app.models.submission import Submission
from app.models.ai_log import AiLog, Score, RollcallRecord, LoginRecord
from app.models.app_setting import AppSetting
from app.models.evaluation import (
    EvalTemplate, EvalPhase, EvalIndicator,
    EvalScorerConfig, EvalRecord, EvalSnapshot
)

__all__ = [
    'User', 'Class', 'Task', 'TaskStep', 'Submission',
    'AiLog', 'Score', 'RollcallRecord', 'AppSetting',
    'EvalTemplate', 'EvalPhase', 'EvalIndicator',
    'EvalScorerConfig', 'EvalRecord', 'EvalSnapshot'
]
