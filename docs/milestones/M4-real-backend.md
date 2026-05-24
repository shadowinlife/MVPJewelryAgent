# M4 — Real Backend 路标

> 父文档:[../roadmap.md](../roadmap.md)
> 前置:[M2-user-pages.md](./M2-user-pages.md)(🟢 已完成 2026-05-22)
> 设计基线:[Backend-Architecture_v0.1.md](../Backend-Architecture_v0.1.md)、[Backend-Database-Schema_v0.1.md](../Backend-Database-Schema_v0.1.md)、[Backend-Security-Checklist_v0.1.md](../Backend-Security-Checklist_v0.1.md)、[Backend-Deployment-Guide_v0.1.md](../Backend-Deployment-Guide_v0.1.md)
> 决策日志:[discussions/M4-backend-rollout-tracker.md](../discussions/M4-backend-rollout-tracker.md)
> 状态:🟡 进行中(Stage 1 完成 2026-05-24,Stage 2 完成 2026-05-24,Stage 3-4 待启动)
> 目标:把前端 mock route 全部替换为**真后端** + **真数据库** + **真 OSS** + **真 OCR** + **真 AI**,达到 [Backend-Architecture §15 M4 验收 checklist](../Backend-Architecture_v0.1.md) 的"实施完成态"。

## 业务背景拍板(承接 tracker §一)

1. **后端语言** = FastAPI(Python 3.12);异步队列 = Arq;**不引入** LangChain / LlamaIndex / DSPy / Celery / NestJS。
2. **数据库** = 阿里云 RDS PostgreSQL 16(原生 pgvector);RAG 召回开关 M4 默认 **关**(只写不读)。
3. **LLM** = Azure OpenAI Service @ HongKong **唯一通道**;后端跨云**公网直连**,不引入 API Gateway / VPN 专线。
4. **OSS** = 阿里云 OSS + **STS 预签名直传**(文件不过后端);Bucket 必须**私有**,客户简洁版**禁** public URL。
5. **登录** = 手机号 + 邮箱 + 密码(微信登录推 P1);短信 = 阿里云短信。
6. **错误信封** `error` 字段本期仅中文短句(i18n 错误码推 P1);**信封形状以 [web/lib/types/domain.ts](../../web/lib/types/domain.ts) 为单一源**。

详见 [tracker §1.1 / §1.2](../discussions/M4-backend-rollout-tracker.md)。

## 目标产出

完成本路标后:

- `backend/` 目录可 `uv sync && uvicorn` 起服,`/health` 同时探活 self / db / redis / oss / aoai
- 13 张核心表 + Alembic 初始迁移 + RLS / CHECK 约束就绪;`pytest` 用 testcontainers 起真 PG 跑迁移
- 7 个 tier(L0~L4_PRO)的 Pydantic schema + 服务端字段裁剪覆盖详情/客户简洁版/导出
- 路由 stub(auth / cases / reports / files / ocr / memberships)+ JWT auth + 8 条 RBAC 红线自动化测试
- `LLMClient` Protocol + Azure OpenAI 适配器 + prompt 模板;OSS / OCR / 短信 client(无 key 时实例化即 `NotImplementedError`)
- `web/app/api/**` 全部 mock route handler 关掉,前端 fetch 直接走 `backend` / `BFF`,**Mock 浮标** + `<MockBadge>` 隐去
- CI 全绿:`uv sync` → `ruff check` → `mypy --strict app/` → `pytest` → `docker build` → `gitleaks` → `pip-audit` → Trivy

## Stage 拆解

M4 切成 4 个 Stage,每个 Stage 单独 PR,每个 Stage 落地后回看本文件 / tracker / roadmap 各加一行。

| Stage | 范围 | 状态 | 验收 |
|---|---|---|---|
| **Stage 1: Foundation** | FastAPI 骨架 + `/health(self)` + envelope / request-id 中间件 + Settings + structlog + Dockerfile + pytest 骨架 | 🟢 完成 (2026-05-24) | 详见下方"Stage 1 任务清单" |
| **Stage 2: Persistence** | 13 张 ORM + Alembic 初始迁移(扩展 + 13 表 + CHECK + 索引 + 触发器 + pgvector 列)+ testcontainers fixture(per-test SAVEPOINT)+ `/health` 扩 `checks.db` | 🟢 完成 (2026-05-24) | 详见下方"Stage 2 任务清单" |
| **Stage 3: Tier Schemas** | 7 个 tier 的 Pydantic schema + `cropReportForUser` 服务端裁剪服务 + 客户简洁版字段集 | ⚪ 未开始 | 8 条 RBAC 红线 + UI-Spec §17.3 数据红线测试全绿 |
| **Stage 4: API + Integrations** | 路由 stub(auth/cases/reports/files/ocr/memberships)+ JWT + RBAC deps + DAO/Service 层 + `LLMClient` Protocol + OSS/OCR/短信 client + `/health` 扩 redis/oss/aoai + Seed(super_admin / 字典) | ⚪ 未开始 | 前端 mock route 全关;`docker build` + gitleaks + pip-audit + Trivy 全绿;Backend-Architecture §15 全部勾选 |

状态图例:🟢 已完成 / 🟡 进行中 / ⚪ 未开始 / 🔴 阻塞

## Stage 1 任务清单(已完成)

| # | 任务 | 状态 | 产出文件 |
|---|------|------|---------|
| 1 | uv 项目初始化(pyproject + uv.lock)+ Python 3.12 + `.python-version` | 🟢 | `backend/pyproject.toml`, `backend/uv.lock`, `backend/.python-version` |
| 2 | `app/core/config.py` — pydantic-settings `Settings` 单例(Stage 1 字段) | 🟢 | `backend/app/core/config.py` |
| 3 | `app/core/logging.py` — structlog JSON 日志 + contextvars | 🟢 | `backend/app/core/logging.py` |
| 4 | `app/core/exceptions.py` — AppException 体系(NotFound 404 / Forbidden 403 / Unauthorized 401 / Validation 422 / RateLimited 429) | 🟢 | `backend/app/core/exceptions.py` |
| 5 | `app/schemas/envelope.py` — `ApiResponse[T]`,严格对齐前端 TS 契约 | 🟢 | `backend/app/schemas/envelope.py` |
| 6 | `app/middleware/request_id.py` — X-Request-ID 透传/生成 + 写 structlog | 🟢 | `backend/app/middleware/request_id.py` |
| 7 | `app/middleware/envelope.py` — FastAPI exception_handler 集合 | 🟢 | `backend/app/middleware/envelope.py` |
| 8 | `app/middleware/error_handler.py` — BaseHTTPMiddleware 兜底 | 🟢 | `backend/app/middleware/error_handler.py` |
| 9 | `app/api/v1/health.py` — `/health` Stage 1 版(只 `checks.self`) | 🟢 | `backend/app/api/v1/health.py` |
| 10 | `app/main.py` — `create_app()` 工厂 + 中间件挂载顺序 | 🟢 | `backend/app/main.py` |
| 11 | `app/deps/db.py` — `get_db()` Stage 2 占位 stub | 🟢 | `backend/app/deps/db.py` |
| 12 | Dockerfile + entrypoint.sh(python:3.12-slim-bookworm + 非 root + tini) | 🟢 | `backend/Dockerfile`, `backend/scripts/entrypoint.sh` |
| 13 | pytest 骨架 + conftest.py(ASGITransport AsyncClient fixture) | 🟢 | `backend/tests/conftest.py`, `backend/tests/__init__.py` |
| 14 | test_health.py × 2 / test_envelope.py × 5 / test_request_id.py × 3 = **10 用例** | 🟢 | `backend/tests/test_*.py` |
| 15 | README.md + .env.example + .gitignore + .dockerignore | 🟢 | `backend/README.md` etc. |
| 16 | AGENT.md 新增「代码规范 / 注释即文档(Code-as-Doc)」7+1 条,覆盖默认"少注释"规则 | 🟢 | `AGENT.md` |
| 17 | 所有 Stage 1 文件按新规范回填中文 docstring + 关键 WHY 注释 | 🟢 | 同 #2~#13 |

## Stage 1 验收清单

完成定义(全部勾选才能转 🟢 Stage 1 完成态):

- [x] `uv sync` 一键拉起依赖,`uv.lock` 入 git
- [x] `uvicorn app.main:app --reload` 启动成功,`GET /health` 返 `{"ok":true,"data":{"status":"ok","version":"0.1.0","checks":{"self":"ok"}},"error":null,"source":"real"}`
- [x] 响应携带 `X-Request-ID`(请求带就回写,不带就 uuid hex 生成)
- [x] `uv run pytest -v` → **10 passed**
- [x] `uv run ruff check .` → clean
- [x] `uv run mypy --strict app/` → no issues in 17 source files
- [x] `docker build -t yaoqi-backend:dev .` 不报错(Dockerfile 语法验证;真 digest 等 ACR 上线再回填)
- [x] 信封形状与 [web/lib/types/domain.ts :: ApiResponse<T>](../../web/lib/types/domain.ts) 四字段严格等值(测试用 set 等值断言锁死)
- [x] 失败信封无多余 key(`code` / `requestId` / 内部异常文案均不能漏出)— `test_envelope.py::test_envelope_has_no_extra_keys_on_failure` + `test_unhandled_exception_returns_500_envelope` 守住
- [x] 中间件挂载顺序文档化:外层 ErrorHandler / 内层 RequestId,`app/main.py` 内有注释解释为什么这么挂

## Stage 1 不做(明确推迟)

| 项 | 推到哪 |
|---|---|
| 13 张 ORM 模型 + Alembic 初始迁移 + testcontainers fixture | Stage 2 |
| 7 个 tier Pydantic schemas + 字段裁剪服务 | Stage 3 |
| 路由 stub(auth/cases/reports/files/ocr/memberships)+ JWT + RBAC deps | Stage 4 |
| `LLMClient` Protocol + Azure OpenAI 适配器 | Stage 4 |
| OSS / OCR / 短信 / Azure OpenAI client(无真 key 时 `NotImplementedError`) | Stage 4 |
| `tests/test_rbac_redlines.py`(8 红线 + RBAC 4 红线自动化) | Stage 4 |
| `Backend-API-Spec_v0.1.yaml` 自动生成(`/openapi.json` 导出) | Stage 4 后 |
| CI 加 `docker build` + gitleaks + pip-audit + Trivy | Stage 4 |
| `/health` 扩 db / redis / oss / aoai 探活 | Stage 2 / Stage 4 分次扩 |

## Stage 2 任务清单(已完成)

| # | 任务 | 状态 | 产出文件 |
|---|---|---|---|
| 1 | pyproject.toml 加 prod 依赖(sqlalchemy[asyncio]/asyncpg/alembic/pgvector)+ dev(testcontainers)+ uv lock | 🟢 | `backend/pyproject.toml`, `backend/uv.lock` |
| 2 | `app/core/config.py` 加 `database_url` / `db_pool_*` / `health_db_timeout_seconds` + `.env.example` 同步 | 🟢 | `backend/app/core/config.py`, `backend/.env.example` |
| 3 | `app/db/base.py` — `Base` + `IdMixin` + `TimestampMixin` + `MockableMixin` 三 mixin | 🟢 | `backend/app/db/base.py` |
| 4 | `app/db/session.py` — async engine + `async_sessionmaker`(`autoflush=False / expire_on_commit=False`) | 🟢 | `backend/app/db/session.py` |
| 5 | 13 个 ORM Model(users / memberships / token_quotas / cases / case_files / ocr_results / ai_reports / ai_call_logs / admin_reviews / admin_operation_logs / knowledge_files / import_jobs / sms_codes) | 🟢 | `backend/app/db/models/*.py` |
| 6 | `alembic.ini` + `alembic/env.py`(async pattern + `compare_type=True` + `compare_server_default=True` + `include_object` 过滤 raw SQL 索引)+ `script.py.mako` | 🟢 | `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/script.py.mako` |
| 7 | `alembic/versions/0001_init.py` 单 revision 全落:3 扩展 + 13 表 + CHECK 约束 + 9 raw SQL 索引(部分索引 / GIN / ivfflat)+ pgvector 列 + 7 触发器(用 `clock_timestamp()` 而非 `now()` 防同事务时间戳塌陷) | 🟢 | `backend/alembic/versions/0001_init.py` |
| 8 | `app/deps/db.py` 由 stub 升级为真 `get_db()`(yield + commit / rollback) | 🟢 | `backend/app/deps/db.py` |
| 9 | `app/api/v1/health.py` 加 `_check_db()`(SELECT 1 + asyncio.timeout)+ `data.status="degraded"` 时 HTTP 仍 200(D5) | 🟢 | `backend/app/api/v1/health.py` |
| 10 | `scripts/entrypoint.sh` 加 `migrate` 子命令(alembic upgrade head) | 🟢 | `backend/scripts/entrypoint.sh` |
| 11 | `tests/conftest.py` 加 `pg_container` / `engine`(session) / `db_session`(per-test SAVEPOINT)三 fixture + `_run_in_thread` 隔离 alembic 同步命令 + `_wait_for_pg_ready` TCP 探活(不引 psycopg2,见 D8) | 🟢 | `backend/tests/conftest.py` |
| 12 | `tests/test_alembic.py` × 7(upgrade head / downgrade base / autogen check / 扩展 / 触发器 / CHECK / pgvector 列) | 🟢 | `backend/tests/test_alembic.py` |
| 13 | `tests/test_models_smoke.py` × 8(user+membership / case+files+report / unique 约束 / 部分索引 / CHECK 月份 / updated_at 触发器 / pgvector 距离查询 / is_mock 默认) | 🟢 | `backend/tests/test_models_smoke.py` |
| 14 | `tests/test_health_db.py` × 2(/health.db ok / 不可达时 degraded 但 HTTP 200) | 🟢 | `backend/tests/test_health_db.py` |
| 15 | README.md 加本地 Postgres docker run + alembic upgrade/downgrade/check 命令 + pytest 需 Docker 注意事项 + 目录结构更新 | 🟢 | `backend/README.md` |

## Stage 2 验收清单

完成定义(全部勾选才能转 🟢 Stage 2 完成态):

- [x] `uv run alembic upgrade head` 在本地 Postgres 上成功(13 表 + 扩展 + 触发器 + pgvector 列)
- [x] `uv run alembic downgrade base` 干净反向(只剩 `alembic_version` 表)
- [x] `uv run alembic check` 无 pending diff(ORM ↔ DDL 同步;raw SQL 索引通过 `include_object` 白名单跳过)
- [x] `uv run pytest -v` 27 用例全绿(Stage 1 × 10 + Stage 2 × 17)
- [x] `uv run ruff check .` 干净
- [x] `uv run mypy --strict app/` 干净
- [x] `/health` 扩 `checks.db`,DB 不可达时 HTTP 200 但 `data.status="degraded"`(D5 红线)
- [x] testcontainers 用 `pgvector/pgvector:pg16`(D3),per-test SAVEPOINT 隔离(D4)
- [x] alembic env 用 async pattern,**未引入 psycopg/psycopg2**(D8)
- [x] AGENT.md 注释即文档规范回填到所有 Stage 2 文件(class / def / 关键变量都有中文 docstring + WHY 注释)

## Stage 2 不做(明确推迟)

| 项 | 推到哪 |
|---|---|
| DAO / Repository / Service / 业务方法层 | Stage 4(随路由)|
| 7 个 tier Pydantic schemas + `cropReportForUser` | Stage 3 |
| 路由 stub + JWT + RBAC + LLMClient + OSS/OCR/SMS clients | Stage 4 |
| Seed(super_admin / 字典) | Stage 4(随 auth)|
| `/health` 扩 `checks.redis/oss/aoai` | Stage 4(client 落了再扩)|
| Arq worker + 队列任务 | Stage 4+ |
| CI 加 docker build / gitleaks / pip-audit / Trivy | Stage 4 |
| 归档作业(archive_old_ai_call_logs 等 cron) | Stage 4+ |

## 完成记录

> 格式:`YYYY-MM-DD #任务编号 一句话说明 / commit hash`

- 2026-05-24 #Stage1 #1-#17 FastAPI 骨架 + 信封中间件 + Request-ID + /health + 10 测试全绿 + ruff/mypy clean + 注释即文档规范落地 / commits [804c56e](.) (M4 前置文档 batch) + [b6cc5b8](.) (Stage 1 实现 batch)
- 2026-05-24 #Stage2 #1-#15 13 ORM + alembic 0001_init(单 revision 全落)+ testcontainers(pgvector/pg16)+ per-test SAVEPOINT + /health.db + 27 测试全绿(新增 17)+ ruff/mypy clean + autogen 无 diff(`include_object` 过滤 raw SQL 索引)/ commit (待补 Stage 2 commit hash)
