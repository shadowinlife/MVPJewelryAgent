"""服务层(service layer)— 业务规则的唯一执行点。

`app.services` 下的模块负责把 ORM / Pydantic schema / 外部 client 组合成
业务用例(use case)。设计约定:

1. **service 函数是无状态纯函数 / 协程**:依赖通过参数注入,不在内部
   `import` SessionLocal / settings,方便测试 mock。
2. **service 只调用 schema + ORM + client,不直接被 ORM 反向依赖**;
   反过来 ORM 不应 import service —— 这是分层底线。
3. **任何"权限相关"的字段裁剪 / 视图投影都必须在 service 层实现**,
   路由层只做 "认证 → 调 service → 包信封" 三步,不准在路由里写
   `if role == 'admin'` 之类的分支(否则跟前端隐藏一样脆弱,违反
   Backend-Architecture §10.3 RBAC 红线 #2)。

Stage 3 只产出 `report_service`;Stage 4 再加 `case_service` / `file_service`
等(各路由对应一个 service 模块)。
"""

from app.services.auth_service import (
    authenticate_user,
    issue_tokens,
    refresh_tokens,
    register_user,
)
from app.services.report_service import (
    TIER_ORDER,
    build_admin_view,
    build_customer_brief,
    crop_report_for_user,
)

__all__ = [
    "TIER_ORDER",
    "authenticate_user",
    "build_admin_view",
    "build_customer_brief",
    "crop_report_for_user",
    "issue_tokens",
    "refresh_tokens",
    "register_user",
]
