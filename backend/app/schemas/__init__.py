"""`app.schemas` 公共导出门面 — 让路由 / service / 测试统一从这里 import。

为什么显式 re-export(`as` 别名 + `__all__`):

- 项目 mypy 配置开启了 `no_implicit_reexport = True`,**裸 import 不算
  导出**;调用方写 `from app.schemas import CaseReport` 时会 type-error
  "Name not defined"。用 `from ... import X as X` 显式声明,mypy 才认。
- `__all__` 同时帮 ruff / IDE 列出真正的对外符号,删字段时一搜即知谁
  在用、能不能删。
"""

from app.schemas.envelope import (
    ApiResponse as ApiResponse,
)
from app.schemas.envelope import (
    DataSource as DataSource,
)
from app.schemas.report import (
    CaseReport as CaseReport,
)
from app.schemas.report import (
    InternalCustomerBrief as InternalCustomerBrief,
)
from app.schemas.report import (
    InternalReport as InternalReport,
)
from app.schemas.report import (
    MembershipTier as MembershipTier,
)
from app.schemas.report import (
    ReportAdmin as ReportAdmin,
)
from app.schemas.report import (
    ReportAudience as ReportAudience,
)
from app.schemas.report import (
    ReportBasic as ReportBasic,
)
from app.schemas.report import (
    ReportBusiness as ReportBusiness,
)
from app.schemas.report import (
    ReportBusinessPro as ReportBusinessPro,
)
from app.schemas.report import (
    ReportCustomerBrief as ReportCustomerBrief,
)
from app.schemas.report import (
    ReportFree as ReportFree,
)
from app.schemas.report import (
    ReportPro as ReportPro,
)

__all__ = [
    "ApiResponse",
    "CaseReport",
    "DataSource",
    "InternalCustomerBrief",
    "InternalReport",
    "MembershipTier",
    "ReportAdmin",
    "ReportAudience",
    "ReportBasic",
    "ReportBusiness",
    "ReportBusinessPro",
    "ReportCustomerBrief",
    "ReportFree",
    "ReportPro",
]
