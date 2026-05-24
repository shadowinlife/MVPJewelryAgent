# 曜齐 YAOQI 后端架构设计 v0.1

> 设计文档(非实现)。对应 [Product-Spec_v0.4](./Product-Spec_v0.4.md)、[UI-Spec_v0.3.1](./UI-Spec_v0.3.1.md)、[Technical-Spec_v0.1](./Technical-Spec_v0.1.md),并兼容 [`web/`](../web) 已实现的 Mock 路由契约。
> 目标:让 M4 真后端可以"前端零改动"接入。
>
> **技术栈拍板(2026-05-22):FastAPI (Python)**。理由:核心资产是 OpenAI 上的私有调整模型与 LLM 工程链路,Python 生态(LangChain / instructor / HuggingFace / pandas)与 AI 资产同语种,避免跨语言搬运。

更新时间:2026-05-22

---

## 1. 设计目标与约束

### 1.1 必达目标(对应 Product-Spec §3.3 Level 3 业务闭环)

1. 用户可真实登录、上传、生成报告并查看历史
2. 文件入项目方私有 OSS,前端不暴露永久 URL
3. AI / OCR 调用在后端统一,密钥不下放
4. 会员等级裁剪在后端完成,高级字段不出库
5. 管理后台可读写、可复核、可导出
6. 所有核心数据可备份、可导出、可迁移

### 1.2 红线(必须由架构而非业务代码兜底)

| 红线 | 落到架构哪一层(FastAPI) |
|---|---|
| 高级字段不下发低权限用户 | Pydantic `response_model` + `crop_report_for_user()` 服务;高级字段定义在独立 schema,按 tier 选择导出 |
| 客户简洁版不生成公开链接 | 该路由强制 `Depends(get_current_user)`;响应模型固定为 `CustomerBriefOut`(字段白名单) |
| OSS 不公开读 | Bucket ACL = private;访问统一走 `/api/files/:id/signed-url`,内部签 STS;Policy 硬编码 `key prefix = user-upload-*/{me.user_id}/` |
| Mock 不混入正式数据 | 所有表带 `is_mock` 列;Service 层根据 `MOCK_*` 设置读 `app.core.settings` 分支 |
| 管理员原图/导出留痕 | 所有 `/api/admin/**` 路由通过 `AuditMiddleware`(或 `Depends(audit_log)`)异步写 `admin_operation_logs` |

### 1.3 非目标(本期不做)

微服务、Kubernetes、多云、IM、支付、复杂订阅、公开分享链接、社区。

---

## 2. 技术栈选型(已拍板)

### 2.1 选型表(FastAPI + Python 主线)

| 层 | 技术 | 版本 | 理由 |
|---|---|---|---|
| 框架 | **FastAPI** | 0.115+ | 异步原生(与 OpenAI / 阿里云 OCR HTTP 调用搭),Pydantic v2 响应模型天然做字段白名单/裁剪,自动生成 OpenAPI 3.1 → 前端 codegen |
| 语言 | **Python** | 3.12 | 与 AI/微调/RAG 资产同语种 |
| ASGI | **Uvicorn** + **Gunicorn**(worker_class=`UvicornWorker`) | 最新稳定 | Gunicorn 管 worker 重启 + 信号,Uvicorn 跑事件循环 |
| ORM | **SQLAlchemy 2.0**(async)+ **Alembic** | 2.0+ / 1.13+ | 异步 session 与 FastAPI Depends 适配;Alembic 迁移成熟 |
| 校验/序列化 | **Pydantic v2** | 2.x | 输入校验 + 响应模型(`response_model_exclude_none/exclude_unset`)做字段裁剪 |
| DB 驱动 | `asyncpg` | 最新 | Postgres 异步驱动 |
| DB | **PostgreSQL** | 16 | 报告/OCR/AI 输出半结构化 JSON,`jsonb` + GIN 优于 MySQL |
| 队列 | **Arq**(主推)或 **Celery 5**(备选) | Arq 最新 / Celery 5.4+ | Arq 异步原生、与 FastAPI 同事件循环;Celery 生态老更成熟但同步模型有点格格不入。本期推荐 **Arq** |
| 队列底层 | **Redis** | 7 | Arq/Celery broker + 缓存 + Session 共用 |
| 缓存 | `redis-py`(async) | 5.x | Session blacklist / 验证码 / 签名 URL 缓存 |
| 文件 | 阿里云 OSS 私有 Bucket + STS | `oss2` SDK | Product-Spec §8.3 数据资产归属硬要求 |
| OCR | 阿里云 OCR(证书类)+ GPT-4o vision 兜底 | `aliyun-python-sdk-ocr` | Technical-Spec §1.6 |
| AI | **Azure OpenAI Service**(唯一 LLM 提供方)+ **instructor**(结构化输出强校验) | `openai` 1.x(Azure 模式)+ `instructor` 1.x | 私调模型以 Azure OpenAI deployment 形式发布;后端代码不直接调 SDK,而是经 `LLMClient` 抽象接口 — M4 只**预留接口**,真正接入由 AI 工程那一脚实现(详见 §9) |
| AI 工程链 | 不引入 LangChain / LlamaIndex / DSPy | - | 裸 `LLMClient` 抽象 + instructor 已足够 MVP;框架的抽象在生产里多半要扒开重写 |
| 知识库/向量 | **pgvector** 扩展(挂在同库) | 0.7+ | MVP 阶段 RAG 用 Postgres + pgvector,不另起 Milvus/Qdrant |
| 短信 | 阿里云短信 | `aliyun-python-sdk-dysmsapi` | 国内合规 |
| 鉴权 | HTTP-only Cookie + JWT | `pyjwt` + `passlib[bcrypt]` + `itsdangerous`(cookie 签名)| Short-lived JWT(7d 用户 / 12h 管理员)+ Redis 黑名单 |
| 配置 | **pydantic-settings** | 2.x | `.env` → 强类型 Settings 对象 |
| 日志 | **structlog** + `python-json-logger` | 最新 | JSON 结构化日志,便于后续接 ES/Loki |
| 限流 | `slowapi`(基于 Redis) | 最新 | 短信验证码 / 登录限频 |
| 测试 | **pytest** + `pytest-asyncio` + `httpx`(ASGI client)+ `factory-boy` | - | 异步测试 + 越权红线自动化 |
| 包管理 | **uv**(主推)或 Poetry | 最新 | uv 速度极快,锁文件 `uv.lock` 适合 CI/CD |
| 容器 | Docker + multi-stage | - | 同一镜像跑 api / worker / cron(`CMD` 区分) |
| 部署 | 阿里云 ECS + Nginx(反代 + TLS) | - | Product-Spec §8.3 一切归项目方账号 |

### 2.2 排除方案(已驳回,不要再回推)

- **NestJS / Node.js 单体**:Python 生态与 AI 资产同语种的优势更重要
- **Next.js Server Actions / Route Handlers 充当后端**:无法承载长任务队列与 Admin 规模

### 2.3 已知代价与对策

| 代价 | 对策 |
|---|---|
| 前端 TS 类型不能直接共享 Python 类 | FastAPI 自动产出 OpenAPI 3.1;前端用 `openapi-typescript` 生成 `web/lib/types/api.ts`,CI 检查 `web/lib/types/domain.ts` 与 codegen 一致(详见 §14.2) |
| Python GIL 限制 CPU 并行 | I/O bound 业务用 `async def`;CPU bound(图片处理/水印)走队列 worker,实在不够再用 `concurrent.futures.ProcessPoolExecutor` |
| `oss2` SDK 是同步的 | 在 worker 里直接用;HTTP 路径需要时套 `asyncio.to_thread()` |

---

## 3. 架构总览

### 3.1 部署拓扑

```text
                     ┌──────────────────┐
                     │  Browser / 手机   │
                     └────────┬──────────┘
                              │ HTTPS
                  ┌───────────▼────────────┐
                  │  Nginx (TLS, 静态)      │
                  └─┬──────────────────┬───┘
                    │                  │
        ┌───────────▼────┐    ┌────────▼─────────┐
        │ Next.js Web    │    │ NestJS API       │
        │ (SSR + 静态)   │◄──►│ (用户端 + 管理端)│
        └─────────┬──────┘    └────────┬─────────┘
                  │                    │
                  │     ┌──────────────┼───────────────┐
                  │     │              │               │
            ┌─────▼─────▼─────┐  ┌─────▼──────┐  ┌─────▼──────┐
            │ PostgreSQL 16   │  │ Redis 7    │  │ BullMQ      │
            │  + pgbackrest   │  │ (Session/  │  │ Worker      │
            └─────────────────┘  │  Queue)    │  │ (NestJS同代码) │
                                 └────────────┘  └────┬───────┘
                                                      │
                       ┌──────────────────────────────┼────────────────────┐
                       │                              │                    │
                ┌──────▼──────┐               ┌───────▼────────┐    ┌──────▼──────┐
                │ 阿里云 OSS   │               │ 阿里云 OCR     │    │ OpenAI API │
                │ 私有 Bucket  │               │                │    │            │
                └─────────────┘               └────────────────┘    └────────────┘
```

### 3.2 进程模型

| 进程 | 实例数 | 职责 |
|---|---|---|
| `api` | 2(双副本) | Gunicorn + Uvicorn workers(每副本 4 workers);HTTP 请求,**禁止**同步执行 OCR/AI |
| `worker` | 1~2 | Arq worker 进程,消费 `ocr.run` / `ai.generate` / `image.process` 队列;复用同一代码库 |
| `cron` | 1 | Arq scheduler(`cron_jobs=[...]`)或 systemd timer 触发的脚本:配额重置(Token 月配额)、签名 URL 清理、备份触发 |

---

## 4. 分层架构

### 4.1 目录结构(FastAPI / Python)

```text
backend/
├─ pyproject.toml              # uv / poetry
├─ uv.lock
├─ alembic.ini
├─ alembic/
│  ├─ env.py
│  └─ versions/                # 迁移脚本
├─ app/
│  ├─ main.py                  # FastAPI() 入口,挂 routers/middlewares
│  ├─ core/
│  │  ├─ config.py             # pydantic-settings: Settings
│  │  ├─ logging.py            # structlog 初始化
│  │  ├─ security.py           # JWT 编解码、密码哈希
│  │  └─ exceptions.py         # 业务异常 + handler
│  ├─ db/
│  │  ├─ base.py               # SQLAlchemy DeclarativeBase
│  │  ├─ session.py            # async_engine, AsyncSession
│  │  └─ models/               # ORM 模型(对应 §5 表)
│  │     ├─ user.py
│  │     ├─ membership.py
│  │     ├─ case.py
│  │     ├─ case_file.py
│  │     ├─ ocr_result.py
│  │     ├─ ai_report.py
│  │     └─ ...
│  ├─ schemas/                 # Pydantic 输入/输出模型
│  │  ├─ envelope.py           # ApiResponse[T] 统一信封
│  │  ├─ user.py
│  │  ├─ case.py
│  │  ├─ report.py             # ReportFree / ReportBasic / ReportPro ...(按 tier 分模型)
│  │  └─ ...
│  ├─ deps/                    # FastAPI Depends 工厂
│  │  ├─ db.py                 # get_db -> AsyncSession
│  │  ├─ auth.py               # get_current_user / require_admin
│  │  ├─ rbac.py               # require_tier(min="pro")
│  │  └─ rate_limit.py
│  ├─ middleware/
│  │  ├─ envelope.py           # 统一响应信封
│  │  ├─ audit.py              # /api/admin/** 写 admin_operation_logs
│  │  ├─ request_id.py
│  │  └─ error_handler.py
│  ├─ api/
│  │  └─ v1/
│  │     ├─ __init__.py        # api_router = APIRouter(prefix="/api")
│  │     ├─ auth.py            # /api/auth/**
│  │     ├─ cases.py           # /api/cases/**
│  │     ├─ files.py           # /api/files/** + /api/uploads/**
│  │     ├─ ocr.py             # /api/cases/:id/ocr/**
│  │     ├─ reports.py         # /api/reports/** + /api/customer-brief/**
│  │     ├─ memberships.py
│  │     └─ admin/
│  │        ├─ users.py
│  │        ├─ cases.py
│  │        ├─ status.py
│  │        ├─ knowledge.py
│  │        ├─ imports.py
│  │        ├─ logs.py
│  │        └─ exports.py
│  ├─ services/                # 纯业务逻辑(被 routes 调用)
│  │  ├─ case_service.py
│  │  ├─ report_service.py     # crop_report_for_user(report, tier)
│  │  ├─ quota_service.py      # 月配额预占 / 回滚
│  │  ├─ membership_service.py
│  │  └─ audit_service.py
│  ├─ integrations/            # 第三方 SDK 封装
│  │  ├─ oss/                  # 阿里云 OSS(oss2 + STS)
│  │  ├─ ocr/                  # 阿里云 OCR
│  │  ├─ ai/                   # OpenAI + instructor + prompt 模板
│  │  │  ├─ client.py
│  │  │  ├─ prompts/
│  │  │  │  ├─ report_v1.md
│  │  │  │  └─ ocr_correct_v1.md
│  │  │  └─ schemas.py         # instructor 用的 Pydantic 响应模型
│  │  └─ sms/                  # 阿里云短信
│  ├─ workers/
│  │  ├─ arq_worker.py         # WorkerSettings: functions=[...], cron_jobs=[...]
│  │  └─ jobs/
│  │     ├─ image_process.py   # 预览/水印
│  │     ├─ ocr_run.py
│  │     ├─ ai_generate.py
│  │     ├─ import_markdown.py
│  │     └─ export_build.py
│  └─ utils/
└─ tests/
   ├─ conftest.py              # AsyncClient + 数据库 fixture
   ├─ test_auth.py
   ├─ test_cases.py
   ├─ test_rbac_redlines.py    # 越权红线(§10.3)
   └─ ...
```

### 4.2 三大横切兜底(FastAPI 实现)

#### 1) 响应信封 `EnvelopeMiddleware`(或 `JSONResponse` 子类)

所有路由返回前包成 `{ ok, data?, error?, source }`,与前端 `ApiResponse<T>` 完全兼容(`web/lib/types/domain.ts:153`)。

实现路线:在 `main.py` 注册全局 `Middleware`,或写一个 `EnvelopeJSONResponse(JSONResponse)` 类做默认 `response_class`。**推荐前者**,可与 `exception_handler` 共享逻辑。

#### 2) 报告字段裁剪(路由级)

不做"通用拦截器",而是**用 Pydantic response_model 按 tier 分模型**:

```python
# schemas/report.py
class ReportFree(BaseModel):
    materialHint: str
    risk: str
    needReinspect: bool

class ReportBasic(ReportFree):
    priceRange: str
    liquidity: str

class ReportPro(ReportBasic):
    recyclePrice: str
    fullRisk: list[str]
# ... business / business_pro

# api/v1/reports.py
@router.get("/reports/{case_id}")
async def get_report(case_id: str, user=Depends(get_current_user)):
    raw = await report_service.load(case_id)
    return crop_report_for_user(raw, user.membership)  # 返回 Union[ReportFree, ...]
```

服务层 `crop_report_for_user()` 必须**返回对应 tier 的模型实例**,Pydantic 序列化时**物理丢弃**未声明字段。前端无法靠抓包绕过。

#### 3) `AuditMiddleware`(`/api/admin/**`)

ASGI middleware,匹配 path 前缀,请求成功(2xx)后投递一个 `audit.write` job 到 Arq(异步,不阻塞响应),包含 actor、action、target、IP、UA、入参 diff(脱敏)。

> 不用 sync 写库以避免拖慢响应;失败靠 worker 重试。

---

## 5. 数据库 Schema(DDL 草案)

> 基于 Technical-Spec §5,补全索引、外键、约束、Mock 标识、配额账户。
> 命名规约:snake_case,主键 `id BIGSERIAL`,时间戳 `*_at TIMESTAMPTZ`,所有面向用户的 ID 对外暴露 `*_no`(如 `case_no = "YQ-2026-000123"`)以避免遍历。

### 5.1 用户与会员

```sql
-- users
CREATE TABLE users (
  id              BIGSERIAL PRIMARY KEY,
  phone           VARCHAR(20) UNIQUE NOT NULL,
  phone_verified_at TIMESTAMPTZ,
  wechat_openid   VARCHAR(64) UNIQUE,
  wechat_unionid  VARCHAR(64),
  nickname        VARCHAR(64),
  avatar_url      TEXT,
  role            VARCHAR(20) NOT NULL DEFAULT 'free_user',
                  -- guest | free_user | member_basic | member_pro
                  -- business | business_pro | admin | super_admin
  status          VARCHAR(20) NOT NULL DEFAULT 'active',  -- active | disabled
  is_mock         BOOLEAN NOT NULL DEFAULT false,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_login_at   TIMESTAMPTZ
);
CREATE INDEX idx_users_role ON users(role) WHERE status = 'active';

-- memberships(独立表,允许历史变更)
CREATE TABLE memberships (
  id                  BIGSERIAL PRIMARY KEY,
  user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  tier                VARCHAR(20) NOT NULL,   -- free | basic | pro | business | business_pro
  started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at          TIMESTAMPTZ,
  granted_by_admin_id BIGINT REFERENCES users(id),
  grant_reason        TEXT,
  is_current          BOOLEAN NOT NULL DEFAULT true,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX uq_membership_current
  ON memberships(user_id) WHERE is_current;

-- token_quotas(每自然月一行,与 memberships.json.tokenPolicy 对齐)
CREATE TABLE token_quotas (
  id              BIGSERIAL PRIMARY KEY,
  user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  period_yyyymm   INTEGER NOT NULL,        -- e.g. 202605
  tokens_total    INTEGER NOT NULL,
  tokens_used     INTEGER NOT NULL DEFAULT 0,
  reports_total   INTEGER NOT NULL,
  reports_used    INTEGER NOT NULL DEFAULT 0,
  admin_extra     INTEGER NOT NULL DEFAULT 0,  -- 管理员临时加量
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, period_yyyymm)
);
```

### 5.2 案例与文件

```sql
-- cases
CREATE TABLE cases (
  id               BIGSERIAL PRIMARY KEY,
  case_no          VARCHAR(32) UNIQUE NOT NULL,    -- YQ-2026-000123
  user_id          BIGINT NOT NULL REFERENCES users(id),
  title            VARCHAR(120) NOT NULL,
  category         VARCHAR(40) NOT NULL,           -- 翡翠手镯/和田玉/钻石…
  sub_category     VARCHAR(40),
  purpose          VARCHAR(20) NOT NULL,           -- 购买/出售/回收/法拍/学习/直播选品/客户咨询/商业选品
  source_channel   VARCHAR(40),
  status           VARCHAR(20) NOT NULL DEFAULT 'draft',
                   -- draft | pending | analyzing | analyzed | pending_recheck | archived
  risk_level       VARCHAR(10),                    -- low | medium | high
  liquidity_level  VARCHAR(20),
  material_guess   VARCHAR(40),
  quality_level    VARCHAR(20),
  -- 物理尺寸
  weight_text      VARCHAR(40),
  dimensions       VARCHAR(80),
  bead_size        VARCHAR(40),
  ring_size        VARCHAR(40),
  -- 证书
  certificate_org  VARCHAR(40),
  certificate_no   VARCHAR(64),
  -- 价格(全部数字,保留 cents 防浮点)
  purchase_price_cents       BIGINT,
  asking_price_cents         BIGINT,
  auction_start_price_cents  BIGINT,
  deal_price_cents           BIGINT,
  expected_price_cents       BIGINT,
  -- 文本
  seller_text      TEXT,
  user_note        TEXT,
  admin_note       TEXT,
  -- 意向
  sell_intent          BOOLEAN NOT NULL DEFAULT false,
  recycle_intent       BOOLEAN NOT NULL DEFAULT false,
  consignment_intent   BOOLEAN NOT NULL DEFAULT false,
  -- 来源
  data_source      VARCHAR(20) NOT NULL DEFAULT 'real',  -- real | import | mock
  is_mock          BOOLEAN NOT NULL DEFAULT false,
  -- 时间
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  archived_at      TIMESTAMPTZ
);
CREATE INDEX idx_cases_user ON cases(user_id, updated_at DESC);
CREATE INDEX idx_cases_status ON cases(status) WHERE status IN ('pending','analyzing','pending_recheck');
CREATE INDEX idx_cases_intents ON cases(user_id) WHERE sell_intent OR recycle_intent OR consignment_intent;
CREATE INDEX idx_cases_search ON cases USING GIN (to_tsvector('simple', coalesce(title,'') || ' ' || coalesce(seller_text,'')));

-- case_files
CREATE TABLE case_files (
  id                 BIGSERIAL PRIMARY KEY,
  case_id            BIGINT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
  user_id            BIGINT NOT NULL REFERENCES users(id),
  file_type          VARCHAR(40) NOT NULL,    -- jewelry_natural_light/certificate/...
  original_filename  TEXT,
  mime_type          VARCHAR(80),
  size_bytes         BIGINT,
  oss_bucket         VARCHAR(80) NOT NULL,
  oss_key_original   TEXT NOT NULL,
  oss_key_preview    TEXT,
  oss_key_watermarked TEXT,
  width              INTEGER,
  height             INTEGER,
  upload_status      VARCHAR(20) NOT NULL DEFAULT 'pending',
                     -- pending | uploaded | processing | ready | failed
  is_private         BOOLEAN NOT NULL DEFAULT true,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_case_files_case ON case_files(case_id);
```

### 5.3 OCR / AI / 报告

```sql
-- ocr_results(每次识别一行,允许重跑)
CREATE TABLE ocr_results (
  id               BIGSERIAL PRIMARY KEY,
  case_id          BIGINT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
  file_id          BIGINT NOT NULL REFERENCES case_files(id),
  provider         VARCHAR(30) NOT NULL,        -- aliyun_ocr | openai_vision | manual
  raw_text         TEXT,
  parsed_json      JSONB,                       -- 抽取的结构化字段
  user_corrected_json JSONB,
  confidence_level VARCHAR(10),
  status           VARCHAR(20) NOT NULL,        -- pending | running | succeeded | succeeded_low_conf | failed | skipped
  error_message    TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ai_reports(每个 case 可有多版本,user_visible 按会员级生成多份)
CREATE TABLE ai_reports (
  id                       BIGSERIAL PRIMARY KEY,
  case_id                  BIGINT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
  user_id                  BIGINT NOT NULL REFERENCES users(id),
  report_type              VARCHAR(20) NOT NULL,
                           -- internal_full | user_visible | customer_simple | admin_reviewed
  model_name               VARCHAR(60),
  prompt_version           VARCHAR(20),
  input_summary_json       JSONB,
  output_json              JSONB,           -- 结构化报告(material/risk/price/...)
  full_markdown            TEXT,
  user_visible_markdown    TEXT,
  customer_simple_markdown TEXT,
  price_fields_json        JSONB,           -- 隔离价格相关字段方便裁剪
  risk_fields_json         JSONB,
  status                   VARCHAR(20) NOT NULL DEFAULT 'pending',
  error_message            TEXT,
  created_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ai_reports_case_latest
  ON ai_reports(case_id, report_type, created_at DESC);

-- ai_call_logs
CREATE TABLE ai_call_logs (
  id                 BIGSERIAL PRIMARY KEY,
  user_id            BIGINT REFERENCES users(id),
  case_id            BIGINT REFERENCES cases(id),
  task_type          VARCHAR(40) NOT NULL,   -- report_generate | ocr_correct | image_summary
  model_name         VARCHAR(60),
  input_token_count  INTEGER,
  output_token_count INTEGER,
  cost_estimate_cents BIGINT,
  status             VARCHAR(20) NOT NULL,    -- success | failed | timeout
  error_message      TEXT,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ai_call_logs_user ON ai_call_logs(user_id, created_at DESC);
CREATE INDEX idx_ai_call_logs_failed ON ai_call_logs(created_at DESC) WHERE status <> 'success';
```

### 5.4 管理与运维

```sql
-- admin_reviews(人工复核)
CREATE TABLE admin_reviews (
  id                       BIGSERIAL PRIMARY KEY,
  case_id                  BIGINT NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
  admin_id                 BIGINT NOT NULL REFERENCES users(id),
  review_status            VARCHAR(20) NOT NULL,  -- approved | needs_more_photos | needs_recheck | rejected
  manual_material_judgment TEXT,
  manual_price_opinion     TEXT,
  manual_risk_note         TEXT,
  follow_up_status         VARCHAR(30),
  created_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- admin_operation_logs
CREATE TABLE admin_operation_logs (
  id           BIGSERIAL PRIMARY KEY,
  admin_id     BIGINT NOT NULL REFERENCES users(id),
  action       VARCHAR(40) NOT NULL,       -- view_original_image | export_cases | update_membership | ...
  target_type  VARCHAR(40),
  target_id    BIGINT,
  detail_json  JSONB,
  ip_address   INET,
  user_agent   TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_admin_logs_admin ON admin_operation_logs(admin_id, created_at DESC);

-- knowledge_files
CREATE TABLE knowledge_files (
  id                    BIGSERIAL PRIMARY KEY,
  title                 VARCHAR(160) NOT NULL,
  file_type             VARCHAR(40) NOT NULL,
                        -- personal_case | market_observation | auction_rule
                        -- gb_certificate_sop | live_sales_script | other
  oss_key               TEXT NOT NULL,
  original_filename     TEXT,
  parsed_status         VARCHAR(20) NOT NULL DEFAULT 'pending',
  parsed_json           JSONB,
  enabled               BOOLEAN NOT NULL DEFAULT true,
  uploaded_by_admin_id  BIGINT NOT NULL REFERENCES users(id),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- import_jobs(历史 Markdown 案例导入)
CREATE TABLE import_jobs (
  id                    BIGSERIAL PRIMARY KEY,
  file_id               BIGINT REFERENCES knowledge_files(id),
  job_type              VARCHAR(40) NOT NULL,
  status                VARCHAR(20) NOT NULL DEFAULT 'pending',
  total_count           INTEGER NOT NULL DEFAULT 0,
  success_count         INTEGER NOT NULL DEFAULT 0,
  error_count           INTEGER NOT NULL DEFAULT 0,
  error_detail_json     JSONB,
  created_by_admin_id   BIGINT NOT NULL REFERENCES users(id),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- sms_codes(短信验证码)
CREATE TABLE sms_codes (
  id           BIGSERIAL PRIMARY KEY,
  phone        VARCHAR(20) NOT NULL,
  code_hash    VARCHAR(128) NOT NULL,       -- 不存明文
  purpose      VARCHAR(20) NOT NULL,        -- login | bind | reset
  expires_at   TIMESTAMPTZ NOT NULL,
  consumed_at  TIMESTAMPTZ,
  attempts     SMALLINT NOT NULL DEFAULT 0,
  ip_address   INET,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_sms_codes_phone_active
  ON sms_codes(phone, expires_at) WHERE consumed_at IS NULL;
```

### 5.5 备份与导出

- `pgbackrest` 每日全量 + 增量
- OSS 生命周期:`/system-temp/*` 7 天清理;`/user-upload-original/*` 永久 + 跨区域复制
- 导出走 §6.6 `/api/admin/export/*`,Excel 由后端流式生成,大表 > 10w 行走异步 job

---

## 6. API 详细清单

### 6.0 通用约定

| 项 | 约定 |
|---|---|
| Base URL | `/api`(与前端 mock 路由完全一致,M4 迁移不改前端) |
| 信封 | `{ ok: boolean, data?: T, error?: string, source: "real" \| "mock" \| "import" }` |
| 鉴权 | HTTP-only Cookie `yq_session`(用户端) + `yq_admin`(管理端) |
| RBAC | Header 无需特殊,Cookie 内 JWT 含 `role` + `tier` |
| Mock | 设 `MOCK_<MODULE>=true` 时返回 `source: "mock"`,不打外部服务 |
| 错误码 | HTTP 状态码 + `error` 中文短句;详细机读码可加 `code` 字段 |
| 列表分页 | `?page=1&size=20`,响应附 `{ data, total, page, size }` |

> 标注:**A** = 需用户登录,**M** = 需管理员登录,**P** = 公开(也允许游客),**裁剪** = 服务端按会员级裁字段。

### 6.1 Auth(`/api/auth`)

| Method | Path | Auth | 说明 |
|---|---|---|---|
| POST | `/auth/send-code` | P | 发短信验证码;限频(单号 60s / 单 IP 5 次/min) |
| POST | `/auth/login` | P | 手机号+验证码登录;**沿用现有 mock 路径**(`/api/auth/login` 已存在) |
| POST | `/auth/wechat-login` | P | 微信扫码;**P1** |
| POST | `/auth/admin-login` | P | 管理员账密;限频 + 失败计数 |
| POST | `/auth/logout` | A/M | 清 cookie |
| GET  | `/auth/me` | P | 返回 `{ user: User \| null, admin: { username } \| null }`,与现有 mock 完全一致 |

请求示例:

```json
POST /api/auth/login
{ "phone": "13800000001", "otp": "123456" }
→ 200 { ok: true, data: User, source: "real" }
```

### 6.2 用户案例(`/api/cases`)

| Method | Path | Auth | 说明 |
|---|---|---|---|
| GET | `/cases?purpose=&risk=&status=&q=&page=&size=` | A | 仅返回当前用户名下案例;支持搜索/筛选 |
| POST | `/cases` | A | 创建草稿;返回 `case_no` |
| GET | `/cases/:id` | A | 权限:`user_id = me`;否则 403 |
| PATCH | `/cases/:id` | A | 编辑可改字段(title/category/purpose/...);`status` 流转用专用接口 |
| POST | `/cases/:id/submit` | A | draft → pending,触发流水线(队列 `image.process` + `ocr.run` + `ai.generate`) |
| POST | `/cases/:id/regenerate` | A | analyzed → 重跑 AI(扣配额) |
| POST | `/cases/:id/archive` | A | 归档 |
| DELETE | `/cases/:id` | A | 软删(`deleted_at`);7 天后 worker 真删 |

### 6.3 文件上传(`/api/files` + `/api/uploads`)

| Method | Path | Auth | 说明 |
|---|---|---|---|
| POST | `/uploads/presign` | A | body: `{ case_id, file_type, mime, size }` → 返回 STS Token 或 Server-side 签名 URL,前端直传 OSS |
| POST | `/uploads/complete` | A | body: `{ case_id, oss_key, file_type, width, height }` → 写 `case_files`,投递 `image.process` 队列(生成预览图+水印图) |
| GET | `/files/:id/signed-url` | A | 校验"文件属于当前用户" → 返回水印图签名 URL(默认 5 分钟有效) |
| GET | `/files/:id/preview-url` | A | 同上,但允许选 `?variant=preview`(尺寸更小) |
| GET | `/admin/files/:id/original-url` | M | 管理员看原图;**强制写 audit log** |
| DELETE | `/files/:id` | A | 软删 |

### 6.4 OCR(`/api/cases/:id/ocr` + `/api/ocr`)

| Method | Path | Auth | 说明 |
|---|---|---|---|
| GET | `/cases/:id/ocr` | A | 查询当前案例最新一次 OCR 结果(包括 status);**沿用现有 mock 路径 `/api/ocr/:caseId`,**M4 迁移时通过 Nginx rewrite |
| POST | `/cases/:id/ocr/start` | A | 投递 `ocr.run` 队列;async,返回 `{ jobId, status: "running" }` |
| PATCH | `/cases/:id/ocr/correct` | A | 用户修正字段;写 `user_corrected_json` |
| POST | `/cases/:id/ocr/skip` | A | 标 `status=skipped`,允许进入下一步 |

### 6.5 报告(`/api/reports` + `/api/customer-brief`)

| Method | Path | Auth | 说明 |
|---|---|---|---|
| POST | `/cases/:id/reports/generate` | A | 投递 `ai.generate`;扣 Token 配额预占,失败回滚 |
| GET | `/reports/:caseId` | A,**裁剪** | **沿用现有 mock 路径**;后端按 `user.membership` 调 `cropReportForUser`,只下发该等级允许字段;支持 `?as=basic` 让管理员预览其它级别 |
| GET | `/customer-brief/:caseId` | A,白名单 | **沿用现有 mock 路径**;只返回 `CustomerBrief`(`web/lib/types/domain.ts:91`);**不生成公开 URL**(不允许任何 `?token=` 形式的免登访问) |
| POST | `/cases/:id/reports/regenerate` | A | 同 generate,版本号 +1 |

### 6.6 会员(`/api/memberships`)

| Method | Path | Auth | 说明 |
|---|---|---|---|
| GET | `/memberships` | P | 返回 5 档 tier 定义(沿用 `memberships.json` 结构) |
| GET | `/me/quota` | A | 当月 token + report 配额使用情况 |

### 6.7 管理后台(`/api/admin`)

| Method | Path | Auth | 说明 |
|---|---|---|---|
| GET | `/admin/status` | M | 各模块接入状态(real/mock/pending);**沿用现有 mock 路径** |
| GET | `/admin/metrics` | M | 工作台数字(总用户/今日新增/待复核/失败计数...) |
| GET | `/admin/users?page=&size=&q=&tier=&status=` | M | 用户列表;**沿用现有 mock 路径** |
| GET | `/admin/users/:id` | M | 用户详情 + 案例计数 + 当前配额 |
| PATCH | `/admin/users/:id` | M | 改 role / status / nickname |
| POST | `/admin/users/:id/membership` | M | 设置会员等级 + 到期 + 备注(写 `memberships` 历史) |
| POST | `/admin/users/:id/quota` | M | 临时加 Token / Report 配额(写 `token_quotas.admin_extra`) |
| GET | `/admin/cases?page=&filters...` | M | 全量案例,可按 `data_source` / `is_mock` 筛选 |
| GET | `/admin/cases/:id` | M | 全字段(含 admin_note / 内部价格) |
| PATCH | `/admin/cases/:id` | M | 改 status / admin_note / risk_level |
| POST | `/admin/cases/:id/review` | M | 提交人工复核(写 `admin_reviews`) |
| GET | `/admin/cases/:id/files/:fileId/original-url` | M | 看原图,audit |
| GET | `/admin/knowledge-files` | M | 列表 |
| POST | `/admin/knowledge-files` | M | 上传(multipart),投递解析 job |
| PATCH | `/admin/knowledge-files/:id` | M | 改 enabled/title |
| DELETE | `/admin/knowledge-files/:id` | M | 软删 |
| POST | `/admin/import-jobs` | M | 上传 Markdown 历史案例,触发解析 |
| GET | `/admin/import-jobs/:id` | M | 解析进度 + 异常清单 |
| POST | `/admin/import-jobs/:id/confirm` | M | 解析结果确认入库 |
| GET | `/admin/logs/ai?status=failed` | M | AI 失败日志 |
| GET | `/admin/logs/ocr?status=failed` | M | OCR 失败日志 |
| GET | `/admin/logs/operations?admin_id=&action=` | M | 管理员操作日志 |
| POST | `/admin/export/users` | M | 异步 job,完成后通过 `GET /admin/export/jobs/:id` 拿下载签名 URL;**二次确认**(body 须含 `confirm: true`) |
| POST | `/admin/export/cases` | M | 同上;字段按 Technical-Spec §11.2 |
| POST | `/admin/export/leads` | M | 同上;筛 `sell_intent OR recycle_intent` |
| POST | `/admin/export/failures` | M | AI/OCR 失败记录 |
| GET | `/admin/export/jobs/:id` | M | 导出任务状态 + 下载 URL |

### 6.8 系统(可选)

| Method | Path | Auth | 说明 |
|---|---|---|---|
| GET | `/health` | P | liveness/readiness |
| GET | `/admin/system/integrations` | M | 各第三方连通性自检 |

### 6.9 与现有 Mock 路由对照

| 当前 Mock 路由 | M4 后端路由 | 是否需 rewrite |
|---|---|---|
| `GET /api/cases` | `GET /api/cases` | 否 |
| `GET /api/cases/:id` | `GET /api/cases/:id` | 否 |
| `GET /api/reports/:caseId` | `GET /api/reports/:caseId` | 否 |
| `GET /api/customer-brief/:caseId` | `GET /api/customer-brief/:caseId` | 否 |
| `GET /api/ocr/:caseId` | `GET /api/cases/:caseId/ocr` | **是**(Nginx `rewrite ^/api/ocr/(.+)$ /api/cases/$1/ocr last;`) |
| `GET /api/memberships` | `GET /api/memberships` | 否 |
| `GET /api/admin/status` | `GET /api/admin/status` | 否 |
| `GET /api/admin/users` | `GET /api/admin/users` | 否 |
| `POST /api/auth/login` | `POST /api/auth/login` | 否 |
| `POST /api/auth/admin-login` | `POST /api/auth/admin-login` | 否 |
| `POST /api/auth/logout` | `POST /api/auth/logout` | 否 |
| `GET /api/auth/me` | `GET /api/auth/me` | 否 |

**结论:11/12 路由零改动,只有 OCR 一条需 rewrite**(M4 可选择反向适配 mock 路径)。

---

## 7. 异步队列(Arq)

### 7.1 队列定义

| 任务函数 | 触发 | 平均耗时 | 重试 | 备注 |
|---|---|---|---|---|
| `image_process` | upload/complete 后 enqueue | 5~15s | 3 次,指数退避 | 用 Pillow + 阿里云 OSS `image/resize` 处理参数生成 preview;水印 Pillow 合成上传回 OSS |
| `ocr_run` | OCR start enqueue | 3~20s | 2 次 | 调阿里云 OCR,失败回写 `ocr_results.status=failed` |
| `ai_generate` | report generate enqueue | 15s~2min | 1 次 | OpenAI + instructor 结构化输出;成功后**写 3 个版本** internal_full + user_visible(按当前 tier)+ customer_simple |
| `import_markdown` | admin 上传 MD | 1~5min | 1 次 | 解析 → 写入 `import_jobs.parsed_json` → 等管理员 confirm 接口才真入库 cases |
| `export_build` | admin 触发导出 | 5s~10min | 0 | 流式 `openpyxl` 或 `polars` 写 Excel/CSV 到 OSS,7 天 OSS 生命周期清理 |
| `audit_write` | AuditMiddleware enqueue | <100ms | 5 次 | 异步落 `admin_operation_logs`,失败重试不影响主请求 |

### 7.2 Cron(Arq `cron_jobs`)

| 任务 | 触发 | 备注 |
|---|---|---|
| `quota_rollover` | 每月 1 号 00:01 | 为活跃用户创建当月 `token_quotas` 行 |
| `signed_url_gc` | 每天 03:00 | 清理 Redis 中过期签名 URL 缓存键 |
| `mock_data_purge` | 每天 04:00 | 删除 7 天以上的 `is_mock=true` 临时数据 |
| `db_backup_trigger` | 每天 02:00 | 调 pgbackrest hook |

### 7.3 Arq Worker 配置示例

```python
# app/workers/arq_worker.py
from arq.connections import RedisSettings
from arq.cron import cron
from app.workers.jobs import (
    image_process, ocr_run, ai_generate,
    import_markdown, export_build, audit_write,
)
from app.workers.cron import quota_rollover, signed_url_gc, mock_data_purge

class WorkerSettings:
    functions = [image_process, ocr_run, ai_generate,
                 import_markdown, export_build, audit_write]
    cron_jobs = [
        cron(quota_rollover, day=1, hour=0, minute=1),
        cron(signed_url_gc, hour=3, minute=0),
        cron(mock_data_purge, hour=4, minute=0),
    ]
    redis_settings = RedisSettings(host="redis", port=6379)
    max_jobs = 10
    job_timeout = 180  # ai_generate 单独覆盖到 300s
```

### 7.4 状态回传

- 长任务(`ai_generate` / `import_markdown`)前端轮询 `GET /cases/:id` 看 `status` 字段
- 或 P1 引入 SSE:`GET /cases/:id/events` 走 `StreamingResponse`(FastAPI 原生支持)
- 不要为 MVP 上 WebSocket

---

## 8. OSS 与文件安全

### 8.1 Bucket 结构

```text
yaoqi-prod (private)
├─ user-upload-original/{user_id}/{case_id}/{file_id}.{ext}
├─ user-upload-preview/{user_id}/{case_id}/{file_id}.jpg
├─ user-upload-watermark/{user_id}/{case_id}/{file_id}.jpg
├─ certificate-images/{user_id}/{case_id}/{file_id}.{ext}
├─ report-files/{case_id}/{report_id}.pdf
├─ knowledge-files/{file_type}/{file_id}.md
├─ exports/{job_id}.xlsx       (7 天后 OSS 生命周期清理)
└─ system-temp/{date}/{file_id}
```

### 8.2 上传流程(STS Token 直传)

```text
Browser              API                       OSS
  │  POST /uploads/presign     │
  ├────────────────────────────►                                          │
  │                            │  权限校验 + 生成 PolicyToken              │
  │                            │  (限制 callback + max-size + key-prefix) │
  │ ◄──────────────────────────┤                                          │
  │  { policy, signature, key }                                            │
  │  PUT 直传(带 policy)                                                  │
  ├────────────────────────────────────────────────────────────────────────►
  │                            │                                          │
  │  POST /uploads/complete                                                │
  ├────────────────────────────►                                          │
  │                            │  写 case_files,投 image.process 队列     │
  │ ◄──────────────────────────┤                                          │
```

> **强制约束**:Policy 签发时硬编码 `key prefix = user-upload-*/{me.user_id}/`,即使前端伪造 case_id 也无法越权写到他人目录。

### 8.3 访问流程

- 用户端默认拿 `oss_key_watermarked` 的 5 分钟签名 URL
- 不返回 `oss_key_original` 字段给前端任何接口(`@Exclude()` 序列化排除)
- 管理员看原图走专用 `/admin/files/:id/original-url`,**audit 日志强制**

---

## 9. AI / OCR 调用策略

> **范围约定(2026-05-22 拍板)**:LLM 唯一提供方 = **Azure OpenAI Service**(Azure HongKong 区域),后端跨云直调。M4 backend 只**预留 `LLMClient` 抽象接口**与 prompt/schema/配额脚手架,真实接入(deployment 名映射、prompt 调优、评测集、RAG 召回链)由 **AI 工程那一脚**承接(对应 [`skills/ai-integration-engineer.md`](../skills/ai-integration-engineer.md))。

### 9.1 分层(Product-Spec §15.1)

| 任务 | 用 Azure OpenAI deployment | 备注 |
|---|---|---|
| OCR 字段修正 / 抽取 | `aoai-gpt-4o-mini`(或私调) | 证书 raw_text → 结构化 JSON |
| 图片可见特征摘要 | `aoai-gpt-4o`(vision) | 一图一次调用,结果缓存 |
| 完整鉴定估价报告 | `aoai-private-report`(**私有微调** deployment) | 输入图片摘要 + 用户字段 + OCR + (可选)pgvector 召回 |
| 高价 / 法拍 / 证书矛盾 | 同上 + **强制 admin_review** | 自动打 `pending_recheck` 状态 |
| Embedding | `aoai-text-embedding-3-small`(或本地 `sentence-transformers`) | 写入 pgvector,M4 召回先关 |

**deployment 名 ≠ 模型基座名**:`Settings.aoai_deployment_report / aoai_deployment_ocr / aoai_deployment_embedding` 在 `.env` 配置,不要硬编码。

### 9.2 实现栈

| 工具 | 用途 |
|---|---|
| `openai` Python SDK(Azure 模式)| 调用 Azure OpenAI Service:`AsyncAzureOpenAI(azure_endpoint, api_version, api_key)` |
| **`instructor`** | 把 Pydantic 模型当 response_schema,自动重试 + 校验 |
| **`pgvector`** | 历史案例 embedding 入库(M4 只写不召回) |
| **`sentence-transformers`**(本地,可选) | 文本 embedding 备用,省 Azure 出口费用 |
| `Jinja2` | Prompt 模板渲染 |
| `tiktoken` | 调用前估算 token,做配额预占 |
| ~~LangChain / LlamaIndex / DSPy~~ | **不引入**(已拍板) |

### 9.3 `LLMClient` 抽象接口(M4 必交付)

后端业务代码**只依赖 `LLMClient` 协议**,不直接 import `openai`。M4 落地:

- 接口定义 + Azure OpenAI 默认实现(可能只是个 stub 返回 `NotImplementedError("由 AI 工程接入")`)
- prompt 模板目录与版本字段(`prompt_version`)
- Pydantic 输出 schema 目录(`app/integrations/ai/schemas.py`)
- 配额预占/结算服务(基于 `tiktoken` 估算)
- `ai_call_logs` 写入

```python
# app/integrations/ai/client.py
from typing import Protocol, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class LLMClient(Protocol):
    async def generate(
        self,
        *,
        deployment: str,          # Azure deployment 名,不是模型基座
        messages: list[dict],
        response_model: type[T],  # Pydantic schema,instructor 校验
        max_retries: int = 2,
    ) -> T: ...

    async def embed(
        self,
        *,
        deployment: str,
        texts: list[str],
    ) -> list[list[float]]: ...


# app/integrations/ai/azure_openai_client.py(M4 stub,AI 工程那一脚填充)
import instructor
from openai import AsyncAzureOpenAI

class AzureOpenAILLMClient:
    def __init__(self, settings: Settings):
        self._raw = AsyncAzureOpenAI(
            azure_endpoint=settings.aoai_endpoint,
            api_version=settings.aoai_api_version,
            api_key=settings.aoai_api_key,
        )
        self._patched = instructor.from_openai(self._raw)

    async def generate(self, *, deployment, messages, response_model, max_retries=2):
        return await self._patched.chat.completions.create(
            model=deployment,                  # Azure 用 deployment 名
            response_model=response_model,
            messages=messages,
            max_retries=max_retries,
        )

    async def embed(self, *, deployment, texts):
        resp = await self._raw.embeddings.create(model=deployment, input=texts)
        return [d.embedding for d in resp.data]
```

### 9.4 Prompt 与输出契约

- 模板存 `app/integrations/ai/prompts/*.md`,文件名带 `prompt_version`(如 `report_v1.md`)
- Pydantic 响应模型存 `app/integrations/ai/schemas.py`,与 `ai_reports.output_json` 字段一致
- schema 必须覆盖 Product-Spec §15.4 全部 13 字段(材质倾向 / 处理风险 / 种水 / 价格区间 / 回收价 / 流通性 / 复检建议 / 风险等级 / 客户简洁版 / 免责声明 / ...)
- `instructor` 强制 parse 成 Pydantic 实例,失败自动重试(max=2)

### 9.5 成本 / 配额

- 调用前用 `tiktoken` 估算 token,`quota_service.reserve(user_id, tokens=estimated)` 预占
- 调用完按 `usage.total_tokens` 修正:`quota_service.settle(reservation_id, actual=usage.total_tokens)`
- 失败回退预占
- 超配额返回 `403 quota_exceeded`,前端弹"联系管理员开通"
- 每次调用写一行 `ai_call_logs`(deployment / token_in / token_out / cost / status / error / prompt_version)

### 9.6 私有微调模型对接

- 私调模型以 **Azure OpenAI deployment** 形式发布,deployment 名通过 `Settings.aoai_deployment_report` 注入
- 评测集独立目录 `app/integrations/ai/evals/`(Pytest 跑离线 quality score)
- Prompt 版本与 deployment 版本独立演进,`ai_reports.prompt_version` + `deployment_name` 双字段追溯

### 9.7 跨云出口(后端在阿里云、AI 在 Azure)

- 主体业务后端跑在**阿里云 ECS**,LLM 调用走公网到 `*.openai.azure.com`(Azure HongKong)
- 出口注意点:
  - 阿里云安全组放行 443 到 Azure 区域
  - 设置 `timeout=60s` 与重试(`tenacity` 指数退避),避免跨云抖动直接 502
  - `ai_call_logs` 记录 latency,便于事后判断是不是出口问题
- **不在 M4 引入** API Gateway / 代理层,直连即可;若后续出口稳定性差再加

---

## 10. 鉴权与 RBAC

### 10.1 Session 策略

- Cookie: `yq_session`(用户) + `yq_admin`(管理员),`HttpOnly; Secure; SameSite=Lax`
- 内容:JWT(HS256 via `pyjwt`,密钥 `JWT_SECRET`),Payload: `{ uid, role, tier, jti, exp }`
- 过期:用户 7d;管理员 12h;有 Refresh 接口
- Logout 把 `jti` 写 Redis 黑名单(TTL = 原 token 剩余有效期),`get_current_user` 依赖项每次检查
- 密码哈希(仅管理员账号):`passlib[bcrypt]`,rounds=12

### 10.1.1 FastAPI Depends 实现

```python
# app/deps/auth.py
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User | None:
    token = request.cookies.get("yq_session")
    if not token: return None
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    if await redis.exists(f"jwt:blacklist:{payload['jti']}"):
        return None
    return await db.get(User, payload["uid"])

async def require_user(user: User | None = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(401, "未登录")
    return user

async def require_admin(user: User = Depends(require_user)) -> User:
    if user.role not in ("admin", "super_admin"):
        raise HTTPException(403, "需要管理员权限")
    return user

def require_tier(min_tier: MembershipTier):
    async def _check(user: User = Depends(require_user)):
        if TIER_ORDER[user.membership] < TIER_ORDER[min_tier]:
            raise HTTPException(403, "会员等级不足")
        return user
    return _check
```

### 10.2 RBAC 矩阵(关键接口)

| 路径模式 | guest | free_user | member_* | business* | admin | super_admin |
|---|---|---|---|---|---|---|
| `POST /api/auth/**`(非 admin-login) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /api/cases`(自己的) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /api/reports/:id` 高级字段 | ❌ | 裁剪 | 裁剪 | 裁剪 | 全量 | 全量 |
| `GET /api/customer-brief/:id` | ❌ | 白名单 | 白名单 | 白名单 | 白名单 | 白名单 |
| `/api/admin/**`(读) | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| `POST /admin/export/**` | ❌ | ❌ | ❌ | ❌ | ✅(留痕) | ✅(留痕) |
| 管理员账号增删 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

### 10.3 跨权限红线测试(M4 必须自动化)

- 普通用户 GET 他人 `/api/cases/:id` → 403
- free_user GET `/api/reports/:id`,响应 JSON **不包含** `priceRange / recyclePrice / negotiationStrategy / channelHint / similarCases`
- 未登录 GET `/api/customer-brief/:id` → 401
- 普通管理员 POST `/admin/export/cases` → 200 但 `admin_operation_logs` 必须新增一行

---

## 11. 错误处理与可观测性

### 11.1 错误响应

```json
{ "ok": false, "error": "案例不存在", "code": "case.not_found", "source": "real" }
```

`code` 字段 P1 引入,供前端做 i18n / 自动化测试。

### 11.2 日志

- 应用日志:Pino → 标准输出 → Filebeat → Elasticsearch(P2 可省,先落本地文件 + logrotate)
- 审计日志:`admin_operation_logs` 表(强一致)
- AI/OCR 调用日志:专用表,便于成本核算

### 11.3 监控(P1)

- `/health` 暴露 DB / Redis / OSS / OpenAI 连通性
- 慢请求 P95、AI 调用成功率、队列堆积量打到 Prometheus

---

## 12. Mock 与真实切换

### 12.1 环境变量

```env
MOCK_AUTH=false       # true: 任意手机号+ 6 位验证码登录
MOCK_OSS=false        # true: 上传不真传,记到本地 ./tmp/mock-oss
MOCK_OCR=false        # true: OCR 返 fixture
MOCK_AI=false         # true: 返 mock 报告
SEED_MOCK_DATA=false  # true: 启动时执行 prisma seed,所有 mock 行 is_mock=true
```

### 12.2 数据隔离

- 所有业务表带 `is_mock BOOLEAN`
- 管理后台默认筛选 `is_mock = false`,可显式切到 mock 视图
- 导出接口**默认拒绝** mock 行,需 `?include_mock=true` 且二次确认

---

## 13. 部署与运维

### 13.1 必须

- 阿里云 ECS(2 台,前置 SLB)+ Postgres RDS(开 pgvector 扩展)+ Redis 云缓存版
- 域名 + ICP 备案 + HTTPS(项目方账号)
- pgbackrest 每日全备
- OSS 跨区复制(冷备)
- 环境变量走阿里云 KMS / 密钥管理服务,不在镜像

### 13.2 进程启动命令

```bash
# api 进程(每副本)
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --timeout 60

# worker 进程
arq app.workers.arq_worker.WorkerSettings

# Alembic 迁移(发版前)
alembic upgrade head
```

### 13.3 容器分层(单镜像多 CMD)

```dockerfile
# Dockerfile 示意
FROM python:3.12-slim AS base
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
# CMD 由 docker-compose / k8s 指定:
#   api    : gunicorn ...
#   worker : arq ...
#   migrate: alembic upgrade head
```

### 13.4 CI/CD(P1)

- GitHub Actions / 阿里云云效:`ruff check` + `pytest` + `alembic check`(无 pending 迁移)+ `mypy` + `docker build`
- 部署:Docker image 推私有 ACR,ECS `docker compose pull && docker compose up -d`,先迁库再切流量

---

## 14. 与前端的迁移策略

### 14.1 路由切换

1. **保留前端代码不动**,仅切 `NEXT_PUBLIC_API_BASE` → 真 FastAPI 域名(或 Nginx 同源代理 `/api` → FastAPI)
2. 第一周双写期:Next.js Route Handler 改为对真后端透传(`fetch(BACKEND_URL + req.url)`),便于灰度回滚
3. 第二周关闭 Mock Route Handler
4. 第三周删除 `web/lib/mock/*.json`(保留 fixture 给 Playwright 测试用)

### 14.2 类型同步(Python ↔ TypeScript)

由于后端 = Python,无法直接 import TS 类型,必须有 codegen 兜底:

1. FastAPI `app.openapi()` 自动产出 `openapi.json`(`/openapi.json` 接口或构建期导出)
2. CI 步骤:`npx openapi-typescript backend/openapi.json -o web/lib/types/api.gen.ts`
3. 前端**新代码**用 `api.gen.ts` 中的类型;`web/lib/types/domain.ts` 保留作业务别名层,**显式重导出**对应 gen 类型,避免漂移
4. CI 加 lint 规则:`domain.ts` 中的 `CaseRecord` / `CaseReport` / `User` 等必须 `extends` 或 `Pick<>` from `api.gen.ts`
5. 后端 schema 改动 → 提 PR 自动跑 codegen diff,review 时能看到前端契约影响

### 14.3 ApiResponse 信封一致性

- Python `app/schemas/envelope.py` 定义 `ApiResponse[T]`(`Generic[T]`),与 `web/lib/types/domain.ts:153` 字段完全对齐:`ok / data? / error? / source`
- 全部路由强制走 `EnvelopeMiddleware`,不允许裸返字典

---

## 15. M4 验收 Checklist(对应 Product-Spec §20.3 / §20.4)

- [ ] 真实手机号验证码登录,验证码 60s 限频
- [ ] 真实图片上传到 OSS private bucket(用 `aws s3api get-bucket-acl` 或阿里云控制台核对)
- [ ] OSS 访问 URL 5 分钟过期,过期再访问 403
- [ ] 普通用户 GET 他人 case → 403
- [ ] free_user GET report,响应字段集合 ⊆ `["materialHint","risk","needReinspect"]`
- [ ] AI 报告真实生成,模型名/token 数写入 `ai_call_logs`
- [ ] 管理员看原图,`admin_operation_logs` 新增一行带 IP
- [ ] 导出案例 Excel,字段与 Technical-Spec §11.2 一致
- [ ] 月配额耗尽返 403 `quota_exceeded`
- [ ] 启动时 `/health` 返回所有第三方连通状态

---

## 16. 已拍板决策清单

> 全部于 2026-05-22 与业务方确认。

| # | 议题 | 决议 | 备注 |
|---|---|---|---|
| 0 | **后端语言/框架** | ✅ FastAPI (Python) | 与 LLM/微调/RAG 资产同语种 |
| 1 | 异步队列 | ✅ **Arq** | 异步原生,与 FastAPI 同事件循环 |
| 2 | 微信登录 | ✅ **推 P1**,M4 不做 | M4 只做手机号 + 邮箱 + 密码;微信 OAuth 资质申请耗时,不阻塞核心闭环 |
| 3 | OSS 上传通道 | ✅ **阿里云 OSS + STS 直传** | 后端只发 Token,文件不过后端 |
| 4 | 短信服务商 | ✅ **阿里云短信** | 与 OSS/OCR 同账号统一计费 |
| 5 | LLM 提供方 | ✅ **Azure OpenAI Service**(唯一)| 部署在 Azure HongKong;私调模型以 deployment 形式发布;**不引入**豆包/通义千问国内备份模型 |
| 5a | M4 AI 落地深度 | ✅ **只预留 `LLMClient` 抽象接口** + prompt/schema/配额脚手架 | 真正接入(deployment 名、prompt、评测、召回)由 AI 工程那一脚承接 |
| 6 | RAG / pgvector | ✅ **M4 装扩展 + 写入 embedding,召回开关默认关** | DDL 一次到位,避免日后回填;召回链路由 AI 工程那一脚开启 |
| 7 | i18n 错误码 | ✅ **推 P1** | 本期 `error` 用中文短句够用 |
| 8 | Postgres | ✅ **阿里云 RDS PostgreSQL 16**(原生 pgvector)| 托管备份/主从/监控,MVP 阶段单人扛得动 |
| 9 | LangChain / LlamaIndex / DSPy | ✅ **不引入** | 裸 `LLMClient` + instructor 已足够 |

### 16.1 跨云部署速记

- **主体业务后端**(FastAPI / Arq worker / Redis / Postgres / OSS / OCR / SMS):**阿里云**(ECS + RDS + Tair/Redis + OSS + OCR + 短信)
- **AI**:**Azure OpenAI Service @ HongKong**,后端跨云直调
- 不在 M4 引入 API Gateway / VPN 专线,公网直连足够;若出口稳定性差再加(详见 §9.7)

---

## 17. 后续文档

本设计敲定后应拆出:

- `Backend-API-Spec_v0.1.yaml`(OpenAPI 3.1,由 FastAPI 自动导出 + 人工补 description)
- `Backend-Database-Schema_v0.1.md`(SQLAlchemy models + Alembic 迁移演进规则)
- `Backend-Security-Checklist_v0.1.md`(渗透测试条目,§10.3 红线展开)
- `Backend-Deployment-Guide_v0.1.md`(阿里云 ECS + RDS + Redis + OSS step-by-step)
- `skills/backend-engineer.md`(给 AI 编程代理的 Python/FastAPI 实现规则)
- `skills/ai-integration-engineer.md`(prompt 版本规范、instructor 使用规范、配额预占规范)
