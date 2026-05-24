"""日志初始化。

后端统一使用 structlog 输出**结构化 JSON 日志**到 stdout,由容器编排(K8s /
Docker)负责采集、转发到 ELK / Loki 等下游。这套配置同时给标准库 `logging`
模块设阈值,避免第三方包绕过 structlog 直接打到 stdout 时出现重复 / 乱序。

不同模块通过 `get_logger(__name__)` 拿到带有调用方上下文的 BoundLogger;
`request_id` 等链路追踪字段由 `RequestIdMiddleware` 在请求开始时
`bind_contextvars` 注入,本模块**不**负责注入业务上下文。
"""

import logging
import sys
from typing import Any, cast

import structlog
from structlog.types import EventDict, Processor

from app.core.config import LogLevel


def _drop_color_message(_: Any, __: str, event_dict: EventDict) -> EventDict:
    """剔除 uvicorn 在日志事件里塞的 `color_message` 字段。

    这个字段包含 ANSI 颜色控制符,只对终端有意义,落到 JSON 里既无用又噪音大,
    所以在序列化前丢掉。
    """
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging(level: LogLevel) -> None:
    """初始化全局日志配置。

    必须在创建 FastAPI app 之前调用一次,后续重复调用会重置 processors 链。
    `cache_logger_on_first_use=True` 在性能敏感路径(每请求多次 log)上
    避免反复构造 logger 实例。

    入参:
        level: 阈值。低于该级别的日志会被 `make_filtering_bound_logger` 过滤掉。
    """
    # 标准库 logging 与 structlog 共用同一阈值;`format="%(message)s"` 保证
    # structlog 接管输出后,标准库不再二次格式化(避免出现 `INFO:root:{json}` 这种夹生输出)。
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level),
    )

    # processors 是日志事件流过的一系列管道节点,顺序敏感:
    #   contextvars  →  level  →  时间戳  →  清洗  →  栈信息  →  exc_info  →  JSON 序列化
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _drop_color_message,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=[*shared_processors, structlog.processors.JSONRenderer()],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level)),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """获取带 `name` 标签的 BoundLogger。

    所有模块统一通过这个工厂取 logger,而不是直接 `structlog.get_logger()`,
    便于日后切换实现或加全局 hook。`name` 约定传 `__name__`。

    返回类型显式 cast 是因为 structlog 没有发布 PEP 561 类型存根,
    `structlog.get_logger()` 在 strict 模式下返回 `Any`。
    """
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
