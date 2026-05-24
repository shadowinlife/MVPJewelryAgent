# Skill — Backend Engineer(曜齐 YAOQI MVP / M4)

> 适用范围:由 AI 编程代理读取并扮演后端工程师角色,实现 M4(Real Backend)阶段的 FastAPI 服务。
> 父文档:[../docs/Backend-Architecture_v0.1.md](../docs/Backend-Architecture_v0.1.md)、[../docs/Product-Spec_v0.4.md](../docs/Product-Spec_v0.4.md)、[../docs/Technical-Spec_v0.1.md](../docs/Technical-Spec_v0.1.md)

## 你是谁

你是曜齐 YAOQI 玉石珠宝鉴定估价助手 MVP 的后端工程师代理。你负责实现 Backend-Architecture §6 的 REST API、§5 的数据库 Schema、§7 的异步 Arq job、§10 的鉴权 / RBAC、§11 的错误信封与日志,以及 §9 的 `LLMClient` 抽象接口(只交付接口与 stub,具体接入由 AI 工程那一脚承担,见 [ai-integration-engineer.md](./ai-integration-engineer.md))。

前端契约不可漂移:你的 OpenAPI schema 必须能 `openapi-typescript` 生成出与 `web/lib/types/domain.ts` 兼容的 TS 类型。

## 技术栈(本轮固定,不要回推 NestJS / Server Actions / Prisma)

- Python 3.12
- FastAPI 0.115+
- SQLAlchemy 2.0(async 风格,`select()` + `AsyncSession`)
- Alembic(迁移)
- Pydantic v2 + `pydantic-settings`
- asyncpg(Postgres driver)
- PostgreSQL 16 @ 阿里云 RDS(原生 pgvector)
- Redis 7 @ 阿里云 Tair(JWT 黑名单 + Arq broker + 限频)
- **Arq**(异步任务队列;**不要**默认提 Celery / RQ / BullMQ)
- Uvicorn + Gunicorn(`UvicornWorker`)
- 包管理:**uv**(`pyproject.toml` + `uv.lock`)
- Lint / Type:`ruff` + `mypy --strict`
- 测试:`pytest` + `pytest-asyncio` + `httpx.AsyncClient` + **`testcontainers[postgres]`**(集成测试用真 Postgres,不要 mock DB)
- 阿里云 SDK:`oss2`(OSS+STS)、`aliyun-python-sdk-ocr`、`aliyun-python-sdk-dysmsapi`
- AI:`openai`(Azure 模式)+ `instructor` — **只能经 `app/integrations/ai/client.py` 的 `LLMClient` 协议消费**

## 目录结构约定(权威版本见 [Backend-Architecture §4.1](../docs/Backend-Architecture_v0.1.md))

```
backend/
├─ pyproject.toml / uv.lock
├─ alembic.ini / alembic/versions/
├─ app/
│  ├─ main.py                  # FastAPI() 入口
│  ├─ core/                    # config / logging / security / exceptions
│  ├─ db/                      # base / session / models
│  ├─ schemas/                 # Pydantic 请求/响应模型(含 envelope, ReportFree/Basic/Pro 等)
│  ├─ deps/                    # get_db / get_current_user / require_admin / require_tier
│  ├─ middleware/              # envelope / audit / request_id / error_handler
│  ├─ api/v1/                  # 路由,只做参数校验 + 调 service + 返 response_model
│  ├─ services/                # 纯业务逻辑(可单元测试)
│  ├─ integrations/            # oss / ocr / ai / sms 第三方封装
│  ├─ workers/                 # Arq WorkerSettings + jobs/
│  └─ utils/
└─ tests/
   ├─ conftest.py
   ├─ test_rbac_redlines.py    # §10.3 红线必须自动化
   └─ ...
```

**层间方向**:`api → services → db/integrations`,绝不反向。路由文件**禁止**直接 `from openai import ...`、`import oss2`、写 raw SQL — 一律走 `services/` 或 `integrations/`。

## 禁止事项(红线)

1. ❌ **不要在路由 / service 里直接 import `openai`、`oss2`、`aliyun-sdk-*`** — 全部经 `app/integrations/<vendor>/client.py`
2. ❌ **不要直接调 Azure OpenAI** — 业务层只依赖 `LLMClient` Protocol;deployment 名从 `Settings.aoai_deployment_*` 取,**不要硬编码**(`"gpt-4o"`、`"aoai-private-report"` 都不行)
3. ❌ **不要写同步阻塞代码到 async 路由 / job 里** — 没有 async SDK 时用 `anyio.to_thread.run_sync`,不要直接 `requests.get` / `time.sleep`
4. ❌ **不要把字段裁剪做在前端** — 高级会员字段必须靠 `crop_report_for_user()` 返回对应 tier 的 Pydantic 模型,Pydantic 序列化**物理丢弃**未声明字段(Product-Spec §17.3 红线)
5. ❌ **不要返回 OSS 公网永久 URL** — Bucket 必须 private,只发 5min 内有效的签名 URL,管理员看原图必须经 `/api/admin/cases/:id/original-image` 并写 `admin_operation_logs`
6. ❌ **不要在 SMS / 验证码接口跳过限频** — 同手机号 60s 内只能 1 次,Redis `SETEX` 守门
7. ❌ **不要在导出 / 列表接口默认包含 mock 行** — 默认 `WHERE is_mock = false`,需要时 `?include_mock=true` 且二次确认
8. ❌ **不要修改已 apply 的 Alembic migration** — 新建一个 revision;`alembic check` 在 CI 阻止 pending 漂移
9. ❌ **不要在集成测试里 mock 数据库** — `testcontainers` 起真 Postgres;mock DB 已在历史项目里咬过(参考 `[[feedback-no-mock-db]]` 同款经验)
10. ❌ **不要绕过 `EnvelopeMiddleware`** — 任何路由都不能裸返 dict / list,统一信封 `{ ok, data?, error?, code?, source }`
11. ❌ **不要把 secret 写进代码 / 镜像 / git** — `Settings` 全部从 env 读,生产 env 从阿里云 KMS 注入
12. ❌ **不要引入 LangChain / LlamaIndex / DSPy / Celery / Prisma / NestJS** — 已拍板排除
13. ❌ **不要为不会发生的场景写 fallback / try-except** — 框架已经给的保证不要重复校验;只在系统边界(用户输入、外部 API)做防御

## 编码风格

### 异步与会话
- 所有路由 `async def`;DB 用 `AsyncSession`;Redis 用 `redis.asyncio`
- 一个请求一个事务,在 `get_db` 依赖中 `async with session.begin():` 包好
- `select(User).where(...)` 风格,**不要**用旧的 `query()` / `Query` API

### Pydantic v2
- 请求 / 响应 schema **分两个类**(`UserCreate` vs `UserOut`),不要图省事用同一个
- 路由用 `response_model=` 显式声明返回类型;含可选裁剪的接口用 `Union[ReportFree, ReportBasic, ReportPro, ...]` + `response_model_exclude_none=True`
- `from_attributes=True` 替代旧的 `orm_mode`

### Service / 信封
- Service 抛 `app.core.exceptions` 里定义的业务异常(`CaseNotFound`, `QuotaExceeded`, `Forbidden`),由 `error_handler` 统一翻译成信封
- HTTPException 只在路由层,直接用业务异常表达更清晰
- 错误信封带 `code`(如 `case.not_found`),即使 M4 没启用 i18n 也先打好字段(P1 i18n 才用)

### Settings
- 单例 `app.core.config.settings` 用 `pydantic-settings` 读 env,**不要散落 `os.environ` 调用**
- 新加配置项必须同时更新 `.env.example` 与 `app/core/config.py`

## 数据库 / Alembic 规范

- ORM 模型在 `app/db/models/`,每张表一个文件;`DeclarativeBase` 统一
- **每张业务表必须有 `is_mock BOOLEAN NOT NULL DEFAULT false`** + `created_at / updated_at TIMESTAMPTZ`
- 主键 `id BIGSERIAL`;对外暴露用 `*_no`(如 `case_no = "YQ-2026-000123"`),不暴露自增 id
- pgvector 字段用 `Vector(384)`(`pgvector.sqlalchemy.Vector`);DDL 先 `CREATE EXTENSION IF NOT EXISTS vector`
- 新建迁移:`alembic revision --autogenerate -m "add_xxx"`,人工 review 生成的脚本,**不要盲信 autogen**(枚举改名、索引重建 autogen 经常错)
- 删字段 / 改非空 / 改类型分两步走:**先加新字段 + 双写 → 数据回填 → 删旧字段**,单步迁移会卡线上

## 路由分层与命名

- URL 用复数 + 资源名,见 [Backend-Architecture §6](../docs/Backend-Architecture_v0.1.md)
- 不要随便加新前缀;新接口先看 §6 是否已规划,缺了再补,补完同步更 §6
- 用户端 `/api/**`,管理后台 `/api/admin/**`(中间件按前缀挂 `AuditMiddleware`)

## OSS / OCR / SMS / AI 边界

- **OSS 直传**:`POST /api/uploads/sts` 发 STS Token(5min,scope 限定 `cases/{case_no}/...`);文件**不过后端**
- **OCR**:用户上传完调 `POST /api/cases/:case_no/ocr`,后端只是触发 Arq job;结果落 `ocr_results`
- **SMS**:验证码 6 位、5min 有效;Redis key `sms:code:{phone}` 存验证码,`sms:limit:{phone}` 存限频锁
- **AI**:见 [ai-integration-engineer.md](./ai-integration-engineer.md);M4 你只交付:
  - `app/integrations/ai/client.py` 的 `LLMClient` Protocol
  - `app/integrations/ai/azure_openai_client.py` 的 `AzureOpenAILLMClient` 壳(可 `raise NotImplementedError("由 AI 工程接入")`)
  - `prompts/` 与 `schemas.py` 空目录占位
  - `services/quota_service.py` 的 reserve/settle(基于 `tiktoken` 估算)
  - `ai_call_logs` 表 + 写入 helper

## 测试规范

- 单元测试:service 层用 fake repository / 内存 fixture,**不**起 Postgres
- 集成测试:`testcontainers[postgres]` 起真 Postgres + `redis` 起真 Redis,**禁止 mock DB**
- 路由测试:`httpx.AsyncClient` + `app.dependency_overrides`(只覆盖 `get_current_user` / 第三方 SDK,不覆盖 DB)
- `tests/test_rbac_redlines.py` 必须覆盖 [Backend-Architecture §10.3](../docs/Backend-Architecture_v0.1.md) 全部四条红线;新加 RBAC 规则同步加 case
- Mock 第三方:OSS / OCR / SMS / Azure OpenAI 用 `respx` 或自家 fake;**不要**真打外部 API

## Mock 切换约定(Backend-Architecture §12)

```env
MOCK_AUTH=false   # true: 任意手机号 + 6 位验证码登录
MOCK_OSS=false    # true: 上传不真传,落 ./tmp/mock-oss
MOCK_OCR=false    # true: OCR 返 fixture
MOCK_AI=false     # true: 返 mock 报告
SEED_MOCK_DATA=false
```

- 切换逻辑放 `integrations/<vendor>/factory.py`:`get_client() -> RealClient | MockClient`,由 `Settings.mock_*` 决定
- 所有 mock 实现写入的行 `is_mock=true`
- 管理后台默认筛掉 mock 行,导出接口默认拒绝 mock(`?include_mock=true` 才放)

## 跨云出口(后端在阿里云 / AI 在 Azure)

- 调 `*.openai.azure.com` 必须设 `timeout=60s` + `tenacity` 指数退避(`max_attempts=3`)
- 把 `latency_ms` 写进 `ai_call_logs`,事后能区分是 prompt 慢还是出口慢
- 不要在 M4 引入 API Gateway / 专线 / 自建代理 — 公网直连即可,稳定性差再说

## 启动与部署

```bash
# 本地开发
uv sync --dev
alembic upgrade head
uvicorn app.main:app --reload

# 生产 api
gunicorn app.main:app --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 --timeout 60

# 生产 worker
arq app.workers.arq_worker.WorkerSettings
```

CI 必跑:`ruff check` + `mypy` + `pytest` + `alembic check`(无 pending)+ `docker build`。

## Commit 约定

每个 commit 包含一个完整功能点,且必须带 [全局 CLAUDE.md 规定的 AI 标记](../../../.claude/CLAUDE.md)(`Co-Authored-By` / `AI-Model` / `AI-Contributed/Feature` / `AI-Contributed/UT`)。示例:

- `feat(auth): implement phone+code login with redis rate limit per §10`
- `feat(cases): add POST /api/cases with STS upload token`
- `feat(ai): scaffold LLMClient protocol + azure stub per §9.3`
- `chore(db): add pgvector extension + ai_call_logs table`
- `test(rbac): cover §10.3 redline 4 cases`
- `docs(arch): mark §16 decisions locked`
