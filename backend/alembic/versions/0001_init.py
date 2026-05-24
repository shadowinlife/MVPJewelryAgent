"""init: 13 tables + extensions + check constraints + indexes + triggers + pgvector.

Revision ID: 0001_init
Revises:
Create Date: 2026-05-24

**手写**(非 autogen):因为以下内容 autogen 全部漏(Schema §7 红线 2):
- CHECK 约束
- 部分索引 WHERE 子句
- pgvector 列类型(Vector(384))与 ivfflat 索引
- PL/pgSQL 函数 + 触发器

按段分块:
1. CREATE EXTENSION × 3
2. 13 张表(依赖顺序:users → memberships/token_quotas → cases →
   case_files/ocr_results/ai_reports/ai_call_logs → admin_reviews/
   admin_operation_logs → knowledge_files → import_jobs → sms_codes)
3. CHECK 约束(VARCHAR + CHECK 替代 ENUM,Schema §1 原则)
4. 部分索引 / GIN 全文索引 / ivfflat 向量索引
5. set_updated_at() function + 7 张表的触发器

downgrade() 严格 reverse 顺序;扩展不 drop(跨 revision 共享)。
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_init"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# === 哪些表挂 set_updated_at() 触发器(有 updated_at 列即挂)===
_TABLES_WITH_UPDATED_AT = (
    "users",
    "cases",
    "ocr_results",
    "ai_reports",
    "knowledge_files",
    "import_jobs",
    "admin_reviews",
)


def upgrade() -> None:
    """创建扩展 → 表 → 约束 → 索引 → 触发器。"""

    # === 1. 扩展 ===
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # === 2. 表(依赖顺序)===

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("phone", sa.String(20), unique=True, nullable=False),
        sa.Column("phone_verified_at", sa.DateTime(timezone=True)),
        sa.Column("wechat_openid", sa.String(64), unique=True),
        sa.Column("wechat_unionid", sa.String(64)),
        sa.Column("nickname", sa.String(64)),
        sa.Column("avatar_url", sa.Text),
        sa.Column("role", sa.String(20), nullable=False, server_default="free_user"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_mock", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
    )

    # --- memberships ---
    op.create_table(
        "memberships",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tier", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("granted_by_admin_id", sa.BigInteger, sa.ForeignKey("users.id")),
        sa.Column("grant_reason", sa.Text),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_mock", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_memberships_user", "memberships", ["user_id"])

    # --- token_quotas ---
    op.create_table(
        "token_quotas",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_yyyymm", sa.Integer, nullable=False),
        sa.Column("tokens_total", sa.Integer, nullable=False),
        sa.Column("tokens_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reports_total", sa.Integer, nullable=False),
        sa.Column("reports_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("admin_extra", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_mock", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "period_yyyymm", name="uq_token_quotas_user_period"),
    )

    # --- cases ---
    op.create_table(
        "cases",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("case_no", sa.String(32), unique=True, nullable=False),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("sub_category", sa.String(40)),
        sa.Column("purpose", sa.String(20), nullable=False),
        sa.Column("source_channel", sa.String(40)),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("risk_level", sa.String(10)),
        sa.Column("liquidity_level", sa.String(20)),
        sa.Column("material_guess", sa.String(40)),
        sa.Column("quality_level", sa.String(20)),
        sa.Column("weight_text", sa.String(40)),
        sa.Column("dimensions", sa.String(80)),
        sa.Column("bead_size", sa.String(40)),
        sa.Column("ring_size", sa.String(40)),
        sa.Column("certificate_org", sa.String(40)),
        sa.Column("certificate_no", sa.String(64)),
        sa.Column("purchase_price_cents", sa.BigInteger),
        sa.Column("asking_price_cents", sa.BigInteger),
        sa.Column("auction_start_price_cents", sa.BigInteger),
        sa.Column("deal_price_cents", sa.BigInteger),
        sa.Column("expected_price_cents", sa.BigInteger),
        sa.Column("seller_text", sa.Text),
        sa.Column("user_note", sa.Text),
        sa.Column("admin_note", sa.Text),
        sa.Column("sell_intent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("recycle_intent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("consignment_intent", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("data_source", sa.String(20), nullable=False, server_default="real"),
        sa.Column("is_mock", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("embedding", Vector(384)),
        sa.Column("embedding_model", sa.String(60)),
        sa.Column("embedding_generated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_cases_user", "cases", ["user_id", "updated_at"])

    # --- case_files ---
    op.create_table(
        "case_files",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("case_id", sa.BigInteger, sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("file_type", sa.String(40), nullable=False),
        sa.Column("original_filename", sa.Text),
        sa.Column("mime_type", sa.String(80)),
        sa.Column("size_bytes", sa.BigInteger),
        sa.Column("oss_bucket", sa.String(80), nullable=False),
        sa.Column("oss_key_original", sa.Text, nullable=False),
        sa.Column("oss_key_preview", sa.Text),
        sa.Column("oss_key_watermarked", sa.Text),
        sa.Column("width", sa.Integer),
        sa.Column("height", sa.Integer),
        sa.Column("upload_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("is_private", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_mock", sa.Boolean, nullable=False, server_default="false"),
        # 不挂 created_at / updated_at:case_files 是文件元数据(不可变,
        # OSS 自带 last-modified),且 §5.5 触发器清单不含 case_files,
        # 强行加 updated_at 列但无 trigger 会让字段说谎
    )
    op.create_index("idx_case_files_case", "case_files", ["case_id"])

    # --- ocr_results ---
    op.create_table(
        "ocr_results",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("case_id", sa.BigInteger, sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_id", sa.BigInteger, sa.ForeignKey("case_files.id"), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("raw_text", sa.Text),
        sa.Column("parsed_json", postgresql.JSONB),
        sa.Column("user_corrected_json", postgresql.JSONB),
        sa.Column("confidence_level", sa.String(10)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text),
        sa.Column("is_mock", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- ai_reports ---
    op.create_table(
        "ai_reports",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("case_id", sa.BigInteger, sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("report_type", sa.String(20), nullable=False),
        sa.Column("model_name", sa.String(60)),
        sa.Column("deployment_name", sa.String(80)),
        sa.Column("prompt_version", sa.String(20)),
        sa.Column("input_summary_json", postgresql.JSONB),
        sa.Column("output_json", postgresql.JSONB),
        sa.Column("full_markdown", sa.Text),
        sa.Column("user_visible_markdown", sa.Text),
        sa.Column("customer_simple_markdown", sa.Text),
        sa.Column("price_fields_json", postgresql.JSONB),
        sa.Column("risk_fields_json", postgresql.JSONB),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text),
        sa.Column("embedding", Vector(384)),
        sa.Column("is_mock", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "idx_ai_reports_case_latest",
        "ai_reports",
        ["case_id", "report_type", "created_at"],
    )

    # --- ai_call_logs(无 is_mock,无 updated_at)---
    op.create_table(
        "ai_call_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.BigInteger, sa.ForeignKey("users.id")),
        sa.Column("case_id", sa.BigInteger, sa.ForeignKey("cases.id")),
        sa.Column("task_type", sa.String(40), nullable=False),
        sa.Column("model_name", sa.String(60)),
        sa.Column("prompt_version", sa.String(20)),
        sa.Column("input_token_count", sa.Integer),
        sa.Column("output_token_count", sa.Integer),
        sa.Column("cost_estimate_cents", sa.BigInteger),
        sa.Column("latency_ms", sa.Integer),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("error_message", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_ai_call_logs_user", "ai_call_logs", ["user_id", "created_at"])

    # --- admin_reviews ---
    op.create_table(
        "admin_reviews",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("case_id", sa.BigInteger, sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("admin_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("review_status", sa.String(20), nullable=False),
        sa.Column("manual_material_judgment", sa.Text),
        sa.Column("manual_price_opinion", sa.Text),
        sa.Column("manual_risk_note", sa.Text),
        sa.Column("follow_up_status", sa.String(30)),
        sa.Column("is_mock", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- admin_operation_logs(无 is_mock,无 updated_at)---
    op.create_table(
        "admin_operation_logs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("admin_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("target_type", sa.String(40)),
        sa.Column("target_id", sa.BigInteger),
        sa.Column("detail_json", postgresql.JSONB),
        sa.Column("ip_address", postgresql.INET),
        sa.Column("user_agent", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_admin_logs_admin", "admin_operation_logs", ["admin_id", "created_at"])

    # --- knowledge_files ---
    op.create_table(
        "knowledge_files",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("file_type", sa.String(40), nullable=False),
        sa.Column("oss_key", sa.Text, nullable=False),
        sa.Column("original_filename", sa.Text),
        sa.Column("parsed_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("parsed_json", postgresql.JSONB),
        sa.Column("content_summary", sa.Text),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("uploaded_by_admin_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("embedding", Vector(384)),
        sa.Column("embedding_model", sa.String(60)),
        sa.Column("is_mock", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- import_jobs ---
    op.create_table(
        "import_jobs",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("file_id", sa.BigInteger, sa.ForeignKey("knowledge_files.id")),
        sa.Column("job_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("total_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("success_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_detail_json", postgresql.JSONB),
        sa.Column("created_by_admin_id", sa.BigInteger, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("is_mock", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # --- sms_codes(无 is_mock,无 updated_at)---
    op.create_table(
        "sms_codes",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("code_hash", sa.String(128), nullable=False),
        sa.Column("purpose", sa.String(20), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True)),
        sa.Column("attempts", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("ip_address", postgresql.INET),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # === 3. CHECK 约束(VARCHAR + CHECK 替代 ENUM)===

    op.execute(
        "ALTER TABLE users ADD CONSTRAINT chk_users_role CHECK ("
        "role IN ('guest','free_user','member_basic','member_pro',"
        "'business','business_pro','admin','super_admin'))"
    )
    op.execute(
        "ALTER TABLE users ADD CONSTRAINT chk_users_status CHECK ("
        "status IN ('active','disabled'))"
    )
    op.execute(
        "ALTER TABLE memberships ADD CONSTRAINT chk_memberships_tier CHECK ("
        "tier IN ('free','basic','pro','business','business_pro'))"
    )
    op.execute(
        "ALTER TABLE token_quotas ADD CONSTRAINT chk_period_yyyymm CHECK ("
        "period_yyyymm BETWEEN 202001 AND 209912 "
        "AND (period_yyyymm % 100) BETWEEN 1 AND 12)"
    )
    op.execute(
        "ALTER TABLE token_quotas ADD CONSTRAINT chk_tokens_nonneg CHECK ("
        "tokens_total >= 0 AND tokens_used >= 0 AND admin_extra >= 0)"
    )
    op.execute(
        "ALTER TABLE cases ADD CONSTRAINT chk_cases_status CHECK ("
        "status IN ('draft','pending','analyzing','analyzed',"
        "'pending_recheck','archived'))"
    )
    op.execute(
        "ALTER TABLE cases ADD CONSTRAINT chk_cases_purpose CHECK ("
        "purpose IN ('buy','sell','recycle','auction','study',"
        "'live_select','customer_consult','business_select'))"
    )
    op.execute(
        "ALTER TABLE case_files ADD CONSTRAINT chk_case_files_file_type CHECK ("
        "file_type IN ('jewelry_natural_light','jewelry_strong_light','jewelry_backlight',"
        "'jewelry_detail','certificate','receipt','other_doc'))"
    )
    op.execute(
        "ALTER TABLE case_files ADD CONSTRAINT chk_case_files_upload_status CHECK ("
        "upload_status IN ('pending','uploaded','processing','ready','failed'))"
    )
    op.execute(
        "ALTER TABLE ai_reports ADD CONSTRAINT chk_ai_reports_type CHECK ("
        "report_type IN ('internal_full','user_visible','customer_simple','admin_reviewed'))"
    )
    op.execute(
        "ALTER TABLE ai_reports ADD CONSTRAINT chk_ai_reports_status CHECK ("
        "status IN ('pending','generating','succeeded','failed'))"
    )
    op.execute(
        "ALTER TABLE ai_call_logs ADD CONSTRAINT chk_ai_call_logs_status CHECK ("
        "status IN ('success','failed','timeout'))"
    )
    op.execute(
        "ALTER TABLE knowledge_files ADD CONSTRAINT chk_knowledge_files_type CHECK ("
        "file_type IN ('personal_case','market_observation','auction_rule',"
        "'gb_certificate_sop','live_sales_script','other'))"
    )
    op.execute(
        "ALTER TABLE knowledge_files ADD CONSTRAINT chk_knowledge_files_parsed_status CHECK ("
        "parsed_status IN ('pending','parsing','parsed','failed'))"
    )
    op.execute(
        "ALTER TABLE admin_operation_logs ADD CONSTRAINT chk_admin_action CHECK ("
        "action IN ('view_original_image','export_cases','update_membership',"
        "'grant_quota','delete_case','review_case','import_knowledge',"
        "'login_admin','logout_admin','create_admin','disable_user'))"
    )

    # === 4. 部分索引 / GIN / ivfflat ===

    # users:按角色筛选(active 用户)
    op.execute(
        "CREATE INDEX idx_users_role ON users(role) WHERE status = 'active'"
    )

    # memberships:用户当前会员唯一(每用户最多 1 行 is_current=true)
    op.execute(
        "CREATE UNIQUE INDEX uq_membership_current "
        "ON memberships(user_id) WHERE is_current"
    )

    # cases:Arq worker 拉待处理
    op.execute(
        "CREATE INDEX idx_cases_status ON cases(status) "
        "WHERE status IN ('pending','analyzing','pending_recheck')"
    )

    # cases:高价值意向看板
    op.execute(
        "CREATE INDEX idx_cases_intents ON cases(user_id) "
        "WHERE sell_intent OR recycle_intent OR consignment_intent"
    )

    # cases:全文搜索(简单版)
    op.execute(
        "CREATE INDEX idx_cases_search ON cases USING GIN ("
        "to_tsvector('simple', coalesce(title,'') || ' ' || coalesce(seller_text,'')))"
    )

    # cases:embedding ivfflat(召回开关关时不查,但索引存在)
    op.execute(
        "CREATE INDEX idx_cases_embedding ON cases "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50)"
    )

    # ai_call_logs:失败率告警
    op.execute(
        "CREATE INDEX idx_ai_call_logs_failed ON ai_call_logs(created_at) "
        "WHERE status <> 'success'"
    )

    # knowledge_files:embedding ivfflat(只对启用的)
    op.execute(
        "CREATE INDEX idx_knowledge_embedding ON knowledge_files "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50) "
        "WHERE enabled"
    )

    # sms_codes:活码查找
    op.execute(
        "CREATE INDEX idx_sms_codes_phone_active ON sms_codes(phone, expires_at) "
        "WHERE consumed_at IS NULL"
    )

    # === 5. set_updated_at() function + 触发器 ===

    # 用 clock_timestamp() 而非 now() / transaction_timestamp():
    # 后者在事务内返回事务开始时间,同事务内 INSERT + UPDATE 会让
    # created_at 与 updated_at 取到相同值,触发器实际"看不出动作";
    # clock_timestamp() 是真实墙钟,每次调用都推进,既符合直觉也方便审计。
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
        BEGIN
          NEW.updated_at = clock_timestamp();
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )

    for tbl in _TABLES_WITH_UPDATED_AT:
        op.execute(
            f"CREATE TRIGGER trg_{tbl}_updated_at BEFORE UPDATE ON {tbl} "
            f"FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
        )


def downgrade() -> None:
    """严格 reverse 顺序:触发器 → function → 索引 → 表;扩展不 drop。"""

    # 触发器(先 drop,否则下面 drop function 报依赖)
    for tbl in _TABLES_WITH_UPDATED_AT:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{tbl}_updated_at ON {tbl}")

    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")

    # 部分索引(drop_table 也会 cascade drop,但显式更清晰)
    op.execute("DROP INDEX IF EXISTS idx_sms_codes_phone_active")
    op.execute("DROP INDEX IF EXISTS idx_knowledge_embedding")
    op.execute("DROP INDEX IF EXISTS idx_ai_call_logs_failed")
    op.execute("DROP INDEX IF EXISTS idx_cases_embedding")
    op.execute("DROP INDEX IF EXISTS idx_cases_search")
    op.execute("DROP INDEX IF EXISTS idx_cases_intents")
    op.execute("DROP INDEX IF EXISTS idx_cases_status")
    op.execute("DROP INDEX IF EXISTS uq_membership_current")
    op.execute("DROP INDEX IF EXISTS idx_users_role")

    # 表(reverse 依赖顺序)
    op.drop_table("sms_codes")
    op.drop_table("import_jobs")
    op.drop_table("knowledge_files")
    op.drop_table("admin_operation_logs")
    op.drop_table("admin_reviews")
    op.drop_table("ai_call_logs")
    op.drop_table("ai_reports")
    op.drop_table("ocr_results")
    op.drop_table("case_files")
    op.drop_table("cases")
    op.drop_table("token_quotas")
    op.drop_table("memberships")
    op.drop_table("users")

    # 扩展不 drop —— 跨 revision 共享,数据库可能还有其它使用者
