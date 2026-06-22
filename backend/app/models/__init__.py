from app.models.user import User, Class
from app.models.task import Task, TaskStep
from app.models.submission import Submission
from app.models.ai_log import AiLog, Score, RollcallRecord
from app.models.grade import GradeScheme, GradeItem, GradeRecord
from app.models.evaluation import (
    EvalTemplate, EvalPhase, EvalIndicator,
    EvalScorerConfig, EvalRecord, EvalSnapshot
)

__all__ = [
    'User', 'Class', 'Task', 'TaskStep', 'Submission',
    'AiLog', 'Score', 'RollcallRecord',
    'GradeScheme', 'GradeItem', 'GradeRecord',
    'EvalTemplate', 'EvalPhase', 'EvalIndicator',
    'EvalScorerConfig', 'EvalRecord', 'EvalSnapshot'
]
