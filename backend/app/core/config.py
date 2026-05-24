"""应用配置。

集中管理后端运行期需要的所有可调参数,通过 pydantic-settings 从环境变量(或
`.env` 文件)注入。**禁止**把任何 secret 直接写默认值;真值走 env / KMS 注入。

Stage 1 只有最少的几个字段(app_env / app_version / log_level /
request_id_header)。Stage 2 起会扩 DB / Redis / OSS / Azure 等字段;扩字段时
直接在 `Settings` 上加,`.env.example` 同步即可,不需要改 `get_settings`。
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 三种部署环境;production 不允许任何 MOCK_* / SEED_MOCK_DATA 为真(由更上层校验)。
AppEnv = Literal["local", "staging", "production"]

# 日志阈值;低于该级别的日志会被 structlog 过滤掉,不会进 stdout。
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]


class Settings(BaseSettings):
    """后端运行期配置单例。

    所有字段名以**蛇形小写**对应环境变量(默认大小写不敏感)。例如
    `app_env` 对应 `APP_ENV`。`extra="ignore"` 允许 `.env` 中存在 Stage 2-4
    才会读取的字段(如 `DATABASE_URL`),Stage 1 程序不会因为冗余字段报错。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # 部署环境;影响日志格式、是否启用调试端点等行为。
    app_env: AppEnv = "local"

    # 应用版本号;同步暴露到 `/health.data.version` 与 OpenAPI title。发版前由 CI 写入。
    app_version: str = "0.1.0"

    # 日志阈值;production 建议 INFO,staging/local 可以放到 DEBUG 排查。
    log_level: LogLevel = "INFO"

    # 入站 Request ID 的 HTTP header 名;前后端必须保持一致,默认遵守事实标准。
    request_id_header: str = Field(default="X-Request-ID", min_length=1)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """返回进程级 `Settings` 单例。

    使用 `lru_cache` 而非模块级常量,目的是让测试可以通过
    `get_settings.cache_clear()` 拿到重新读取 env 的实例(例如改 `os.environ`
    后立刻生效),而不必重启进程。
    """
    return Settings()
