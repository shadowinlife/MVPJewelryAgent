# M4 后端铺设 — 讨论进度跟踪

> 临时讨论区。用来跟踪**已有结论**与**尚未讨论**的部分,避免重复对齐。
> 起始:2026-05-22 / 最后更新:2026-06-01(Stage 4 LLM 子系统落地 + DashScope 连通验证)
> 父文档:[Backend-Architecture_v0.1.md](../Backend-Architecture_v0.1.md)、[roadmap.md](../roadmap.md)、[milestones/M4-real-backend.md](../milestones/M4-real-backend.md)

---

## 一、已有结论(2026-05-22 拍板)

### 1.1 后端核心选型(对应 Backend-Architecture §16)

| # | 议题 | 决议 |
|---|---|---|
| 0 | 后端语言 / 框架 | ✅ FastAPI(Python 3.12) |
| 1 | 异步队列 | ✅ Arq(排除 Celery / BullMQ) |
| 2 | 微信登录 | ✅ 推 P1;M4 只做手机号 + 邮箱 + 密码 |
| 3 | OSS 上传通道 | ✅ 阿里云 OSS + STS 直传(文件不过后端) |
| 4 | 短信服务商 | ✅ 阿里云短信 |
| 5 | LLM 提供方 | ✅ **prod: Azure OpenAI @ HK**;**dev/staging: DashScope qwen3.7-max**(2026-06-01 确认连通) |
| 5a | M4 AI 落地深度 | ✅ `LLMClient` Protocol 已实现 + DashScope/Azure 双 adapter + admin 配置页动态切换;DashScope 作为开发默认不再 stub |
| 6 | RAG / pgvector | ✅ M4 装扩展 + 写入 embedding,**召回开关默认关** |
| 7 | i18n 错误码 | ✅ 推 P1(本期 `error` 用中文短句) |
| 8 | Postgres | ✅ 阿里云 RDS PostgreSQL 16(原生 pgvector) |
| 9 | LangChain / LlamaIndex / DSPy | ✅ 不引入 |

### 1.2 跨云部署拓扑(Backend-Architecture §16.1 / §9.7)

- **前端(Next.js)**:**HK 节点**(2026-05-26 决议;Vercel HK / 阿里云 HK / Cloudflare,Stage 4 前定型)
- **主体业务后端**:阿里云华东(ECS + RDS + Tair/Redis + OSS + OCR + 短信)
- **AI**:Azure OpenAI Service @ HongKong,后端跨云**公网直连**
- M4 **不**引入 API Gateway / VPN 专线;`timeout=60s` + `tenacity` 重试 + `ai_call_logs.latency_ms` 兜底
- **前端 → 后端跨境**:80-150ms 公网 RTT,MVP 可接受;Stage 4 前端调后端用绝对 URL + CORS 白名单;cookie SameSite=None+Secure
- 排除项(不要回推):OpenAI 平台直连 / 把后端整体搬到 Azure / 国内 LLM 备份 / 前端境内服务器(ICP 备案路线已废弃)

**2026-05-26 决议**:网站前端部署 HK 节点 → 工信部 ICP 备案不再需要(ICP 只针对接入境内服务器的网站);原 M-04 关键路径直接消除,详见 [M-13 HK 前端节点](./M4-materials-acquisition-workpack.md#m-13-hk-前端节点选型--域名-dns-接管新增-2026-05-26替代-m-04)。

### 1.3 §17 后续文档进度(5/6)

| 文档 | 状态 | 链接 |
|---|---|---|
| `skills/backend-engineer.md` | 🟢 已产出 | [skills/backend-engineer.md](../../skills/backend-engineer.md) |
| `skills/ai-integration-engineer.md` | 🟢 已产出 | [skills/ai-integration-engineer.md](../../skills/ai-integration-engineer.md) |
| `Backend-Database-Schema_v0.1.md` | 🟢 已产出 (2026-05-22) | [Backend-Database-Schema_v0.1.md](../Backend-Database-Schema_v0.1.md) |
| `Backend-Security-Checklist_v0.1.md` | 🟢 已产出 (2026-05-22) | [Backend-Security-Checklist_v0.1.md](../Backend-Security-Checklist_v0.1.md) |
| `Backend-Deployment-Guide_v0.1.md` | 🟢 已产出 (2026-05-23) | [Backend-Deployment-Guide_v0.1.md](../Backend-Deployment-Guide_v0.1.md) |
| `Backend-API-Spec_v0.1.yaml` | 🟡 推后 | 待 FastAPI 骨架起来后从 `/openapi.json` 自动导出 |

### 1.4 M4 实施进度(2026-05-24 更新)

实施侧迁移到 [milestones/M4-real-backend.md](../milestones/M4-real-backend.md);本节只留**阶段性结论**,细任务别复制。

| Stage | 范围 | 状态 | 完成日 |
|---|---|---|---|
| **Stage 1: Foundation** | FastAPI 骨架 + `/health(self)` + envelope / request-id 中间件 + Settings + structlog + Dockerfile + pytest 骨架(10 用例) | 🟢 完成 | 2026-05-24 |
| **Stage 2: Persistence** | 13 张 ORM + Alembic 初始迁移(扩展 + 13 表 + CHECK + 索引 + 触发器 + pgvector 列)+ testcontainers fixture(per-test SAVEPOINT)+ `/health` 扩 `checks.db` | 🟢 完成 | 2026-05-24 |
| **Stage 3: Tier Schemas** | 5 tier slot + 2 独立 schema(ReportAdmin/ReportCustomerBrief)+ CaseReport envelope + InternalReport + `crop_report_for_user` 唯一裁剪入口 + 8 条 RBAC 红线锁定(54 测试全绿) | 🟢 完成 | 2026-05-26 |
| **Stage 4: API + Integrations** | auth/cases/reports/files/ocr/memberships 路由 + JWT + RBAC + `LLMClient` + OSS/OCR/短信 client | 🟡 进行中 | — |

**Stage 4 子进度**(2026-06-01 更新):

| 子系统 | 状态 | 说明 |
|---|---|---|
| LLMClient 多 Provider 抽象 | 🟢 完成 | Protocol + DashScope adapter + Azure adapter + Fernet 加密 + factory |
| Admin 配置页(后端 API + 前端 UI) | 🟢 完成 | GET/PUT /admin/llm-config + POST test + 前端 form |
| DashScope 连通验证 | 🟢 完成 | qwen3.7-max 端到端 OK(多模态,支持图片) |
| Alembic 0002 (llm_provider_configs) | 🟢 完成 | 单行配置表 + CHECK 约束 |
| Auth(JWT + 登录/注册) | ⚪ 未启动 | — |
| Cases/Reports CRUD 路由 | ⚪ 未启动 | — |
| OSS 直传(STS 预签名) | ⚪ 未启动 | 需 M-07 |
| OCR client | ⚪ 未启动 | — |
| 短信 client | ⚪ 未启动 | 需 M-05/M-06 |
| AI 鉴定/估价业务链路 | ⚪ 未启动 | LLMClient 已就绪,待 prompt 编排 |

**Stage 1 落地附带的工程约定**(本会话引入,跨会话生效):

- AGENT.md 新增「代码规范 / 注释即文档(Code-as-Doc)」:`class` / `def` / 关键业务逻辑 / 关键变量 必须中文 docstring + WHY 注释。**覆盖 Claude Code 默认"少注释"规则**,Stage 2~4 全部继承。
- 信封 `{ok, data, error, source}` 四字段对齐前端 TS,`extra="forbid"` 锁死;失败信封**禁泄漏** `code` / `requestId` / 内部异常类型(测试守住)。
- 中间件挂载顺序固定:外层 `ErrorHandlerMiddleware`(兜底)/ 内层 `RequestIdMiddleware`(给错误日志带 request_id)。Stage 2~4 加新中间件需在 `app/main.py` 注释清楚相对位置。

**Stage 2 落地附带的工程约定**(本会话引入,跨会话生效):

- **不引入 psycopg / psycopg2**(D8):alembic env.py 用 async pattern(`asyncpg + run_sync`);`_coerce_async_driver()` 把任何前缀(包括 testcontainers 给的 `+psycopg2`)统一升级为 `+asyncpg`。Stage 3~4 任何 sync DB 工具(脚本 / 一次性任务)也走 asyncpg。
- **alembic 触发器函数用 `clock_timestamp()` 而非 `now()`**:`now()` 同事务内返回相同值,`updated_at` 触发器在同一 transaction(SAVEPOINT 隔离测试)中"看不出动作";`clock_timestamp()` 是真实墙钟,行为正确。
- **autogen 假阳性走 `include_object` 白名单**:9 条 raw SQL 维护的索引(`uq_membership_current` / `idx_*_embedding` / GIN / 部分索引)在 alembic env.py 的 `_RAW_SQL_INDEX_NAMES` 跳过 ——SQLAlchemy `Index()` 对 `postgresql_where` + `using="ivfflat"` + 表达式 GIN 支持弱,与其勉强落到 `__table_args__` 不如 raw SQL + 白名单清晰。
- **pytest 跑 alembic 同步命令必走线程隔离**:`tests/conftest.py::_run_in_thread()`;直接在 pytest event loop 里调 `command.upgrade()` 会撞 env.py 的 `asyncio.run()`。
- **testcontainers 用 `pgvector/pgvector:pg16`**(D3),自带 TCP 探活(`_wait_for_pg_ready`,不依赖 psycopg2);per-test SAVEPOINT 隔离(`join_transaction_mode="create_savepoint"`),不每用例 DROP/CREATE schema。
- **`/health.db` 失败不返 503**(D5):HTTP 仍 200,只在 `data.status="degraded"` + `data.checks.db="unavailable"` 标记;K8s liveness 看 HTTP code,readiness 才看 status。

**Stage 3 落地附带的工程约定**(本会话引入,跨会话生效):

- **`ReportAdmin` 独立 export,**不进** `CaseReport` envelope**:即便 `/api/reports/:id` 路由未来漏掉 `crop_report_for_user`,envelope 中也不会出现 `admin: null` 字段(暴露"有 admin 字段"本身就是泄漏);Stage 4 admin 路由必须显式 `build_admin_view(internal)` 才能拿到 adminNote。
- **`TIER_ORDER: Final[Mapping[ReportAudience, int]]`**:tier 排序用数字而非字符串比较(`"business_pro" < "free"` 字符串顺序反了);`_can_view(audience, "pro")` 这种业务语义封装比裸 `TIER_ORDER[audience] >= 2` 更可读。Stage 4 加新 tier(微信会员等)只改本 dict 一处。
- **"全字段齐才下发整 slot"语义**:若 `InternalReport` 中某 tier 字段部分缺失(e.g. `recycle_price=None` 但 `full_risk=["x"]`),整 `ReportPro` slot 返回 `None`,前端逻辑只判 slot 是否 null,不必逐字段判空。Stage 4 AI 模板 prompt 必须按此口径输出。
- **入口宽容、出口严格**:`InternalReport` `extra="ignore"`(AI 升级新字段不让历史报告反序列化炸开);所有 5 tier slot `extra="forbid"`(物理拒绝越权字段)。Stage 4 加新 schema 必须沿用本分层。
- **`schemas/__init__.py` 显式 re-export 模式**:项目 mypy `no_implicit_reexport=True`,必须 `from x import Y as Y` + `__all__` 双重声明 —— Stage 4 加新 schema 沿用本模式。
- **测试用 inline `_make_internal_full()` 而非 conftest fixture / polyfactory**:Stage 3 拍板"测试自包含 > 抽象工厂",reader 在单文件内能看清"测试输入长什么样";Stage 4 写 service 测试时再补抽象。

下一步候选(2026-06-01 更新):

- ✅ **§2.5 事实上已 bypass** — LLMClient 不再是 stub,DashScope 已真接入;"AI 工程接手时机"的顾虑不再阻塞 Stage 4 路由编写
- 🟡 **§2.6 前端双写期灰度策略**仍未拍板 — 但不阻塞后端路由开发,只影响前端切换顺序
- 🟢 **推荐下一步**:Auth(JWT 登录/注册)→ Cases/Files CRUD → AI 鉴定业务链路(图片 + prompt → 报告)
- 🟡 **物料并行** — M-01 ✅ 已完成;M-03 Azure 准入仍在等(但 DashScope 已可完全替代 dev);M-05/M-06/M-07/M-09 待推动

---

## 二、尚未讨论的部分(等业务方 / 待对齐)

### 2.1 ~~§17 文档进度 5/6 — 进入实施前的下一步~~(2026-05-24 已结案,迁移到 §1.4)

~~A + B 并行~~ 已拍板 + 已执行:
- ✅ **B 路径 Stage 1** 完成于 2026-05-24,产物详见 [milestones/M4-real-backend.md](../milestones/M4-real-backend.md);后续 Stage 2~4 在 §1.4 跟踪。
- 🟡 **A 路径物料收集** 仍在业务方手里,跟踪表见 §2.4 / [M4-materials-acquisition-workpack.md](./M4-materials-acquisition-workpack.md)。
- ⚪ **C 路径** M3 未启动,等业务方决定是否插队。

### 2.2 `Backend-API-Spec_v0.1.yaml` 的解锁触发

当前推后理由:手写 OpenAPI YAML 与 §6 完全重复,信息密度低。
解锁触发条件(任一):
- FastAPI 骨架代码已落,可跑 `python -c "import app.main; print(app.main.app.openapi())"` 导出
- 业务方对外**提前**披露 API 给第三方(如客户的 SaaS / 经销商) — 这种情况需要手写 YAML

### 2.3 M3 vs M4 路标顺序(roadmap 一直挂着)

| 路径 | 含义 | 适合时机 |
|---|---|---|
| **先 M3** | 把后台 11 页面 mock 完整,再一起接真后端 | 业务方需要"全功能演示"路演 |
| **先 M4** | 现在就铺真后端,后台页面以后再补 | 业务方需要数据真存进去 / 真鉴定真出报告 |

未决。

### 2.4 M4 实施前还需要业务方提供的物料

🟡 **2026-05-23 已展开为工作包**:[M4-materials-acquisition-workpack.md](./M4-materials-acquisition-workpack.md)(12 项执行卡 + 关键路径 + RAM/KMS/ICP/短信模板)。每周一同步状态;阻塞抬到本节。

- [x] M-01 阿里云主账号 access(项目方负责人)✅ 2026-06-01 完成
- [ ] M-02 工程师子账号 + RAM 策略(ops)
- [ ] M-03 Azure 订阅 + OpenAI 资源 ownership ⚠️ **新关键路径最长 7-14 天**(项目方 + AI 工程接口人)
- ~~[ ] M-04 域名 + ICP 备案~~ 🚫 **已废弃 2026-05-26** — 决议改 HK 前端节点(M-13),工信部 ICP 不再需要
- [ ] M-05 阿里云短信签名审核(ops)
- [ ] M-06 短信模板审核(ops)
- [ ] M-07 OSS Bucket 创建(ops + tech lead)
- [ ] M-08 私调 Azure deployment 名 — M4 不卡,用 `gpt-4o-mini` 顶
- [ ] M-09 KMS CMK + Secret 入库(ops + DevOps)
- [ ] M-10 真实玉石 / 珠宝样本 — 滚动收集,不卡上线但卡 AI 评测
- [ ] M-11 监控告警通道(ops)
- [ ] M-12 跳板机 SSH 公钥白名单(tech lead)
- [ ] **M-13 HK 前端节点选型 + 域名 DNS 接管**(新增 2026-05-26,替代 M-04;项目方 + tech lead;1-3 天)

### 2.5 AI 工程那一脚的接手时机

`skills/ai-integration-engineer.md` 已就位,但**何时切**还没说:
- 选项 1:M4 后端实施完成、`LLMClient` stub 已落,再由 AI 工程进场填实
- 选项 2:M4 与 AI 并行(各自一个分支),最后合
- 选项 3:同一个代理身份切换(同一个人 / 同一个 AI 代理串行扮演两个角色)

未决。

### 2.6 M4 与前端的合流方式

Backend-Architecture §14 已给方案(双写期 → 关 mock route → 删 mock json),但**双写期的具体灰度策略**(按用户 / 按接口 / 按比例)未拍板。

---

## 三、参考索引(避免重读长文档)

- 已拍板决议表:[Backend-Architecture_v0.1.md §16](../Backend-Architecture_v0.1.md)
- 跨云拓扑速记:[Backend-Architecture_v0.1.md §16.1 + §9.7](../Backend-Architecture_v0.1.md)
- 后端目录结构:[Backend-Architecture_v0.1.md §4.1](../Backend-Architecture_v0.1.md)
- `LLMClient` Protocol 与 Azure stub:[Backend-Architecture_v0.1.md §9.3](../Backend-Architecture_v0.1.md)
- M4 验收 Checklist:[Backend-Architecture_v0.1.md §15](../Backend-Architecture_v0.1.md)
- 跨会话长期记忆:`.claude/projects/-Users-mgong-PycharmProjects-ZhuBaoTest/memory/`
  - `yaoqi-backend-stack` / `yaoqi-deployment-topology` / `yaoqi-membership-tiers`

---

## 维护规则

1. **新结论拍板**:从 §二 移到 §一,带日期(`(2026-MM-DD 拍板)`)
2. **新开放议题**:加进 §二,标明等谁、为什么没决
3. **文档关闭**:M4 实施开工后,可整体迁到 `docs/milestones/M4-real-backend.md`,本文件归档或删除
4. 不要在这里复制 Backend-Architecture 的细节 — 只放**决策**与**未决项**,长文继续在 §三 链回去
