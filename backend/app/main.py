"""FastAPI 应用入口。

通过 `create_app()` 工厂构建实例,而非模块级直接 `app = FastAPI()`,目的:
- 测试可以独立 `create_app()` 拿到全新实例,避免 import 顺序产生隐式耦合;
- 一次性集中决策中间件挂载顺序、exception handler 注册、路由聚合,日后
  排查"为什么这条请求没经过 X middleware"只看本文件就够。

模块底部仍然导出 `app = create_app()`,这是 uvicorn / gunicorn 入口契约
(`uvicorn app.main:app`)。
"""

from fastapi import FastAPI

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.middleware.envelope import register_exception_handlers
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.request_id import RequestIdMiddleware


def create_app() -> FastAPI:
    """构造 FastAPI 实例。返回值作为 ASGI app 暴露给 uvicorn / gunicorn。"""
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="YAOQI Backend",
        version=settings.app_version,
        openapi_url="/openapi.json",
        docs_url="/docs",
        # 关掉 redoc 端点,只留 Swagger UI;减少攻击面。
        redoc_url=None,
    )

    # 中间件顺序很重要(Starlette 后 add 的更靠外):
    #   外层 ErrorHandlerMiddleware  ← 兜底,任何漏网异常都包成信封 500
    #     内层 RequestIdMiddleware    ← 给 ErrorHandlerMiddleware 的日志也带 request_id
    #       业务 handlers / 路由
    # 反过来调用 add_middleware 的顺序意味着:RequestId 先于 ErrorHandler 执行 dispatch,
    # 但 ErrorHandler 的 except 仍能捕获到 RequestId 内部异常。
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RequestIdMiddleware, header_name=settings.request_id_header)

    # 异常 → 信封 的统一处理器集合(详见 app.middleware.envelope)。
    register_exception_handlers(app)

    # API 路由聚合(详见 app.api.v1.__init__)。
    app.include_router(api_router)

    log = get_logger("app.main")
    log.info("app_started", env=settings.app_env, version=settings.app_version)

    return app


# uvicorn / gunicorn 入口契约:`uvicorn app.main:app` 找的就是这个变量。
app = create_app()
