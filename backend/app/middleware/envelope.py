"""信封式异常处理器。

约定:
- **成功响应**由路由函数显式返回 `ApiResponse[T]`(通过 `response_model`),
  本模块不处理。
- **失败响应**由本模块统一拦截:`AppException` / `RequestValidationError` /
  其它未捕获 `Exception` → 全部转换为 `ApiResponse.failure(...)` 形态。

物理上不是 Starlette middleware(不是 BaseHTTPMiddleware 子类),而是
FastAPI exception handler 集合;放在 `app/middleware/` 目录只是延续项目
约定的目录结构,不要被 module 名字误导。

注:路由内手 raise `HTTPException`(FastAPI 内置)会**绕过**本套信封 —
请坚持 raise `AppException` 子类,这是 [skills/backend-engineer.md 红线 #10]
"禁止绕开 EnvelopeMiddleware"的精神。
"""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppException
from app.core.logging import get_logger
from app.schemas.envelope import ApiResponse

log = get_logger(__name__)


def _envelope_response(status_code: int, message: str) -> JSONResponse:
    """构造一个失败信封 JSONResponse(内部 helper)。

    `exclude_none=False` 保留 `data: null` 字段,确保前端 TS interface 拿到
    完整 4 个 key(`ok` / `data` / `error` / `source`),否则前端 narrowing
    可能踩到 `data` 字段不存在的 undefined 行为。
    """
    payload = ApiResponse[Any].failure(error=message)
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(payload, exclude_none=False),
    )


async def _app_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """业务异常 → 信封;状态码由异常子类自带。

    日志同时打 `code`(机器可读)和 `message`(人话),前者方便聚合统计,
    后者方便看到具体哪个用户哪条数据。
    """
    # 这里用 assert 而非 cast 是因为 FastAPI 已经按 (Exception 类型, 处理器) 路由,
    # 进到本函数的 exc 一定是 AppException;assert 同时给 mypy 提示类型。
    assert isinstance(exc, AppException)
    log.info(
        "app_exception",
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
    )
    return _envelope_response(exc.status_code, exc.message)


async def _validation_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Pydantic / FastAPI 入参校验失败 → 信封 422。

    取 errors 列表第一条作为面向用户的简短消息;完整 errors 进日志便于排查。
    """
    assert isinstance(exc, RequestValidationError)
    first = exc.errors()[0] if exc.errors() else {"msg": "请求参数不合法"}
    message = str(first.get("msg", "请求参数不合法"))
    log.info("validation_error", errors=exc.errors())
    return _envelope_response(status.HTTP_422_UNPROCESSABLE_ENTITY, message)


async def _unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """兜底:任何未捕获的 `Exception` → 500 信封。

    返回给前端的 `error` 文案**绝不能**泄漏内部堆栈或第三方 endpoint;真异常
    细节进日志(`log.exception` 自动带 traceback)由 Sentry / Filebeat 收集。
    """
    log.exception("unhandled_exception", error_type=type(exc).__name__)
    return _envelope_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "服务器内部错误")


def register_exception_handlers(app: FastAPI) -> None:
    """把上面三个 handler 注册到 FastAPI 实例上。

    `app.main:create_app` 在构建阶段调用一次即可;handler 顺序无关
    (FastAPI 按异常类型最具体匹配,不是先注册先优先)。
    """
    app.add_exception_handler(AppException, _app_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    # `Exception` 必须放最后注册没有意义(FastAPI 按类型最具体匹配),
    # 这里写法上放最后纯粹是阅读上的"兜底"语义提示。
    app.add_exception_handler(Exception, _unhandled_exception_handler)
