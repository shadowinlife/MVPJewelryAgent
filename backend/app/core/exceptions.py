"""业务异常。

后端所有可预期的业务错误(用户非法输入、权限不足、资源不存在、配额耗尽等)
**必须**抛 `AppException` 或其子类,由 `app.middleware.envelope` 注册的
exception handler 转成统一信封返回给前端,响应体形如:

```json
{"ok": false, "error": "案例不存在", "source": "real"}
```

`code`(机器可读错误码)按 Backend-Architecture §11.1 标 P1 引入;Stage 1
**只**把 code 写进结构化日志方便排查,不进响应体(对齐前端
`web/lib/types/domain.ts :: ApiResponse<T>` 形状)。
"""

from http import HTTPStatus


class AppException(Exception):
    """业务异常基类。

    携带三样东西:
    - `code`(`str`)— `domain.subdomain` 形态的稳定错误码,例如
      `case.not_found` / `auth.invalid_credentials` / `quota.exceeded`。
      仅用于内部日志与未来的 i18n / 自动化测试断言,**不**进响应体。
    - `message`(`str`)— 人类可读的中文短句,直接进响应体 `error` 字段。
    - `status_code`(`int`)— HTTP 状态码,默认 400;鉴权/授权/限流子类按需覆盖。

    使用建议:**业务代码抛具体子类**(`NotFoundError` / `ForbiddenError` 等),
    而不是直接抛 `AppException`,这样阅读者一眼看清意图。如果确实需要自定义
    code,显式传第一个位置参:`raise NotFoundError(code="case.not_found", message="...")`。
    """

    # 默认 code;子类覆盖。
    code: str = "app.error"
    # 默认 HTTP 状态;子类覆盖。
    status_code: int = HTTPStatus.BAD_REQUEST

    def __init__(
        self,
        code: str | None = None,
        message: str = "请求异常",
        status_code: int | None = None,
    ) -> None:
        # 父类 `Exception.args` 保留 message,方便 `str(exc)` 拿到人话。
        super().__init__(message)
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        # `message` 单独保留一份,避免子类覆盖 `__str__` 时丢失原始字符串。
        self.message = message


class NotFoundError(AppException):
    """资源不存在(404)。

    用于:`GET /cases/:case_no` 没找到、`reports/:id` 不属于当前用户(此时
    出于安全考虑也返 404 而非 403,避免泄漏资源存在性)。
    """

    code = "common.not_found"
    status_code = HTTPStatus.NOT_FOUND


class UnauthorizedError(AppException):
    """未登录(401)。

    用于:session 失效、缺少 `Authorization`、JWT 签名校验失败。
    与 `ForbiddenError` 区分:**未携带身份** vs **身份不够**。
    """

    code = "auth.unauthorized"
    status_code = HTTPStatus.UNAUTHORIZED


class ForbiddenError(AppException):
    """权限不足(403)。

    用于:RBAC 红线触发(跨用户访问、低 tier 看高 tier 字段、普通管理员碰
    super-only 路径)。详见 [Backend-Architecture §10.3]。
    """

    code = "auth.forbidden"
    status_code = HTTPStatus.FORBIDDEN


class ValidationError(AppException):
    """业务级参数校验失败(422)。

    Pydantic / FastAPI 自动捕获的 `RequestValidationError` 由 `envelope.py` 单独
    处理(也返 422 + 统一信封);这里的 `ValidationError` 专给**业务规则**
    校验用,例如"会员到期不能续费同一档"。
    """

    code = "common.validation_failed"
    status_code = HTTPStatus.UNPROCESSABLE_ENTITY


class RateLimitedError(AppException):
    """限频触发(429)。

    用于:短信验证码 60s 限频(RL-06)、登录 IP 限频、AI 接口配额耗尽时的瞬时拒绝。
    返回时建议中间件追加 `Retry-After` header(Security-Checklist E-07)。
    """

    code = "common.rate_limited"
    status_code = HTTPStatus.TOO_MANY_REQUESTS
