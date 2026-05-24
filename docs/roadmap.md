# 曜齐 YAOQI 玉石珠宝鉴定估价助手 — Roadmap

> 总览文件,按 AGENT.md §2 工作流维护。每个路标(里程碑)对应 [`milestones/`](./milestones/) 下的独立文件。

## 项目背景

定位:**奢侈品下游服务商**,服务范围聚焦 **玉石 + 珠宝**(明确不含箱包/手表/贵金属/古董字画),为客户的"购买、质量鉴定、定价"三件事提供 AI 辅助。

参考文档:

| 文档 | 作用 |
|------|------|
| [Product-Spec_v0.4.md](./Product-Spec_v0.4.md) | 产品边界、MVP Level 划分、数据资产策略 |
| [UI-Spec_v0.3.1.md](./UI-Spec_v0.3.1.md) | UI 规范(配色 / 字体 / 21 个页面 / 验收) |
| [Technical-Spec_v0.1.md](./Technical-Spec_v0.1.md) | 技术栈、API、数据库 Schema、OSS 安全 |

技术栈(本轮拍板):**Next.js 15 App Router + TypeScript + Tailwind CSS + shadcn/ui**,Mock 数据通过 Next.js Route Handlers 返回。

---

## 里程碑总览

| ID | 名称 | 状态 | MVP Level | 范围 | 链接 |
|----|------|------|-----------|------|------|
| M1 | Foundation | 🟢 已完成 (2026-05-22) | Level 1 → 2 准备 | 项目骨架 + 设计系统 + 共享组件 + mock 数据契约 | [M1-foundation.md](./milestones/M1-foundation.md) |
| M2 | User Pages | 🟢 已完成 (2026-05-22) | Level 2 | 用户端 10 个页面,登录 → 报告全流程可点击 | [M2-user-pages.md](./milestones/M2-user-pages.md) |
| M3 | Admin Pages | ⚪ 未开始 | Level 2 | 管理后台 11 个页面 | [M3-admin-pages.md](./milestones/M3-admin-pages.md)(待创建)|
| M4 | Real Backend | 🟡 进行中 (Stage 1+2/4 完成 2026-05-24) | Level 3 | 接真后端 / 数据库 / OSS / OCR / AI | [M4-real-backend.md](./milestones/M4-real-backend.md) |
| M5 | Pre-public Beta | ⚪ 未开始 | Level 4 | 域名 / HTTPS / 协议 / 备份 / 安全验收 | (待规划)|

状态图例:🟢 已完成 / 🟡 进行中 / ⚪ 未开始 / 🔴 阻塞

---

## 当前 Sprint 焦点

**M4 Stage 1 + Stage 2 已完成 (2026-05-24)**:`backend/` FastAPI 骨架(Stage 1)+ 持久层(Stage 2,13 张 ORM + Alembic 0001_init + testcontainers per-test SAVEPOINT + `/health.db`)落地。`uv run pytest -v` 27 用例全绿(Stage 1 × 10 + Stage 2 × 17),`uv run ruff check / mypy --strict` 全清,`alembic upgrade/downgrade/check` 三连验证 OK。详见 [M4-real-backend.md](./milestones/M4-real-backend.md)。

**M4 进度速览**(4 Stage):

| Stage | 范围 | 状态 |
|---|---|---|
| Stage 1: Foundation | 骨架 + `/health(self)` + 信封 + Request-ID + Dockerfile + pytest 骨架 | 🟢 完成 2026-05-24 |
| Stage 2: Persistence | 13 张 ORM + Alembic 单 revision 全落 + testcontainers(pgvector/pg16)+ `/health` 扩 `checks.db` | 🟢 完成 2026-05-24 |
| Stage 3: Tier Schemas | 7 个 tier Pydantic + 服务端字段裁剪(覆盖详情/客户简洁版) | ⚪ 未启动 |
| Stage 4: API + Integrations | 路由 stub + JWT + RBAC + DAO/Service + `LLMClient` + OSS/OCR/短信 client + Seed | ⚪ 未启动 |

**M4 §17 前置文档进度 5/6**(`Backend-API-Spec_v0.1.yaml` 留 Stage 4 后由 `/openapi.json` 自动导出):
[skills/backend-engineer.md](../skills/backend-engineer.md) / [skills/ai-integration-engineer.md](../skills/ai-integration-engineer.md) / [Backend-Architecture](./Backend-Architecture_v0.1.md) / [Backend-Database-Schema](./Backend-Database-Schema_v0.1.md) / [Backend-Security-Checklist](./Backend-Security-Checklist_v0.1.md) / [Backend-Deployment-Guide](./Backend-Deployment-Guide_v0.1.md) — 全 🟢 已产出。

**M4 Stage 1+2 附带的工程约定**(跨会话生效):

- AGENT.md 新增「代码规范 / 注释即文档」7+1 条 — `class` / `def` / 关键业务逻辑 / 关键变量必须中文 docstring + WHY 注释,**覆盖默认"少注释"规则**。Stage 2~4 全部继承。
- 信封 `{ok, data, error, source}` 四字段对齐前端 `web/lib/types/domain.ts`,`extra="forbid"` 锁死;失败信封禁泄漏内部异常类型(测试守住)。
- **不引入 psycopg/psycopg2**(D8):alembic env.py 用 async pattern + `_coerce_async_driver()` 统一升 asyncpg。
- alembic 触发器用 `clock_timestamp()` 而非 `now()`(同事务时间戳塌陷防护);autogen 假阳性走 `include_object` 白名单(9 条 raw SQL 索引)。
- testcontainers 用 `pgvector/pgvector:pg16`(D3)+ per-test SAVEPOINT(D4);`/health.db` 失败 HTTP 仍 200 仅标 `degraded`(D5)。

**下一步候选**(等业务方拍):

- **A. 启动 M4 Stage 3**(7 tier Pydantic schema + `cropReportForUser` 服务端裁剪;工程方独立可推)— 推荐
- **B. 等物料解锁后跨 Stage 推进** — KMS / OSS Bucket / ICP / Azure ownership,见 [M4-materials-acquisition-workpack.md](./discussions/M4-materials-acquisition-workpack.md)
- **C. 回头铺 M3** 管理后台 11 页

讨论决策日志详见 [discussions/M4-backend-rollout-tracker.md](./discussions/M4-backend-rollout-tracker.md)。

---

## 待业务方决策的开放问题

参见 [smooth-juggling-thimble.md 计划文件 "待解决的开放问题" 节](../../../.claude/plans/smooth-juggling-thimble.md) — 不在本仓库内,需要时由 AI 代理回读。

主要待确认项:

- ~~真实品牌 Logo / VI 手册是否存在?~~ → 2026-05-22 拍板:暂无,`BrandLogo` 占位
- 真实案例样本(玉石/珠宝图片 + 证书扫描件 + 报告文本)是否能提供?
- ~~5 档会员等级解锁映射是否符合商业策略?~~ → 2026-05-22 拍板:差异核心为月度 Token 配额(2 万 → 200 万)
- 后端正式接入时选 NestJS / Next.js Server Actions / FastAPI?
- OSS 上传走中转还是预签名直传?

---

## 工作流约定(摘自 AGENT.md)

1. 先制定计划,有争议点 Human-in-loop 讨论清楚后再开发
2. 每个里程碑独立文件跟踪进度
3. 每完成一个任务,在路标文件中记录完成内容
4. 每完成一个路标,更新本文件的状态
5. 及时补充测试和执行 git commit,每个 commit 包含一个完整功能点
6. 及时更新 `docs/` 下的相关文档
