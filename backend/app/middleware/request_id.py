"""Request ID 中间件。

每个 HTTP 请求要么携带前端/网关塞进来的 `X-Request-ID`,要么由本中间件生成
一个新的 UUID hex(32 位无横线)。无论哪种,都会:

1. 写入 `request.state.request_id`,后续业务代码可读;
2. `bind_contextvars(request_id=...)`,让本请求范围内的所有 structlog 日志
   自动带这个字段,跨日志检索时一查就到链路;
3. 写回响应 header(同名),前端 fetch 拿到后落到错误上报里,客服收到工单
   能直接定位后端日志。

header 名通过构造参数注入(默认 `X-Request-ID`),Settings 决定具体值。
"""

import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """读 / 生成 / 透传 Request ID 的 Starlette 中间件。

    放在中间件栈的**最内层**(最早执行 `dispatch`),保证 ErrorHandler /
    EnvelopeMiddleware / 业务路由 看到的日志上下文都已经绑好。
    """

    def __init__(self, app: object, header_name: str = "X-Request-ID") -> None:
        # `app: object` 是为绕过 Starlette `BaseHTTPMiddleware.__init__` 的弱类型签名;
        # 实际类型是 `ASGIApp`,运行期 Starlette 自己负责传入。
        super().__init__(app)  # type: ignore[arg-type]
        self.header_name = header_name

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """请求生命周期 hook:进 → bind → 路由 → unbind → 出。"""
        incoming = request.headers.get(self.header_name)
        # 透传上游 ID(如果有),否则生成新的;`uuid.uuid4().hex` 是 32 位无横线
        # 形式,日志检索/grep 更友好,且与标准 UUID 信息熵一致。
        request_id = incoming if incoming else uuid.uuid4().hex
        request.state.request_id = request_id

        # contextvars 必须先 clear 再 bind:防止上一个请求的残留(理论上 ASGI 协议
        # 每请求隔离,实际中如果中间件链中有同步包装可能漏掉,故主动清理一次更安全)。
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
        finally:
            # 退出前 unbind,避免 worker 复用线程时把上一个请求的 ID 漏到下一个。
            structlog.contextvars.clear_contextvars()

        response.headers[self.header_name] = request_id
        return response
