"""ORM Model 集中 re-export。

**关键**:Alembic autogenerate 只能看到 `Base.metadata.tables` 里已注册的
表;而表的注册时机是 Model 类被 import 加载。这个 `__init__.py` 的唯一职责
就是**强制 import** 所有 13 个 Model 模块,触发它们绑定到 `Base.metadata`。

**禁止**省略任何 Model 的 import —— 漏一张就意味着 Alembic 不认识它,
`alembic upgrade head` 不会创建该表,`alembic check` 也不会报漂移。

外部代码可以从这里集中拿:
    from app.db.models import User, Case, AIReport
"""

from app.db.models.admin_operation_log import AdminOperationLog
from app.db.models.admin_review import AdminReview
from app.db.models.ai_call_log import AICallLog
from app.db.models.ai_report import AIReport
from app.db.models.case import Case
from app.db.models.case_file import CaseFile
from app.db.models.import_job import ImportJob
from app.db.models.knowledge_file import KnowledgeFile
from app.db.models.llm_provider_config import LLMProviderConfig
from app.db.models.membership import Membership
from app.db.models.ocr_result import OcrResult
from app.db.models.sms_code import SmsCode
from app.db.models.token_quota import TokenQuota
from app.db.models.user import User

__all__ = [
    "AICallLog",
    "AIReport",
    "AdminOperationLog",
    "AdminReview",
    "Case",
    "CaseFile",
    "ImportJob",
    "KnowledgeFile",
    "LLMProviderConfig",
    "Membership",
    "OcrResult",
    "SmsCode",
    "TokenQuota",
    "User",
]
