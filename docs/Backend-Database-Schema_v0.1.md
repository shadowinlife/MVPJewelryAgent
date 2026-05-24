# 曜齐 YAOQI — Backend Database Schema v0.1

> M4 数据库 Schema 权威文档。**DDL 草案**在 [Backend-Architecture §5](./Backend-Architecture_v0.1.md);本文在其基础上补全:pgvector 扩展与 embedding 列、SQLAlchemy 2.0 ORM 映射、Alembic 演进规则、索引策略、数据保留与归档、种子数据、测试 fixture、字段裁剪映射。
>
> 父文档:[Backend-Architecture_v0.1.md](./Backend-Architecture_v0.1.md) / [Product-Spec_v0.4.md §12 §15.4 §16](./Product-Spec_v0.4.md) / [Technical-Spec_v0.1.md §5](./Technical-Spec_v0.1.md)
> 兄弟文档:[skills/backend-engineer.md](../skills/backend-engineer.md) / [skills/ai-integration-engineer.md](../skills/ai-integration-engineer.md)
> 起始:2026-05-22

---

## 0. 文档定位

| 在哪 | 内容 |
|---|---|
| Backend-Architecture §5 | **物理 DDL 草案**(SQL 语句、字段、索引)— 设计源头 |
| **本文档** | DDL 的**补强**(向量列、约束、状态机) + **ORM 映射规范** + **Alembic 演进规则** + **索引/备份/保留** + **种子/测试/裁剪映射** |
| Product-Spec §12 | 数据模型**概要**(字段清单) |
| Technical-Spec §5 | 早期草案(以本文为准,Tech-Spec 不再回头改) |

**冲突仲裁**:本文 ≻ Backend-Architecture §5 ≻ Product-Spec §12 ≻ Technical-Spec §5。
**改 schema 的唯一入口**:本文档 + Alembic revision,**禁止**只改 ORM 不改 DDL,也**禁止**只改 DDL 不改本文档。

---

## 1. 设计原则(全表统一)

| # | 原则 | 说明 |
|---|---|---|
| 1 | snake_case 命名 | 表名复数(`users` / `cases`),字段全小写;**禁止**驼峰、大写、保留字 |
| 2 | 主键 `id BIGSERIAL` | 内部 PK;**对外**暴露 `*_no`(`case_no = "YQ-2026-000123"`)避免遍历 |
| 3 | 时间戳 `TIMESTAMPTZ` | 一律 `timestamptz`,默认 `now()`;`updated_at` 由触发器自动更新(见 §5.5) |
| 4 | `is_mock BOOLEAN NOT NULL DEFAULT false` | 每张业务表必备;管理端默认 `WHERE is_mock = false`,导出强制拒绝(`?include_mock=true` 才放) |
| 5 | 金额用 `BIGINT cents` | **禁止** `NUMERIC` / `FLOAT`;¥1234.56 → 123456;字段名后缀 `_cents` |
| 6 | JSONB 边界 | 仅在"结构频繁演进"或"半结构化"场景使用(OCR 抽取、AI 输出、admin 操作详情);**禁止**把核心查询字段塞 JSONB |
| 7 | 软删 vs 硬删 | `cases` / `users` 用 `status` 状态机(无物理删除);`sms_codes` / `case_files` 临时数据可硬删 |
| 8 | 外键 + ON DELETE | 子表显式声明 `ON DELETE CASCADE`(`case_files` 跟 `cases`)或 `ON DELETE RESTRICT`(`ai_reports` 留痕);**禁止**默认 NO ACTION |
| 9 | 索引附 `WHERE` 子句 | 高基数列上的部分索引(`status` / `is_mock`)优先,避免全表索引膨胀 |
| 10 | 注释强制 | `COMMENT ON TABLE` + `COMMENT ON COLUMN` 写中文业务含义,Alembic op 同步执行 |

**强制 enum 用 VARCHAR + CHECK 约束**(不是 Postgres ENUM 类型),理由:Postgres `ENUM` 改值要 `ALTER TYPE`,跨环境迁移痛苦;VARCHAR + CHECK 灵活,Pydantic `Literal[...]` 在应用层兜底。

---

## 2. 扩展与依赖

### 2.1 必装扩展(Alembic 初始 revision 创建)

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";    -- 仅 jti 等场景备用,主键不用
CREATE EXTENSION IF NOT EXISTS pg_trgm;        -- 案例标题/卖家文本模糊搜索备用
CREATE EXTENSION IF NOT EXISTS vector;         -- pgvector(原生 RDS PG16 已带,M4 一次到位)
```

`vector` 扩展启用对应 [Backend-Architecture §16 决议 6](./Backend-Architecture_v0.1.md):**M4 装扩展 + 写入 embedding,召回开关默认关**。embedding 列在 §5.3 提前落,避免日后回填全量。

### 2.2 不引入的扩展(已拍板排除)

- ❌ `PostGIS`(无地理需求)
- ❌ `pg_partman`(M4 数据量级 < 10w,不到分区阈值)
- ❌ `timescaledb`(日志走 `ai_call_logs` + 时间索引足矣)

---

## 3. ER 概览

```text
                        ┌──────────────┐
                        │    users     │◄──┐
                        └──────┬───────┘   │ admin_id
                               │           │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌──────────┐    ┌──────────────┐  ┌─────────────────────┐
       │memberships│    │token_quotas │  │admin_operation_logs │
       └──────────┘    └──────────────┘  └─────────────────────┘
                               │
                               ▼ user_id
                        ┌──────────────┐
                        │    cases     │──── case_no (对外)
                        └──────┬───────┘
                               │
              ┌────────────────┼────────────────┬─────────────────┐
              ▼                ▼                ▼                 ▼
       ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
       │ case_files   │ │ ocr_results  │ │  ai_reports  │ │admin_reviews │
       └──────────────┘ └──────────────┘ └──────┬───────┘ └──────────────┘
                                                │
                                                ▼ (cost / latency)
                                         ┌──────────────┐
                                         │ai_call_logs  │
                                         └──────────────┘

       ┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
       │ knowledge_files  │◄────│   import_jobs    │     │  sms_codes   │
       └──────────────────┘     └──────────────────┘     └──────────────┘
              │
              ▼ embedding (pgvector)
       (RAG 召回池,M4 只写不读)
```

---

## 4. 表清单

| 域 | 表 | 是否 `is_mock` | 备份策略 | 保留策略 |
|---|---|---|---|---|
| 用户与会员 | `users` | ✅ | 每日全量 | 永久(状态机软删) |
| 用户与会员 | `memberships` | ✅ | 每日全量 | 永久(历史变更留痕) |
| 用户与会员 | `token_quotas` | ✅ | 每日全量 | 永久(账期统计) |
| 案例与文件 | `cases` | ✅ | 每日全量 | 永久(`status='archived'` 软删) |
| 案例与文件 | `case_files` | ✅ | 每日全量 | 永久 |
| OCR/AI/报告 | `ocr_results` | ✅ | 每日全量 | 6 个月后归档(冷表) |
| OCR/AI/报告 | `ai_reports` | ✅ | 每日全量 | 永久(报告版本溯源) |
| OCR/AI/报告 | `ai_call_logs` | ❌(无业务态) | 每周全量 | 6 个月后归档(冷表) |
| 知识库 | `knowledge_files` | ✅ | 每日全量 | 永久 |
| 管理 | `admin_reviews` | ✅ | 每日全量 | 永久 |
| 管理 | `admin_operation_logs` | ❌ | 每日全量 | **永久,禁删** |
| 管理 | `import_jobs` | ✅ | 每日全量 | 1 年后归档 |
| 临时 | `sms_codes` | ❌ | 不备份 | 30 天后清理 |

---

## 5. DDL 详细(补 §5 的不足)

> 与 [Backend-Architecture §5](./Backend-Architecture_v0.1.md) 字段一致,本节补:embedding 列、CHECK 约束、updated_at 触发器、跨表唯一约束、状态机。

### 5.1 users / memberships / token_quotas

字段定义同 [§5.1](./Backend-Architecture_v0.1.md),补:

```sql
-- users:角色 / 状态 用 CHECK 而非 ENUM
ALTER TABLE users
  ADD CONSTRAINT chk_users_role CHECK (
    role IN ('guest','free_user','member_basic','member_pro',
             'business','business_pro','admin','super_admin')
  ),
  ADD CONSTRAINT chk_users_status CHECK (status IN ('active','disabled'));

-- memberships:tier 收紧
ALTER TABLE memberships
  ADD CONSTRAINT chk_memberships_tier CHECK (
    tier IN ('free','basic','pro','business','business_pro')
  );

-- token_quotas:period 形态校验
ALTER TABLE token_quotas
  ADD CONSTRAINT chk_period_yyyymm CHECK (
    period_yyyymm BETWEEN 202001 AND 209912
    AND (period_yyyymm % 100) BETWEEN 1 AND 12
  ),
  ADD CONSTRAINT chk_tokens_nonneg CHECK (
    tokens_total >= 0 AND tokens_used >= 0 AND admin_extra >= 0
  );
```

> **会员等级映射**:`tier` 5 档与 `web/lib/mock/memberships.json` 的 `tokenPolicy` 对齐,核心差异是月度 Token 配额(2 万 → 200 万)。详见 [yaoqi-membership-tiers memory](../.claude/projects/-Users-mgong-PycharmProjects-ZhuBaoTest/memory/yaoqi-membership-tiers.md)。

### 5.2 cases / case_files

字段同 [§5.2](./Backend-Architecture_v0.1.md),补 **embedding 列** 与 **状态机约束**:

```sql
-- cases:补 embedding(M4 写入,默认不召回)
ALTER TABLE cases
  ADD COLUMN embedding vector(384),                       -- sentence-transformers 输出维度
  ADD COLUMN embedding_model VARCHAR(60),                 -- 标注生成 embedding 的模型/版本
  ADD COLUMN embedding_generated_at TIMESTAMPTZ;

CREATE INDEX idx_cases_embedding
  ON cases USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
-- 召回开关 Settings.rag_recall_enabled=False 时,索引存在但不查;无运行时代价

-- cases.status 状态机(应用层 service 强制,DB 层只兜底)
ALTER TABLE cases
  ADD CONSTRAINT chk_cases_status CHECK (
    status IN ('draft','pending','analyzing','analyzed',
               'pending_recheck','archived')
  ),
  ADD CONSTRAINT chk_cases_purpose CHECK (
    purpose IN ('buy','sell','recycle','auction','study',
                'live_select','customer_consult','business_select')
  );
```

**状态机转换**(service 层):
```
draft ──提交──▶ pending ──Arq worker接──▶ analyzing
                                              │
                ┌─────────────────────────────┼────────────┐
                ▼                             ▼            ▼
            analyzed                  pending_recheck   (失败回 pending)
                │
                └──用户/管理员──▶ archived
```

`case_files`:

```sql
ALTER TABLE case_files
  ADD CONSTRAINT chk_case_files_file_type CHECK (
    file_type IN ('jewelry_natural_light','jewelry_strong_light','jewelry_backlight',
                  'jewelry_detail','certificate','receipt','other_doc')
  ),
  ADD CONSTRAINT chk_case_files_upload_status CHECK (
    upload_status IN ('pending','uploaded','processing','ready','failed')
  );
```

### 5.3 ocr_results / ai_reports / ai_call_logs

字段同 [§5.3](./Backend-Architecture_v0.1.md),补 **AI 报告 embedding** 与 **私调 deployment 字段**:

```sql
-- ai_reports:补 deployment_name(对应 ai-integration-engineer 私调 deployment)
ALTER TABLE ai_reports
  ADD COLUMN deployment_name VARCHAR(80),                 -- Azure 端 deployment(如 aoai-private-report)
  ADD COLUMN embedding vector(384),                       -- 报告文本 embedding(RAG 召回池)
  ADD CONSTRAINT chk_ai_reports_type CHECK (
    report_type IN ('internal_full','user_visible','customer_simple','admin_reviewed')
  ),
  ADD CONSTRAINT chk_ai_reports_status CHECK (
    status IN ('pending','generating','succeeded','failed')
  );

-- ai_call_logs:补 prompt_version + latency
ALTER TABLE ai_call_logs
  ADD COLUMN prompt_version VARCHAR(20),                  -- 与 ai_reports.prompt_version 对齐
  ADD COLUMN latency_ms INTEGER,                          -- 跨云出口必填,事后归因用
  ADD CONSTRAINT chk_ai_call_logs_status CHECK (
    status IN ('success','failed','timeout')
  );
```

**13 字段对应**:`ai_reports.output_json` 必须是 [Product-Spec §15.4](./Product-Spec_v0.4.md) 13 字段的超集,Pydantic schema 在 [skills/ai-integration-engineer.md §Pydantic schema](../skills/ai-integration-engineer.md) 定义为 `GeneratedReport`。`price_fields_json` / `risk_fields_json` 是裁剪辅助,从 `output_json` 派生写入。

### 5.4 knowledge_files / import_jobs / admin_*

字段同 [§5.4](./Backend-Architecture_v0.1.md),补 **知识库 embedding**(RAG 召回主源):

```sql
ALTER TABLE knowledge_files
  ADD COLUMN embedding vector(384),
  ADD COLUMN embedding_model VARCHAR(60),
  ADD COLUMN content_summary TEXT,                        -- 解析后的摘要(召回 top-k 后参与 prompt)
  ADD CONSTRAINT chk_knowledge_files_type CHECK (
    file_type IN ('personal_case','market_observation','auction_rule',
                  'gb_certificate_sop','live_sales_script','other')
  ),
  ADD CONSTRAINT chk_knowledge_files_parsed_status CHECK (
    parsed_status IN ('pending','parsing','parsed','failed')
  );

CREATE INDEX idx_knowledge_embedding
  ON knowledge_files USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)
  WHERE enabled;

ALTER TABLE admin_operation_logs
  ADD CONSTRAINT chk_admin_action CHECK (
    action IN ('view_original_image','export_cases','update_membership',
               'grant_quota','delete_case','review_case','import_knowledge',
               'login_admin','logout_admin','create_admin','disable_user')
  );
```

### 5.5 跨表约束、触发器、状态机

```sql
-- updated_at 自动更新触发器(所有有 updated_at 字段的表都挂一个)
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END; $$ LANGUAGE plpgsql;

-- 应用到每张需要的表(Alembic 中循环创建,不要手写)
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_cases_updated_at BEFORE UPDATE ON cases
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
-- ... ai_reports / ocr_results / knowledge_files / import_jobs / memberships
```

**唯一约束(已有,本文重申)**:
- `users(phone)` UNIQUE
- `users(wechat_openid)` UNIQUE WHERE NOT NULL
- `cases(case_no)` UNIQUE
- `memberships(user_id) WHERE is_current` UNIQUE — 保证用户只有 1 个当前会员
- `token_quotas(user_id, period_yyyymm)` UNIQUE

**禁止跨表事务陷阱**:
- 报告生成同时写 `ai_reports` + `ai_call_logs` + 扣 `token_quotas` → 同一 `async with session.begin()` 包,失败全回
- `case_files.upload_status = 'ready'` 触发 OCR 异步 job → Arq enqueue **在事务 commit 之后**,避免事务回滚但 job 已派发

---

## 6. SQLAlchemy 2.0 ORM 映射规范

### 6.1 文件组织

```
backend/app/db/
├─ __init__.py
├─ base.py             # DeclarativeBase + 公共 mixin
├─ session.py          # async_engine / async_sessionmaker / get_db dependency
└─ models/
   ├─ __init__.py      # 显式 re-export 所有 Model(让 Alembic autogenerate 看得见)
   ├─ user.py
   ├─ membership.py
   ├─ token_quota.py
   ├─ case.py
   ├─ case_file.py
   ├─ ocr_result.py
   ├─ ai_report.py
   ├─ ai_call_log.py
   ├─ admin_review.py
   ├─ admin_operation_log.py
   ├─ knowledge_file.py
   ├─ import_job.py
   └─ sms_code.py
```

**一表一文件**,理由:Alembic autogenerate 看 `Base.metadata`,只要 `models/__init__.py` re-export 即可,但 review diff 时一文件改动一张表更清楚。

### 6.2 公共 mixin(`base.py`)

```python
from datetime import datetime
from sqlalchemy import BigInteger, Boolean, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

class MockableMixin:
    is_mock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

class IdMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
```

### 6.3 Model 示例(`models/case.py`)

```python
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, ForeignKey, String, Index
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from app.db.base import Base, IdMixin, TimestampMixin, MockableMixin

if TYPE_CHECKING:
    from .user import User
    from .case_file import CaseFile
    from .ai_report import AIReport

class Case(Base, IdMixin, TimestampMixin, MockableMixin):
    __tablename__ = "cases"

    case_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    # ... 其余字段对照 §5.2 DDL,Pydantic Literal 在 schemas/ 收紧
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)

    user: Mapped["User"] = relationship(back_populates="cases")
    files: Mapped[list["CaseFile"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    reports: Mapped[list["AIReport"]] = relationship(back_populates="case")

    __table_args__ = (
        Index("idx_cases_user", "user_id", "updated_at"),
        # 部分索引在 Alembic op 里用 raw SQL,SQLAlchemy 2.0 对 WHERE 子句支持有限
    )
```

### 6.4 ORM 红线

1. ❌ **禁止 `lazy='dynamic'` / 隐式懒加载** — async 下会炸;预先 `selectinload()` / `joinedload()`
2. ❌ **禁止在 Model 里写 business 方法** — Model 只描述 schema;查询/写入逻辑在 `services/`
3. ❌ **禁止 `default=lambda: datetime.utcnow()`** — 用 `server_default=func.now()`,时区一致性靠 DB
4. ❌ **禁止 `nullable` 默认靠 Python None** — 一律显式 `nullable=False` 或 `nullable=True`
5. ❌ **禁止把 enum 在 ORM 用 `Enum` 类型** — 用 `String` + CHECK 约束(见 §1)
6. ❌ **禁止跨 module 循环 import** — relationship 用字符串 `"User"`,真实类型用 `TYPE_CHECKING`

---

## 7. Alembic 演进规则

### 7.1 目录与初始化

```
backend/
├─ alembic.ini
└─ alembic/
   ├─ env.py            # 加载 Base.metadata + Settings.database_url
   ├─ script.py.mako
   └─ versions/
      ├─ 0001_init.py              # 创建扩展 + 全部表
      ├─ 0002_add_embeddings.py    # pgvector 列(若 0001 不一次落)
      └─ ...
```

`env.py` 必须:
- 用 `async_engine_from_config` + `run_sync()`(SQLAlchemy 2.0 async pattern)
- `target_metadata = Base.metadata`(导入 `app.db.models` 触发 re-export)
- 启用 `compare_type=True` + `compare_server_default=True`(默认不开,改类型/默认值会漏)

### 7.2 演进红线

1. **不要修改已 apply 的 revision** — 新建 revision 演进。CI 中 `alembic check` 阻止 pending 漂移
2. **autogen 不可盲信** — `alembic revision --autogenerate -m "..."` 后**必须人工 review**;以下场景必错或漏:
   - 重命名(autogen 看作 drop + add → 数据丢失)
   - CHECK 约束(autogen 部分版本忽略)
   - 部分索引 WHERE 子句
   - pgvector 列(autogen 不识别 `Vector(384)` 维度变更)
   - 触发器 / function
3. **破坏性变更走两步迁移**:
   ```
   删字段:  add new col → 双写 deploy → 数据回填 → 删旧 col deploy
   改非空:  add nullable col → 数据回填 → set not null deploy
   改类型:  add new col(新类型) → 双写 → 数据回填 → 删旧 col
   ```
4. **migration 必须 reversible** — `downgrade()` 必填且能跑通(`alembic downgrade -1` 在 CI 跑)
5. **数据 migration 与 schema migration 分开 revision**:
   ```python
   # 错:同一 revision 既改 schema 又跑 UPDATE
   # 对:0010_add_xxx.py(只改 schema), 0011_backfill_xxx.py(只跑数据)
   ```
   理由:schema migration 几秒,数据 migration 可能几分钟,失败回滚粒度不同
6. **不要在 migration 里 import ORM Model** — Model 会跟着代码版本漂移,旧 migration 在新代码下跑会炸;用 `op.execute("INSERT INTO ...")` 或临时定义 `sa.Table(...)`

### 7.3 命名与 commit

- revision 文件名:`{4位序号}_{动作}_{对象}.py`,如 `0007_add_embedding_to_ai_reports.py`
- 一个 commit = 一个 revision(参见 [skills/backend-engineer.md §Commit 约定](../skills/backend-engineer.md))
- commit message 写 revision id + 一句话变更摘要

### 7.4 生产 apply 流程

```bash
# 1) 本地 → 测试环境
uv run alembic upgrade head

# 2) 生产前 dry-run
uv run alembic upgrade head --sql > pending.sql   # 给 DBA review

# 3) 生产 apply(滚动,只有一台应用先跑 migration,其它后续)
uv run alembic upgrade head

# 4) 失败回滚
uv run alembic downgrade -1
```

**不允许**:
- `alembic stamp head` 跳过 migration
- 手工在生产 DB 执行 `ALTER TABLE`(必须走 revision,任何改动都要 IaC)

---

## 8. 索引策略

### 8.1 索引清单(归口 [Backend-Architecture §5](./Backend-Architecture_v0.1.md) + 本文补)

| 表 | 索引 | 类型 | 服务于 |
|---|---|---|---|
| users | `idx_users_role WHERE status='active'` | btree 部分索引 | 管理后台按角色筛 |
| users | `users(phone)` UNIQUE | btree | 登录查询 |
| memberships | `uq_membership_current WHERE is_current` | btree 部分唯一 | 取当前会员 |
| token_quotas | `(user_id, period_yyyymm)` UNIQUE | btree | 月度配额查询 |
| cases | `idx_cases_user(user_id, updated_at DESC)` | btree | 我的案例分页 |
| cases | `idx_cases_status WHERE status IN (...)` | btree 部分索引 | Arq worker 拉待处理 |
| cases | `idx_cases_intents WHERE sell_intent OR ...` | btree 部分索引 | 高价值意向看板 |
| cases | `idx_cases_search USING GIN(to_tsvector(...))` | GIN | 全文搜索(M4 简单版) |
| cases | `idx_cases_embedding USING ivfflat` | ivfflat | RAG 召回(M4 默认不查) |
| case_files | `idx_case_files_case(case_id)` | btree | 案例详情拉文件 |
| ai_reports | `idx_ai_reports_case_latest(case_id, report_type, created_at DESC)` | btree | 取最新版本 |
| ai_call_logs | `idx_ai_call_logs_user(user_id, created_at DESC)` | btree | 用户调用账单 |
| ai_call_logs | `idx_ai_call_logs_failed WHERE status<>'success'` | btree 部分索引 | 失败率告警 |
| knowledge_files | `idx_knowledge_embedding ... WHERE enabled` | ivfflat 部分索引 | RAG 召回 |
| admin_operation_logs | `idx_admin_logs_admin(admin_id, created_at DESC)` | btree | 管理员行为审计 |
| sms_codes | `idx_sms_codes_phone_active(phone, expires_at) WHERE consumed_at IS NULL` | btree 部分索引 | 验证码查找 |

### 8.2 索引补加原则

- **加索引前先 EXPLAIN ANALYZE** — `seq_scan` 行数 < 1k 不加;`Filter` 选择性 < 5% 加
- **复合索引最左前缀原则** — `(user_id, updated_at)` 服务 `WHERE user_id=? ORDER BY updated_at` 与 `WHERE user_id=?`,但不服务 `WHERE updated_at>?`
- **ivfflat lists 参数**:`lists = sqrt(rows)`,M4 估算 < 2500 行 → `lists=50` 即可;数据量过万后再调
- **不加索引的场景**:写多读少(`ai_call_logs.error_message`)、低基数(`status` 只有 4 值时不要单独建)

### 8.3 索引 review 流程

新 PR 加索引时,description 必须贴:
- `EXPLAIN ANALYZE` 加索引前后对比
- 表当前行数 + 预估增长率
- 索引体积估算(`pg_size_pretty(pg_relation_size('idx_xxx'))`)

---

## 9. 数据保留 / 归档 / 备份

### 9.1 保留策略矩阵

| 数据 | 保留 | 归档时机 | 归档目标 |
|---|---|---|---|
| `cases` / `case_files` | 永久 | `status='archived'` 6 个月后冷存 | OSS 冷归档 |
| `ai_reports` | 永久 | 不归档(报告版本溯源) | — |
| `ai_call_logs` | 6 个月 | 跨月迁移 | `ai_call_logs_archive` 表 / 离线 Parquet |
| `ocr_results` | 6 个月 | 跨月迁移 | `ocr_results_archive` 表 |
| `admin_operation_logs` | **永久,禁删** | 季度归档 | 不动 / OSS 备份 |
| `sms_codes` | 30 天 | cron 硬删 | — |
| `import_jobs` | 1 年 | 跨年迁移 | `import_jobs_archive` 表 |

### 9.2 归档作业(Arq cron)

```python
# backend/app/workers/jobs/archive.py
async def archive_old_ai_call_logs(ctx):
    cutoff = datetime.utcnow() - timedelta(days=180)
    await session.execute("""
      WITH moved AS (
        DELETE FROM ai_call_logs WHERE created_at < :cutoff
        RETURNING *
      )
      INSERT INTO ai_call_logs_archive SELECT * FROM moved
    """, {"cutoff": cutoff})
```

cron 表达式:每周日 02:00 UTC+8 跑一次。

### 9.3 备份

- **`pgbackrest`** 每日全量 + 每 6 小时增量;保留 14 天
- 备份目标:阿里云 OSS 同区域 Bucket(不出区免出口费),跨区域复制到杭州/北京备灾
- 恢复演练:**季度一次**,从前一天备份恢复到测试环境,跑 smoke test
- 恢复时间目标 RTO < 1h;恢复点目标 RPO < 6h

详见 [Backend-Deployment-Guide(待产出)](./Backend-Deployment-Guide_v0.1.md)。

### 9.4 OSS 文件生命周期(与 DB 行同寿)

- `cases.status='archived'` 6 个月后:`case_files.oss_key_*` 迁阿里云 OSS 归档存储
- 用户删除案例(`status='archived'` 1 年后):OSS 永久删除 + DB 行加 `deleted_at`(不物理删,留痕)
- 知识文件:跟随 `knowledge_files.enabled=false` 7 天后归档,但**不删 embedding**(可能仍被 RAG 命中)

---

## 10. 种子数据(Alembic data revision 落)

### 10.1 系统账号

```python
# 0002_seed_super_admin.py
def upgrade():
    op.execute("""
      INSERT INTO users (phone, role, status, nickname, created_at, updated_at)
      VALUES ('+8600000000000', 'super_admin', 'active', '系统超管',
              now(), now())
      ON CONFLICT (phone) DO NOTHING
    """)
```

> 真实手机号 / 密码哈希由部署时 `python -m app.scripts.bootstrap_admin --phone xxx --password xxx` 注入,**不**在 migration 里写明文。

### 10.2 字典数据

种子项(写入 Alembic 0001 之后的 `seed_*.py`):

- `knowledge_files.file_type` 枚举说明(不入表,在代码常量)
- 默认 token_quotas 模板(由 `Settings.MEMBERSHIP_QUOTA_DEFAULTS` 在用户开通会员时按月生成,**不**在 migration 预生成)

### 10.3 不入种子的数据

- ❌ Mock 案例(由 `seed_mock_data.py` 脚本独立跑,带 `is_mock=true`,生产 env 禁用)
- ❌ 真实样本数据(待业务方提供,详见 [tracker §2.4](./discussions/M4-backend-rollout-tracker.md))

---

## 11. 测试数据契约

### 11.1 testcontainers 起真 Postgres

```python
# backend/tests/conftest.py
import pytest_asyncio
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine

@pytest_asyncio.fixture(scope="session")
async def pg_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        # 装 pgvector
        pg.exec("psql -U test -c 'CREATE EXTENSION vector'")
        yield pg

@pytest_asyncio.fixture
async def db_session(pg_container):
    engine = create_async_engine(pg_container.get_connection_url())
    # 跑 Alembic 到 head
    from alembic.config import Config
    from alembic import command
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", pg_container.get_connection_url())
    command.upgrade(cfg, "head")
    # 提供 session...
```

### 11.2 Fixture 数据

- `factories/` 用 `polyfactory` 给每张表造 Pydantic / SQLAlchemy 双层 factory
- 所有测试数据 `is_mock=true`(便于 cleanup 与生产隔离训练)
- 跨表 fixture:`case_with_files_and_report(...)` 一次造完整案例链,避免每个测试重复

### 11.3 Migration 测试

- `tests/test_migrations.py`:
  - `alembic upgrade head` 跑通
  - `alembic downgrade base` 能回到初始(reversible)
  - autogen 应生成空 diff(防 ORM/DDL 漂移):`alembic check` 退出码 = 0

---

## 12. 字段裁剪映射(权限 ↔ 13 字段)

> 对应 [Product-Spec §15.4](./Product-Spec_v0.4.md) 13 字段 + [§16 报告权限](./Product-Spec_v0.4.md)。后端 `crop_report_for_user(report, user.tier)` 返回对应 tier 的 Pydantic 模型,**物理丢弃**未声明字段。

| AI 字段 | free | basic | pro | business | business_pro | admin | 客户简洁版 |
|---|---|---|---|---|---|---|---|
| `material_hint`(材质倾向) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `process_risk`(处理风险) | ✅(简) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅(简) |
| `species_water`(种水/颜色/结构) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `cert_summary`(证书摘要) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `evidence_warning`(证据不足提示) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `price_range`(价格区间) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `recycle_price`(回收价区间) | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `liquidity`(流通性) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `buy_recommendation`(是否建议入手) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `need_reinspect`(是否建议复检) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `risk_level`(风险等级) | ✅(粗) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅(粗) |
| `customer_brief`(客户简洁版文案) | — | — | — | — | — | — | ✅ |
| `disclaimer`(免责声明) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `negotiation_strategy`(压价策略) | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |
| `channel_hint`(渠道判断) | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| `similar_cases`(相似历史案例) | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| `admin_note`(管理员备注) | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

> 注:此表是 **schema 维度** 的裁剪定义;**API 维度** 由 `app/schemas/report.py` 的 `ReportFree / ReportBasic / ReportPro / ReportBusiness / ReportBusinessPro / ReportAdmin / ReportCustomerBrief` 7 个 Pydantic 模型物理实现。`crop_report_for_user()` 是唯一裁剪入口,**禁止**前端裁剪(参见 [Product-Spec §17.3](./Product-Spec_v0.4.md))。

---

## 13. 与前端类型的契约

- 后端 OpenAPI:`uv run python -m app.scripts.export_openapi > openapi.json`
- 前端类型:`openapi-typescript openapi.json -o web/lib/types/api.ts`
- **`web/lib/types/domain.ts` 不要手写**;由 `api.ts` re-export + 必要时窄化
- CI 检查:`openapi-typescript --check`,字段漂移 fail

### 13.1 字段命名对齐

- DB:`snake_case`(`material_hint`)
- API JSON:**驼峰**(`materialHint`)— Pydantic v2 用 `alias_generator=to_camel` + `populate_by_name=True`
- TS:同 API,驼峰(`materialHint`)

---

## 14. 与 tracker §二 关联的未决项

本文未涉及但需业务方拍板(详见 [docs/discussions/M4-backend-rollout-tracker.md §二](./discussions/M4-backend-rollout-tracker.md)):

- [ ] §2.3 M3 vs M4 顺序 — 决定本文 schema 何时落 Postgres
- [ ] §2.4 真实样本(影响 `is_mock=false` 行的首次产出)
- [ ] §2.5 AI 工程接手时机 — 决定 `ai_reports.output_json` 何时填实
- [ ] §2.6 前端双写期灰度策略 — 决定 schema 与 mock JSON 共存的过渡期

---

## 维护规则

1. 每次新增 / 改字段:**先改 [Backend-Architecture §5](./Backend-Architecture_v0.1.md) DDL,再同步本文,最后 Alembic revision**
2. 索引调整:在 §8.1 加行 + EXPLAIN ANALYZE 数据
3. 保留策略变更:§9.1 + §9.2 cron 同时改
4. 裁剪映射变更:§12 + `app/schemas/report.py` Pydantic 类同时改;`tests/test_rbac_redlines.py` 加 case
5. M4 实施开工后,本文随代码迁入 `backend/docs/schema.md`,与 ORM 在同一仓维护
