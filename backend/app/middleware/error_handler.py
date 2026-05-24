"""中间件链兜底异常处理。

FastAPI 的 exception handler(见 `app.middleware.envelope`)只能拦截**路由函数
内部**抛的异常;如果异常发生在**其它中间件**里(例如 RequestIdMiddleware 内
部 bug、第三方中间件崩了),exception handler 不会触发,响应会是裸的 Starlette
500 / ASGI 异常 — 形状不是信封,前端拿到会崩。

本中间件是防线之 2:在所有路由 + 业务 middleware 的最外层包一层 try/except,
把任何漏网异常也压成统一信封。**正常情况下不应该被触发**;一旦触发,日志里
要能看到完整堆栈用于复盘。
"""

from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger
from app.schemas.envelope import ApiResponse

log = get_logger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """中间件链兜底异常包装。挂在中间件栈的**最外层**(最晚执行 `dispatch` 包装)。"""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            # 注意:`log.exception` 自动把 traceback 写进结构化日志;敏感信息已经
            # 在 structlog `format_exc_info` processor 链中处理。
            log.exception("middleware_unhandled", error_type=type(exc).__name__)
            payload = ApiResponse[Any].failure(error="服务器内部错误")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=jsonable_encoder(payload, exclude_none=False),
            )
