"""统一响应信封。

后端所有 HTTP JSON 响应都包成 `ApiResponse[T]`,严格对齐前端 TypeScript
契约 `web/lib/types/domain.ts :: ApiResponse<T>`:

```ts
export interface ApiResponse<T> {
  ok: boolean;
  data?: T;
  error?: string;       // 人类可读中文短句
  source: DataSource;   // "real" | "import" | "mock"
}
```

约定:
- 成功响应 `ok=True`,`data` 非空,`error` 为 `None`。
- 失败响应 `ok=False`,`error` 非空,`data` 为 `None`。
- `source` 默认 `"real"`(真后端真数据);后续 Stage 接 MOCK_* 开关时,被
  mock 的接口要在响应中显式声明 `source="mock"`,前端据此选择是否展示
  "演示数据"标签。
- 错误 `code`(机器可读)Backend-Architecture §11.1 标 P1 引入,Stage 1
  **不**进响应体,只进结构化日志。
"""

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

# 数据来源枚举;与前端 `DataSource` 字面量保持一致。
# - "real":真后端真数据(默认)
# - "import":批量导入的历史数据(在管理后台明确标识)
# - "mock":mock 数据(只在 staging/local 出现,production 不应见到)
DataSource = Literal["real", "import", "mock"]

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应信封。

    禁止任何接口绕过本信封直接返回裸数据。`extra="forbid"` 防止 Pydantic
    自动接收未声明字段(避免前端某天加了 `requestId` 字段后,后端不知情但
    单元测试又过得去这种漂移)。

    用法:
        return ApiResponse[UserSchema].success(data=user)
        raise NotFoundError(message="案例不存在")   # 由 exception handler 转信封
    """

    model_config = ConfigDict(extra="forbid")

    ok: bool
    data: T | None = None
    error: str | None = None
    source: DataSource = "real"

    @classmethod
    def success(cls, data: T, source: DataSource = "real") -> "ApiResponse[T]":
        """构造一个成功响应(`ok=True`)。

        路由函数显式调用本工厂,避免散落各处的 `{"ok": True, ...}` 字典字面量。
        """
        return cls(ok=True, data=data, source=source)

    @classmethod
    def failure(cls, error: str, source: DataSource = "real") -> "ApiResponse[T]":
        """构造一个失败响应(`ok=False`)。

        正常路径走"抛业务异常 → exception handler 转信封";本工厂只在
        exception handler 内部使用。**业务代码不应**主动 `return failure(...)`。
        """
        return cls(ok=False, error=error, source=source)
